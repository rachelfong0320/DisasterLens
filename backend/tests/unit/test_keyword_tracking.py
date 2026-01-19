import pytest
import sys
import os
import asyncio
import json
from collections import Counter
from unittest.mock import AsyncMock, MagicMock, patch

# --- SETUP: MOCK DEPENDENCIES BEFORE IMPORT ---
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

# Mock OpenAI
sys.modules["openai"] = MagicMock()

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import module to test
from core.jobs.main_keywordTracking import (
    generate_main_topic_async, 
    consolidate_topics_sync, 
    run_trend_analysis_sweep
)

# --- UT-05-001: Keyword Generation (Async) ---
@pytest.mark.asyncio
@patch("core.jobs.main_keywordTracking.aclient")
async def test_ut_05_001_keyword_generation(mock_aclient):
    """
    Verify extraction of keywords from "Authentic" posts.
    """
    # Setup: Mock OpenAI Response
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content="flood in kuala lumpur"))
    ]
    mock_aclient.chat.completions.create = AsyncMock(return_value=mock_completion)

    # Test Data
    post = {
        "_id": "123",
        "postText": "Banjir kilat di KL",
        "hashtags": "#emergency"
    }

    # Action
    result = await generate_main_topic_async(post)

    # Assertion
    assert result == "flood in kuala lumpur"
    # Ensure generated keyword is valid string (not None)
    assert isinstance(result, str)


# --- UT-05-003: Topic Consolidation (Sync) ---
@patch("core.jobs.main_keywordTracking.OpenAI") # Patch the class constructor
def test_ut_05_003_topic_consolidation(mock_openai_class):
    """
    Verify AI consolidation of semantically similar keywords.
    """
    # Setup: Mock the sync client instance
    mock_client_instance = mock_openai_class.return_value
    
    # Setup: Mock response JSON
    mapping_response = {
        "flood": "flood",
        "flooding": "flood",
        "banjir": "flood"
    }
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps(mapping_response)))
    ]
    mock_client_instance.chat.completions.create.return_value = mock_completion

    # Test Data
    raw_keywords = ["flood", "flooding", "banjir"]

    # Action
    result_mapping = consolidate_topics_sync(raw_keywords)

    # Assertion
    assert result_mapping["flooding"] == "flood"
    assert result_mapping["banjir"] == "flood"
    assert len(set(result_mapping.values())) == 1  # All map to 1 root word


# --- UT-05-002 & UT-05-004: Frequency Counting & Null Handling ---
@patch("core.jobs.main_keywordTracking.consolidate_topics_sync")
@patch("core.jobs.main_keywordTracking.run_topic_generation_batch_async")
def test_ut_05_002_and_004_tracking_and_nulls(mock_generation_batch, mock_consolidation):
    """
    Combined Test for UT-05-002 (Counting) and UT-05-004 (Null Handling).
    We test run_trend_analysis_sweep logic.
    """
    # 1. Setup: Stop the Generation Loop immediately
    # Returning 0 tells the loop "No more posts to generate", so it proceeds to Phase 2
    mock_generation_batch.return_value = 0

    # 2. Setup: Mock DB Data (The "Find" cursor)
    mock_db = MagicMock()
    
    # Data for UT-05-002: 3 floods, 2 kilats
    # Data for UT-05-004: 1 post with "null" hashtag
    mock_posts = [
        # Post 1
        {"keywords": "flood", "hashtag": "kilat", "keywords_generated": True},
        # Post 2
        {"keywords": "flood", "hashtags": ["kilat"], "keywords_generated": True}, # List format
        # Post 3
        {"keywords": "flood", "hashtag": "emergency", "keywords_generated": True},
        # Post 4 (UT-05-004 case)
        {"keywords": "landslide", "hashtag": "null", "keywords_generated": True} 
    ]
    
    # Mock the cursor to behave like a list
    mock_db.posts_collection.find.return_value = mock_posts

    # 3. Setup: Mock Consolidation to be a simple pass-through (Identity mapping)
    # This isolates the counting logic from the AI mapping logic
    mock_consolidation.return_value = {
        "flood": "flood",
        "landslide": "landslide"
    }

    # Action
    run_trend_analysis_sweep(mock_db, batch_size=10)

    # Assertion
    # Check what was passed to db.save_trend_analysis(keyword_counter, hashtag_counter)
    args, _ = mock_db.save_trend_analysis.call_args
    keyword_counter = args[0]
    hashtag_counter = args[1]

    # UT-05-002 Verification
    assert keyword_counter["flood"] == 3
    assert hashtag_counter["kilat"] == 2
    
    # UT-05-004 Verification
    # "null" string should NOT be in the counter
    assert "null" not in hashtag_counter
    # "landslide" should be there
    assert keyword_counter["landslide"] == 1