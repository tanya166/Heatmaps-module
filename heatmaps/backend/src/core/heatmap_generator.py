from datetime import datetime, timedelta
from ..database.connection import sync_zone_events, sync_hourly_heatmaps, sync_daily_heatmaps, sync_zones

class HeatmapGenerator:
    def __init__(self, store_id):
        self.store_id = store_id
    
    def generate_hourly_heatmaps(self):
        """Generate hourly heatmap aggregations"""
        print(f"Generating hourly heatmaps for store {self.store_id}")
        
        # Get all events
        all_events = list(sync_zone_events.find({
            'store_id': self.store_id,
            'event_type': 'exit',
            'is_valid_visit': True
        }))
        
        if not all_events:
            print("No valid visit events found")
            return []
        
        # Get time range
        timestamps = [event['timestamp'] for event in all_events]
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        # Round to hour boundaries
        start_hour = start_time.replace(minute=0, second=0, microsecond=0)
        end_hour = end_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        # Get all zones
        all_zones = list(sync_zones.find({}))
        zone_map = {str(z['_id']): z for z in all_zones}
        
        hourly_heatmaps = []
        current_hour = start_hour
        
        while current_hour < end_hour:
            next_hour = current_hour + timedelta(hours=1)
            
            # Filter events in this hour
            hour_events = [
                e for e in all_events
                if current_hour <= e['timestamp'] < next_hour
            ]
            
            # Group by zone
            zone_events = {}
            for event in hour_events:
                zone_id = event['zone_id']
                if zone_id not in zone_events:
                    zone_events[zone_id] = []
                zone_events[zone_id].append(event)
            
            # Create heatmap for each zone
            for zone_id, events in zone_events.items():
                zone = zone_map.get(zone_id)
                if not zone:
                    continue
                
                visit_count = len(events)
                unique_visitors = len(set(e['person_id'] for e in events))
                dwell_times = [e['dwell_time'] for e in events if e.get('dwell_time')]
                
                total_dwell = sum(dwell_times) if dwell_times else 0.0
                avg_dwell = total_dwell / len(dwell_times) if dwell_times else 0.0
                crowd_density = visit_count / 60.0  # visits per minute
                
                heatmap = {
                    'store_id': self.store_id,
                    'zone_id': zone_id,
                    'zone_name': zone.get('name', zone.get('zone_identifier')),
                    'camera_id': zone['camera_id'],
                    'hour_start': current_hour,
                    'hour_end': next_hour,
                    'visit_count': visit_count,
                    'unique_visitors': unique_visitors,
                    'total_dwell_time': round(total_dwell, 2),
                    'avg_dwell_time': round(avg_dwell, 2),
                    'crowd_density': round(crowd_density, 4),
                    'created_at': datetime.utcnow()
                }
                
                sync_hourly_heatmaps.insert_one(heatmap)
                hourly_heatmaps.append(heatmap)
                
                print(f"  Hour {current_hour.hour:02d}:00 - Zone '{zone.get('name')}': {visit_count} visits")
            
            current_hour = next_hour
        
        print(f"Generated {len(hourly_heatmaps)} hourly heatmaps")
        return hourly_heatmaps
    
    def generate_daily_heatmaps(self):
        """Generate daily summary heatmaps"""
        print(f"Generating daily heatmaps for store {self.store_id}")
        
        # Get all hourly heatmaps
        hourly_heatmaps = list(sync_hourly_heatmaps.find({'store_id': self.store_id}))
        
        if not hourly_heatmaps:
            print("No hourly heatmaps found")
            return []
        
        # Group by zone
        zone_hourly_data = {}
        for heatmap in hourly_heatmaps:
            zone_id = heatmap['zone_id']
            if zone_id not in zone_hourly_data:
                zone_hourly_data[zone_id] = []
            zone_hourly_data[zone_id].append(heatmap)
        
        # Get date range
        dates = set()
        for heatmap in hourly_heatmaps:
            dates.add(heatmap['hour_start'].date())
        
        daily_heatmaps = []
        
        for date in dates:
            date_start = datetime.combine(date, datetime.min.time())
            date_end = datetime.combine(date, datetime.max.time())
            
            for zone_id, hourly_data in zone_hourly_data.items():
                # Filter for this date
                day_data = [
                    h for h in hourly_data
                    if date_start <= h['hour_start'] <= date_end
                ]
                
                if not day_data:
                    continue
                
                # Aggregate
                total_visits = sum(h['visit_count'] for h in day_data)
                
                # Get unique visitors from events
                zone_events = list(sync_zone_events.find({
                    'store_id': self.store_id,
                    'zone_id': zone_id,
                    'event_type': 'exit',
                    'is_valid_visit': True,
                    'timestamp': {'$gte': date_start, '$lte': date_end}
                }))
                unique_visitors = len(set(e['person_id'] for e in zone_events))
                
                total_dwell = sum(h['total_dwell_time'] for h in day_data)
                avg_dwell = total_dwell / total_visits if total_visits > 0 else 0.0
                
                # Find peak hour
                max_hour_data = max(day_data, key=lambda h: h['visit_count'])
                peak_hour = max_hour_data['hour_start'].hour
                max_hourly_crowd = max_hour_data['visit_count']
                
                # Calculate crowd density (average visits per hour)
                hours_active = len(day_data)
                crowd_density = total_visits / hours_active if hours_active > 0 else 0.0
                
                # Engagement rate from events
                all_zone_exits = list(sync_zone_events.find({
                    'store_id': self.store_id,
                    'zone_id': zone_id,
                    'event_type': 'exit',
                    'timestamp': {'$gte': date_start, '$lte': date_end}
                }))
                pass_through = len([e for e in all_zone_exits if not e['is_valid_visit']])
                engagement_rate = (total_visits / (total_visits + pass_through) * 100) if (total_visits + pass_through) > 0 else 0.0
                
                daily_heatmap = {
                    'store_id': self.store_id,
                    'zone_id': zone_id,
                    'zone_name': day_data[0]['zone_name'],
                    'camera_id': day_data[0]['camera_id'],
                    'date': date_start,
                    'total_visits': total_visits,
                    'unique_visitors': unique_visitors,
                    'total_dwell_time': round(total_dwell, 2),
                    'avg_dwell_time': round(avg_dwell, 2),
                    'max_hourly_crowd': max_hourly_crowd,
                    'peak_hour': peak_hour,
                    'crowd_density': round(crowd_density, 2),
                    'engagement_rate': round(engagement_rate, 2),
                    'created_at': datetime.utcnow()
                }
                
                sync_daily_heatmaps.insert_one(daily_heatmap)
                daily_heatmaps.append(daily_heatmap)
                
                print(f"  Zone '{day_data[0]['zone_name']}': {total_visits} visits, peak at {peak_hour}:00")
        
        print(f"Generated {len(daily_heatmaps)} daily heatmaps")
        return daily_heatmaps