from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from ..config.settings import settings

# Async client for FastAPI
async_client = AsyncIOMotorClient(settings.mongodb_url)
async_db = async_client[settings.database_name]

# Sync client for processing
sync_client = MongoClient(settings.mongodb_url)
sync_db = sync_client[settings.database_name]

# Async collections
stores_collection = async_db.stores
cameras_collection = async_db.cameras
zones_collection = async_db.zones
zone_events_collection = async_db.zone_events
hourly_heatmaps_collection = async_db.hourly_heatmaps
daily_heatmaps_collection = async_db.daily_heatmaps
daily_insights_collection = async_db.daily_insights

# Sync collections
sync_stores = sync_db.stores
sync_cameras = sync_db.cameras
sync_zones = sync_db.zones
sync_zone_events = sync_db.zone_events
sync_hourly_heatmaps = sync_db.hourly_heatmaps
sync_daily_heatmaps = sync_db.daily_heatmaps
sync_daily_insights = sync_db.daily_insights

async def init_db():
    """Create indexes"""
    await cameras_collection.create_index("store_id")
    await zones_collection.create_index("camera_id")
    await zone_events_collection.create_index([("store_id", 1), ("timestamp", 1)])
    await zone_events_collection.create_index("zone_id")
    await zone_events_collection.create_index("person_id")
    await hourly_heatmaps_collection.create_index([("store_id", 1), ("hour_start", 1)])
    await daily_heatmaps_collection.create_index([("store_id", 1), ("date", 1)])
    await daily_insights_collection.create_index([("store_id", 1), ("date", 1)])
    print("Database indexes created")