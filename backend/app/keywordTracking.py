import sys
import os

# Add the parent directory ('backend') to sys.path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
import time
from datetime import datetime, timezone
from collections import Counter
from openai import OpenAI
from app.database import db_connection
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================
# CONFIGURATION
# ==========================================
# Set this to True if you want to ERASE existing keywords and start fresh.
# Use with caution! It removes 'keywords' and 'keywords_generated' fields.
RESET_ALL = False 

def generate_main_topic(text: str):
    """
    Uses OpenAI to extract the ONE main topic/event from the text.
    Returns a single string like "Heavy rain in Subang".
    """
    if not text or len(text) < 10:
        return None

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a very famous and expert disaster analyst. Extract the SINGLE most important event and location from the text. Format: '[Event] in [Location]' or just '[Event]' if no location. Keep it short (max 5 words). Examples: 'Flood in Johor', 'Landslide Ampang', 'Heavy Rain'. Return ONLY the phrase."
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=20 # Keep it very short
        )
        topic = response.choices[0].message.content.strip().lower()
        # Remove any trailing punctuation
        topic = topic.strip(".").strip()
        return topic
    except Exception as e:
        print(f"Error generating AI topic: {e}")
        return None

def normalize_term(term: str):
    """
    Normalizes a phrase to handle word order differences.
    e.g., "Johor Flood" -> "flood johor"
    e.g., "Flood in Johor" -> "flood in johor" -> (sort) -> "flood in johor"
    """
    if not term:
        return None
        
    # Remove punctuation except spaces
    clean_term = re.sub(r'[^\w\s]', '', term).lower()
    
    # Remove common stop words that don't add meaning to the trend
    stop_words = {'in', 'at', 'the', 'is', 'a', 'of', 'on'}
    words = [w for w in clean_term.split() if w not in stop_words]
    
    # Sort alphabetically to unify "Flood Johor" and "Johor Flood"
    words.sort()
    return " ".join(words)

def process_posts_and_analyze_trends():
    print("🚀 Starting Single-Keyword Generation & Trend Analysis...")

    # --- OPTIONAL: RESET ---
    if RESET_ALL:
        print("⚠️ RESET DETECTED: Clearing previous keyword data...")
        db_connection.posts_data_collection.update_many(
            {}, 
            {"$unset": {"keywords": "", "keywords_generated": ""}}
        )
        print("✅ Data cleared. Starting fresh generation.")

    # --- PHASE 1: Generate Keyword (One Main Topic) ---
    
    query = {"keywords_generated": {"$ne": True}}
    total_to_generate = db_connection.posts_data_collection.count_documents(query)
    cursor = db_connection.posts_data_collection.find(query)
    
    print(f"📊 Generating main topic for {total_to_generate} posts...")

    count = 0
    for post in cursor:
        source_id = post.get("_id")
        text_content = (
            post.get("postText") or 
            post.get("raw_text") or 
            post.get("description") or 
            ""
        )

        # 1. Generate SINGLE phrase (e.g. "flood in johor")
        main_topic = generate_main_topic(text_content)
        
        # 2. Save back to post as a STRING (not a list)
        if main_topic:
            try:
                db_connection.posts_data_collection.update_one(
                    {"_id": source_id},
                    {
                        "$set": {
                            "keywords": main_topic,       # Saved as String
                            "keywords_generated": True 
                        }
                    }
                )
            except Exception as e:
                print(f"Error updating post {source_id}: {e}")
        else:
            # Mark as processed even if no topic found, so we don't retry forever
             db_connection.posts_data_collection.update_one(
                {"_id": source_id},
                {"$set": {"keywords_generated": True}}
            )

        count += 1
        if count % 10 == 0:
            print(f"   - Generated for {count}/{total_to_generate} posts")

    print("✅ Phase 1 Complete.")

    # --- PHASE 2: Analyze Trends ---
    
    print("📊 Analyzing trends from ALL posts...")
    
    all_posts = db_connection.posts_data_collection.find({})
    
    keyword_counter = Counter()
    hashtag_counter = Counter()

    for post in all_posts:
        # A. Process Keyword (String)
        topic = post.get("keywords")
        if topic and isinstance(topic, str):
            normalized = normalize_term(topic)
            if normalized:
                keyword_counter[normalized] += 1

        # B. Process Hashtags (List/String)
        raw_hashtags = post.get("hashtag") or post.get("hashtags") or post.get("tweet_hashtags")
        
        tag_list = []
        if raw_hashtags and raw_hashtags != 'null':
             if isinstance(raw_hashtags, str):
                tag_list = raw_hashtags.split(',')
             elif isinstance(raw_hashtags, list):
                tag_list = raw_hashtags
        
        for tag in tag_list:
            if isinstance(tag, str):
                clean_tag = tag.strip().lower().replace("#", "")
                if clean_tag:
                    hashtag_counter[clean_tag] += 1

    # --- PHASE 3: Save Analysis ---
    
    print("💾 Saving analysis to 'tracking_keyword' collection...")
    
    tracking_collection = db_connection.analytics_db["tracking_keyword"]
    
    # Save Keywords (Topics)
    for term, freq in keyword_counter.items():
        doc = {
            "term": term,
            "type": "keyword",
            "frequency": freq,
            "updated_at": datetime.now(timezone.utc)
        }
        tracking_collection.update_one(
            {"term": term, "type": "keyword"}, 
            {"$set": doc}, 
            upsert=True
        )

    # Save Hashtags
    for term, freq in hashtag_counter.items():
        doc = {
            "term": f"#{term}", 
            "type": "hashtag",
            "frequency": freq,
            "updated_at": datetime.now(timezone.utc)
        }
        tracking_collection.update_one(
            {"term": f"#{term}", "type": "hashtag"}, 
            {"$set": doc}, 
            upsert=True
        )
        
    print(f"🎉 Complete! Found {len(keyword_counter)} unique topics.")

if __name__ == "__main__":
    process_posts_and_analyze_trends()