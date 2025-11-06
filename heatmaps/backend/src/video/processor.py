import cv2
from datetime import datetime, timedelta
from ..database.connection import sync_zones, sync_zone_events
from ..detection.openvino_detector import OpenVINOPersonDetector
from ..reid.openvino_reid import OpenVINOReID
from ..core.zone_manager import ZoneManager
from ..core.heatmap_generator import HeatmapGenerator
from ..core.insights_generator import InsightsGenerator

class VideoProcessor:
    def __init__(self, detector_model_path, reid_model_path, store_id):
        self.detector = OpenVINOPersonDetector(detector_model_path)
        self.reid = OpenVINOReID(reid_model_path)
        self.store_id = store_id
        self.zone_managers = {}
        
    def load_zones_for_camera(self, camera_id):
        """Load zones from MongoDB for a camera."""
        zones = list(sync_zones.find({'camera_id': camera_id}))
        for zone in zones:
            zone['_id'] = str(zone['_id'])
            zone['camera_id'] = str(zone['camera_id'])
        return zones
    
    def process_video(self, camera_id, video_path, progress_callback=None):
        """Process a single video file."""
        print(f"Processing video for camera {camera_id}: {video_path}")
        
        zones = self.load_zones_for_camera(camera_id)
        if not zones:
            print(f"No zones defined for camera {camera_id}, skipping...")
            return
        
        zone_manager = ZoneManager(zones)
        self.zone_managers[camera_id] = zone_manager
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        frame_count = 0
        start_time = datetime.utcnow()
        
        print(f"Video FPS: {fps}, Total frames: {total_frames}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            timestamp = start_time + timedelta(seconds=frame_count / fps)
            
            detections = self.detector.detect(frame)
            
            for detection in detections:
                bbox = detection['bbox']
                person_id = self.reid.identify_person(frame, bbox)
                
                events = zone_manager.check_zones(person_id, bbox, timestamp)
                
                for event in events:
                    event['store_id'] = str(self.store_id)
                    sync_zone_events.insert_one(event)
            
            frame_count += 1
            
            if progress_callback and frame_count % 30 == 0:
                progress = (frame_count / total_frames) * 100
                progress_callback(camera_id, progress)
        
        final_timestamp = start_time + timedelta(seconds=total_frames / fps)
        final_events = zone_manager.finalize_all_visits(final_timestamp)
        
        for event in final_events:
            event['store_id'] = str(self.store_id)
            sync_zone_events.insert_one(event)
        
        cap.release()
        print(f"Finished processing video for camera {camera_id}")
        
        if progress_callback:
            progress_callback(camera_id, 100.0)
    
    def process_all_and_generate_insights(self, cameras, progress_callback=None):
        """Process all videos and generate heatmaps + insights"""
        print(f"\nStarting video processing for {len(cameras)} cameras...")
        
        # Process each video
        for camera in cameras:
            camera_id = str(camera['_id'])
            video_path = camera['video_source']
            self.process_video(camera_id, video_path, progress_callback)
        
        print("\nAll videos processed. Generating heatmaps and insights...")
        
        # Generate hourly heatmaps
        heatmap_gen = HeatmapGenerator(self.store_id)
        hourly_heatmaps = heatmap_gen.generate_hourly_heatmaps()
        
        # Generate daily heatmaps
        daily_heatmaps = heatmap_gen.generate_daily_heatmaps()
        
        # Generate daily insights
        insights_gen = InsightsGenerator(self.store_id)
        insights = insights_gen.generate_daily_insights()
        
        print("\n✅ Processing complete!")
        return {
            'hourly_heatmaps': len(hourly_heatmaps),
            'daily_heatmaps': len(daily_heatmaps),
            'insights': insights
        }