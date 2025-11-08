from datetime import datetime, timedelta
from ..utils.geometry import point_in_polygon, calculate_bbox_center

class ZoneManager:
    def __init__(self, zones, visit_timeout_seconds=300):
        self.zones = zones
        self.active_visits = {}
        self.visit_timeout_seconds = visit_timeout_seconds  # 5 minutes default
        
    def clean_stale_visits(self, current_timestamp):
        """Remove visits that haven't been seen for longer than timeout period"""
        stale_visits = []
        
        for person_id, visit_data in self.active_visits.items():
            last_seen = visit_data['last_seen']
            time_since_seen = (current_timestamp - last_seen).total_seconds()
            
            if time_since_seen > self.visit_timeout_seconds:
                stale_visits.append(person_id)
        
        # Generate exit events for stale visits
        events = []
        for person_id in stale_visits:
            visit_data = self.active_visits[person_id]
            zone_id = visit_data['zone_id']
            entry_time = visit_data['entry_time']
            last_seen = visit_data['last_seen']
            
            # Calculate dwell time from entry to last seen
            dwell_time = (last_seen - entry_time).total_seconds()
            
            # Find the zone
            zone = next((z for z in self.zones if z['_id'] == zone_id), None)
            
            if zone:
                minimum_threshold = zone.get('minimum_dwell_threshold', 5)
                is_valid = dwell_time >= minimum_threshold
                
                exit_event = {
                    'zone_id': str(zone_id),
                    'camera_id': zone['camera_id'],
                    'person_id': person_id,
                    'event_type': 'exit',
                    'timestamp': last_seen,  # Use last seen time, not current time
                    'dwell_time': dwell_time,
                    'is_valid_visit': is_valid,
                    'rejection_reason': None if is_valid else "stale_visit_timeout"
                }
                events.append(exit_event)
            
            # Remove from active visits
            del self.active_visits[person_id]
        
        if stale_visits:
            print(f"Cleaned {len(stale_visits)} stale visits from ZoneManager")
        
        return events
        
    def check_zones(self, person_id, bbox, timestamp):
        """Check zone entries/exits and clean stale visits periodically"""
        events = []
        
        # Clean stale visits every check (minimal overhead)
        stale_events = self.clean_stale_visits(timestamp)
        events.extend(stale_events)
        
        person_center = calculate_bbox_center(bbox)
        
        current_zone = None
        for zone in self.zones:
            if point_in_polygon(person_center, zone['polygon']):
                current_zone = zone
                break
        
        if person_id in self.active_visits:
            previous_zone_id = self.active_visits[person_id]['zone_id']
            
            if current_zone and current_zone['_id'] == previous_zone_id:
                # Still in same zone, update last seen
                self.active_visits[person_id]['last_seen'] = timestamp
            else:
                # Exited previous zone
                entry_time = self.active_visits[person_id]['entry_time']
                dwell_time = (timestamp - entry_time).total_seconds()
                
                previous_zone = next((z for z in self.zones if z['_id'] == previous_zone_id), None)
                
                if previous_zone:
                    minimum_threshold = previous_zone.get('minimum_dwell_threshold', 5)
                    is_valid = dwell_time >= minimum_threshold
                    
                    exit_event = {
                        'zone_id': str(previous_zone_id),
                        'camera_id': previous_zone['camera_id'],
                        'person_id': person_id,
                        'event_type': 'exit',
                        'timestamp': timestamp,
                        'dwell_time': dwell_time,
                        'is_valid_visit': is_valid,
                        'rejection_reason': None if is_valid else "below_minimum_dwell"
                    }
                    events.append(exit_event)
                
                del self.active_visits[person_id]
                
                # Entered new zone
                if current_zone:
                    entry_event = {
                        'zone_id': str(current_zone['_id']),
                        'camera_id': current_zone['camera_id'],
                        'person_id': person_id,
                        'event_type': 'entry',
                        'timestamp': timestamp,
                        'dwell_time': None,
                        'is_valid_visit': False,
                        'rejection_reason': None
                    }
                    events.append(entry_event)
                    
                    self.active_visits[person_id] = {
                        'zone_id': current_zone['_id'],
                        'entry_time': timestamp,
                        'last_seen': timestamp
                    }
        
        elif current_zone:
            # New entry into a zone
            entry_event = {
                'zone_id': str(current_zone['_id']),
                'camera_id': current_zone['camera_id'],
                'person_id': person_id,
                'event_type': 'entry',
                'timestamp': timestamp,
                'dwell_time': None,
                'is_valid_visit': False,
                'rejection_reason': None
            }
            events.append(entry_event)
            
            self.active_visits[person_id] = {
                'zone_id': current_zone['_id'],
                'entry_time': timestamp,
                'last_seen': timestamp
            }
        
        return events
    
    def finalize_all_visits(self, final_timestamp):
        """Finalize all active visits at the end of video processing"""
        events = []
        
        for person_id, visit_data in list(self.active_visits.items()):
            zone_id = visit_data['zone_id']
            entry_time = visit_data['entry_time']
            dwell_time = (final_timestamp - entry_time).total_seconds()
            
            zone = next((z for z in self.zones if z['_id'] == zone_id), None)
            
            if zone:
                minimum_threshold = zone.get('minimum_dwell_threshold', 5)
                is_valid = dwell_time >= minimum_threshold
                
                exit_event = {
                    'zone_id': str(zone_id),
                    'camera_id': zone['camera_id'],
                    'person_id': person_id,
                    'event_type': 'exit',
                    'timestamp': final_timestamp,
                    'dwell_time': dwell_time,
                    'is_valid_visit': is_valid,
                    'rejection_reason': None if is_valid else "below_minimum_dwell"
                }
                events.append(exit_event)
        
        self.active_visits.clear()
        return events
    
    def get_active_visits_count(self):
        """Get the number of currently active visits"""
        return len(self.active_visits)
    
    def get_zone_occupancy(self):
        """Get current occupancy count per zone"""
        occupancy = {}
        for visit_data in self.active_visits.values():
            zone_id = str(visit_data['zone_id'])
            occupancy[zone_id] = occupancy.get(zone_id, 0) + 1
        return occupancy
    
    def clear_active_visits(self):
        """Manually clear all active visits (use with caution)"""
        self.active_visits.clear()
        print("All active visits cleared from ZoneManager")