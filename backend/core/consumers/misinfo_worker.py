#use scrapped data to filter misinfo and combine data into unified schema (raw_social_data -> authentic_posts)

import asyncio
import json
import logging
import time
from kafka import KafkaConsumer, KafkaProducer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SSL_CONFIG

# --- AI Classifier Imports ---
from core.scrapers.TweetDataScraper.main_misinfoClassifier import classify_tweet_async
from core.scrapers.InstagramDataScraper.main_misinfoClassifier import classify_instagram_post

# --- Import your existing Nominatim logic ---
# This pulls the thread-safe, cached function from your twitter dataCombine file
from core.scrapers.TweetDataScraper.main_dataCombine import get_geo_data_safe

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MisinfoCombineWorker")
sem = asyncio.Semaphore(20)

async def process_message(data, producer):
    platform = data.get('platform')
    
    try:
        # 1. GATEKEEPER: MISINFO CLASSIFICATION
        if platform == 'twitter':
            res = await classify_tweet_async(data, sem)
            is_auth = res.get('check_label') == "AUTHENTIC" if res else False
        else:
            res = await classify_instagram_post(data, sem)
            is_auth = res.get('check_label') == "AUTHENTIC" if res else False

        if not is_auth:
            logger.info(f"Filtering out MISINFO from {platform}")
            return

        # 2. DATACOMBINE: GEO-FIX & SCHEMA UNIFICATION
        # Extract variables
        lat = data.get('latitude')
        lng = data.get('longitude')
        loc_string = data.get('location') or data.get('location_name', '')
        address, city = None, None

        # If it's a Tweet (or any post missing coords), use your high-quality fixer
        if lat is None:
            logger.info(f"Fixing Geo for {platform} using get_geo_data_safe: {loc_string}")
            # get_geo_data_safe returns (address, city, lat, lng)
            address, city, lat, lng = get_geo_data_safe(loc_string)

        # 3. CONSTRUCT MASTER SCHEMA (Unifying author_id, author_name, and text)
        combined_payload = {
            "postId": data.get("tweet_id") or data.get("ig_post_id"),
            "postText": (
                data.get('translated_text') or 
                data.get('cleaned_text') or 
                data.get('cleaned_description') or 
                data.get('description') or 
                data.get('raw_text')
            ),
            "createdAt": data.get('tweet_created_at') or data.get('created_at'),
            "hashtag": data.get('tweet_hashtags') or data.get('hashtags') or "null",
            "location": loc_string,
            "address": address or data.get('address'),
            "city": city or data.get('city'),
            "latitude": lat,
            "longitude": lng,
            "author_id": data.get('user_id') or data.get('author_id'),
            "author_name": data.get('user_name') or data.get('author_username') or "",
            "processedAt": time.time(),
            "source": platform.capitalize()
        }

        # 4. PRODUCE TO TOPIC 2: authentic_posts
        producer.send('authentic_posts', value=combined_payload)
        logger.info(f"{platform} verified, geo-fixed, and unified: {combined_payload['postId']}")

    except Exception as e:
        logger.error(f"Error in Misinfo Worker: {e}")

async def run():
    consumer = KafkaConsumer(
        'raw_social_data',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        **KAFKA_SSL_CONFIG,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='misinfo-gatekeeper-group',
        request_timeout_ms=30000,
        max_poll_interval_ms=600000,  # 10 minutes (adjust as needed)
        max_poll_records=1             # optional: process 1 message at a time
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        **KAFKA_SSL_CONFIG,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        request_timeout_ms=30000
    )

    logger.info("Misinfo & DataCombine Worker active and listening...")
    for message in consumer:
        await process_message(message.value, producer)

if __name__ == "__main__":
    asyncio.run(run())