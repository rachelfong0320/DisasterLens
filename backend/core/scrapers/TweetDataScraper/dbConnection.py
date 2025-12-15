import logging
from pymongo import MongoClient, errors
from core.config import MONGO_URI, DB_TWEET, TWEET_COLLECTION, TWEET_MISINFO_COLLECTION

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
db = client[DB_TWEET]
# Export specific collections
tweet_collection = db[TWEET_COLLECTION]
misinfo_collection = db[TWEET_MISINFO_COLLECTION]

# Ensure indexes
try:
    tweet_collection.create_index("tweet_id", unique=True)
    misinfo_collection.create_index("tweet_id", unique=True)
except Exception:
    pass

# Check if mongoDB connected successfully
try:
    client.admin.command('ping')
    logging.info("MongoDB connection successful.")
except Exception as e:
    logging.error(f"MongoDB connection failed: {e}")
    
def insert_tweet(tweet_info):
    try:
        tweet_collection.insert_one(tweet_info)
        logging.info(f"Tweet {tweet_info['tweet_id']} inserted.")
    except errors.DuplicateKeyError:
        logging.info("Duplicate tweet skipped.")
    except Exception as e:
        logging.error(f"Unknown insert error: {e}")
