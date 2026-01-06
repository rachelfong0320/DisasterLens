# backend/jobs/main_trendAnalysis.py

import re
import time
import json
import logging
import asyncio
import os # Needed for os.getenv in consolidate_topics_sync
from datetime import datetime, timezone
from collections import Counter
from typing import List, Dict, Any, Union

# --- Centralized Imports ---
from openai import AsyncOpenAI, OpenAI 
from core.config import OPENAI_API_KEY 

from .schemas import TopicExtractionOutput
from .prompts import TOPIC_GENERATION_SYSTEM_PROMPT, TOPIC_CONSOLIDATION_SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)


# ==========================================
# PHASE 1: GENERATION (ASYNC WORKER)
# ==========================================

async def generate_main_topic_async(post: dict) -> Union[str, None]:
    """
    ASYNC worker: Generates the main topic for a single post.
    NOTE: DB I/O is handled outside the worker to maintain async purity.
    """
    post_id = post.get("_id")
    text_content = (post.get("postText") or post.get("raw_text") or post.get("description") or "")
    
    if not text_content or len(text_content) < 10:
        return {"post_id": post_id, "topic": None}

    try:
        response = await aclient.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": TOPIC_GENERATION_SYSTEM_PROMPT}, {"role": "user", "content": text_content}],
            temperature=0.3, max_tokens=20 
        )
        topic = response.choices[0].message.content.strip().lower().strip(".").strip()
        
        # Returns the topic for the batch runner to save in bulk
        return topic
        
    except Exception as e:
        logging.error(f"Error generating AI topic for {post_id}: {e}")
        return {"post_id": post_id, "topic": None} # Return for bulk update


async def run_topic_generation_batch_async(db, batch_size: int = 100) -> int:
    """
    ASYNCHRONOUS BATCH RUNNER (Phase 1): Orchestrates workers and handles bulk DB I/O.
    """
    try:
        # CRITICAL FIX: Run synchronous DB fetch safely in a threadpool
        unprocessed_posts = await asyncio.to_thread(db.get_unclassified_posts_for_keyword, batch_size) 
    except Exception as e:
        logging.error(f"DB fetch error in trend analysis: {e}")
        return 0
    
    if not unprocessed_posts: return 0

    logging.info(f"Generating main topic for {len(unprocessed_posts)} posts...")

    tasks = [generate_main_topic_async(post) for post in unprocessed_posts]
    
    # Run the workers concurrently
    results = await asyncio.gather(*tasks) 
    clean_results = [r for r in results if r is not None]
    
    # CRITICAL FIX: Update the DB in bulk using a synchronous threadpool call
    await asyncio.to_thread(db.update_posts_keywords_bulk_sync, clean_results) 
    
    valid_results = [r for r in clean_results if r.get('topic') is not None]    
    return len(valid_results)


# ==========================================
# PHASE 2 & 3: CONSOLIDATION & SWEEP MANAGER
# ==========================================

def consolidate_topics_sync(topics_list: List[str]) -> Dict[str, str]:
    """Synchronous helper function to call the AI for topic consolidation."""
    if not topics_list: return {}
    unique_topics = list(set(topics_list))
    mapping = {}
    client = OpenAI(api_key=OPENAI_API_KEY) 
    batch_size = 100 
    
    for i in range(0, len(unique_topics), batch_size):
        batch = unique_topics[i:i + batch_size]
        logging.info(f"Consolidating batch {i//batch_size + 1} with {len(batch)} topics...")
        
        prompt = (TOPIC_CONSOLIDATION_SYSTEM_PROMPT + "\n\n" + "Input List:\n" + json.dumps(batch) + "\n\n" + "Return ONLY the JSON object.")

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini", messages=[{"role": "system", "content": "You output only valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.1, response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            mapping.update(json.loads(content))
        except Exception as e:
            logging.error(f"Error consolidating topics batch: {e}")
            mapping.update({t: t for t in batch})
            time.sleep(1)
            
    return mapping


def run_trend_analysis_sweep(db, batch_size: int = None):
    """
    MAIN ENTRY POINT: Orchestrates the entire trend analysis (Generation + Consolidation).
    Accepts batch_size to fix API error.
    """
    logging.info("--- STARTING TREND ANALYSIS SWEEP ---")
    
    # Use the passed batch size if it's sensible, otherwise default to 50
    BATCH_SIZE_TO_USE = batch_size if batch_size is not None and batch_size > 0 else 50
    
    # 1. Continuous Generation Sweep Loop
    total_generated = 0
    while True:
        # CRITICAL FIX: Run the ASYNC batch runner synchronously here
        posts_generated_count = asyncio.run(run_topic_generation_batch_async(db, batch_size=BATCH_SIZE_TO_USE)) 
        
        if posts_generated_count == 0: break
        total_generated += posts_generated_count
        logging.info(f"Generated keywords for {posts_generated_count} posts. Total: {total_generated}. Continuing sweep...")
        time.sleep(1) 

    logging.info("--- PHASE 2: CONSOLIDATION AND SAVING ANALYTICS ---")
    
    # 2. Collect ALL Processed Posts for Trend Analysis
    all_posts_cursor = db.posts_collection.find({"keywords_generated": True})
    
    raw_keywords = []
    hashtag_counter = Counter()

    for post in all_posts_cursor:
        topic = post.get("keywords")
        if topic and isinstance(topic, str):
            clean_topic = re.sub(r'[^\w\s]', '', topic).lower()
            if clean_topic: raw_keywords.append(clean_topic)

        # Process Hashtags
        raw_hashtags = post.get("hashtag") or post.get("hashtags")
        if raw_hashtags and raw_hashtags != 'null':
            tag_list = raw_hashtags if isinstance(raw_hashtags, list) else raw_hashtags.split(',')
            for tag in tag_list:
                if isinstance(tag, str):
                    clean_tag = tag.strip().lower().replace("#", "")
                    if clean_tag: hashtag_counter[clean_tag] += 1

    # 3. Consolidate ALL Keywords via AI
    topic_mapping = consolidate_topics_sync(raw_keywords)
    
    # 4. Count the Consolidated Topics
    final_keyword_counter = Counter()
    for raw_k in raw_keywords:
        standardized_name = topic_mapping.get(raw_k, raw_k)
        final_keyword_counter[standardized_name] += 1

    # 5. Save Analysis to dedicated collection 
    db.save_trend_analysis(final_keyword_counter, hashtag_counter) 
    
    logging.info("Trend Analysis Sweep Complete.")
    return total_generated