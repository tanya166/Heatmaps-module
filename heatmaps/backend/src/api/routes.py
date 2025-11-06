from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import shutil
from datetime import datetime
from bson import ObjectId
import json

from ..database.connection import (
    init_db, stores_collection, cameras_collection, zones_collection,
    zone_events_collection, hourly_heatmaps_collection, 
    daily_heatmaps_collection, daily_insights_collection, sync_cameras
)
from ..database.models import Store, Camera, Zone
from ..video.processor import VideoProcessor
from ..config.settings import settings

app = FastAPI(title="Retail Heatmap API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

processing_status = {}

@app.on_event("startup")
async def startup_event():
    await init_db()
    print("Database initialized")

# ==================== Store Endpoints ====================

@app.post("/api/stores")
async def create_store(name: str = Form(...), location: str = Form(None)):
    """Create a new store."""
    store = Store(name=name, location=location)
    result = await stores_collection.insert_one(store.dict(by_alias=True, exclude={'id'}))
    
    return {
        "id": str(result.inserted_id),
        "name": name,
        "location": location,
        "message": "Store created successfully"
    }

@app.get("/api/stores")
async def list_stores():
    """List all stores."""
    stores = []
    async for store in stores_collection.find():
        store['_id'] = str(store['_id'])
        stores.append(store)
    return {"stores": stores}

@app.get("/api/stores/{store_id}")
async def get_store(store_id: str):
    """Get store details."""
    store = await stores_collection.find_one({"_id": ObjectId(store_id)})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    store['_id'] = str(store['_id'])
    return store

# ==================== Camera Endpoints ====================

@app.post("/api/stores/{store_id}/cameras")
async def upload_camera_video(
    store_id: str,
    camera_identifier: str = Form(...),
    name: str = Form(...),
    video: UploadFile = File(...)
):
    """Upload a video for a camera."""
    store = await stores_collection.find_one({"_id": ObjectId(store_id)})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    video_filename = f"{store_id}_{camera_identifier}_{video.filename}"
    video_path = os.path.join(UPLOAD_DIR, video_filename)
    
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
    
    import cv2
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    
    camera = Camera(
        store_id=store_id,
        camera_identifier=camera_identifier,
        name=name,
        video_source=video_path,
        resolution_width=width,
        resolution_height=height,
        fps=fps
    )
    
    result = await cameras_collection.insert_one(camera.dict(by_alias=True, exclude={'id'}))
    
    return {
        "id": str(result.inserted_id),
        "camera_identifier": camera_identifier,
        "name": name,
        "video_path": video_path,
        "message": "Video uploaded successfully"
    }

@app.get("/api/stores/{store_id}/cameras")
async def list_cameras(store_id: str):
    """List all cameras for a store."""
    cameras = []
    async for camera in cameras_collection.find({"store_id": store_id}):
        camera['_id'] = str(camera['_id'])
        cameras.append(camera)
    return {"cameras": cameras}

# ==================== Zone Endpoints ====================

@app.post("/api/cameras/{camera_id}/zones")
async def create_zone(
    camera_id: str,
    zone_identifier: str = Form(...),
    name: str = Form(...),
    polygon: str = Form(...),
    zone_type: str = Form(...),
    color: str = Form("#FF5733"),
    minimum_dwell_threshold: int = Form(5)
):
    """Create a zone for a camera."""
    try:
        polygon_coords = json.loads(polygon)
    except:
        raise HTTPException(status_code=400, detail="Invalid polygon format")
    
    camera = await cameras_collection.find_one({"_id": ObjectId(camera_id)})
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    
    zone = Zone(
        camera_id=camera_id,
        zone_identifier=zone_identifier,
        name=name,
        polygon=polygon_coords,
        zone_type=zone_type,
        color=color,
        minimum_dwell_threshold=minimum_dwell_threshold
    )
    
    result = await zones_collection.insert_one(zone.dict(by_alias=True, exclude={'id'}))
    
    return {
        "id": str(result.inserted_id),
        "zone_identifier": zone_identifier,
        "name": name,
        "message": "Zone created successfully"
    }

@app.get("/api/cameras/{camera_id}/zones")
async def list_zones(camera_id: str):
    """List all zones for a camera."""
    zones = []
    async for zone in zones_collection.find({"camera_id": camera_id}):
        zone['_id'] = str(zone['_id'])
        zones.append(zone)
    return {"zones": zones}

@app.delete("/api/zones/{zone_id}")
async def delete_zone(zone_id: str):
    """Delete a zone."""
    result = await zones_collection.delete_one({"_id": ObjectId(zone_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Zone not found")
    
    return {"message": "Zone deleted successfully"}

# ==================== Processing Endpoints ====================

def process_videos_background(store_id: str):
    """Background task to process all videos."""
    try:
        processing_status[store_id] = {
            "status": "processing",
            "progress": {},
            "message": "Processing videos..."
        }
        
        cameras = list(sync_cameras.find({"store_id": store_id}))
        
        if not cameras:
            processing_status[store_id] = {
                "status": "error",
                "message": "No cameras found for store"
            }
            return
        
        for camera in cameras:
            camera_id = str(camera['_id'])
            processing_status[store_id]["progress"][camera_id] = {
                "name": camera['name'],
                "progress": 0.0
            }
        
        processor = VideoProcessor(
            settings.detector_model_path,
            settings.reid_model_path,
            store_id
        )
        
        def update_progress(camera_id, progress):
            if store_id in processing_status:
                processing_status[store_id]["progress"][camera_id]["progress"] = progress
        
        # Process all videos and generate insights
        result = processor.process_all_and_generate_insights(cameras, update_progress)
        
        processing_status[store_id] = {
            "status": "completed",
            "message": "Processing complete!",
            "result": {
                "hourly_heatmaps": result['hourly_heatmaps'],
                "daily_heatmaps": result['daily_heatmaps'],
                "insights_generated": len(result['insights']) if result['insights'] else 0
            }
        }
        
    except Exception as e:
        processing_status[store_id] = {
            "status": "error",
            "message": f"Error during processing: {str(e)}"
        }
        print(f"Error processing store {store_id}: {e}")
        import traceback
        traceback.print_exc()

@app.post("/api/stores/{store_id}/process")
async def start_processing(store_id: str, background_tasks: BackgroundTasks):
    """Start processing all videos for a store."""
    store = await stores_collection.find_one({"_id": ObjectId(store_id)})
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    if store_id in processing_status and processing_status[store_id]["status"] == "processing":
        raise HTTPException(status_code=400, detail="Processing already in progress")
    
    background_tasks.add_task(process_videos_background, store_id)
    
    return {
        "message": "Processing started",
        "store_id": store_id
    }

@app.get("/api/stores/{store_id}/processing-status")
async def get_processing_status(store_id: str):
    """Get current processing status."""
    if store_id not in processing_status:
        return {
            "status": "not_started",
            "message": "Processing has not been started"
        }
    
    return processing_status[store_id]

# ==================== Heatmap Endpoints ====================

@app.get("/api/stores/{store_id}/heatmaps/hourly")
async def get_hourly_heatmaps(store_id: str):
    """Get hourly heatmaps for a store."""
    heatmaps = []
    async for heatmap in hourly_heatmaps_collection.find({"store_id": store_id}):
        heatmap['_id'] = str(heatmap['_id'])
        heatmaps.append(heatmap)
    
    if not heatmaps:
        raise HTTPException(status_code=404, detail="No hourly heatmaps found. Please process videos first.")
    
    return {"heatmaps": heatmaps}

@app.get("/api/stores/{store_id}/heatmaps/daily")
async def get_daily_heatmaps(store_id: str):
    """Get daily heatmaps for a store."""
    heatmaps = []
    async for heatmap in daily_heatmaps_collection.find({"store_id": store_id}):
        heatmap['_id'] = str(heatmap['_id'])
        heatmaps.append(heatmap)
    
    if not heatmaps:
        raise HTTPException(status_code=404, detail="No daily heatmaps found. Please process videos first.")
    
    return {"heatmaps": heatmaps}

# ==================== Insights Endpoints ====================

@app.get("/api/stores/{store_id}/insights")
async def get_daily_insights(store_id: str):
insights = []
    async for insight in daily_insights_collection.find({"store_id": store_id}):
        insight['_id'] = str(insight['_id'])
        insights.append(insight)
    
    if not insights:
        raise HTTPException(status_code=404, detail="No insights found. Please process videos first.")
    
    return {"insights": insights}

# ==================== Health Check ====================

@app.get("/")
async def root():
    return {
        "message": "Retail Heatmap API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}