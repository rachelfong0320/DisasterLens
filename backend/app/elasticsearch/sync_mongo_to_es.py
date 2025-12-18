import os
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient
from elasticsearch import Elasticsearch, helpers

load_dotenv()

# 1. Setup Connections
MONGO_URI = os.getenv("MONGO_URI")
# Use the service name 'elasticsearch' if in Docker, else 'localhost'
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

mongo_client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = mongo_client["SocialMediaPosts"] # Your database name

# Force version 8 compatibility to fix your 400 error
es_client = Elasticsearch(
    ES_URL,
    verify_certs=False,
)

# 2. Sync Logic for 'disaster_events'
def sync_events():
    collection = db['disaster_events']
    actions = []
    print(f"Reading events from Atlas...")
    
    for doc in collection.find():
        # Clean the document for ES
        start_time = doc.get("start_time")
        if hasattr(start_time, "isoformat"):
            start_time = start_time.isoformat()
            
        # Standardize coordinates for ES geo_point [lon, lat]
        coords = doc.get("geometry", {}).get("coordinates")
        
        actions.append({
            "_index": "disaster_events",
            "_id": str(doc["_id"]),
            "classification_type": doc.get("classification_type"),
            "location_district": doc.get("location_district"),
            "location_state": doc.get("location_state"),
            "start_time": start_time,
            "coordinates": coords, # [lon, lat] works for geo_point
            "total_posts_count": doc.get("total_posts_count")
        })
    
    if actions:
        helpers.bulk(es_client, actions)
        print(f"✅ Synced {len(actions)} events.")

# 3. Sync Logic for 'combined_disaster_data' (Social Media Posts)
def sync_posts():
    collection = db['combined_disaster_data']
    actions = []
    print(f"Reading posts from Atlas...")
    
    for doc in collection.find():
        start_time = doc.get("start_time")
        if hasattr(start_time, "isoformat"):
            start_time = start_time.isoformat()

        actions.append({
            "_index": "disaster_posts",
            "_id": str(doc["_id"]),
            "disaster_type": doc.get("disaster_type"),
            "post_text": doc.get("post_text"),
            "location_state": doc.get("location", {}).get("state"),
            "location_district": doc.get("location", {}).get("district"),
            "start_time": start_time,
            "sentiment": doc.get("sentiment", {}).get("label")
        })
    
    if actions:
        helpers.bulk(es_client, actions)
        print(f"✅ Synced {len(actions)} posts.")

if __name__ == "__main__":
    try:
        sync_events()
        sync_posts()
        print("🚀 All data copied to local Elasticsearch!")
    except Exception as e:
        print(f"❌ Error during sync: {e}")