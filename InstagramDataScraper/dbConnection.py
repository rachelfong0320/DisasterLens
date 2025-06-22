from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, COLLECTION_NAME

class DatabaseConnection:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]

    def insert_post(self, post_info):
        """Insert a single post into the database"""
        try:
            return self.collection.insert_one(post_info)
        except Exception as e:
            print(f"Error inserting post: {e}")
            return None

    def insert_many_posts(self, posts):
        """Insert multiple posts into the database"""
        try:
            return self.collection.insert_many(posts)
        except Exception as e:
            print(f"Error inserting posts: {e}")
            return None

    def format_post_for_db(self, row):
        """Format a pandas row for database insertion"""
        return {
            "ig_post_id": row["ig_post_id"],
            "created_at": row["created_at"],
            "description": row["description"],
            "cleaned_description": row["cleaned_description"],
            "hashtags": row["cleaned_hashtags_str"],   
            "author_id": row["author_id"],
            "author_username": row["author_username"],
            "author_full_name": row["author_full_name"],
            "is_verified": bool(row["account_is_verified"]),
            "address": row["address"],
            "city": row["city"],
            "location_name": row["location_name"],
            "location_short_name": row["location_short_name"],
            "latitude": float(row["latitude"]) if row["latitude"] else None,
            "longitude": float(row["longitude"]) if row["longitude"] else None,
            "reported_as_spam": row["reported_as_spam"],
            "gen_ai_detection_method": row["gen_ai_detection_method"],
            "high_risk_genai_flag": bool(row["high_risk_genai_flag"]),
            "integrity_review_decision": row["integrity_review_decision"],
        }