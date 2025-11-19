import os
import time
import uuid
from pymongo import MongoClient, errors
from google import genai
from pydantic import BaseModel, Field
from typing import Literal, Union  # <-- ADDED Union HERE
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- 1. Define Output Structure ---
# Changed to include a confidence score (simulated) for better data structure
class ClassificationOutput(BaseModel):
    """Schema for the misinformation classification output."""
    check_label: Literal["MISINFORMATION", "AUTHENTIC", "UNCERTAIN"] = Field(
        description="The classification label for the tweet content."
    )
    justification: str = Field(
        description="A brief, one-sentence reason for the classification."
    )
    # Simulate a confidence field since the base API doesn't provide it directly.
    # We ask the model to provide a score, which is stored as a string here.
    confidence_score: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        description="Confidence level in the classification: HIGH, MEDIUM, or LOW."
    )

# --- 2. Configuration & MongoDB Connection ---

# Database names from your existing setup (CleanedTweet is the source, the new one is the target)
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable not set. Please check your .env file.")

DB_NAME = "TweetData"
SOURCE_COLLECTION_NAME = "CleanedTweet"
TARGET_COLLECTION_NAME = "misinfo_classific"

mongo_client = MongoClient(MONGO_URI)
source_collection = mongo_client[DB_NAME][SOURCE_COLLECTION_NAME]
target_collection = mongo_client[DB_NAME][TARGET_COLLECTION_NAME]

# Initialize Gemini Client (automatically uses GEMINI_API_KEY from environment)
try:
    # We pass the API key explicitly here as a fallback in case the environment variable isn't loaded correctly 
    # for the entire session, although os.getenv should handle it.
    gemini_client = genai.Client()
except Exception as e:
    raise RuntimeError(f"Gemini Client initialization failed. Check GEMINI_API_KEY. Error: {e}")

# --- 3. Gemini API Function ---
# CHANGED: Replaced 'dict | None' with 'Union[dict, None]'
def classify_tweet_with_gemini(tweet_text: str) -> Union[dict, None]:
    # System Instruction: Define the model's role and rules
    system_instruction = (
        "You are an expert social media misinformation classifier. "
        "Analyze the provided text, which is a translation of a public disaster-related tweet from Malaysia. "
        "Your task is to classify it into one of three categories: 'MISINFORMATION', 'AUTHENTIC', or 'UNCERTAIN'. "
        "Also, provide your confidence in this classification (HIGH, MEDIUM, or LOW)."
        "Your final output MUST strictly conform to the requested JSON schema."
    )
    
    # Prompt: The user's input text
    contents = [
        {"role": "user", "parts": [{"text": f"Classify this tweet: {tweet_text}"}]}
    ]

    # Implement basic exponential backoff for resilience
    for attempt in range(3):
        try:
            response = gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=contents,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json",
                    "response_schema": ClassificationOutput,
                    "temperature": 0.1 # Keep temperature low for factual classification
                }
            )
            # Validate and return the structured data
            return ClassificationOutput.model_validate_json(response.text).model_dump()
            
        except Exception as e:
            print(f"Gemini API Error (Attempt {attempt + 1}): {e}")
            if attempt < 2:
                time.sleep(2 ** attempt) # Exponential backoff: 1s, 2s, 4s...
            else:
                return None
    return None

# --- 4. Main Processing Loop ---
def process_tweets_for_classification():
    # Only fetch tweets that have not yet been classified by checking the target collection
    
    # Get all tweet_ids that are already classified
    classified_ids = target_collection.distinct("tweet_id")
    
    # Query for documents from the source collection where 'tweet_id' is NOT in the classified list
    query = {"tweet_id": {"$nin": classified_ids}}
    
    # Use a batch size for efficient processing
    batch_size = 50
    
    print(f"Starting classification. Source: {SOURCE_COLLECTION_NAME}, Target: {TARGET_COLLECTION_NAME}")

    while True:
        # Fetch the next batch of unclassified tweets
        unclassified_tweets = list(source_collection.find(query).limit(batch_size))

        if not unclassified_tweets:
            print("All available tweets have been classified. Exiting.")
            break

        print(f"Processing a batch of {len(unclassified_tweets)} unclassified tweets...")
        
        insert_documents = []
        for tweet in unclassified_tweets:
            tweet_id = tweet.get('tweet_id')
            # Use the pre-processed and translated text
            text = tweet.get('translated_text') 

            if not text:
                print(f"Skipping tweet {tweet_id}: Missing translated_text.")
                continue

            classification_result = classify_tweet_with_gemini(text)
            
            if classification_result:
                # --- Create new classification document ---
                new_doc = {
                    "check_id": str(uuid.uuid4()), # Generate a new unique ID for the classification record
                    "tweet_id": tweet_id,         # Reference to the original tweet
                    "check_label": classification_result["check_label"],
                    "confidence": classification_result["confidence_score"],
                    "classification_justification": classification_result["justification"],
                    "classification_model": "gemini-2.5-flash",
                    "timestamp": time.time()
                }
                insert_documents.append(new_doc)
            else:
                # Add the failed ID back to the exclusion list for this run to avoid immediate retry
                classified_ids.append(tweet_id)


        # --- 5. Insert New Classification Records into the Target Collection ---
        if insert_documents:
            try:
                target_collection.insert_many(insert_documents, ordered=False)
                print(f"Successfully inserted {len(insert_documents)} new classification records into {TARGET_COLLECTION_NAME}.")
            except errors.BulkWriteError as bwe:
                # Handle cases where some inserts might fail (e.g. duplicate check_id, though UUID should prevent this)
                print(f"Bulk write error encountered. Check logs for details: {bwe.details}")
        else:
            print("No new successful classifications in this batch.")
            
if __name__ == "__main__":
    process_tweets_for_classification()