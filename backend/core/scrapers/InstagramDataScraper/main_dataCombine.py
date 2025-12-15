import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient, errors

# Import configs
from core.config import (
    MONGO_URI, 
    DB_INSTAGRAM, 
    COMBINED_DB_NAME, 
    IG_COLLECTION, 
    IG_MISINFO_COLLECTION, 
    POSTS_COLLECTION 
) 

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# 1. Setup Database Connections
client = MongoClient(MONGO_URI)

# --- CONFIGURATION ---
MAX_WORKERS = 10  # Number of parallel threads

# Database Setup
src_db = client[DB_INSTAGRAM]
raw_post_col = src_db[IG_COLLECTION] # Raw Instagram posts
misinfo_col = src_db[IG_MISINFO_COLLECTION] # Instagram Misinfo results
dest_db = client[COMBINED_DB_NAME]
posts_col = dest_db[POSTS_COLLECTION] # Combined posts collection

# Ensure unique index on postId to prevent duplicates in the new DB
posts_col.create_index("postId", unique=True)


def process_single_post(doc):
    """
    Worker function to process a single joined document.
    Directly uses existing structured geo-data.
    """
    try:
        post_id = doc.get('ig_post_id')
        post_data = doc.get('details', {})

        # Directly get structured location data from the raw post
        loc_string = post_data.get('location_name', '') 
        address = post_data.get('address')
        city = post_data.get('city')
        # Ensure lat/lng are properly typed (float)
        lat = float(post_data.get('latitude')) if post_data.get('latitude') is not None else None
        lng = float(post_data.get('longitude')) if post_data.get('longitude') is not None else None

        new_post = {
            "postId": post_id,
            "postText": post_data.get('cleaned_description') or post_data.get('description'), 
            "createdAt": post_data.get('created_at'),
            "hashtag": post_data.get('hashtags'),
            "location": loc_string,
            "address": address,
            "city": city,
            "latitude": lat,
            "longitude": lng,
            "author_id": post_data.get('author_id'),
            "author_name": post_data.get('author_username'), 
            "processedAt": time.time(),
            "source": "Instagram"
        }

        posts_col.insert_one(new_post)
        return 1 # Success count
    except errors.DuplicateKeyError:
        return 0 # Skipped
    except Exception as e:
        logging.error(f"Error processing {doc.get('ig_post_id')}: {e}")
        return 0

def run_enrichment_pipeline():
    print("\n" + "="*40)
    print("STEP 3: CONCURRENT DATA ENRICHMENT (Instagram)")
    print("="*40 + "\n")

    # 1. INCREMENTAL LOGIC: Get IDs we already have
    logging.info("Fetching existing IDs to skip...")
    existing_ids = set(posts_col.distinct("postId"))
    logging.info(f"Found {len(existing_ids)} existing posts. Skipping them.")

    # 2. AGGREGATION: Fetch AUTHENTIC data joined with Instagram content
    pipeline = [
        # Filter AUTHENTIC only
        { "$match": { "check_label": "AUTHENTIC" } },
        { "$lookup": {
            "from": IG_COLLECTION, # Raw Instagram posts collection (from config)
            "localField": "ig_post_id",
            "foreignField": "ig_post_id",
            "as": "details"
        }},
        { "$unwind": "$details" }
    ]

    cursor = misinfo_col.aggregate(pipeline)

    # 3. FILTERING & BATCHING
    to_process = []
    for doc in cursor:
        if doc.get('ig_post_id') not in existing_ids:
            to_process.append(doc)

    if not to_process:
        logging.info("No new authentic Instagram posts to process.")
        return

    logging.info(f"Starting processing for {len(to_process)} new Instagram posts with {MAX_WORKERS} threads...")

    # 4. CONCURRENT EXECUTION
    count = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        futures = [executor.submit(process_single_post, item) for item in to_process]
        
        # Wait for completion and count results
        for future in as_completed(futures):
            count += future.result()
            if count % 10 == 0 and count > 0:
                print(f"Progress: {count}/{len(to_process)} saved...", end='\r')

    logging.info(f"\nJob Finished. Successfully added {count} new posts.")

if __name__ == "__main__":
    run_enrichment_pipeline()