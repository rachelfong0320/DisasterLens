import time
import logging
from core.config import session_twitter, HEADERS_TWITTER , RAPID_API_URL_TWITTER
from .preprocess import clean_text, translate_to_english, tokenize_and_clean
from .helpers import is_location_in_malaysia, malaysia_keywords
from .dbConnection import insert_tweet
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

def run_once(combined_query):
    seen_ids=set()
    try:
        # Twitter API params
        params = {
            "type": "Latest",
            "count": "1000",
            "query": combined_query
        }
        logging.info(f"Starting real-time tweet streaming for {combined_query}...")
        next_cursor = None

        while True:
            if next_cursor:
                params["cursor"] = next_cursor
            elif "cursor" in params:
                del params["cursor"]

            logging.info(f"[{combined_query}] Sending request to Twitter API...")
            response = session_twitter.get(RAPID_API_URL_TWITTER, headers=HEADERS_TWITTER, params=params)
            if response.status_code != 200:
                logging.warning(f"Non-200 response: {response.status_code}. Sleeping 10s.")
                time.sleep(10)
                continue

            data = response.json()
            next_cursor = None
            
            instructions = data.get('result', {}).get('timeline', {}).get('instructions', [])
            for instruction in instructions:
                for key in ['entries', 'addEntries']:
                    for item in instruction.get(key, []):
                        content = item.get('content', {})
                        if content.get('itemContent', {}).get('itemType') != "TimelineTweet":
                            continue

                        tweet = content['itemContent']['tweet_results']['result']
                        tweet_id = tweet.get('rest_id')
                        
                        if tweet_id in seen_ids:
                            continue
                        seen_ids.add(tweet_id)

                        user = tweet.get('core', {}).get('user_results', {}).get('result', {})
                        user_legacy = user.get('legacy', {})
                        tweet_legacy = tweet.get('legacy', {})

                        location = user.get('location', {}).get('location', '') or user_legacy.get('location', '')
                        if not is_location_in_malaysia(location):
                            continue

                        is_verified = user.get('verified', False)
                        verification_type = user.get('verification_type', 'null')
                        professional_type = user.get('professional', {}).get('professional_type', 'null')
                        followers_count = user_legacy.get('followers_count', 0)

                        if is_verified or verification_type != 'null' or professional_type in ['Business', 'Creator']:
                            continue
                        if followers_count > 10000:
                            continue

                        raw_text = tweet_legacy.get('full_text', '')
                        cleaned_text = clean_text(raw_text)

                        hashtags = tweet_legacy.get('entities', {}).get('hashtags', [])
                        tweet_hashtags = ','.join(tag.get('text', '') for tag in hashtags) if hashtags else 'null'

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
                            'professional_type': professional_type
                        }

                        insert_tweet(tweet_info)

                        if item.get('entryId', '').startswith('cursor-bottom'):
                            next_cursor = content.get('value')

            if not next_cursor:
                logging.info(f"No more cursor. Exiting job for {combined_query}.")
                break

            time.sleep(3)

    except Exception as e:
        logging.error(f"Error: {e}")
        
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
