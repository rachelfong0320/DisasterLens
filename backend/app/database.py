# app/database.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

COMBINED_DB_NAME = "SocialMediaPosts"
POSTS_COLLECTION_NAME = "posts_data"
INCIDENT_COLLECTION_NAME = "incident_classification"
SENTIMENT_COLLECTION_NAME = "sentiment_analysis"

class Database:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        # Assuming you want to access both databases defined in your scrapers
        self.tweet_db = self.client["TweetData"]
        self.tweet_collection = self.tweet_db["CleanedTweet"]
        
        self.ig_db = self.client["Instagram"]
        self.ig_collection = self.ig_db["cleaned_posts"]

        self.combined_db = self.client[COMBINED_DB_NAME]
        
        # 1. The main combined post collection (Twitter + Instagram)
        self.posts_collection = self.combined_db[POSTS_COLLECTION_NAME] 
        
        # 2. Incident classification results (FR-022)
        self.incident_collection = self.combined_db[INCIDENT_COLLECTION_NAME] 
        # Ensure we have a unique index on post_id to avoid duplicate classification records
        try:
            self.incident_collection.create_index("post_id", unique=True)
        except Exception:
            # Ignore index creation errors at startup, but having this index prevents duplicate work
            pass
        
        # 3. Sentiment analysis results (Friend's part)
        self.sentiment_collection = self.combined_db[SENTIMENT_COLLECTION_NAME]

    def get_unclassified_incident_posts(self, batch_size=100):
        """Fetches posts from the unified posts_collection not yet classified for incident type."""
        classified_ids = self.incident_collection.distinct("post_id") 
        query = {
            "postId": {"$nin": classified_ids},
        }
        return list(self.posts_collection.find(query).limit(batch_size))
        
    def insert_many_incidents(self, results):
        """Inserts incident classification results (FR-022)."""
        # Note: Added simple error handling for demonstration
        try:
            return self.incident_collection.insert_many(results, ordered=False)
        except Exception:
            return None        

db_connection = Database()