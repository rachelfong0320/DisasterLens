import os
from elasticsearch import Elasticsearch, helpers
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Configs
ES_HOST = os.environ.get("ES_HOST", "http://disasterlens_es:9200")
ES_CLIENT = Elasticsearch(ES_HOST)
MONGO_URI = os.environ.get("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["SocialMediaPosts"]

def convert_date(value):
    """Convert MongoDB date to ISO string for Elasticsearch"""
    if value:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict) and "$date" in value:
            return value["$date"]
    return None

def copy_collection_to_es(collection_name, es_index, transform_func=None):
    documents = list(db[collection_name].find())
    actions = []

    for doc in documents:
        source = transform_func(doc) if transform_func else doc
        actions.append({
            "_index": es_index,
            "_id": str(doc["_id"]),
            "_source": source
        })

    if actions:
        helpers.bulk(ES_CLIENT, actions)
        print(f"Synced {len(actions)} documents from '{collection_name}' to '{es_index}'.")

# Transform functions for each collection
def transform_combined_disaster_data(doc):
    return {
        "post_id": doc.get("post_id"),
        "classification_status": doc.get("classification_status"),
        "disaster_type": doc.get("disaster_type"),
        "location_state": doc.get("location", {}).get("state"),
        "location_district": doc.get("location", {}).get("district"),
        "coordinates": doc.get("location", {}).get("lat_lon"),  # [lon, lat] for ES geo_point
        "post_text": doc.get("post_text"),
        "sentiment": doc.get("sentiment"),
        "start_time": convert_date(doc.get("start_time")),
        "keywords": doc.get("keywords")
    }

def transform_disaster_events(doc):
    return {
        "event_id": doc.get("event_id"),
        "classification_type": doc.get("classification_type"),
        "location_state": doc.get("location_state"),
        "location_district": doc.get("location_district"),
        "start_time": convert_date(doc.get("start_time")),
        "most_recent_report": convert_date(doc.get("most_recent_report")),
        "coordinates": doc.get("geometry", {}).get("coordinates"),
        "total_posts_count": doc.get("total_posts_count"),
        "related_post_ids": doc.get("related_post_ids")
    }

def transform_event_analytics(doc):
    return {
        "timestamp": convert_date(doc.get("timestamp")),
        "type_counts": doc.get("type_counts"),
        "district_ranking": doc.get("district_ranking"),
        "monthly_events": doc.get("monthly_events"),
        "sentiment_counts": doc.get("sentiment_counts")
    }

def transform_tracking_keyword(doc):
    return {
        "term": doc.get("term"),
        "type": doc.get("type"),
        "frequency": doc.get("frequency"),
        "updated_at": convert_date(doc.get("updated_at"))
    }

if __name__ == "__main__":
    copy_collection_to_es("combined_disaster_data", "combined_disaster_data", transform_combined_disaster_data)
    copy_collection_to_es("disaster_events", "disaster_events", transform_disaster_events)
    copy_collection_to_es("event_analytics", "event_analytics", transform_event_analytics)
    copy_collection_to_es("tracking_keyword", "tracking_keyword", transform_tracking_keyword)