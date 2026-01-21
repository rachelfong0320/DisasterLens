import pytest
import json
from unittest.mock import MagicMock, patch, AsyncMock
from collections import Counter
from core.jobs import main_keywordTracking

# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture
def mock_db():
    """Mocks the database object."""
    db = MagicMock()
    # Mock collections
    db.posts_collection = MagicMock()
    return db

@pytest.fixture
def sample_unprocessed_posts():
    """Raw posts from DB needing keyword generation."""
    return [
        {"_id": "post_1", "postText": "Huge flood in KL right now!", "hashtags": "#klflood"},
        {"_id": "post_2", "postText": "Banjir teruk di kawasan rendah.", "hashtags": ["#emergency"]}
    ]

@pytest.fixture
def sample_processed_posts_cursor():
    """
    Simulates the DB cursor returned when fetching ALL posts 
    to calculate the final trends (Phase 2).
    Includes raw keywords generated in Phase 1.
    """
    return [
        {
            "_id": "post_1", 
            "keywords": "flood in kl", 
            "keywords_generated": True,
            "hashtags": "#klflood"
        },
        {
            "_id": "post_2", 
            "keywords": "banjir", 
            "keywords_generated": True,
            "hashtags": ["#emergency"]
        }
    ]

# ==========================================
# TEST CASE: ST-05-001
# ==========================================

def test_st_05_001_end_to_end_trend_sweep(mock_db, sample_unprocessed_posts, sample_processed_posts_cursor):
    """
    Test Case ID: ST-05-001
    Scenario: Verify End-to-End Extraction, Frequency Tracking, and Trend Persistence
    Coverage: Generation -> Consolidation -> Counting -> Persistence
    """
    
    # ----------------------------------------------------
    # 1. MOCK SETUP: DATABASE
    # ----------------------------------------------------
    
    # A. Mock fetching unclassified posts (Phase 1 Loop)
    # Call 1: Returns sample data. Call 2: Returns [] to stop the 'while True' loop.
    mock_db.get_unclassified_posts_for_keyword.side_effect = [sample_unprocessed_posts, []]
    
    # B. Mock fetching ALL posts for final counting (Phase 2)
    mock_db.posts_collection.find.return_value = sample_processed_posts_cursor

    # ----------------------------------------------------
    # 2. MOCK SETUP: OPENAI (Generation & Consolidation)
    # ----------------------------------------------------
    
    # Mock Async Client (Phase 1: Generation)
    mock_async_client = MagicMock()
    
    # Define side effects for generation (matches post_1 and post_2 text)
    # Note: The order depends on how asyncio.gather processes them, 
    # but we just need valid return values.
    gen_response_1 = MagicMock(choices=[MagicMock(message=MagicMock(content="flood in kl"))])
    gen_response_2 = MagicMock(choices=[MagicMock(message=MagicMock(content="banjir"))])
    
    # We set return_value to be a generic success if we can't easily map exact inputs in AsyncMock
    mock_async_client.chat.completions.create = AsyncMock(return_value=gen_response_1)

    # Mock Sync Client (Phase 2: Consolidation)
    mock_sync_client = MagicMock()
    
    # The consolidation prompt sends a list ["flood in kl", "banjir"]
    # We expect the LLM to map both to "Flood"
    consolidation_response_content = json.dumps({
        "flood in kl": "Flood",
        "banjir": "Flood"
    })
    
    mock_sync_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=consolidation_response_content))]
    )

    # ----------------------------------------------------
    # 3. EXECUTE PIPELINE
    # ----------------------------------------------------
    
    # Patch dependencies
    with patch("core.jobs.main_keywordTracking.aclient", mock_async_client), \
         patch("core.jobs.main_keywordTracking.OpenAI", return_value=mock_sync_client), \
         patch("time.sleep", return_value=None): # Skip sleeps
        
        # Run the Main Entry Point
        total_generated = main_keywordTracking.run_trend_analysis_sweep(mock_db, batch_size=2)

    # ----------------------------------------------------
    # 4. VERIFY RESULTS (Actual vs Expected)
    # ----------------------------------------------------
    
    # Check 1: Was Generation Triggered? (Phase 1)
    # get_unclassified_posts_for_keyword should be called
    assert mock_db.get_unclassified_posts_for_keyword.called
    
    # Check 2: Were keywords saved back to posts?
    # update_posts_keywords_bulk_sync should be called with the generated topics
    assert mock_db.update_posts_keywords_bulk_sync.called
    updates_arg = mock_db.update_posts_keywords_bulk_sync.call_args[0][0]
    assert len(updates_arg) == 2 # 2 posts processed
    
    # Check 3: Consolidation Logic (Phase 2 & 3)
    # We verified mock_sync_client was set up to return "Flood" for both inputs.
    
    # Check 4: Persistence (Step 5)
    # verify save_trend_analysis was called with correct counters
    mock_db.save_trend_analysis.assert_called_once()
    
    call_args = mock_db.save_trend_analysis.call_args[0]
    keyword_counter = call_args[0]
    hashtag_counter = call_args[1]
    
    # ASSERTIONS (Matching Expected Results in ST-05-001)
    
    # 1. Consolidated Keyword "Flood" frequency should be 2
    # ("flood in kl" -> "Flood", "banjir" -> "Flood")
    assert keyword_counter["Flood"] == 2
    
    # 2. Hashtags #klflood and #emergency frequency 1 each
    # Logic cleans hashtags: removes '#', lowercases
    assert hashtag_counter["klflood"] == 1
    assert hashtag_counter["emergency"] == 1
    
    print("\nTest ST-05-001 Passed: Trends correctly extracted, consolidated, and counted.")