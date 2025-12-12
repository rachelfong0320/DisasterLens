# main_misinfo_classifier.py
import time
import uuid
import asyncio
from typing import Union
from pymongo import errors
from tqdm.asyncio import tqdm_asyncio

from .config import aclient
from .dbConnection import DatabaseConnection
from .classifier_schemas import ClassificationOutput
from .prompts import MISINFO_SYSTEM_PROMPT_INSTAGRAM

db = DatabaseConnection()

async def classify_instagram_post(post: dict, sem: asyncio.Semaphore) -> Union[dict, None]:
    ig_post_id = post.get("ig_post_id")
    text = (
        post.get("translated_description")
        or post.get("cleaned_description")
        or post.get("description")
        or ""
    )

    hashtags = post.get("hashtags")
    if hashtags:
        text += f" Hashtags: {hashtags.replace(',', ' ')}"
    location = post.get("location_name") or post.get("city") or ""
    if location:
        text += f" Location: {location}"

    if not text or len(text) < 5:
        print(f"Skipping {ig_post_id}: text too short")
        db.mark_as_attempted(ig_post_id)
        return None

    async with sem:
        for attempt in range(3):
            try:
                completion = await aclient.beta.chat.completions.parse(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": MISINFO_SYSTEM_PROMPT_INSTAGRAM},
                        {"role": "user", "content": f"Instagram Post: {text}"},
                    ],
                    response_format=ClassificationOutput,
                    temperature=0.1,
                )
                result = completion.choices[0].message.parsed
                return {
                    "check_id": str(uuid.uuid4()),
                    "ig_post_id": ig_post_id,
                    "check_label": result.check_label,
                    "confidence": result.confidence_score,
                    "reasoning": result.reasoning,
                    "classification_justification": result.justification,
                    "classification_model": "gpt-4o-mini",
                    "timestamp": time.time(),
                }
            except Exception as e:
                if "429" in str(e) or "5" in str(e):
                    print(f"Retrying {ig_post_id} due to error: {e}")
                    await asyncio.sleep(2 ** (attempt + 1))
                else:
                    print(f"Error processing {ig_post_id}: {e}")
                    break

        db.mark_as_attempted(ig_post_id)
        return None


async def run_classification_job():
    sem = asyncio.Semaphore(20)
    batch_size = 100
    print("Starting Instagram misinformation classification...")

    while True:
        batch_posts = db.get_unclassified_posts(batch_size=batch_size)

        if not batch_posts:
            print("No more posts to classify. Exiting.")
            break

        print(f"Processing {len(batch_posts)} posts...")
        tasks = [classify_instagram_post(post, sem) for post in batch_posts]
        results = await tqdm_asyncio.gather(*tasks, desc="Classifying posts")

        valid_results = [res for res in results if res is not None]
        if valid_results:
            db.insert_many_classifications(valid_results)

        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(run_classification_job())
