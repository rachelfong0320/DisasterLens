import os
from pymongo import MongoClient
from datetime import datetime
import logging
from typing import Union
from core.config import MONGO_URI, COMBINED_DB_NAME,DISASTER_EVENTS_COLLECTION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_mongo_client():
    """Returns a new MongoDB client connection."""
    try:
        # Use serverSelectionTimeoutMS to ensure quick failure if Mongo is down
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping') # Attempt to connect and check server status
        return client
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB at {MONGO_URI}: {e}")
        return None


def save_disaster_event(event_data: dict) -> Union[str, None]:
    client = None
    try:
        client = get_mongo_client()
        if not client: return None

        db = client[COMBINED_DB_NAME]
        collection = db[DISASTER_EVENTS_COLLECTION]

        # Use post_id (the original post ID) for Idempotency Check
        post_identifier = event_data.get("post_id") # <--- USE "post_id" KEY
        if not post_identifier:
            logger.error("Attempted to save event with missing or None 'post_id'. Skipping.")
            return None 

        # Use update_one with upsert=True for robust Idempotency
        # Query based on "post_id"
        result = collection.update_one(
            {"post_id": post_identifier}, # Query: Does this ID exist?
            {"$set": event_data},         # Update: Replace/Set the data
            upsert=True                   # Option: Insert if not found
        )
        
        if result.upserted_id:
            logger.info(f"SUCCESS: Created new Disaster Event with ID: {result.upserted_id}")
            return str(result.upserted_id)
        elif result.modified_count > 0:
            logger.info(f"SUCCESS: Updated existing Disaster Event: {post_identifier}")
            return post_identifier
        else:
            logger.info(f"Skipped save for already existing, unmodified event: {post_identifier}")
            return post_identifier

    except Exception as e:
        logger.error(f"ERROR saving event with ID {post_identifier}: {e}")
        return None
    finally:
        if client:
            client.close()