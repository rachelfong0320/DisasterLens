from pymongo import MongoClient
from config import MONGO_URI, DB_NAME, COLLECTION_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
collection.create_index("tweet_id", unique=True)

def insert_tweet(tweet_info):
    try:
        collection.insert_one(tweet_info)
        print(f"Tweet {tweet_info['tweet_id']} inserted.")
    except Exception as e:
        print(f"Insert error: {e}")
