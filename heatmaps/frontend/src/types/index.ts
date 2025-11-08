export interface Store {
  _id: string;
  name: string;
  location?: string;
  created_at: string;
}

export interface Camera {
  _id: string;
  store_id: string;
  camera_identifier: string;
  name: string;
  video_source: string;
  resolution_width?: number;
  resolution_height?: number;
  fps?: number;
  status: string;
}

export interface Zone {
  _id: string;
  camera_id: string;
  zone_identifier: string;
  name: string;
  polygon: number[][];
  zone_type: string;
  color: string;
  minimum_dwell_threshold: number;
}

export interface HourlyHeatmap {
  _id: string;
  store_id: string;
  zone_id: string;
  zone_name: string;
  camera_id: string;
  hour_start: string;
  hour_end: string;
  visit_count: number;
  unique_visitors: number;
  total_dwell_time: number;
  avg_dwell_time: number;
  crowd_density: number;
}

export interface DailyHeatmap {
  _id: string;
  store_id: string;
  zone_id: string;
  zone_name: string;
  camera_id: string;
  date: string;
  total_visits: number;
  unique_visitors: number;
  total_dwell_time: number;
  avg_dwell_time: number;
  max_hourly_crowd: number;
  peak_hour: number;
  crowd_density: number;
  engagement_rate: number;
}

export interface ZoneInsight {
  zone_id: string;
  zone_name: string;
  zone_type: string;
  total_visits: number;
  unique_visitors: number;
  avg_dwell_time: number;
  crowd_density: number;
  engagement_rate: number;
  peak_hour: number;
}

export interface DailyInsights {
  _id: string;
  store_id: string;
  date: string;
  total_unique_customers: number;
  total_zones_analyzed: number;
  zone_insights: ZoneInsight[];
  hottest_zone: {
    zone_name: string;
    visits: number;
    avg_dwell_time: number;
    crowd_density: number;
  };
  coldest_zone: {
    zone_name: string;
    visits: number;
    avg_dwell_time: number;
    crowd_density: number;
  };
  avg_store_dwell_time: number;
  peak_hour: number;
  peak_hour_customers: number;
}

export interface ProcessingStatus {
  status: 'not_started' | 'processing' | 'completed' | 'error';
  message?: string;
  progress?: {
    [camera_id: string]: {
      name: string;
      progress: number;
    };
  };
  result?: {
    hourly_heatmaps: number;
    daily_heatmaps: number;
    insights_generated: number;
  };
}