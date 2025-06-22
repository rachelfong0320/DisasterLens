import pandas as pd
from helpers import safe_get, clean_caption, clean_hashtag, translate_caption, contains_malaysia_location

def parse_disaster_post(posts):
    """Parse raw Instagram posts into structured format"""
    parsed_posts = []

    for idx, post in enumerate(posts):
        if post is None or not isinstance(post, dict):
            print(f"Skipping item at index {idx}: Invalid post")
            continue

        try:
            caption = post.get("caption") or {}
            user = post.get("user") or {}
            loc = post.get("location") or {}

            hashtags_list = caption.get("hashtags")
            hashtags_str = ", ".join(hashtags_list) if isinstance(hashtags_list, list) else None

            post_data = {
                "ig_post_id": post.get("id"),
                "created_at": post.get("taken_at", ""),
                "caption_id": caption.get("id"),
                "description": caption.get("text"),
                "reported_as_spam": caption.get("did_report_as_spam"),
                "author_id": user.get("id"),
                "author_username": user.get("username"),
                "author_full_name": user.get("full_name"),
                "account_type": user.get("account_type"),
                "account_is_verified": user.get("is_verified"),
                "hashtags": hashtags_str,
                "gen_ai_detection_method": safe_get(post, "gen_ai_detection_method", "detection_method"),
                "high_risk_genai_flag": post.get("has_high_risk_gen_ai_inform_treatment"),
                "integrity_review_decision": post.get("integrity_review_decision"),
                "address": loc.get("address"),
                "city": loc.get("city"),
                "latitude": loc.get("lat"),
                "longitude": loc.get("lng"),
                "location_name": loc.get("name"),
                "location_short_name": loc.get("short_name"),
            }

            parsed_posts.append(post_data)

        except Exception as e:
            print(f"Error parsing post at index {idx}: {e!r}")

    return parsed_posts

def process_dataframe(df):
    """Process and clean the DataFrame"""
    # Filter out invalid account types and empty descriptions
    if "account_type" not in df.columns:
        print("account_type' column missing. Skipping filtering.")
    else:
        df = df[df["account_type"] != 2]

    if "description" in df.columns:
        df = df[df["description"].notna()]
    else:
        df["description"] = ""

    # Filter for valid location information
    location_fields = ['city', 'address', 'latitude', 'longitude', 'location_name', 'location_short_name']
    df = df.dropna(subset=location_fields, how='all')

    # Convert timestamps
    df['created_at'] = pd.to_datetime(df['created_at'], unit='s', errors='coerce')

    df = df.drop_duplicates(subset='ig_post_id')

    # Clean and translate descriptions
    df['description'] = df['description'].apply(clean_caption)
    df['cleaned_description'] = df['description'].apply(translate_caption)

    # Process location fields
    for field in location_fields:
        df[field] = df[field].astype(str).str.lower()

    # Filter for Malaysian locations
    df = df[df.apply(lambda row: contains_malaysia_location(row, location_fields), axis=1)]

    # Clean hashtags
    if "hashtags" in df.columns:
        df["hashtags"] = df["hashtags"].fillna("")
     
        df["cleaned_hashtags"] = df["hashtags"].apply(
            lambda x: [clean_hashtag(tag) for tag in x.split(",")] if x else []
        )
        df["cleaned_hashtags_str"] = df["cleaned_hashtags"].apply(lambda tags: ", ".join(tags))
    else:
        print("Warning: 'hashtags' column missing. Skipping hashtag cleaning.")
        df["cleaned_hashtags"] = [[] for _ in range(len(df))]
        df["cleaned_hashtags_str"] = ["" for _ in range(len(df))]

    # Fill missing values and optimize data types
    df = df.fillna("")
    df = df.infer_objects(copy=False)

    return df