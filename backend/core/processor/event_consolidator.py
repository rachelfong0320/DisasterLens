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
    master_collection: Collection = db[DISASTER_EVENTS_COLLECTION]
    
    post_id = new_post_event.get('post_id')
    event_type = new_post_event.get('disaster_type') 
    
    # 1. GET THE TIME SAFELY
    post_time = new_post_event.get('start_time')

    # 2. CONVERT STRING TO DATETIME IF NECESSARY
    if isinstance(post_time, str):
        try:
            # Handle Twitter format: "Fri Apr 11 13:57:55 +0000 2025"
            post_time = datetime.strptime(post_time, '%a %b %d %H:%M:%S +0000 %Y')
        except ValueError:
            try:
                # Handle ISO format: "2025-04-11T13:57:55Z"
                post_time = datetime.fromisoformat(post_time.replace('Z', '+00:00'))
            except:
                post_time = datetime.now(timezone.utc)

    # 3. ENSURE IT IS TIMEZONE AWARE (Prevent the 'str.replace' error)
    if isinstance(post_time, datetime):
        if post_time.tzinfo is None:
            post_time = post_time.replace(tzinfo=timezone.utc)
        else:
            post_time = post_time.astimezone(timezone.utc)
    else:
        post_time = datetime.now(timezone.utc)

    # 4. GET LOCATION SAFELY
    loc = new_post_event.get('location', {})
    post_district = loc.get('district', 'unknown').lower() 
    post_state = loc.get('state', 'unknown').lower()
    post_coordinates = loc.get('lat_lon')
    
    # --- SEARCH QUERY ---
    search_query = {
        "classification_type": event_type,
        "location_district": post_district,
        "most_recent_report": { "$gte": post_time - TIME_WINDOW },
    }
    
    existing_master_event = master_collection.find_one(search_query)

    if existing_master_event:
        event_id = existing_master_event["event_id"]
        
        # FIX: Handle existing DB dates safely too
        existing_start = existing_master_event['start_time']
        existing_recent = existing_master_event['most_recent_report']
        
        # Ensure existing times have timezone info for comparison
        if existing_start.tzinfo is None: existing_start = existing_start.replace(tzinfo=timezone.utc)
        if existing_recent.tzinfo is None: existing_recent = existing_recent.replace(tzinfo=timezone.utc)
        
        new_start_time = min(existing_start, post_time) 
        new_recent_time = max(existing_recent, post_time) 

        is_significant_update = new_recent_time > existing_recent
        
        update_operation = {
            "$set": {
                "start_time": new_start_time,           
                "most_recent_report": new_recent_time,
                "location_state": post_state,    
            },
            "$addToSet": { "related_post_ids": post_id } 
        }
        
        master_collection.update_one({"_id": existing_master_event["_id"]}, update_operation)
        
        # Aggregation Update for count
        master_collection.update_one(
            {"_id": existing_master_event["_id"]},
            [{"$set": {"total_posts_count": {"$size": "$related_post_ids"}}}]
        )

        if is_significant_update:
            process_event_for_alerts(existing_master_event["_id"])
        
        return event_id
        
    else:
        # CREATE NEW EVENT
        event_id = _get_unique_event_id(event_type, post_district, post_time)
        new_master_event = {
            "event_id": event_id, 
            "classification_type": event_type, 
            "location_district": post_district,
            "location_state": post_state,
            "start_time": post_time, 
            "most_recent_report": post_time,
            "geometry": { "type": "Point", "coordinates": post_coordinates or [0,0] },
            "total_posts_count": 1,
            "related_post_ids": [post_id]
        }
        inserted = master_collection.insert_one(new_master_event)
        process_event_for_alerts(inserted.inserted_id)
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