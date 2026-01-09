# backend/app/chatbot/chatbot_service.py
import os
import json
from datetime import datetime

def get_full_events_by_ids(db, event_ids: list):
    """
    Business logic to fetch and format events from MongoDB.
    """
    collection = db["disaster_events"]
    
    # Fetch all matching documents
    cursor = collection.find({"event_id": {"$in": event_ids}})
    events = list(cursor)
    
    # Data Transformation Logic
    for event in events:
        event["_id"] = str(event["_id"])
        
        # Format timestamps for Frontend (Leaflet/Charts) compatibility
        if "start_time" in event and hasattr(event["start_time"], "isoformat"):
            event["start_time"] = event["start_time"].isoformat()
            
        # Add derived fields needed by the map UI
        if "related_post_ids" in event:
            event["total_posts_count"] = len(event["related_post_ids"])
            
    return events