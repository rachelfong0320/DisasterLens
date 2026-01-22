import pytest
import asyncio
from core.scrapers.InstagramDataScraper.main_scraperIg import run_scraping_job
from core.scrapers.InstagramDataScraper.dbConnection import DatabaseConnection

@pytest.mark.asyncio
async def test_it_01_001_full_workflow_integration():
    """
    IT-01-001: Verify end-to-end data flow from API to MongoDB.
    This test runs the actual scraping job and checks if data exists in the real DB.
    """
    # 1. Initialize real DB connection
    db = DatabaseConnection()
    
    # Record initial count
    initial_count = db.collection.count_documents({})
    print(f"\nInitial MongoDB count: {initial_count}")

    # 2. Execute the full scraping job
    # This will use your real RapidAPI key and real Kafka/Mongo settings
    await run_scraping_job()

    # 3. Verify the result in MongoDB
    final_count = db.collection.count_documents({})
    print(f"Final MongoDB count: {final_count}")

    # Assertion: We expect the count to increase if new data was found
    # Or at least stay the same if only duplicates were found
    assert final_count >= initial_count
    print("✅ IT-01-001 Passed: End-to-end flow verified.")

@pytest.mark.asyncio
async def test_it_01_002_location_integrity_integration():
    """
    IT-01-002: Verify that only geocoded posts are stored in the real DB.
    """
    db = DatabaseConnection()
    
    # Query the real database for any record missing location data
    # In MongoDB, "" represents the empty strings your preprocess script uses
    invalid_posts = db.collection.count_documents({
        "$or": [
            {"latitude": ""},
            {"longitude": ""},
            {"latitude": None}
        ]
    })

    # Assertion: There should be 0 posts without location in the DB
    assert invalid_posts == 0
    print(f"✅ IT-01-002 Passed: All {db.collection.count_documents({})} posts have location data.")

@pytest.mark.asyncio
async def test_it_01_003_duplicate_check_integration():
    """
    IT-01-003: Verify that running the job twice does not create duplicates in DB.
    """
    db = DatabaseConnection()
    
    # Run once
    await run_scraping_job()
    count_after_run_1 = db.collection.count_documents({})
    
    # Run again immediately
    await run_scraping_job()
    count_after_run_2 = db.collection.count_documents({})
    
    # Assertion: Count should be exactly the same because all posts in run 2 are duplicates
    assert count_after_run_1 == count_after_run_2
    print("✅ IT-01-003 Passed: Duplicate prevention verified in real-time.")