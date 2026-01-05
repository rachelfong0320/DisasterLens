from core.db.disaster_event_saver import get_mongo_client, save_disaster_event
import logging
from datetime import datetime, timezone
from typing import List, Dict, Union
from core.config import POSTS_COLLECTION, INCIDENT_COLLECTION, SENTIMENT_COLLECTION, COMBINED_DB_NAME

logger = logging.getLogger(__name__)

def transform_post_to_event(post_id: str, db) -> Union[Dict, None]:
    """
    Extracts data from all intermediate tables and transforms it 
    into the final structured DisasterEvent document.
    """
    
    # 1. EXTRACT: Fetch all related documents using the postId
    post = db[POSTS_COLLECTION].find_one({"postId": post_id})
    classification = db[INCIDENT_COLLECTION].find_one({"post_id": post_id})
    sentiment = db[SENTIMENT_COLLECTION].find_one({"post_id": post_id})

    geo = post.get("geo_data")

    # Basic data integrity check: must have all core components
    if not all([post, classification, geo, sentiment]):
        logger.warning(f"Missing core data for Post ID {post_id} (Post:{'Yes' if post else 'No'}, Class:{'Yes' if classification else 'No'}, Sent:{'Yes' if sentiment else 'No'}, Geo:{'Yes' if geo else 'No'}). Skipping event creation.")
        return None

    # 2. TRANSFORM: Map fields to the FINAL DisasterEvent schema
    start_time_value = post.get("createdAt")
    start_time = datetime.now(timezone.utc)
    if isinstance(start_time_value, datetime):
        # If it's already a datetime object (from MongoDB BSON Date), use it directly
        start_time = start_time_value.replace(tzinfo=timezone.utc) # Ensure it's aware
        
    elif isinstance(start_time_value, str):
        # Only attempt string parsing if the value is a string
        start_time_str = start_time_value
        try:
            # Attempt to parse the common Twitter format
            start_time = datetime.strptime(start_time_str, "%a %b %d %H:%M:%S +0000 %Y")
            start_time = start_time.replace(tzinfo=timezone.utc) # Make aware
            
        except ValueError:
            try:
                # Fallback for ISO format
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except Exception as e:
                logger.error(f"Could not parse start_time for {post_id}: {start_time_str}. Using UTC now. Error: {e}")
                start_time = datetime.now(timezone.utc)

            
    # Build the final structured document
    final_event = {
        # Core Identifiers
        "post_id": post_id,
        "classification_status": "Confirmed", # Assumed Confirmed if all data is present
        
        # Time and Type for GIS/Filtering
        "disaster_type": classification.get("classification_type"),
        "start_time": start_time,
        
        # Location for GIS Mapping
        "location": {
            "state": geo.get("state"),
            "district": geo.get("district"),
            "lat_lon": [geo.get("lon"), geo.get("lat")], 
        },
        
        # Post Details (for linking/context)
        "post_text": post.get("postText"),
        "keywords": post.get("keywords"),
        "hashtags": post.get("hashtag"),
        
        # Sentiment Data
        "sentiment": {
            "label": sentiment.get("sentiment_label"),
            "confidence": sentiment.get("confidence_level"),
            "reasoning": sentiment.get("reasoning"),
        }
    }
    
    return final_event

def run_event_creator_pipeline() -> List[Union[str, None]]:
    """
    Main function to orchestrate the creation of DisasterEvent documents 
    from all pre-processed data currently in MongoDB.
    """
    logger.info("Starting Disaster Event Creation Pipeline...")
    client = get_mongo_client()
    if not client:
        return ["Failed to connect to MongoDB."]

    db = client[COMBINED_DB_NAME]
    
    # 1. Identify all unique posts that have been processed
    # We use a distinct query on the classification table as a proxy for "ready to process"
    all_post_ids = db[INCIDENT_COLLECTION].distinct("post_id")
    
    results = []
    
    for i, post_id in enumerate(all_post_ids):
        logger.info(f"Processing Post {i+1}/{len(all_post_ids)}: {post_id}")
        
        # 2. Transform the data for the current post ID
        event_document = transform_post_to_event(post_id, db)
        
        if event_document:
            # 3. LOAD: Save the final document (includes idempotency check)
            saved_id = save_disaster_event(event_document)
            if saved_id:
                results.append(saved_id)

    client.close()
    logger.info(f"Event Creator Pipeline Finished. Successfully processed {len(results)} new events.")
    return [f"Successfully created {len(results)} new Disaster Events."]
    