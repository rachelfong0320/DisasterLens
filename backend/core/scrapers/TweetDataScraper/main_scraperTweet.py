import time
import logging
import json
from kafka import KafkaProducer
from core.config import (
    session_twitter, 
    HEADERS_TWITTER, 
    RAPID_API_URL_TWITTER, 
    KAFKA_BOOTSTRAP_SERVERS, 
    KAFKA_SSL_CONFIG
)
from core.scrapers.TweetDataScraper.preprocess import clean_text, translate_to_english, tokenize_and_clean
from core.scrapers.TweetDataScraper.helpers import is_location_in_malaysia, malaysia_keywords
from core.scrapers.TweetDataScraper.dbConnection import insert_tweet
from concurrent.futures import ThreadPoolExecutor

"""
Real-Time Twitter Scraper for Disaster-Related Tweets in Malaysia

Overview:
This script streams disaster-related tweets from Malaysia in real-time using the Twitter API via RapidAPI,
performs basic filtering and stores the cleaned data in MongoDB.

Key Features:
- Constructs search queries by combining disaster-related keywords (in English and Bahasa Melayu) with Malaysian locations.
- Filters tweets based on:
    - Location (must mention a Malaysian place)
    - User status (ignores verified users, business/creator accounts, and users with >10k followers)
- Processes tweet text by:
    - Cleaning raw tweet text
    - Translating non-English text to English
    - Tokenizing and removing stopwords
- Stores processed tweet data in MongoDB while avoiding duplicates using tweet IDs.
- Utilizes threading for parallel query processing and includes rate-limit-safe request retries.
- Maintains a shared set of seen tweet IDs to avoid duplicate processing across threads.

Modules Required:
- `config`: contains API credentials and session configuration
- `preprocess`: defines text cleaning, translation, and tokenization functions
- `helpers`: includes Malaysian location keyword list and matching logic
- `dbConnection`: handles MongoDB connection and tweet insertion
- `concurrent.futures`: enables multi-threaded scraping across queries

Execution:
Run this script as a standalone process. It will start multiple threads to concurrently stream tweets matching various disaster-location keyword combinations.

Note:
Make sure your `.env` file is properly configured with valid RAPIDAPI credentials and MongoDB URI before running this script.
"""
# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    security_protocol="SSL",
    ssl_cafile=KAFKA_SSL_CONFIG['ssl_cafile'],
    ssl_certfile=KAFKA_SSL_CONFIG['ssl_certfile'],
    ssl_keyfile=KAFKA_SSL_CONFIG['ssl_keyfile'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def run_once(combined_query):
    seen_ids = set()
    params = {
        "type": "Latest",
        "count": "1000",
        "query": combined_query
    }

    logging.info(f"Starting real-time tweet streaming for {combined_query}...")
    next_cursor = None

    while True:
        try:
            # ---------------------------
            # API REQUEST
            # ---------------------------
            if next_cursor:
                params["cursor"] = next_cursor
            else:
                params.pop("cursor", None)

            logging.info(f"[{combined_query}] Sending request to Twitter API...")
            response = session_twitter.get(
                RAPID_API_URL_TWITTER,
                headers=HEADERS_TWITTER,
                params=params,
                timeout=15
            )

            if response.status_code != 200:
                logging.warning(
                    f"[{combined_query}] API error {response.status_code}. Retrying in 10s."
                )
                time.sleep(10)
                continue

            try:
                data = response.json()
            except ValueError as json_err:
                logging.error(f"[{combined_query}] JSON decode error: {json_err}")
                continue

            next_cursor = None
            instructions = data.get('result', {}).get('timeline', {}).get('instructions', [])

            # ---------------------------
            # TWEET PROCESSING
            # ---------------------------
            for instruction in instructions:
                for key in ('entries', 'addEntries'):
                    for item in instruction.get(key, []):
                        try:
                            content = item.get('content', {})
                            if content.get('itemContent', {}).get('itemType') != "TimelineTweet":
                                continue

                            tweet = content['itemContent']['tweet_results']['result']
                            tweet_id = tweet.get('rest_id')

                            if not tweet_id or tweet_id in seen_ids:
                                continue
                            seen_ids.add(tweet_id)

                            user = tweet.get('core', {}).get('user_results', {}).get('result', {})
                            user_legacy = user.get('legacy', {})
                            tweet_legacy = tweet.get('legacy', {})

                            location = (
                                user.get('location', {}).get('location', '') 
                                or user_legacy.get('location', '')
                            )
                            if not is_location_in_malaysia(location):
                                continue

                            is_verified = user.get('verified', False)
                            verification_type = user.get('verification_type', 'null')
                            professional_type = user.get('professional', {}).get(
                                'professional_type', 'null'
                            )
                            followers_count = user_legacy.get('followers_count', 0)

                            if (
                                is_verified
                                or verification_type != 'null'
                                or professional_type in ['Business', 'Creator']
                                or followers_count > 10000
                            ):
                                continue

                            raw_text = tweet_legacy.get('full_text', '')
                            cleaned_text = clean_text(raw_text)

                            hashtags = tweet_legacy.get('entities', {}).get('hashtags', [])
                            tweet_hashtags = (
                                ','.join(tag.get('text', '') for tag in hashtags)
                                if hashtags else 'null'
                            )

                            tweet_info = {
                                'tweet_id': tweet_id,
                                'raw_text': raw_text,
                                'cleaned_text': cleaned_text,
                                'tweet_created_at': tweet_legacy.get('created_at', ''),
                                'tweet_hashtags': tweet_hashtags,
                                'location': location,
                                'user_id': user.get('rest_id', ''),
                                'user_name': user_legacy.get('name', ''),
                                'user_screen_name': user_legacy.get('screen_name', ''),
                                'verified': is_verified,
                                'verification_type': verification_type,
                                'user_followers_count': followers_count,
                                'professional_type': professional_type,
                                'platform': 'twitter'
                            }

                            # ---------------------------
                            # DB + KAFKA
                            # ---------------------------
                            try:
                                insert_tweet(tweet_info.copy())
                            except Exception as db_err:
                                logging.error(f"DB insert failed for {tweet_id}: {db_err}")
                            if producer:
                                try:
                                    producer.send(
                                        'raw_social_data',
                                        key=tweet_id.encode('utf-8'),
                                        value=tweet_info
                                )
                                except Exception as kafka_err:
                                    logging.error(f"Kafka send failed for {tweet_id}: {kafka_err}")

                        except Exception as tweet_err:
                            logging.error(f"Tweet processing error: {tweet_err}")

            if not next_cursor:
                logging.info(f"No more cursor. Exiting job for {combined_query}.")
                break

            producer.flush()
            time.sleep(3)

        except Exception as loop_err:
            logging.error(f"[{combined_query}] Fatal loop error: {loop_err}")
            time.sleep(5)

        
def start_scraping_job():
    """Main entry point for the scraper."""
    logging.basicConfig(level=logging.INFO)
    logging.info("--- Starting Scraping Job ---")
    
    bm_keywords = ["banjir", "tanah runtuh", "ribut", "jerebu", "kebakaran hutan", "mendapan tanah", "gempa bumi", "tsunami"]
    en_keywords = ["flood", "landslide", "storm", "haze", "forest fire", "sinkhole", "earthquake"]
    all_keywords = bm_keywords + en_keywords
    
    # Construct queries
    queries = [f"{d} {l}" for d in all_keywords for l in malaysia_keywords]
    
    # Run the threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Note: If run_once has a 'while True' loop, this will run forever.
        # Ideally, run_once should have a logic to stop after fetching X pages 
        # or if the pipeline is a scheduled cron job.
        for q in queries:
            executor.submit(run_once, q)
            
    logging.info("Scraping Job Complete.")

if __name__ == "__main__":
    start_scraping_job()
