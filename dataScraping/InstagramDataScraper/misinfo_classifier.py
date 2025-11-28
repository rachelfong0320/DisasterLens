import os
import time
import uuid
import asyncio
from typing import Literal, List, Union, Optional
from dotenv import load_dotenv
from pymongo import MongoClient, errors
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm_asyncio

#Setup and configuration
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
 
if not MONGO_URI or not OPENAI_API_KEY:
    raise ValueError("Missing environment variables. Check MONGO_URI and OPENAI_API_KEY.")

mongoClient = MongoClient(MONGO_URI)

#mongoDB Setup
DB_NAME = "Instagram"
SOURCE_COLLECTION = "cleaned_posts"
TARGET_COLLECTION = "misinfo_classific_data"

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
source_collection = db[SOURCE_COLLECTION]
target_collection = db[TARGET_COLLECTION]

try:
    source_collection.create_index("ig_post_id", unique=True)
except errors.OperationFailure:
    pass

try:
    target_collection.create_index("ig_post_id", unique=True)
except errors.OperationFailure:
    pass

aclient = AsyncOpenAI(api_key=OPENAI_API_KEY)

#output schema
class ClassificationOutput(BaseModel):
    reasoning: str = Field(
        description="Step-by-step analysis of the posts's content, tone, and specificity."
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

 #prompt template
SYSTEM_PROMPT = """
You are a senior misinformation analyst specializing in Malaysian disaster events
(floods, storms, landslides, haze, typhoons). Your task is to classify **Instagram posts**, 
which are usually short, emotional, and lack structured reporting.

Instagram content is NOT like news, NOT like tweets, and often mixes daily life stories 
with partial weather mentions. You must be extremely strict about what counts as 
real disaster reporting.

-------------------------------------
CLASSIFICATION DEFINITIONS
-------------------------------------

1. AUTHENTIC  
A post is AUTHENTIC ONLY IF:
- It clearly describes a real event the poster directly witnessed, OR
- Includes **specific, verifiable details**, such as:
  • measurable conditions (e.g., “water level up to my knees at Kampung XYZ”),  
  • **precise location** (town/road/area),  
  • **clear evidence of firsthand experience**,  
  • **official alerts** (NADMA, JPS, MetMalaysia).
- Tone is factual, not dramatic or vague.

If the post *mentions rain or flood casually without specifics*, it is NOT authentic.

2. MISINFORMATION  
Label MISINFORMATION when:
- The post exaggerates danger without evidence (“Penang is sinking!”, “KL totally flooded!”),
- Uses dramatic warnings with no factual basis,
- Shares **old events as if new**,
- Contains **false claims**, conspiracy, or viral panic,
- Misleads the reader about the severity or timing of the event.

3. UNCERTAIN  
Label UNCERTAIN when:
- The caption is vague (“Penang ribut, everyone stay safe…”),
- The post mentions bad weather but gives no factual detail,
- The post is a **personal story** with rain/flood mentioned incidentally,
- The event cannot be verified,
- It might be real, but evidence is weak.

-------------------------------------
CLASSIFICATION LOGIC (MUST FOLLOW)
-------------------------------------

You MUST examine:
- Specificity of details (time, location, measurable impact),
- Whether the poster is a direct witness,
- Whether the tone is factual vs dramatic,
- Whether the location matches known Malaysian geography,
- Whether hashtags repeat rumors (#banjir #ribut #prayforpenang without details → UNCERTAIN).

-------------------------------------
DECISION RULES
-------------------------------------

IF a post has:
- NO specific details → UNCERTAIN  
- ONLY emotional/hopeful prayers (“Stay safe guys…”) → UNCERTAIN  
- A long personal story irrelevant to disaster → UNCERTAIN  
- Specific witnessed conditions WITH proof → AUTHENTIC  
- Dramatic claims without evidence → MISINFORMATION  
- Outdated / misleading information → MISINFORMATION

-------------------------------------
OUTPUT REQUIREMENTS
-------------------------------------

Give:
1. Step-by-step reasoning (must show your thought process)
2. One of: AUTHENTIC, MISINFORMATION, UNCERTAIN
3. One-line justification
4. Confidence score between 0.0 and 1.0
"""  

#classifier function
async def classify_instagram_post(post: dict, sem: asyncio.Semaphore):
    ig_post_id = post.get("ig_post_id")
    
    #text priority
    text = (
        post.get("transalated_description") or
        post.get("cleaned_description") or
        post.get("description") or ""
    )

    hashtags = post.get("hashtags")
    if hashtags:
        text += " Hashtags: " + hashtags.replace(",", " ")

    location = post.get("location_name") or post.get("city") or ""
    if location:
        text += f" Location: {location}"

    # Skip if still too short
    if not text or len(text) < 5:
        print(f"Skipping {ig_post_id}: text too short or missing")
        source_collection.update_one(
            {"ig_post_id": ig_post_id},
            {"$set": {"classification_attempted": True}}
        )
        return None
    
    async with sem:
        for attempt in range(3):
            try:
                completion = await aclient.beta.chat.completions.parse(
                    model = "gpt-4o-mini",
                    messages=[
                        {"role":"system","content": SYSTEM_PROMPT},
                        {"role":"user","content": f"Instagram Post:{text}"},
                    ],
                    response_format=ClassificationOutput,
                    temperature = 0.1,
                )

                result = completion.choices[0].message.parsed

                return {
                    "check_id": str(uuid.uuid4()),
                    "ig_post_id": ig_post_id,
                    "check_label": result.check_label,
                    "confidence" : result.confidence_score,
                    "reasoning": result.reasoning,
                    "classification_justification": result.justification,
                    "classification_model": "gpt-4o-mini",
                    "timestamp": time.time(),
                }
            
            except Exception as e:
                if "429" in str(e) or "5" in str(e):  # Rate limit or server errors
                    print(f"Retrying {ig_post_id} due to error: {e}")
                    await asyncio.sleep(2 ** (attempt + 1))
                else:
                    print(f"Error processing {ig_post_id}: {e}")
                    break

        # Mark as attempted if failed after retries
        source_collection.update_one(
            {"ig_post_id": ig_post_id},
            {"$set": {"classification_attempted": True}}
        )
        return None        
    
# Main loop
async def main():
    sem = asyncio.Semaphore(20)
    batch_size = 100

    print("Starting instagram misinformation classification...")

    while True:
        classified_ids = target_collection.distinct("ig_post_id")
        query = {
            "ig_post_id": {"$nin": classified_ids},
            "classification_attempted": {"$ne": True}  # Skip already attempted failures
        }
        batch_posts = list(source_collection.find(query).limit(batch_size))

        if not batch_posts:
            print("No more posts to classify. Exiting.")
            break

        print(f"Processing {len(batch_posts)} posts...")
        
        tasks = [classify_instagram_post(post, sem) for post in batch_posts]
        results = await tqdm_asyncio.gather(*tasks, desc = "Classifying posts")

        valid_results = [res for res in results if res is not None]

        if valid_results:
            try:
                target_collection.insert_many(valid_results, ordered=False)
                print(f"Inserted {len(valid_results)} classified posts.")
            except errors.BulkWriteError as bwe:
                print(f"Inserted {bwe.details['nInserted']}(some duplicates).")

        await asyncio.sleep(1)  # Brief pause between batches

if __name__ == "__main__":
    asyncio.run(main())