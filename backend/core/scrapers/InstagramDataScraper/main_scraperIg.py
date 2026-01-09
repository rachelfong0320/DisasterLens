import asyncio
import aiohttp
import pandas as pd
import traceback
import json
import time
from kafka import KafkaProducer

# FIX: Remove "from requests import session" as it conflicts with aiohttp
from core.config import (
    HEADERS_IG, 
    RAPID_API_URL_IG, 
    keywords, 
    KAFKA_BOOTSTRAP_SERVERS, 
    KAFKA_SSL_CONFIG
)
from core.scrapers.InstagramDataScraper.preprocess import parse_disaster_post, process_dataframe
from core.scrapers.InstagramDataScraper.dbConnection import DatabaseConnection

# Limit concurrent tasks
MAX_RETRIES = 3
TIMEOUT = aiohttp.ClientTimeout(total=10)

async def fetch_data(session, keyword, semaphore, pagination_token=None):
    params = {"search_query": keyword}
    if pagination_token:
        params["pagination_token"] = pagination_token

    retries = 0
    while retries < MAX_RETRIES:
        try:
            async with semaphore:
                async with session.get(
                    RAPID_API_URL_IG,
                    headers=HEADERS_IG,
                    params=params,
                    timeout=TIMEOUT
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"[{keyword}] Error {response.status}")
                        return None
        except Exception as e:
            print(f"[{keyword}] Connection Error: {e}")

        retries += 1
        await asyncio.sleep(2 * retries)
    return None

async def fetch_all_pages(session, keyword, semaphore, delay=0.1, max_pages=20):
    all_posts = []
    pagination_token = None
    page = 1
    while page <= max_pages:
        data = await fetch_data(session, keyword, semaphore, pagination_token)
        if not data or "data" not in data or not data["data"].get("items"):
            break
        items = data["data"]["items"]
        all_posts.extend(items)
        pagination_token = data.get("pagination_token")
        if not pagination_token:
            break
        page += 1
        await asyncio.sleep(delay)
    return all_posts

async def run_all_fetches(session, semaphore):
    # Pass the correctly initialized session and semaphore
    tasks = [fetch_all_pages(session, kw, semaphore, max_pages=20) for kw in keywords]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_posts = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"Error fetching for keyword '{keywords[i]}': {result}")
        else:
            all_posts.extend(result)
    return all_posts

async def run_scraping_job():
    try:
        # 1. Initialize logic inside the loop
        semaphore = asyncio.Semaphore(10) # 10 is safer for RapidAPI rate limits
        
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            **KAFKA_SSL_CONFIG,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            request_timeout_ms=30000
        )

        # 2. CREATE THE SESSION HERE
        print("Fetching posts...")
        async with aiohttp.ClientSession() as session:
            all_posts = await run_all_fetches(session, semaphore)
        
        # 3. Process the results
        if not all_posts:
            print("No posts found. Exiting.")
            return

        parsed_posts = parse_disaster_post(all_posts)
        post_df = pd.DataFrame(parsed_posts)
        processed_df = process_dataframe(post_df)
        
        db = DatabaseConnection()
        existing_ids = set(db.collection.distinct("ig_post_id"))
        documents = [db.format_post_for_db(row) for _, row in processed_df.iterrows()]

        for doc in documents:
            if doc["ig_post_id"] not in existing_ids:
                db.collection.insert_one(doc)
                doc['platform'] = 'instagram'
                doc['raw_text'] = doc.get('caption', '') 
                
                producer.send('raw_social_data', value=doc)
                print(f"Produced Instagram ID {doc['ig_post_id']} to Kafka")

        producer.flush()
        print("Processing completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_scraping_job())