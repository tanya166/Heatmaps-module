from datetime import datetime
from ..utils.geometry import point_in_polygon, calculate_bbox_center

class ZoneManager:
    def __init__(self, zones):
        self.zones = zones
        self.active_visits = {}
        
    def check_zones(self, person_id, bbox, timestamp):
        events = []
        person_center = calculate_bbox_center(bbox)
        
        current_zone = None
        for zone in self.zones:
            if point_in_polygon(person_center, zone['polygon']):
                current_zone = zone
                break
        
        if person_id in self.active_visits:
            previous_zone_id = self.active_visits[person_id]['zone_id']
            
            if current_zone and current_zone['_id'] == previous_zone_id:
                self.active_visits[person_id]['last_seen'] = timestamp
            else:
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