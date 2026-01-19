# app/models/data_models.py

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
from datetime import datetime

# --- A. CORE DATA MODELS (Used by /events/filtered) ---

class Geometry(BaseModel):
    """GeoJSON structure for map plotting."""
    type: str = "Point"
    coordinates: List[float] # [Longitude, Latitude]

class DisasterEvent(BaseModel):
    """The full consolidated event document structure."""
    event_id: str
    classification_type: str
    location_district: str
    location_state: str
    start_time: datetime
    most_recent_report: datetime
    geometry: Geometry
    total_posts_count: int
    related_post_ids: List[str]

    # Allows MongoDB document fields to be accessed like Pydantic fields
    # class Config:
    #    from_attributes = True
    model_config = ConfigDict(from_attributes=True)


# --- B. ANALYTICS MODELS (Used by /analytics/global and /analytics/filtered) ---

class TypeCount(BaseModel):
    type: str
    frequency: int

class DistrictRanking(BaseModel):
    district: str
    event_count: int

class MonthlyEvent(BaseModel):
    year: int
    month: int
    total_events: int
    
class SentimentCount(BaseModel):
    label: str
    count: int

class GlobalAnalytics(BaseModel):
    """The structure for the single master analytics document."""
    timestamp: datetime
    type_counts: List[TypeCount]
    district_ranking: List[DistrictRanking]
    monthly_events: List[MonthlyEvent]
    sentiment_counts: List[SentimentCount]

class KeywordTrend(BaseModel):
    keyword: str
    frequency: int
    
    # class Config:
    #    from_attributes = True
    model_config = ConfigDict(from_attributes=True)
