import time
import logging
from config import session, HEADERS, RAPID_API_URL
from preprocess import clean_text, translate_to_english, tokenize_and_clean
from helpers import is_location_in_malaysia
from dbConnection import insert_tweet
from config import session

# Initialise disaster keywords
bm_keywords = ["banjir", "tanah runtuh", "ribut", "jerebu", "kebakaran hutan", "mendapan tanah", "gempa bumi", "tsunami"]
en_keywords = ["flood", "landslide", "storm", "haze", "forest fire", "sinkhole", "earthquake", "tsunami"]
disaster_query = " OR ".join(bm_keywords + en_keywords)

params = {
    "type": "Latest",
    "count": "100",
    "query": f"({disaster_query})"
}

seen_ids = set()
next_cursor = None

while True:
    logging.info("Starting real-time tweet streaming...")

    try:
        next_cursor = None
        while True:
            if next_cursor:
                params["cursor"] = next_cursor
            elif "cursor" in params:
                del params["cursor"]

            response = session.get(RAPID_API_URL, headers=HEADERS, params=params)
            if response.status_code != 200:
                time.sleep(10)
                continue

            data = response.json()
            next_cursor = None
            instructions = data.get('result', {}).get('timeline', {}).get('instructions', [])

            for instruction in instructions:
                for key in ['entries', 'addEntries']:
                    for item in instruction.get(key, []):
                        content = item.get('content', {})

                        if content.get('itemContent', {}).get('itemType') == "TimelineTweet":
                            tweet = content['itemContent']['tweet_results']['result']
                            tweet_id = tweet.get('rest_id')
                            if tweet_id in seen_ids:
                                continue
                            seen_ids.add(tweet_id)

                            user = tweet.get('core', {}).get('user_results', {}).get('result', {})
                            location = user.get('legacy', {}).get('location', '')
                            if not is_location_in_malaysia(location):
                                continue

                            # (skip verified / pro users and follower filtering...)

                            raw_text = tweet['legacy'].get('full_text', '')
                            cleaned = clean_text(raw_text)
                            translated = translate_to_english(cleaned)
                            tokens = tokenize_and_clean(translated)

                            tweet_info = {
                                'tweet_id': tweet_id,
                                'raw_text': raw_text,
                                'cleaned_text': cleaned,
                                'translated_text': translated,
                                'tokens': tokens,
                                # add other metadata
                            }

                            insert_tweet(tweet_info)

                        if item.get('entryId', '').startswith('cursor-bottom'):
                            next_cursor = content.get('value')

            if not next_cursor:
                logging.info("No more cursor. Sleeping 1 hour.")
                break

        time.sleep(3600)

    except Exception as e:
        logging.error(f"Error: {e}")
        time.sleep(3600)
