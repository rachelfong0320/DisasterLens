import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from core.scrapers.TweetDataScraper import main_misinfoClassifier
from core.scrapers.TweetDataScraper.schemas import ClassificationOutput

# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture
def mock_tweet_doc():
    """Returns a sample tweet document from the database."""
    return {
        "tweet_id": "tweet_101",
        "cleaned_text": "Water levels rising rapidly in Taman Sri Muda. Send help!",
        "timestamp": "2023-10-27T10:00:00Z"
    }

@pytest.fixture
def mock_classification_result():
    """Returns the expected Pydantic parsed output from OpenAI."""
    return ClassificationOutput(
        check_label="AUTHENTIC",
        confidence_score=0.95,
        reasoning="Eyewitness account mentioning specific location and urgent condition.",
        justification="Specific location 'Taman Sri Muda' and water level description."
    )

# ==========================================
# TEST CASE: ST-03-001 (Success Path)
# ==========================================

@pytest.mark.asyncio
async def test_st_03_001_end_to_end_classification(mock_tweet_doc, mock_classification_result):
    """
    Test Case ID: ST-03-001 (Steps 1-4)
    Scenario: Verify End-to-End Misinformation Classification
    Coverage: DB Fetch -> AI Submission -> Label Retrieval -> Data Persistence
    """
    
    # 1. Mock Database Collections
    # We need to mock tweet_collection to return 1 batch then empty (to break while loop)
    mock_cursor = MagicMock()
    mock_cursor.limit.return_value = [mock_tweet_doc] # First batch
    
    mock_tweet_coll = MagicMock()
    # side_effect controls consecutive calls: First call returns cursor, Second returns []
    mock_tweet_coll.find.side_effect = [mock_cursor, MagicMock(limit=MagicMock(return_value=[]))]
    
    mock_misinfo_coll = MagicMock()
    mock_misinfo_coll.distinct.return_value = [] # No tweets classified yet

    # 2. Mock OpenAI Response
    # The code uses aclient.beta.chat.completions.parse
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(parsed=mock_classification_result))
    ]

    # 3. Patch Dependencies
    with patch.object(main_misinfoClassifier, "tweet_collection", mock_tweet_coll), \
         patch.object(main_misinfoClassifier, "misinfo_collection", mock_misinfo_coll), \
         patch.object(main_misinfoClassifier, "aclient") as mock_aclient, \
         patch("asyncio.sleep", return_value=None): # Skip sleeps
        
        # Setup Async Mock for OpenAI
        mock_aclient.beta.chat.completions.parse = AsyncMock(return_value=mock_completion)

        # 4. Trigger the Job
        # Note: We run the actual function logic, but controlled via mocks
        await main_misinfoClassifier.run_classification_job()

        # 5. Verify Label Retrieval & Logic (Step 3)
        # Verify OpenAI was called with the correct text
        mock_aclient.beta.chat.completions.parse.assert_called()
        call_args = mock_aclient.beta.chat.completions.parse.call_args
        assert "Taman Sri Muda" in str(call_args) # Check prompt content
        
        # 6. Verify Data Persistence (Step 4)
        mock_misinfo_coll.insert_many.assert_called_once()
        inserted_docs = mock_misinfo_coll.insert_many.call_args[0][0]
        
        assert len(inserted_docs) == 1
        doc = inserted_docs[0]
        assert doc["tweet_id"] == "tweet_101"
        assert doc["check_label"] == "AUTHENTIC"
        assert doc["confidence"] == 0.95
        assert "check_id" in doc  # Ensure UUID was generated
        assert "timestamp" in doc

# ==========================================
# TEST CASE: ST-03-001 (Exception Handling)
# ==========================================

@pytest.mark.asyncio
async def test_st_03_001_exception_handling_retry(mock_tweet_doc, mock_classification_result):
    """
    Test Case ID: ST-03-001 (Step 5)
    Scenario: Verify Exception Handling and Retry Logic
    Coverage: API 429 Error -> Retry -> Success
    """
    
    # 1. Mock DB (Same as above)
    mock_cursor = MagicMock()
    mock_cursor.limit.return_value = [mock_tweet_doc]
    
    mock_tweet_coll = MagicMock()
    mock_tweet_coll.find.side_effect = [mock_cursor, MagicMock(limit=MagicMock(return_value=[]))]
    mock_misinfo_coll = MagicMock()
    mock_misinfo_coll.distinct.return_value = []

    # 2. Mock OpenAI with Rate Limit then Success
    # Call 1: Raises Exception("429 Rate Limit")
    # Call 2: Returns Success
    mock_success_completion = MagicMock()
    mock_success_completion.choices = [
        MagicMock(message=MagicMock(parsed=mock_classification_result))
    ]

    with patch.object(main_misinfoClassifier, "tweet_collection", mock_tweet_coll), \
         patch.object(main_misinfoClassifier, "misinfo_collection", mock_misinfo_coll), \
         patch.object(main_misinfoClassifier, "aclient") as mock_aclient, \
         patch("asyncio.sleep", return_value=None) as mock_sleep: # Spy on sleep
        
        # Setup Side Effect for Retry Logic
        mock_aclient.beta.chat.completions.parse = AsyncMock(
            side_effect=[Exception("429 Rate Limit Exceeded"), mock_success_completion]
        )

        # 3. Trigger Job
        await main_misinfoClassifier.run_classification_job()

        # 4. Verify Retry Logic (Step 5)
        # OpenAI should have been called twice (1 fail + 1 success)
        assert mock_aclient.beta.chat.completions.parse.call_count == 2
        
        # Verify backoff sleep was called
        mock_sleep.assert_called() 
        
        # Verify persistence happened eventually
        mock_misinfo_coll.insert_many.assert_called_once()
        inserted_docs = mock_misinfo_coll.insert_many.call_args[0][0]
        assert inserted_docs[0]["check_label"] == "AUTHENTIC"

@pytest.mark.asyncio
async def test_st_03_001_hard_failure(mock_tweet_doc):
    """
    Test Case ID: ST-03-001 (Edge Case)
    Scenario: Hard Failure (Non-Recoverable)
    Coverage: API 500 Error -> Log Error -> Skip Persistence
    """
    mock_cursor = MagicMock()
    mock_cursor.limit.return_value = [mock_tweet_doc]
    mock_tweet_coll = MagicMock()
    mock_tweet_coll.find.side_effect = [mock_cursor, MagicMock(limit=MagicMock(return_value=[]))]
    mock_misinfo_coll = MagicMock()
    mock_misinfo_coll.distinct.return_value = []

    with patch.object(main_misinfoClassifier, "tweet_collection", mock_tweet_coll), \
         patch.object(main_misinfoClassifier, "misinfo_collection", mock_misinfo_coll), \
         patch.object(main_misinfoClassifier, "aclient") as mock_aclient:
        
        # Persistent Error
        mock_aclient.beta.chat.completions.parse = AsyncMock(side_effect=Exception("500 Server Error"))

        await main_misinfoClassifier.run_classification_job()

        # Verify NO data was saved
        mock_misinfo_coll.insert_many.assert_not_called()