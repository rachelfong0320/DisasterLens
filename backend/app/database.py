# app/database.py
from pymongo import MongoClient,UpdateOne, errors
import os
from dotenv import load_dotenv
from collections import Counter
from datetime import datetime, timezone
from typing import List, Dict, Any

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

COMBINED_DB_NAME = "SocialMediaPosts"
POSTS_COLLECTION_NAME = "posts_data"
INCIDENT_COLLECTION_NAME = "incident_classification"
SENTIMENT_COLLECTION_NAME = "sentiment_check"


class Database:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        # Assuming you want to access both databases defined in your scrapers
        self.tweet_db = self.client["TweetData"]
        self.tweet_collection = self.tweet_db["CleanedTweet"]
        
        self.ig_db = self.client["Instagram"]
        self.ig_collection = self.ig_db["cleaned_posts"]

        self.combined_db = self.client[COMBINED_DB_NAME]

        self.analytics_db = self.client["SocialMediaPosts"]
        self.posts_data_collection = self.analytics_db["posts_data"]
        self.tracking_collection = self.analytics_db["tracking_data"]
        self.combined_disaster_posts_collection = self.analytics_db["combined_disaster_posts"]

        self.sub_db = self.client["Subscriptions"]
        self.subscriber_collection = self.sub_db["subscriber"]
        self.notification_queue = self.sub_db["notification_queue"]

        self.notification_queue.create_index([("user_email", 1), ("status", 1)])

        try:
            self.subscriber_collection.create_index("email", unique=True)
        except Exception:
            pass
        
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

    def get_subscribers_for_location(self, disaster_location: str):
        """Finds all emails subscribed to a location mentioned in the disaster."""
        # Simple regex matching: find subscriptions where the subscribed place is inside the tweet's location string
        # e.g., if tweet location is "Sungai Buloh, Selangor", find subs for "Selangor" or "Sungai Buloh"
        
        # NOTE: Ideally, you should normalize locations. For MVP, we fetch all and filter in Python
        # or use a text search. Here is a simple python-side filter approach:
        all_subs = list(self.subscriptions_collection.find())
        matches = []
        for sub in all_subs:
            if sub['location'].lower() in disaster_location.lower():
                matches.append(sub['email'])
        return list(set(matches)) # Return unique emails
    
    def get_unclassified_posts_for_keyword(self, batch_size=100):
        """Fetches posts that have not yet had their main keyword generated (Phase 1)."""
        # Looks for posts where the 'keywords_generated' field is missing or False/null
        query = {"keywords_generated": {"$ne": True}}
        return list(self.posts_collection.find(query).limit(batch_size))

    def update_posts_keywords_bulk_sync(self, results: List[Dict[str, Any]]):
        updates = []
        for item in results:
            post_id_value = item['post_id']
            topic = item.get('topic')
            
            set_fields = {"keywords_generated": True}
            if topic:
                set_fields["keywords"] = topic
                
            # --- CRITICAL FIX: Use the UpdateOne class ---
            updates.append(
                UpdateOne(
                    # Filter: Find the document by its unique ObjectId
                    {"_id": post_id_value}, 
                    # Update: Set the new fields
                    {"$set": set_fields}
                )
            )
        
        if updates:
            try:
                # Use bulk write for efficiency
                # bulk_write accepts the list of UpdateOne objects
                self.posts_collection.bulk_write(updates, ordered=False) 
            except Exception as e:
                # Re-raise error to see the full context if it still fails
                raise Exception(f"Bulk write failed: {e}")

    def save_trend_analysis(self, keyword_counter: Counter, hashtag_counter: Counter):
            """Saves the final consolidated keywords and hashtag analysis to the dedicated table."""
            
            # You need a new collection for this final output
            analytics_collection = self.combined_db["tracking_keyword"] 
            
            analytics_collection.delete_many({}) 
            new_documents = []
            
            # Save Keywords (Topics)
            for term, freq in keyword_counter.items():
                new_documents.append({
                    "term": term,
                    "type": "keyword",
                    "frequency": freq,
                    "updated_at": datetime.now(timezone.utc)
                })

            # Save Hashtags
            for term, freq in hashtag_counter.items():
                new_documents.append({
                    "term": f"#{term}", 
                    "type": "hashtag",
                    "frequency": freq,
                    "updated_at": datetime.now(timezone.utc)
                })

            if new_documents:
                analytics_collection.insert_many(new_documents)
                return len(new_documents)
            return 0
    
    def get_unclassified_sentiment_posts(self, batch_size=100):
        """Fetches posts from the unified posts_collection not yet classified for sentiment."""
        # Find all post_ids that already exist in the sentiment results collection
        classified_ids = self.sentiment_collection.distinct("post_id") 
        
        query = {
            "postId": {"$nin": list(classified_ids)},
        }
        return list(self.posts_collection.find(query).limit(batch_size))
        
    def insert_many_sentiments(self, results: List[Dict[str, Any]]):
        """Inserts sentiment analysis results into the dedicated collection."""
        try:
            # NOTE: You need to import 'errors' from pymongo at the top of database.py
            self.sentiment_collection.insert_many(results, ordered=False)
            return len(results)
        except errors.BulkWriteError as bwe:
            return bwe.details['nInserted']
        except Exception as e:
            return None 

db_connection = Database()