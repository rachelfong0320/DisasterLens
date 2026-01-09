import os
from pymongo import MongoClient
from datetime import datetime
import logging
from typing import Union
from elasticsearch import Elasticsearch
from core.config import MONGO_URI, COMBINED_DB_NAME, DISASTER_POSTS_COLLECTION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ES Client once (Ensure ELASTICSEARCH_URL is in your .env)
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
es_client = Elasticsearch(ES_URL, verify_certs=False)

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
    post_identifier = event_data.get("post_id")

    if not post_identifier:
        logger.error("Attempted to save event with missing 'post_id'. Skipping.")
        return None
    
    try:
        # 1. Save to MongoDB
        client = get_mongo_client()
        if not client: return None

        db = client[COMBINED_DB_NAME]
        collection = db[DISASTER_POSTS_COLLECTION]

        # Use update_one with upsert=True for robust Idempotency
        # Query based on "post_id"
        result = collection.update_one(
            {"post_id": post_identifier}, # Query: Does this ID exist?
            {"$set": event_data},         # Update: Replace/Set the data
            upsert=True                   # Option: Insert if not found
        )

        # 2. Sync to Elasticsearch (Immediate Real-time Sync)
        # We do this BEFORE the return statements so it actually runs
        try:
            # Standardize the time format for ES
            start_time = event_data.get("start_time")
            if hasattr(start_time, "isoformat"):
                start_time = start_time.isoformat()

            es_client.index(
                index="disaster_events",
                id=str(post_identifier),
                document={
                    "event_id": event_data.get("event_id"),
                    "classification_type": event_data.get("classification_type"),
                    "location_district": event_data.get("location_district"),
                    "location_state": event_data.get("location_state"),
                    "start_time": start_time,
                    "coordinates": event_data.get("geometry", {}).get("coordinates") if event_data.get("geometry") else None
                }
            )
            logger.info(f"✅ ES Sync Success for post: {post_identifier}")
        except Exception as es_e:
            logger.error(f"❌ ES Sync Failed: {es_e}")
        
        # 3. Handle Returns
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