import pytest
import sys
import os
import asyncio
import json
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
from core.jobs.main_sentimentAnalysis import analyze_sentiment_async, run_sentiment_job_batch_async

# --- UT-06-001, UT-06-002, UT-06-003: Verify Sentiment Classifications ---
@pytest.mark.asyncio
@pytest.mark.parametrize("input_text, mock_ai_label, expected_label", [
    # UT-06-001: Urgent
    ("Help! The water is rising fast and we are trapped on the roof!", "Urgent", "Urgent"),
    # UT-06-002: Warning
    ("Heavy rain expected tonight, please avoid low-lying areas.", "Warning", "Warning"),
    # UT-06-003: Informational
    ("The local government has opened three new relief centers for flood victims.", "Informational", "Informational")
])
@patch("core.jobs.main_sentimentAnalysis.aclient")
async def test_ut_06_xxx_sentiment_classification(mock_aclient, input_text, mock_ai_label, expected_label):
    """
    Combined test for UT-06-001, 002, and 003 to verify correct classification 
    into Urgent, Warning, or Informational based on input text.
    """
    # Setup: Mock OpenAI Response
    # Note: 'sentiment' is the alias Pydantic looks for in the JSON
    mock_response_content = json.dumps({
        "sentiment": mock_ai_label,
        "confidence_score": 0.95,
        "reasoning": "Test reasoning"
    })
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=mock_response_content))
    ]
    mock_aclient.chat.completions.create = AsyncMock(return_value=mock_completion)

    # Test Data
    post = {"postId": "test_123", "postText": input_text}
    sem = asyncio.Semaphore(1)

    # Action
    result = await analyze_sentiment_async(post, sem)

    # Assertion
    assert result is not None
    assert result["sentiment_label"] == expected_label
    assert result["confidence_level"] == 0.95


# --- UT-06-004: Verify Storage of Sentiment Label ---
@pytest.mark.asyncio
@patch("core.jobs.main_sentimentAnalysis.analyze_sentiment_async")
async def test_ut_06_004_db_storage(mock_analyze_func):
    """
    Verify that the system correctly calls the database update function 
    with the processed sentiment results.
    """
    # 1. Setup: Mock the analysis function to return a ready-made result
    # We mock this so we don't need to run the AI part again
    mock_analyze_func.return_value = {
        "sentiment_id": "uuid-123",
        "post_id": "789",
        "sentiment_label": "Warning",
        "confidence_level": 0.88,
        "reasoning": "Potential flood",
        "model": "gpt-4o-mini",
        "analyzed_at": 1234567890
    }

    # 2. Setup: Mock the Database Object
    mock_db = MagicMock()
    
    # Mock 'get_unclassified_sentiment_posts' to return 1 post
    mock_db.get_unclassified_sentiment_posts.return_value = [{"postId": "789", "postText": "Rain"}]
    
    # Mock 'insert_many_sentiments' to just pass (we verify the call later)
    mock_db.insert_many_sentiments = MagicMock()

    # 3. Action: Run the batch job
    processed_count = await run_sentiment_job_batch_async(mock_db, batch_size=1)

    # 4. Assertion
    assert processed_count == 1
    
    # Check if DB save function was called
    mock_db.insert_many_sentiments.assert_called_once()
    
    # Verify the data passed to the DB
    args, _ = mock_db.insert_many_sentiments.call_args
    saved_data = args[0] # The list of results
    
    assert len(saved_data) == 1
    assert saved_data[0]["post_id"] == "789"
    assert saved_data[0]["sentiment_label"] == "Warning"
    
    print("\n✅ UT-06-004 Passed: Database update called with correct sentiment data")