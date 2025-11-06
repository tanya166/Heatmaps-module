from datetime import datetime
from ..database.connection import sync_zone_events, sync_daily_insights, sync_daily_heatmaps

class InsightsGenerator:
    def __init__(self, store_id):
        self.store_id = store_id
    
    def generate_daily_insights(self):
        """Generate end-of-day insights summary"""
        print(f"Generating daily insights for store {self.store_id}")
        
        # Get all daily heatmaps
        daily_heatmaps = list(sync_daily_heatmaps.find({'store_id': self.store_id}))
        
        if not daily_heatmaps:
            print("No daily heatmaps found")
            return None
        
        # Get unique date
        dates = set(h['date'] for h in daily_heatmaps)
        
        insights_list = []
        
        for date in dates:
            date_heatmaps = [h for h in daily_heatmaps if h['date'] == date]
            
            # Total unique customers across all zones
            all_events = list(sync_zone_events.find({
                'store_id': self.store_id,
                'is_valid_visit': True,
                'timestamp': {
                    '$gte': date,
                    '$lt': datetime.combine(date.date(), datetime.max.time())
                }
            }))
            total_unique_customers = len(set(e['person_id'] for e in all_events))
            
            # Zone insights
            zone_insights = []
            for heatmap in date_heatmaps:
                zone_insight = {
                    'zone_id': heatmap['zone_id'],
                    'zone_name': heatmap['zone_name'],
                    'zone_type': 'retail',
                    'total_visits': heatmap['total_visits'],
                    'unique_visitors': heatmap['unique_visitors'],
                    'avg_dwell_time': heatmap['avg_dwell_time'],
                    'crowd_density': heatmap['crowd_density'],
                    'engagement_rate': heatmap['engagement_rate'],
                    'peak_hour': heatmap['peak_hour']
                }
                zone_insights.append(zone_insight)
            
            # Sort by visits to find hottest/coldest
            sorted_zones = sorted(zone_insights, key=lambda x: x['total_visits'], reverse=True)
            
            hottest_zone = {
                'zone_name': sorted_zones[0]['zone_name'],
                'visits': sorted_zones[0]['total_visits'],
                'avg_dwell_time': sorted_zones[0]['avg_dwell_time'],
                'crowd_density': sorted_zones[0]['crowd_density']
            } if sorted_zones else None
            
            coldest_zone = {
                'zone_name': sorted_zones[-1]['zone_name'],
                'visits': sorted_zones[-1]['total_visits'],
                'avg_dwell_time': sorted_zones[-1]['avg_dwell_time'],
                'crowd_density': sorted_zones[-1]['crowd_density']
            } if sorted_zones else None
            
            # Average store dwell time
            total_dwell = sum(z['avg_dwell_time'] * z['total_visits'] for z in zone_insights)
            total_visits = sum(z['total_visits'] for z in zone_insights)
            avg_store_dwell = total_dwell / total_visits if total_visits > 0 else 0.0
            
            # Peak hour across all zones
            hour_visits = {}
            for heatmap in date_heatmaps:
                hour = heatmap['peak_hour']
                if hour not in hour_visits:
                    hour_visits[hour] = 0
                hour_visits[hour] += heatmap['max_hourly_crowd']
            
            peak_hour = max(hour_visits.items(), key=lambda x: x[1]) if hour_visits else (None, 0)
            
            # Create insights document
            insights = {
                'store_id': self.store_id,
                'date': date,
                'total_unique_customers': total_unique_customers,
                'total_zones_analyzed': len(zone_insights),
                'zone_insights': zone_insights,
                'hottest_zone': hottest_zone,
                'coldest_zone': coldest_zone,
                'avg_store_dwell_time': round(avg_store_dwell, 2),
                'peak_hour': peak_hour[0],
                'peak_hour_customers': peak_hour[1],
                'created_at': datetime.utcnow()
            }
            
            sync_daily_insights.insert_one(insights)
            insights_list.append(insights)
            
            print(f"\n{'='*60}")
            print(f"DAILY INSIGHTS SUMMARY - {date.strftime('%Y-%m-%d')}")
            print(f"{'='*60}")
            print(f"Total Unique Customers: {total_unique_customers}")
            print(f"Total Zones Analyzed: {len(zone_insights)}")
            print(f"Average Store Dwell Time: {avg_store_dwell:.2f} seconds")
            print(f"Peak Hour: {peak_hour[0]}:00 with {peak_hour[1]} customers")
            print(f"\nHottest Zone: {hottest_zone['zone_name']} ({hottest_zone['visits']} visits)")
            print(f"Coldest Zone: {coldest_zone['zone_name']} ({coldest_zone['visits']} visits)")
            print(f"\nZone-wise Details:")
            for zone in sorted_zones:
                print(f"  - {zone['zone_name']}: {zone['total_visits']} visits, "
                      f"{zone['avg_dwell_time']:.2f}s avg dwell, "
                      f"{zone['crowd_density']:.2f} visits/hour")
            print(f"{'='*60}\n")
        
        return insights_list