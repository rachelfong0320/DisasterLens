import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient, errors
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Import configs
from config import MONGO_URI, DB_NAME, COMBINED_DB_NAME ,TWEET_COLLECTION, MISINFO_COLLECTION, POSTS_COLLECTION

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# 1. Setup Database Connections
client = MongoClient(MONGO_URI)

# --- CONFIGURATION ---
MAX_WORKERS = 10  # Number of parallel threads
GEO_REQUEST_DELAY = 1.1  # Seconds to wait between API calls (required by Nominatim)

# Database Setup
src_db = client[DB_NAME]
misinfo_col = src_db[MISINFO_COLLECTION]
tweet_col = src_db[TWEET_COLLECTION]
dest_db = client[COMBINED_DB_NAME]
posts_col = dest_db[POSTS_COLLECTION]

# Ensure unique index on postId to prevent duplicates in the new DB
posts_col.create_index("postId", unique=True)

# 2. Setup Geocoder (User Agent is required by Nominatim)
geolocator = Nominatim(user_agent="disaster_lens_app_v1")

# --- SHARED RESOURCES ---
# 1. Cache for locations (saves API calls)
geo_cache = {}
geo_cache_lock = threading.Lock()

# 2. Lock for API Rate Limiting (prevents banning)
api_lock = threading.Lock()

def get_geo_data_safe(location_name):
    """
    Thread-safe geocoding. 
    Returns from cache immediately if available.
    Otherwise, locks the API to ensure only 1 request per second.
    """
    if not location_name:
        return None, None, None, None

    loc_key = location_name.strip().lower()

    # 1. CHECK CACHE (Fast, Concurrent)
    with geo_cache_lock:
        if loc_key in geo_cache:
            return geo_cache[loc_key]

    # 2. CALL API (Slow, Serialized)
    # We must lock this section so 10 threads don't hit the API at once
    with api_lock:
        try:
            # Check cache again just in case another thread filled it while we waited
            with geo_cache_lock:
                if loc_key in geo_cache:
                    return geo_cache[loc_key]

            logging.info(f"API Call for: {location_name}")
            location = geolocator.geocode(location_name, timeout=10)
            
            # Crucial: sleep inside the lock to enforce rate limit
            time.sleep(GEO_REQUEST_DELAY) 

            if location:
                lat = location.latitude
                lng = location.longitude
                address = location.address
                
                raw = location.raw.get('address', {})
                city = raw.get('city') or raw.get('town') or raw.get('state')
                
                result = (address, city, lat, lng)
            else:
                result = (None, None, None, None)

            # Update cache
            with geo_cache_lock:
                geo_cache[loc_key] = result
            
            return result

        except (GeocoderTimedOut, Exception) as e:
            logging.warning(f"Geocoding failed for {location_name}: {e}")
            return None, None, None, None

def process_single_tweet(doc):
    """
    Worker function to process a single joined document.
    """
    try:
        tweet_id = doc.get('tweet_id')
        tweet_data = doc.get('details', {})

        # Get Location
        loc_string = tweet_data.get('location', '')
        address, city, lat, lng = get_geo_data_safe(loc_string)

        new_post = {
            "postId": tweet_id,
            "postText": tweet_data.get('translated_text') or tweet_data.get('cleaned_text'),
            "createdAt": tweet_data.get('tweet_created_at'),
            "hashtag": tweet_data.get('tweet_hashtags'),
            "location": loc_string,
            "address": address,
            "city": city,
            "latitude": lat,
            "longitude": lng,
            "author_id": tweet_data.get('user_id'),
            "author_name": tweet_data.get('user_name'),
            "processedAt": time.time(),
            "source": "Twitter"
        }

        posts_col.insert_one(new_post)
        return 1 # Success count
    except errors.DuplicateKeyError:
        return 0 # Skipped
    except Exception as e:
        logging.error(f"Error processing {doc.get('tweet_id')}: {e}")
        return 0

def run_enrichment_pipeline():
    # 1. INCREMENTAL LOGIC: Get IDs we already have
    # Fetching only _id is very fast even for 100k+ records
    logging.info("Fetching existing IDs to skip...")
    existing_ids = set(posts_col.distinct("postId"))
    logging.info(f"Found {len(existing_ids)} existing posts. Skipping them.")

    # 2. AGGREGATION: Fetch AUTHENTIC data joined with Tweet content
    pipeline = [
        # Filter AUTHENTIC only
        { "$match": { "check_label": "AUTHENTIC" } },
        # Optimization: Filter out IDs we already processed at the DB level if possible,
        # but passing a massive array to $nin can be slow. 
        # Better to fetch authentic candidates and filter in Python for medium datasets (<50k).
        { "$lookup": {
            "from": TWEET_COLLECTION, 
            "localField": "tweet_id",
            "foreignField": "tweet_id",
            "as": "details"
        }},
        { "$unwind": "$details" }
    ]

    cursor = misinfo_col.aggregate(pipeline)

    # 3. FILTERING & BATCHING
    to_process = []
    for doc in cursor:
        if doc.get('tweet_id') not in existing_ids:
            to_process.append(doc)

    if not to_process:
        logging.info("No new authentic tweets to process.")
        return

    logging.info(f"Starting processing for {len(to_process)} new tweets with {MAX_WORKERS} threads...")

    # 4. CONCURRENT EXECUTION
    count = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        futures = [executor.submit(process_single_tweet, item) for item in to_process]
        
        # Wait for completion and count results
        for future in as_completed(futures):
            count += future.result()
            if count % 10 == 0 and count > 0:
                print(f"Progress: {count}/{len(to_process)} saved...", end='\r')

    logging.info(f"\nJob Finished. Successfully added {count} new posts.")

if __name__ == "__main__":
    run_enrichment_pipeline()