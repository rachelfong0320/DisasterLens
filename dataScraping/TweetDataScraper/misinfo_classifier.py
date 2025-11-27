import os
import time
import uuid
import asyncio
from typing import Literal, List, Union, Optional # Added Union and Optional for Python 3.9 compatibility
from dotenv import load_dotenv
from pymongo import MongoClient, errors
from pydantic import BaseModel, Field
from openai import AsyncOpenAI  # <-- CHANGED: Import Async Client
from tqdm.asyncio import tqdm_asyncio # <-- CHANGED: Async progress bar

# --- 1. Setup & Configuration ---

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not MONGO_URI or not OPENAI_API_KEY:
    raise ValueError("Missing environment variables. Check MONGO_URI and OPENAI_API_KEY.")

# MongoDB Setup
DB_NAME = "TweetData"
SOURCE_COLLECTION = "CleanedTweet"
TARGET_COLLECTION = "misinfo_classific_data"

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
source_collection = db[SOURCE_COLLECTION]
target_collection = db[TARGET_COLLECTION]

# Ensure indexes exist for speed
# We use try-except to strictly avoid 'IndexKeySpecsConflict' if the index exists with different options
try:
    source_collection.create_index("tweet_id", unique=True)
except errors.OperationFailure:
    # Index likely exists with different options (e.g., non-unique), which is fine for reading
    pass

try:
    target_collection.create_index("tweet_id", unique=True)
except errors.OperationFailure:
    pass

# Initialize Async Client
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

# --- 2. Advanced Output Schema ---

class ClassificationOutput(BaseModel):
    """Schema for the misinformation classification output."""
    
    reasoning: str = Field(
        description="Step-by-step analysis of the tweet's content, tone, and specificity."
    )
    check_label: Literal["MISINFORMATION", "AUTHENTIC", "UNCERTAIN"] = Field(
        description="The final classification label."
    )
    justification: str = Field(
        description="A brief, one-sentence summary justification."
    )
    confidence_score: float = Field(
        description="A float score between 0.0 and 1.0 representing confidence."
    )

# --- 3. Enhanced Prompt (System Instruction) ---

SYSTEM_PROMPT = """
You are an elite misinformation analyst specializing in Malaysian disaster events (floods, landslides, etc.).
Your goal is to classify public tweets with high precision.

**Definitions:**
1. **AUTHENTIC**: Contains specific, verifiable details (e.g., "Water level at Sungai Golok is 9.5m at 2PM"), first-hand witness accounts with photos/videos implied, or official government alerts (NADMA, MetMalaysia).
2. **MISINFORMATION**: Contains debunked rumors, exaggerated panic without proof, conspiracy theories, or old footage reposted as new.
3. **UNCERTAIN**: Vague complaints, questions ("Is it raining in KL?"), or unverified third-party hearsay.

**Instructions:**
- Analyze the *specificity* of location and time.
- Analyze the *tone* (factual vs. sensationalist).
- If the tweet is an official alert or distinct first-hand report, label AUTHENTIC with high confidence (>0.85).
- If the tweet is vague or opinionated, label UNCERTAIN.
- First, think through your reasoning step-by-step in the 'reasoning' field to ensure accuracy.
"""

# --- 4. Async Classification Function ---

async def classify_tweet_async(tweet: dict, sem: asyncio.Semaphore) -> Union[dict, None]: # Changed return type hint for Python 3.9 compatibility
    """
    Classifies a single tweet using OpenAI with rate limiting.
    """
    tweet_id = tweet.get('tweet_id')
    # Prefer translated text, fallback to cleaned, then raw
    text = tweet.get('translated_text') or tweet.get('cleaned_text') or tweet.get('raw_text')

    if not text or len(text) < 5:
        return None

    async with sem: # Wait for a free slot in the semaphore
        for attempt in range(3):
            try:
                completion = await aclient.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Tweet: {text}"},
                    ],
                    response_format=ClassificationOutput,
                    temperature=0.1, # Low temperature for consistency
                )
                
                result = completion.choices[0].message.parsed
                
                return {
                    "check_id": str(uuid.uuid4()),
                    "tweet_id": tweet_id,
                    "check_label": result.check_label,
                    "confidence": result.confidence_score,
                    "reasoning": result.reasoning, # Capture the deep thinking
                    "classification_justification": result.justification,
                    "classification_model": "gpt-4o-mini",
                    "timestamp": time.time()
                }

            except Exception as e:
                if "429" in str(e): # Rate limit error
                    await asyncio.sleep(2 ** (attempt + 1)) # Exponential backoff
                else:
                    print(f"Error processing {tweet_id}: {e}")
                    break
        return None

# --- 5. Main Async Loop ---

async def main():
    # Rate Limit Control (Adjust based on your OpenAI Tier)
    # Tier 1 usually allows ~500 RPM. A semaphore of 20-30 is usually safe.
    # Initialize inside main() so it attaches to the correct event loop
    sem = asyncio.Semaphore(20)

    batch_size = 100 # Larger batch size for async
    print(f"🚀 Starting Async Classification.")
    print(f"Source: {SOURCE_COLLECTION} | Target: {TARGET_COLLECTION}")

    while True:
        # 1. Fetch IDs that are ALREADY classified
        # We do this every loop to ensure we don't re-do work if the script restarts
        classified_ids = target_collection.distinct("tweet_id")
        print(f"Found {len(classified_ids)} already classified tweets.")

        # 2. Query for tweets NOT IN that list
        query = {"tweet_id": {"$nin": classified_ids}}
        
        # Fetch a batch of unclassified tweets
        # Convert cursor to list immediately for async processing
        cursor = source_collection.find(query).limit(batch_size)
        batch_tweets = list(cursor)

        if not batch_tweets:
            print("All tweets classified! Exiting.")
            break

        print(f"\nProcessing batch of {len(batch_tweets)} tweets concurrently...")

        # 3. Process batch concurrently
        # This creates a list of tasks and runs them all at once
        # Pass the semaphore to the worker function
        tasks = [classify_tweet_async(tweet, sem) for tweet in batch_tweets]
        
        # tqdm_asyncio.gather shows the progress bar as tasks complete
        results = await tqdm_asyncio.gather(*tasks, desc="Classifying")

        # 4. Filter out None results (failed/skipped)
        valid_results = [res for res in results if res is not None]

        # 5. Bulk Insert
        if valid_results:
            try:
                # ordered=False allows valid docs to be inserted even if one fails (e.g. duplicate)
                target_collection.insert_many(valid_results, ordered=False)
                print(f"Saved {len(valid_results)} records to MongoDB.")
            except errors.BulkWriteError as bwe:
                print(f"Bulk write warning: {bwe.details['nInserted']} inserted, some failed (likely duplicates).")
        else:
            print("No valid classifications in this batch.")

        # Small pause between batches to be nice to the database
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())