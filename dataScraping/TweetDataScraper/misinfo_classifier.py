import os
import time
import uuid
import asyncio
from typing import Literal, List, Union, Optional # Added Union and Optional for Python 3.9 compatibility
from dotenv import load_dotenv
from pymongo import MongoClient, errors
from pydantic import BaseModel, Field
from openai import AsyncOpenAI 
from tqdm.asyncio import tqdm_asyncio 

# --- 1. Setup & Configuration ---

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not MONGO_URI or not OPENAI_API_KEY:
    raise ValueError("Missing environment variables. Check MONGO_URI and OPENAI_API_KEY.")

# MongoDB Setup
DB_NAME = "TweetData"
SOURCE_COLLECTION = "CleanedTweet"
TARGET_COLLECTION = "misinfo_classific"

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
You are an elite misinformation analyst specializing in Malaysian disaster events.
Your goal is to classify public tweets (user-generated content) to identify credible on-the-ground information.
**Note:** This system processes NON-OFFICIAL posts. The input is text-only (no images/videos provided).

**Target Keywords / Event Scope:**
The tweets were collected using these keywords. Use this to understand the context of the disaster:
- **Malay**: banjir (flood), tanah runtuh (landslide), ribut (storm), jerebu (haze), kebakaran hutan (forest fire), mendapan tanah (sinkhole), gempa bumi (earthquake), tsunami.
- **English**: flood, landslide, storm, haze, forest fire, sinkhole, earthquake.

**Definitions:**
1. **AUTHENTIC**: Credible, user-generated reports of disaster events. Includes:
    - **Eyewitness Accounts**: First-hand observations (e.g., "Water is entering my porch in Taman Sri Muda", "Landslide blocking the road to Genting").
    - **Descriptive Text**: Tweets describing current conditions, water levels, or weather at specific locations.
    - **Community Alerts**: Warnings from citizens about specific, verifiable locations (e.g., "Avoid highway X, it's flooded").
    - **Proxy Reports**: Credible reports from relatives/friends on the ground (e.g., "My mom in [Kampung] says electricity is cut").
2. **MISINFORMATION**: Demonstrably false or misleading information. Includes:
    - Debunked rumors, hoaxes, or "fake news".
    - Claims of old events being new (recycling old flood stories).
    - Conspiracy theories or politically motivated fabrication about the disaster.
    - Exaggerated panic without any basis in reality.
3. **UNCERTAIN**: Ambiguous, unverifiable, or low-value content. Includes:
    - Vague questions ("Is it flooding anywhere?").
    - General complaints or emotional expressions without location/event context ("I hate the rain", "Scared of floods").
    - Unverified third-party hearsay ("I heard a rumor that...").
    - Jokes or memes unrelated to the actual disaster situation.

**Instructions:**
- **Bias towards AUTHENTIC for First-Hand Info**: If a tweet sounds like a real person describing a disaster event in a specific place, label it AUTHENTIC.
- **Text-Only Context**: You cannot see images. If a tweet says "Look at this photo", judge authenticity based on the accompanying text description and hashtags.
- **Context Matters**: "Heavy rain" in a known flood-prone area (e.g., Klang, Kelantan) during monsoon season is a valid observation.
- **Tone Analysis**: Urgent or distressed tone is normal. Only label MISINFORMATION if the content is highly suspicious or contradicts known facts.
- **Reasoning**: Briefly explain *why* the tweet seems credible (e.g., "Specific location mentioned", "First-hand tone") or not.
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
    print(f"Starting Async Classification.")
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