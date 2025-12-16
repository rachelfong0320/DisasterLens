import logging
from datetime import timedelta, datetime, timezone
from typing import Dict, Any, Optional
from pymongo.database import Database
from pymongo.collection import Collection
from bson.objectid import ObjectId
# We only import the output collection name here, as the input collection 
# is handled by the calling function (run_master_event_consolidator).
from core.db.disaster_event_saver import get_mongo_client
from core.config import DISASTER_EVENTS_COLLECTION, DISASTER_POSTS_COLLECTION, COMBINED_DB_NAME
from core.jobs.alert_generator import process_event_for_alerts

# --- CONFIGURATION (Ensuring timedelta is correctly defined) ---
TIME_WINDOW_HOURS = 24
TIME_WINDOW = timedelta(hours=TIME_WINDOW_HOURS)
DEFAULT_ALERT_COOLDOWN_MINUTES = 60
# ---------------------------------------------------------------

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_unique_event_id(post_type: str, post_district: str, post_time: datetime) -> str:
    """Generates a base unique ID for the event based on type, district, and date."""
    prefix = f"{post_type.upper()}-{post_district.replace(' ', '').upper()}-{post_time.strftime('%Y%m%d')}"
    return f"{prefix}-{post_time.strftime('%H%M%S')}"


def run_event_consolidation(db: Database, new_post_event: Dict[str, Any]) -> Optional[str]:
    """
    Checks if a new event_post belongs to an existing master event 
    based on Type, District, and Time Proximity. Updates or creates a master record.
    """
    
    master_collection: Collection = db[DISASTER_EVENTS_COLLECTION]
    
    post_id = new_post_event.get('post_id')
    event_type = new_post_event.get('disaster_type') 
    post_district = new_post_event.get('location', {}).get('district') 
    post_time: datetime = new_post_event.get('start_time')
    post_coordinates = new_post_event.get('location', {}).get('lat_lon') 

    if not all([post_id, event_type, post_district, post_time, post_coordinates]):
        logger.warning(f"Skipping consolidation for post {post_id}: Missing critical data.")
        return None

    post_time = post_time.replace(tzinfo=timezone.utc)
    
    # 2. Search for a Matching Existing Event (Type, District, and Time Proximity)
    search_query = {
        # FIX 4: Use the correct key for searching: disaster_type
        "classification_type": event_type,
        "location_district": post_district,
        "most_recent_report": { 
            "$gte": post_time - TIME_WINDOW,
            },
        }
    
    existing_master_event = master_collection.find_one(search_query)

    
    # 3. Decision Logic: UPDATE or CREATE
    if existing_master_event:
        # A. MATCH FOUND: Update the Existing Master Event
        event_id = existing_master_event["event_id"]
        
        existing_start_time = existing_master_event['start_time'].replace(tzinfo=timezone.utc)
        existing_recent_time = existing_master_event['most_recent_report'].replace(tzinfo=timezone.utc)
        
        # Calculate the new aggregated times
        new_start_time = min(existing_start_time, post_time) 
        new_recent_time = max(existing_recent_time, post_time) 

        # Check if this update actually advances the 'most_recent_report' time
        is_significant_update = new_recent_time > existing_recent_time
        
        update_operation = {
            "$set": {
                "start_time": new_start_time,           
                "most_recent_report": new_recent_time    
            },
            "$inc": { "total_posts_count": 1 },
            "$addToSet": { "related_post_ids": post_id } 
        }
        
        master_collection.update_one(
            {"_id": existing_master_event["_id"]},
            update_operation
        )
        logger.info(f"Post {post_id} linked to existing event: {event_id}")

        # --- ALERT GENERATION TRIGGER (Update) ---
        if is_significant_update:
             # Trigger alerts only if a new report time updates the event
            process_event_for_alerts(existing_master_event["_id"])
        # -----------------------------------------
        return event_id
        
    else:
        # B. NO MATCH FOUND: Create a Brand New Master Event
        
        event_id = _get_unique_event_id(event_type, post_district, post_time)
        
        new_master_event = {
            "event_id": event_id, 
            # Output key for the Master table
            "classification_type": event_type, 
            "location_district": post_district,
            "start_time": post_time, 
            "most_recent_report": post_time,
            "geometry": { 
                "type": "Point", 
                "coordinates": post_coordinates # Coordinates from location.lat_lon
            },
            "total_posts_count": 1,
            "related_post_ids": [post_id]
        }
        
        master_collection.insert_one(new_master_event)
        logger.info(f"Created new master event: {event_id}")

        # --- ALERT GENERATION TRIGGER (Creation) ---
        # A new event always triggers the first alert
        process_event_for_alerts(new_master_event["_id"])
        # -------------------------------------------
        return event_id

def run_master_event_consolidator():
    """Loops over all DISASTER_POSTS and runs consolidation to create master events."""
    client = get_mongo_client()
    if not client: return 0

    db = client[COMBINED_DB_NAME] # Connects to the main database
    
    # Input is the POSTS collection
    cursor = db[DISASTER_POSTS_COLLECTION].find() 
    
    count = 0
    for post in cursor:
        # Calls the function that handles one post (the logic you already wrote)
        run_event_consolidation(db, post) 
        count += 1
        
    client.close()
    return count