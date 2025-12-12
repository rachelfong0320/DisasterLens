# backend/jobs/main_sentimentAnalysis.py (FINAL LOGIC FILE)

import time
import uuid
import asyncio
import logging
import os # Required for os.getenv in the synchronous consolidation step if used
from typing import Union, List, Dict, Any
from pymongo import errors
from tqdm.asyncio import tqdm_asyncio

# --- Centralized Imports ---
from openai import AsyncOpenAI
from app.database import db_connection as db # Centralized DB instance
from config import OPENAI_API_KEY 

# Relative Imports for sibling files
from .schemas import SentimentOutput # Now imported from the unified schemas.py
from .prompts import SENTIMENT_SYSTEM_PROMPT # Now imported from the unified prompts.py

# Initialize Async OpenAI Client (Centralized)
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# ==========================================
# ASYNC WORKER
# ==========================================

async def analyze_sentiment_async(post: dict, sem: asyncio.Semaphore) -> Union[dict, None]:
    """
    ASYNC Worker: Analyzes sentiment/priority for a single post using the LLM.
    Uses standard JSON response_format and manual Pydantic validation for stability.
    """
    post_id = post.get('postId')
    text = post.get('postText')

    if not text:
        return None

    async with sem:
        for attempt in range(3):
            try:
                completion = await aclient.chat.completions.create( 
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Post: {text}"},
                    ],
                    # CRITICAL FIX 1: Use the standard JSON type argument
                    response_format={"type": "json_object"}, 
                    temperature=0.0,
                )
                
                # Get the raw JSON string content
                json_string = completion.choices[0].message.content
                
                # CRITICAL FIX 2: Manually validate and parse the JSON string using Pydantic
                result = SentimentOutput.model_validate_json(json_string)
                
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
                # We need to catch JSON/Validation errors here too
                if "429" in str(e): 
                    wait_time = 2 ** (attempt + 1)
                    logging.warning(f"Rate limited. Retrying post {post_id} in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    # Log the specific error
                    logging.error(f"Error analyzing post {post_id}: {e}")
                    return None
        return None

# ==========================================
# ASYNC BATCH RUNNER
# ==========================================

async def run_sentiment_job_batch_async(batch_size: int = 100) -> int:
    """
    ASYNCHRONOUS BATCH RUNNER: Fetches a batch, runs analysis, and saves results.
    """
    try:
        # Fetch data via threadpool for safe sync I/O (Calls db.get_unclassified_sentiment_posts)
        posts_to_process = await asyncio.to_thread(db.get_unclassified_sentiment_posts, batch_size) 
    except Exception as e:
        logging.error(f"DB fetch error in sentiment job: {e}")
        return 0

    if not posts_to_process: return 0

    logging.info(f"Starting sentiment analysis for {len(posts_to_process)} posts...")

    sem = asyncio.Semaphore(20) 
    tasks = [analyze_sentiment_async(post, sem) for post in posts_to_process]
    
    results = await asyncio.gather(*tasks)
    
    valid_results = [res for res in results if res is not None]
    
    if valid_results:
        # Save results via threadpool for safe sync I/O (Calls db.insert_many_sentiments)
        await asyncio.to_thread(db.insert_many_sentiments, valid_results)
        
    return len(valid_results)


# ==========================================
# SYNCHRONOUS SWEEP MANAGER (FastAPI Entry Point)
# ==========================================

def run_sentiment_job_sweep(batch_size: int = None) -> int:
    """
    SYNCHRONOUS ENTRY POINT: Orchestrates the continuous sweeping of the sentiment job.
    """
    logging.info("--- STARTING SENTIMENT ANALYSIS SWEEP ---")
    
    BATCH_SIZE_TO_USE = batch_size if batch_size is not None and batch_size > 0 else 100
    total_analyzed = 0
    
    while True:
        # Run the ASYNC batch runner synchronously using asyncio.run()
        analyzed_count = asyncio.run(run_sentiment_job_batch_async(BATCH_SIZE_TO_USE))
        
        if analyzed_count == 0:
            logging.info("Sentiment analysis sweep complete. No new posts found.")
            break
        
        total_analyzed += analyzed_count
        logging.info(f"Analyzed {analyzed_count} posts in batch. Total: {total_analyzed}.")
        time.sleep(1) 
        
    return total_analyzed