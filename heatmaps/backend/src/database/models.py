from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class Store(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Camera(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    store_id: str
    camera_identifier: str
    name: str
    video_source: str
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    fps: Optional[float] = None
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class Zone(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    camera_id: str
    zone_identifier: str
    name: str
    polygon: List[List[float]]
    zone_type: str
    color: str = "#FF5733"
    minimum_dwell_threshold: int = 5
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ZoneEvent(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    store_id: str
    camera_id: str
    zone_id: str
    person_id: str
    event_type: str
    timestamp: datetime
    dwell_time: Optional[float] = None
    is_valid_visit: bool = False
    rejection_reason: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class HourlyHeatmap(BaseModel):
    """Hourly heatmap aggregation"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    store_id: str
    zone_id: str
    zone_name: str
    camera_id: str
    hour_start: datetime  # Start of the hour
    hour_end: datetime    # End of the hour
    visit_count: int = 0
    unique_visitors: int = 0
    total_dwell_time: float = 0.0
    avg_dwell_time: float = 0.0
    crowd_density: float = 0.0  # visits per minute
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DailyHeatmap(BaseModel):
    """Daily summary heatmap"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    store_id: str
    zone_id: str
    zone_name: str
    camera_id: str
    date: datetime  # Date for this summary
    total_visits: int = 0
    unique_visitors: int = 0
    total_dwell_time: float = 0.0
    avg_dwell_time: float = 0.0
    max_hourly_crowd: int = 0  # Peak hour crowd
    peak_hour: Optional[int] = None  # Hour of day (0-23)
    crowd_density: float = 0.0  # Average visits per hour
    engagement_rate: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DailyInsights(BaseModel):
    """End-of-day insights summary"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    store_id: str
    date: datetime
    total_unique_customers: int = 0
    total_zones_analyzed: int = 0
    zone_insights: List[Dict] = []  # List of zone-level insights
    hottest_zone: Optional[Dict] = None
    coldest_zone: Optional[Dict] = None
    avg_store_dwell_time: float = 0.0
    peak_hour: Optional[int] = None
    peak_hour_customers: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}