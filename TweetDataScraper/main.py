import time
import logging
from config import session, HEADERS, RAPID_API_URL
from preprocess import clean_text, translate_to_english, tokenize_and_clean
from helpers import is_location_in_malaysia, malaysia_keywords
from dbConnection import insert_tweet

def run_once(combined_query):
    # Twitter API params
    params = {
        "type": "Latest",
        "count": "1000",
        "query": combined_query
    }
    logging.info(f"Starting real-time tweet streaming for {combined_query}...")
    seen_ids = set()
    next_cursor = None

    try:
        while True:
            if next_cursor:
                params["cursor"] = next_cursor
            elif "cursor" in params:
                del params["cursor"]

            response = session.get(RAPID_API_URL, headers=HEADERS, params=params)
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

                        location = user_legacy.get('location', '')
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
                        translated_text = translate_to_english(cleaned_text)
                        tokens = tokenize_and_clean(translated_text)

                        hashtags = tweet_legacy.get('entities', {}).get('hashtags', [])
                        tweet_hashtags = ','.join(tag.get('text', '') for tag in hashtags) if hashtags else 'null'

                        tweet_info = {
                            'tweet_id': tweet_id,
                            'raw_text': raw_text,
                            'cleaned_text': cleaned_text,
                            'translated_text': translated_text,
                            'tokens': tokens,
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
                logging.info(f"No more cursor. Exiting job for {keyword}.")
                break

            time.sleep(3)

    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    # Disaster keywords
    bm_keywords = ["banjir", "tanah runtuh", "ribut", "jerebu", "kebakaran hutan", "mendapan tanah", "gempa bumi", "tsunami"]
    en_keywords = ["flood", "landslide", "storm", "haze", "forest fire", "sinkhole", "earthquake"]
    all_keywords = bm_keywords + en_keywords
    
    for keyword in all_keywords:
        for location_keyword in malaysia_keywords:
            combined_query = f"{keyword} {location_keyword}"
            run_once(combined_query)
