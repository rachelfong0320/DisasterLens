import time
import uuid
import asyncio
import logging
from typing import Union
from openai import AsyncOpenAI 
from tqdm.asyncio import tqdm_asyncio 

# --- ASSUMPTIONS FOR KAFKA/FASTAPI STRUCTURE ---
# These imports must resolve correctly from the 'backend/jobs' folder.
# 'IncidentClassificationOutput' and 'INCIDENT_SYSTEM_PROMPT' are assumed to be sibling files/constants.
# 'db' refers to the centralized connection object exposed by backend/app/database.py.
from config import OPENAI_API_KEY 
from .schemas import IncidentClassificationOutput 
from .prompts import INCIDENT_SYSTEM_PROMPT 
from app.database import db_connection as db 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)


async def classify_incident_async(post: dict, sem: asyncio.Semaphore) -> Union[dict, None]:
    """
    ASYNC WORKER: Processes a single post using LLM classification (FR-019, FR-020).
    """
    # Use fields from the COMBINED POSTS SCHEMA
    post_id = post.get('postId')
    text = post.get('postText')
    hashtags = post.get('hashtag')
    created_at = post.get('createdAt') 

    if not text or len(text) < 5:
        return None

    prompt_text = f"Caption: {text}\nHashtags: {hashtags}"

    async with sem:
        for attempt in range(3):
            try:
                completion = await aclient.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": INCIDENT_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_text},
                    ],
                    response_format=IncidentClassificationOutput, 
                    temperature=0.1,
                )
                result = completion.choices[0].message.parsed
                
                return {
                    "classification_id": str(uuid.uuid4()), 
                    "post_id": post_id,
                    "classification_type": result.classification_type, 
                    "confidence_score": result.confidence_score,
                    "createdAt": created_at, 
                    "classifiedAt": time.time(),
                }
            except Exception as e:
                if "429" in str(e):
                    logging.warning(f"Rate limit hit for {post_id}. Retrying (Attempt {attempt + 1}).")
                    await asyncio.sleep(2 ** (attempt + 1))
                else:
                    logging.error(f"Critical error classifying incident for {post_id}: {e}") 
                    break
        return None

async def run_incident_classification_batch(batch_size: int = 100) -> int:
    """
    ASYNCHRONOUS ENTRY POINT: Executes one batch of classification jobs.
    FIXED: Now runs as an ASYNC function, removing the need for asyncio.run() and fixing the conflict.
    """
    # 1. Fetch posts (This part is still synchronous, so we use a threadpool utility for DB I/O)
    try:
        # Use a threadpool to safely run the blocking DB operation inside this async function
        batch_posts = await asyncio.to_thread(db.get_unclassified_incident_posts, batch_size)
    except Exception as e:
        logging.error(f"Database fetch error in incident classifier: {e}")
        return 0
    
    if not batch_posts:
        logging.info("No new posts in the combined collection to classify.")
        return 0

    logging.info(f"Starting classification for {len(batch_posts)} posts...")

    # 2. Run the asynchronous workers concurrently (Now we can use await directly!)
    sem = asyncio.Semaphore(10) 
    tasks = [classify_incident_async(post, sem) for post in batch_posts]
    
    # CRITICAL FIX: Direct use of await gather, removing the conflicting asyncio.run()
    results = await tqdm_asyncio.gather(*tasks, desc="Classifying Incidents") 

    valid_results = [res for res in results if res is not None]

    # 3. Store results (This is synchronous DB I/O, so we run it in a threadpool)
    if valid_results:
        await asyncio.to_thread(db.insert_many_incidents, valid_results)
        logging.info(f"Successfully saved {len(valid_results)} incident classifications.")
        
    return len(valid_results)

def sweep_incident_classification_job(batch_size: int = 100) -> int:
    """
    SYNCHRONOUS ENTRY POINT (Called by FastAPI test endpoint).
    Continuously calls the async batch processor until all posts are classified.
    """
    total_classified = 0
    
    # We need a synchronous function that runs the async job repeatedly.
    # We will use the synchronous function that calls the async one inside a loop.
    
    while True:
        try:
            # 1. Run the ASYNC batch job synchronously and get the count.
            # We must use asyncio.run() here because this is a synchronous function 
            # and it needs to execute the async job logic.
            classified_count = asyncio.run(run_incident_classification_batch(batch_size))
        except Exception as e:
            # Handle potential event loop errors if the threadpool isn't perfectly isolated
            logging.error(f"Sweep interrupted by error: {e}")
            break

        if classified_count == 0:
            logging.info("Incident classification sweep complete. All posts checked.")
            break
        
        total_classified += classified_count
        logging.info(f"Continuing sweep: {classified_count} classified in this batch. Total classified: {total_classified}")
        
        # Introduce a small pause to prevent database/CPU strain during continuous loops
        time.sleep(1) 
        
    return total_classified
# def run_incident_classification_batch(batch_size: int = 100) -> int:
    """
    SYNCHRONOUS ENTRY POINT (Called by the external job scheduler/FastAPI test endpoint).
    Fetches a batch of unclassified data from the unified table and processes it.
    """
    # 1. Fetch posts from the unified posts_data collection
    try:
        batch_posts = db.get_unclassified_incident_posts(batch_size=batch_size) 
    except Exception as e:
        logging.error(f"Database fetch error in incident classifier: {e}")
        return 0
    
    if not batch_posts:
        logging.info("No new posts in the combined collection to classify.")
        return 0

    logging.info(f"Starting classification for {len(batch_posts)} posts...")

    # 2. Run the asynchronous workers concurrently
    sem = asyncio.Semaphore(10) 
    tasks = [classify_incident_async(post, sem) for post in batch_posts]
    
    # asyncio.run handles the event loop call synchronously
    results = asyncio.run(tqdm_asyncio.gather(*tasks, desc="Classifying Incidents")) 

    valid_results = [res for res in results if res is not None]

    # 3. Store results (FR-022)
    if valid_results:
        # Writes to the incident_classification table via the centralized DB connection
        db.insert_many_incidents(valid_results) 
        logging.info(f"Successfully saved {len(valid_results)} incident classifications.")
        
    return len(valid_results)