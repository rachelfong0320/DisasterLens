# main_classifier.py
import time
import uuid
import asyncio
from typing import Union
from openai import AsyncOpenAI 
from tqdm.asyncio import tqdm_asyncio 
from pymongo import errors

# Import from our new modules
from core.config import OPENAI_API_KEY
from .dbConnection import tweet_collection, misinfo_collection
from .schemas import ClassificationOutput
from .prompts import MISINFO_SYSTEM_PROMPT

# Initialize Async Client
aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

async def classify_tweet_async(tweet: dict, sem: asyncio.Semaphore) -> Union[dict, None]:
    tweet_id = tweet.get('tweet_id')
    text = tweet.get('translated_text') or tweet.get('cleaned_text') or tweet.get('raw_text')

    if not text or len(text) < 5:
        return None

    async with sem:
        for attempt in range(3):
            try:
                completion = await aclient.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": MISINFO_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Tweet: {text}"},
                    ],
                    response_format=ClassificationOutput,
                    temperature=0.1,
                )
                result = completion.choices[0].message.parsed
                
                return {
                    "check_id": str(uuid.uuid4()),
                    "tweet_id": tweet_id,
                    "check_label": result.check_label,
                    "confidence": result.confidence_score,
                    "reasoning": result.reasoning,
                    "classification_justification": result.justification,
                    "classification_model": "gpt-4o-mini",
                    "timestamp": time.time()
                }
            except Exception as e:
                if "429" in str(e):
                    await asyncio.sleep(2 ** (attempt + 1))
                else:
                    print(f"Error {tweet_id}: {e}")
                    break
        return None

async def run_classification_job():
    """Main entry point for the classifier."""
    sem = asyncio.Semaphore(20)
    batch_size = 100 
    print(f"--- Starting Classification Job ---")

    while True:
        classified_ids = misinfo_collection.distinct("tweet_id")
        query = {"tweet_id": {"$nin": classified_ids}}
        
        # Get tweets not yet classified
        batch_tweets = list(tweet_collection.find(query).limit(batch_size))
        if not batch_tweets:
            print("No new unclassified tweets found. Classification finished.")
            break

        print(f"Classifying batch of {len(batch_tweets)} tweets...")
        tasks = [classify_tweet_async(tweet, sem) for tweet in batch_tweets]
        results = await tqdm_asyncio.gather(*tasks, desc="Processing")

        valid_results = [res for res in results if res is not None]

        if valid_results:
            try:
                misinfo_collection.insert_many(valid_results, ordered=False)
                print(f"Saved {len(valid_results)} classifications.")
            except errors.BulkWriteError:
                print("Partial write completed (duplicates skipped).")
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_classification_job())