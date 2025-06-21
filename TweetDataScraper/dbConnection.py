import logging
from pymongo import MongoClient, errors
from config import MONGO_URI, DB_NAME, COLLECTION_NAME

"""
This script connects to a MongoDB database and defines functionality for storing cleaned tweet data.

Features:
- Connects to a MongoDB database using URI, DB name, and collection name imported from a config file.
- Creates a unique index on the 'tweet_id' field to prevent duplicate tweet entries.
- Defines the `insert_tweet` function to insert a tweet document into the database, handling duplicates gracefully.

Note:
- Assumes that `tweet_info` passed to `insert_tweet` is a dictionary containing a unique 'tweet_id' field.
"""

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]
collection.create_index("tweet_id", unique=True)

def insert_tweet(tweet_info):
    try:
        collection.insert_one(tweet_info)
        logging.info(f"✅ Tweet {tweet_info['tweet_id']} inserted.")
    except errors.DuplicateKeyError:
        logging.info("⚠️ Duplicate tweet skipped.")
        pass
