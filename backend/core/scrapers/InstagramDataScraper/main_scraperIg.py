import asyncio
import aiohttp
import pandas as pd
import traceback
import time
from core.config import HEADERS_IG, RAPID_API_URL_IG, keywords
from .preprocess import parse_disaster_post, process_dataframe
from .dbConnection import DatabaseConnection

# Limit concurrent tasks
semaphore = asyncio.Semaphore(40)  
MAX_RETRIES = 3
TIMEOUT = aiohttp.ClientTimeout(total=10)

async def fetch_data(session, keyword, pagination_token=None):
    """Fetch a single page of data with retry and timeout handling"""
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
        except asyncio.TimeoutError:
            print(f"[{keyword}] Timeout (retry {retries+1}/{MAX_RETRIES})")
        except aiohttp.ClientError as e:
            print(f"[{keyword}] Client error: {e} (retry {retries+1}/{MAX_RETRIES})")

        retries += 1
        await asyncio.sleep(2 * retries)  # backoff

    print(f"[{keyword}] Failed after {MAX_RETRIES} retries.")
    return None


async def fetch_all_pages(session, keyword, delay=0.1, max_pages=20):
    """Fetch all pages for one keyword"""
    all_posts = []
    pagination_token = None
    page = 1

    while page <= max_pages:
        print(f"{keyword} - Page {page}")
        data = await fetch_data(session, keyword, pagination_token)

        if not data or "data" not in data or not data["data"].get("items"):
            print(f"{keyword} - No more data.")
            break

        items = data["data"]["items"]
        all_posts.extend(items)
        print(f"{keyword} - {len(items)} items")

        pagination_token = data.get("pagination_token")
        if not pagination_token:
            break

        page += 1
        await asyncio.sleep(delay)

    return all_posts

async def run_all_fetches():
    """Run fetch tasks for all keywords"""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_all_pages(session, kw, max_pages=20) for kw in keywords]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_posts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error fetching for keyword '{keywords[i]}': {result}")
            else:
                all_posts.extend(result)

    print(f"\nTotal posts fetched: {len(all_posts)}")
    return all_posts

async def run_scraping_job():
    """Main execution function"""
    try:
        # 1. Fetch data
        print("Fetching posts...")
        all_posts = await run_all_fetches()
        
        # 2. Parse posts
        print("\nParsing posts...")
        parsed_posts = parse_disaster_post(all_posts)
        
        # 3. Create DataFrame
        print("Creating DataFrame...")
        post_df = pd.DataFrame(parsed_posts)
        
        # 4. Process and clean data
        print("Processing and cleaning data...")
        processed_df = process_dataframe(post_df)
        
        # 5. Save to MongoDB
        print("Saving to MongoDB...")
        db = DatabaseConnection()
        
        existing_ids = set(db.collection.distinct("ig_post_id"))

        # Format and filter out duplicates
        documents = [db.format_post_for_db(row) for _, row in processed_df.iterrows()]
        new_documents = [doc for doc in documents if doc["ig_post_id"] not in existing_ids]

        if new_documents:
            db.collection.insert_many(new_documents, ordered=False)
            print(f"Inserted {len(new_documents)} new posts. Skipped {len(documents) - len(new_documents)} duplicates.")
        else:
            print("No new posts to insert. All are duplicates.")

        print("Processing completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_scraping_job())
