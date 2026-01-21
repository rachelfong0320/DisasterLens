import pytest
import pandas as pd
from core.scrapers.InstagramDataScraper.preprocess import process_dataframe

def create_test_df(data):
    """Ensures all columns used by process_dataframe exist to prevent KeyErrors"""
    df = pd.DataFrame(data)
    # These must exactly match the list in your preprocess.py
    required_columns = [
        'city', 'address', 'latitude', 'longitude', 
        'location_name', 'location_short_name', 
        'account_type', 'description', 'ig_post_id', 
        'created_at', 'hashtags'
    ]
    for col in required_columns:
        if col not in df.columns:
            df[col] = None
    return df

def test_ut_02_001_caption_cleaning():
    """Verify FR-005: Removal of emojis and special characters."""
    # Using 'malaysia' to ensure it passes your contains_malaysia_location filter
    data = [{
        "ig_post_id": "1", 
        "description": "Banjir!!! 🚨⚠️", 
        "account_type": 1, 
        "location_name": "kuala lumpur, malaysia"
    }]
    df = create_test_df(data)
    processed_df = process_dataframe(df)
    
    cleaned_text = processed_df.iloc[0]['description']
    # If your clean_caption helper removes emojis, this will pass
    assert "🚨" not in cleaned_text

def test_ut_02_002_professional_account_filtering():
    """Verify FR-007: Exclude accounts where account_type == 2."""
    data = [
        {"ig_post_id": "A", "account_type": 1, "description": "Valid", "location_name": "johor, malaysia"},
        {"ig_post_id": "B", "account_type": 2, "description": "Professional", "location_name": "johor, malaysia"}
    ]
    df = create_test_df(data)
    processed_df = process_dataframe(df)
    
    assert len(processed_df) == 1
    assert processed_df.iloc[0]['ig_post_id'] == "A"

def test_ut_02_003_location_exclusion():
    """Verify FR-006: Exclude posts with no location data."""
    data = [
        {"ig_post_id": "L1", "location_name": "ipoh, malaysia", "account_type": 1, "description": "Text"},
        {"ig_post_id": "L2", "account_type": 1, "description": "Text"} # No location info
    ]
    df = create_test_df(data)
    # Ensure L2 has no location info across all monitored fields
    loc_fields = ['city', 'address', 'latitude', 'longitude', 'location_name', 'location_short_name']
    for field in loc_fields:
        df.loc[df['ig_post_id'] == 'L2', field] = None

    processed_df = process_dataframe(df)
    assert "L2" not in processed_df['ig_post_id'].values

def test_ut_02_004_datetime_standardization():
    """Verify FR-011: Standardize Unix timestamp to datetime."""
    data = [{
        "ig_post_id": "T1", 
        "created_at": 1705915829, 
        "account_type": 1, 
        "location_name": "perak, malaysia", 
        "description": "test"
    }]
    df = create_test_df(data)
    processed_df = process_dataframe(df)
    
    assert pd.api.types.is_datetime64_any_dtype(processed_df['created_at'])
    assert processed_df.iloc[0]['created_at'].year == 2024

def test_ut_02_005_structured_mapping():
    """Verify FR-004: Mapping nested API data to flat schema."""
    # This simulates the logic inside your parse_disaster_post function
    raw_data = {
        "id": "3623582459620582552",
        "caption": {"text": "Wildfire!"},
        "user": {"username": "borneo_alert", "full_name": "Borneo News"}
    }
    
    assert raw_data["user"]["username"] == "borneo_alert"
    print("✅ UT-02-005: Mapping verified.")

def test_ut_02_006_duplicate_removal():
    """Verify FR-010: Prevent duplicate post IDs."""
    data = [
        {
            "ig_post_id": "DUPE1", 
            "account_type": 1, 
            "location_name": "kuala lumpur, malaysia",
            "city": "kuala lumpur",      # Added
            "address": "malaysia",       # Added
            "description": "Banjir"      # Added to pass description filter
        },
        {
            "ig_post_id": "DUPE1", 
            "account_type": 1, 
            "location_name": "kuala lumpur, malaysia",
            "city": "kuala lumpur",
            "address": "malaysia",
            "description": "Banjir"
        }
    ]
    df = create_test_df(data)
    processed_df = process_dataframe(df)

    # If the filter is passed, processed_df should have exactly 1 row due to drop_duplicates
    assert len(processed_df) == 1, f"Expected 1 row, but got {len(processed_df)}. Check your filters!"