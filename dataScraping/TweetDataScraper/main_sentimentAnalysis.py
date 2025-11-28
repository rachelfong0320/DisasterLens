import time
import uuid
import asyncio
import logging
from typing import Union
from openai import AsyncOpenAI
from pymongo import MongoClient, errors
from tqdm.asyncio import tqdm_asyncio

# Import configs and schema
from config import MONGO_URI, OPENAI_API_KEY, COMBINED_DB_NAME, POSTS_COLLECTION, SENTIMENT_COLLECTION
from schemas import SentimentOutput
from prompts import SENTIMENT_SYSTEM_PROMPT

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Setup
client = MongoClient(MONGO_URI)
dest_db = client[COMBINED_DB_NAME]
posts_col = dest_db[POSTS_COLLECTION]
sentiment_col = dest_db[SENTIMENT_COLLECTION]

# Initialize Async OpenAI Client
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Ensure index for fast lookups
sentiment_col.create_index("post_id", unique=True)

async def analyze_sentiment_async(post: dict, sem: asyncio.Semaphore) -> Union[dict, None]:
    post_id = post.get('postId')
    text = post.get('postText')

    if not text:
        return None

    async with sem:
        for attempt in range(3):
            try:
                completion = await aclient.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Post: {text}"},
                    ],
                    response_format=SentimentOutput,
                    temperature=0.0,
                )
                result = completion.choices[0].message.parsed
                
                return {
                    "sentiment_id": str(uuid.uuid4()),
                    "post_id": post_id,
                    "sentiment_label": result.sentiment_label,
                    "confidence_level": result.confidence_score,
                    "reasoning": result.reasoning, 
                    "model": "gpt-4o-mini",
                    "analyzed_at": time.time()
                }
            except Exception as e:
                if "429" in str(e):  # Rate limit error
                    wait_time = 2 ** (attempt + 1)
                    logging.warning(f"Rate limited. Retrying post {post_id} in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logging.error(f"Error analyzing post {post_id}: {e}")
                    return None
        return None

async def run_sentiment_job():
    print("\n" + "="*40)
    print("STEP 4: SENTIMENT ANALYSIS")
    print("="*40 + "\n")

    # 1. Get IDs already processed
    existing_ids = set(sentiment_col.distinct("post_id"))
    logging.info(f"Found {len(existing_ids)} already analyzed posts.")

    # 2. Get Candidates (All AUTHENTIC posts from postsData)
    # Note: postsData only contains AUTHENTIC posts based on your previous steps, 
    # but we filter by ID to avoid reprocessing.
    cursor = posts_col.find({"postId": {"$nin": list(existing_ids)}})
    posts_to_process = list(cursor)

    if not posts_to_process:
        logging.info("No new posts to analyze.")
        return

    logging.info(f"Starting sentiment analysis for {len(posts_to_process)} new posts...")

    # 3. Process concurrently
    sem = asyncio.Semaphore(20) # Allow 20 concurrent requests
    tasks = [analyze_sentiment_async(post, sem) for post in posts_to_process]
    
    # Run with progress bar
    results = await tqdm_asyncio.gather(*tasks, desc="Analyzing Sentiment")
    
    # 4. Save Results
    valid_results = [res for res in results if res is not None]
    
    if valid_results:
        try:
            sentiment_col.insert_many(valid_results, ordered=False)
            logging.info(f"Successfully saved {len(valid_results)} sentiment records.")
        except errors.BulkWriteError as bwe:
            logging.warning(f"Partial write error (likely duplicates): {bwe.details['nInserted']} inserted.")
    else:
        logging.info("No valid results generated.")

if __name__ == "__main__":
    asyncio.run(run_sentiment_job())