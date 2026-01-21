import pytest
import pandas as pd
from unittest.mock import patch
from core.scrapers.InstagramDataScraper.preprocess import process_dataframe
from core.scrapers.InstagramDataScraper.dbConnection import DatabaseConnection

# --- Helper for IT-02-002 ---
def create_integration_df(post_id, description, acc_type=1):
    """Refined helper to ensure the row SURVIVES initial DF creation for filtering tests"""
    data = [{
        "ig_post_id": post_id,
        "description": description,
        "account_type": acc_type, 
        "author_username": "borneo_alert",
        "location_name": "malaysia", 
        "city": "miri",
        "address": "malaysia",
        "latitude": 4.5886,
        "longitude": 114.1255,
        "created_at": 1705915829,
        "hashtags": "sarawak, wildfire",
        "location_short_name": "miri"
    }]
    return pd.DataFrame(data)

# --- Integration Tests ---

@pytest.mark.asyncio
async def test_it_02_001_storage_integration():
    """Verify FR-009: Data Persistence Integration using Borneo Sample"""
    db = DatabaseConnection()
    test_id = "3623582459620582552" # Your Borneo Post ID
    
    # 1. Cleanup
    db.collection.delete_one({"ig_post_id": test_id})

    # 2. Processed Data (The expected structured output)
    processed_data = {
        "ig_post_id": test_id,
        "description": "Wildfire reported near Miri. #sarawak #wildfire",
        "cleaned_description": "Wildfire reported near Miri.",
        "author_username": "borneo_alert",
        "city": "miri, sarawak",
        "address": "kuala baram",
        "latitude": 4.5886,
        "longitude": 114.1255,
        "account_type": 1,
        "created_at": pd.Timestamp.now()
    }

    # 3. Integration Step: Real MongoDB Storage
    db.collection.insert_one(processed_data)
        
    # 4. Verification
    stored_doc = db.collection.find_one({"ig_post_id": test_id})
    assert stored_doc is not None
    assert stored_doc["author_username"] == "borneo_alert"
    print(f"\n✅ IT-02-001 Passed: Processed Borneo record successfully persisted in MongoDB.")

@pytest.mark.asyncio
async def test_it_02_002_filter_storage_integration():
    """Verify FR-007: Professional Account Filter Integration"""
    db = DatabaseConnection()
    test_id = "INT_PROF_FILTER_001"
    db.collection.delete_one({"ig_post_id": test_id})

    # Ingest Professional Account (type 2)
    df = create_integration_df(test_id, "Official News", acc_type=2)
    
    # Execute preprocessing logic
    processed_df = process_dataframe(df)

    # Only attempt storage if not filtered
    if not processed_df.empty:
        db.collection.insert_many(processed_df.to_dict('records'))

    # Verify storage remains empty for Type 2
    stored_doc = db.collection.find_one({"ig_post_id": test_id})
    assert stored_doc is None
    print(f"\n✅ IT-02-002 Passed: Professional account (Type 2) successfully blocked from DB.")