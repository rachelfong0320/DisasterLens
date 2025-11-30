import sys
import os

# Add the parent directory ('backend') to sys.path so we can import 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import re
import time
import json
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
                    "content": "You are a disaster analyst. Extract the SINGLE most important event and location from the text. Format: '[Event] in [Location]' or just '[Event]' if no location. Keep it short (max 5 words). Examples: 'Flood in Johor', 'Landslide Ampang', 'Heavy Rain'. Return ONLY the phrase."
                },
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=20 
        )
        topic = response.choices[0].message.content.strip().lower()
        # Remove any trailing punctuation
        topic = topic.strip(".").strip()
        return topic
    except Exception as e:
        print(f"Error generating AI topic: {e}")
        return None

def consolidate_topics(topics_list):
    """
    Uses OpenAI to group similar variations of topics into a single canonical name.
    Input: ["landslide along km48 sibubintulu road", "landslide in sibu bintulu road"]
    Output: {"landslide along km48 sibubintulu road": "Landslide Sibu-Bintulu Road", ...}
    """
    if not topics_list:
        return {}
        
    # Remove duplicates for the API call
    unique_topics = list(set(topics_list))
    
    # For efficiency, if there are too many unique topics, process in batches.
    # Here we process all at once for simplicity, assuming < 100 unique topics.
    # In production, you'd chunk this list.
    
    print(f"Asking AI to consolidate {len(unique_topics)} unique topics...")
    
    prompt = (
        "You are a strict data normalization expert. I have a list of disaster-related topics. "
        "Your goal is to MERGE variations that refer to the same event into a single, standardized, Capitalized Name.\n\n"
        "CRITICAL RULES:\n"
        "1. Treat 'Landslide Sibu', 'Landslide Bintulu', 'Landslide KM48' as the SAME event if they likely refer to the 'Sibu-Bintulu Road Landslide'.\n"
        "2. Treat 'Flood Johor', 'Johor Bahru Flooding', 'Floods in JB' as the SAME event: 'Flood in Johor'.\n"
        "3. Ignore minor differences like 'in', 'at', 'road', 'jalan', 'km'.\n\n"
        "Input List:\n" + "\n".join(unique_topics) + "\n\n"
        "Return ONLY a valid JSON object where keys are the input topics and values are the standardized group name.\n"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # Slightly higher temp allows for better semantic matching
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        mapping = json.loads(content)
        return mapping
    except Exception as e:
        print(f"Error consolidating topics: {e}")
        # Fallback: map topics to themselves if AI fails
        return {t: t for t in unique_topics}


def process_posts_and_analyze_trends():
    print("\n" + "="*40)
    print("STEP 5: KEYWORD & HASHTAG TRACKING")
    print("="*40 + "\n")

    print("Starting Single-Keyword Generation & Trend Analysis...")

    # --- PHASE 1: Generate Keyword (One Main Topic) ---
    
    query = {"keywords_generated": {"$ne": True}}
    total_to_generate = db_connection.posts_data_collection.count_documents(query)
    cursor = db_connection.posts_data_collection.find(query)
    
    print(f"Generating main topic for {total_to_generate} posts...")

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

    print("Phase 1 Complete.")

    # --- PHASE 2: Analyze Trends (With Consolidation) ---
    
    print("Analyzing trends from ALL posts...")
    
    all_posts = db_connection.posts_data_collection.find({})
    
    # 1. Collect ALL raw terms first
    raw_keywords = []
    hashtag_counter = Counter()

    for post in all_posts:
        # A. Collect Keyword (String)
        topic = post.get("keywords")
        if topic and isinstance(topic, str):
            # Basic cleanup before list collection
            clean_topic = re.sub(r'[^\w\s]', '', topic).lower()
            if clean_topic:
                raw_keywords.append(clean_topic)

        # B. Process Hashtags (List/String) - Standard count is fine for hashtags
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

    # 2. Consolidate Keywords via AI
    # This is the critical step you asked for.
    # It sends ALL collected raw keywords to OpenAI to group them semantically.
    topic_mapping = consolidate_topics(raw_keywords)
    
    # 3. Count the Consolidated Topics
    final_keyword_counter = Counter()
    for raw_k in raw_keywords:
        # Get the standardized name from the map. 
        # e.g. raw_k="landslide sibu" -> standardized_name="Landslide Sibu-Bintulu Road"
        standardized_name = topic_mapping.get(raw_k, raw_k)
        final_keyword_counter[standardized_name] += 1


    # --- PHASE 3: Save Analysis ---
    
    print("Saving analysis to 'tracking_keyword' collection...")
    
    tracking_collection = db_connection.analytics_db["tracking_keyword"]
    
    tracking_collection.delete_many({}) 
    new_documents = []
    
    # Save Keywords (Topics) - These are now consolidated
    for term, freq in final_keyword_counter.items():
        new_documents.append({
            "term": term,
            "type": "keyword",
            "frequency": freq,
            "updated_at": datetime.now(timezone.utc)
        })

    # Save Hashtags
    for term, freq in hashtag_counter.items():
        new_documents.append({
            "term": f"#{term}", 
            "type": "hashtag",
            "frequency": freq,
            "updated_at": datetime.now(timezone.utc)
        })

    if new_documents:
        tracking_collection.insert_many(new_documents)
        
    print(f"Complete!")
    print(f" - Unique Consolidated Topics: {len(final_keyword_counter)}")
    print(f" - Unique Hashtags: {len(hashtag_counter)}")

if __name__ == "__main__":
    process_posts_and_analyze_trends()