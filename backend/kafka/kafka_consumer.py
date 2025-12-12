import json
import logging
from kafka import KafkaConsumer
from app.database import db  # Assuming this gives you access to your Mongo collections
# Alternatively import the insert functions from your existing dbConnection.py files

logging.basicConfig(level=logging.INFO)

def start_consumer():
    consumer = KafkaConsumer(
        'tweets_topic', 'instagram_topic', # Listen to both topics
        bootstrap_servers=['kafka:9092'],
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='disaster_lens_group',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    logging.info("Kafka Consumer started...")

    for message in consumer:
        data = message.value
        topic = message.topic

        try:
            if topic == 'tweets_topic':
                # Logic from dbConnection.insert_tweet
                # Check duplicates and insert
                db.tweets.update_one(
                    {'tweet_id': data['tweet_id']}, 
                    {'$set': data}, 
                    upsert=True
                )
                logging.info(f"Saved Tweet: {data.get('tweet_id')}")

            elif topic == 'instagram_topic':
                # Logic for Instagram
                db.instagram.update_one(
                    {'ig_post_id': data['ig_post_id']}, 
                    {'$set': data}, 
                    upsert=True
                )
                logging.info(f"Saved IG Post: {data.get('ig_post_id')}")

        except Exception as e:
            logging.error(f"Failed to save message from {topic}: {e}")

if __name__ == "__main__":
    start_consumer()