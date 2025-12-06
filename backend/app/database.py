# app/database.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

class Database:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        # Assuming you want to access both databases defined in your scrapers
        self.tweet_db = self.client["TweetData"]
        self.tweet_collection = self.tweet_db["CleanedTweet"]
        
        self.ig_db = self.client["Instagram"]
        self.ig_collection = self.ig_db["cleaned_posts"]

        self.analytics_db = self.client["SocialMediaPosts"]
        self.posts_data_collection = self.analytics_db["posts_data"]
        self.tracking_collection = self.analytics_db["tracking_data"]

db_connection = Database()