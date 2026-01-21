import pytest
import sys
import os
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock

# --- SETUP: PATHS ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# --- IMPORTS ---
# We use the specific path based on your folder structure
from core.scrapers.TweetDataScraper import main_misinfoClassifier
from core.scrapers.TweetDataScraper.main_misinfoClassifier import classify_tweet_async, run_classification_job
from core.scrapers.TweetDataScraper.schemas import ClassificationOutput
from core.scrapers.TweetDataScraper.prompts import MISINFO_SYSTEM_PROMPT
from core.scrapers.TweetDataScraper import dbConnection

# --- INTEGRATION TESTS ---

# IT-03-001: Verify Schema Import
def test_it_03_001_schema_availability():
    """
    IT-03-001: Verify that the ClassificationOutput schema is successfully imported 
    and available for use.
    """
    try:
        model = ClassificationOutput(
            check_label="AUTHENTIC",
            confidence_score=0.9,
            justification="Verified source",
            reasoning="Detailed reasoning" # Added to satisfy schema
        )
        assert model.check_label == "AUTHENTIC"
        print("\n✅ IT-03-001 Passed: ClassificationOutput schema is importable and valid.")
    except Exception as e:
        pytest.fail(f"Schema import failed: {e}")


# IT-03-002: Verify Prompt Integration
@pytest.mark.asyncio
@patch.object(main_misinfoClassifier, 'aclient')
async def test_it_03_002_prompt_integration(mock_aclient):
    """
    IT-03-002: Verify that the system prompt is correctly imported and included 
    in the classification request.
    """
    # Setup: Text > 5 chars to pass validation
    mock_tweet = {"tweet_id": "T1", "cleaned_text": "This text is long enough"}
    
    # Mock Response
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=json.dumps({
            "check_label": "UNCERTAIN",
            "confidence_score": 0.5,
            "justification": "Not enough info",
            "reasoning": "Reasoning..."
        })))
    ]
    
    # Use AsyncMock for the awaitable call
    mock_aclient.beta.chat.completions.parse = AsyncMock(return_value=mock_completion)
    
    sem = asyncio.Semaphore(1)

    # Action
    await classify_tweet_async(mock_tweet, sem)

    # Assertion
    if mock_aclient.beta.chat.completions.parse.call_count == 0:
        pytest.fail("OpenAI API was never called. Check validation logic.")
        
    mock_aclient.beta.chat.completions.parse.assert_called_once()
    
    # Check arguments for System Prompt
    call_args = mock_aclient.beta.chat.completions.parse.call_args
    messages_sent = call_args[1]['messages']
    
    system_msg = next((m for m in messages_sent if m['role'] == 'system'), None)
    assert system_msg is not None
    assert MISINFO_SYSTEM_PROMPT in system_msg['content']
    print("\n✅ IT-03-002 Passed: System prompt correctly integrated into API call.")


# IT-03-003: Verify Database Connection Usage
def test_it_03_003_db_integration():
    """
    IT-03-003: Verify that the DatabaseConnection class can be imported and used.
    """
    assert dbConnection.tweet_collection is not None
    assert dbConnection.misinfo_collection is not None
    print("\n✅ IT-03-003 Passed: Database collections successfully initialized.")


# IT-03-004: End-to-End Classification -> DB Storage
@pytest.mark.asyncio
@patch.object(main_misinfoClassifier, 'classify_tweet_async') # Mock the AI part
# FIXED: Patch the collections ON THE IMPORTED MODULE to ensure the loop sees the mock
@patch.object(main_misinfoClassifier, 'misinfo_collection')
@patch.object(main_misinfoClassifier, 'tweet_collection')
async def test_it_03_004_end_to_end_storage(mock_tweet_col, mock_misinfo_col, mock_classifier):
    """
    IT-03-004: Verify that a valid Twitter post is stored in the database.
    """
    # 1. Setup: Mock the chaining of find().limit()
    
    # This is the final cursor object that list() iterates over
    mock_cursor_final = MagicMock()
    
    # Configure it to yield 1 item first, then empty list (Breaking the loop)
    mock_cursor_final.__iter__.side_effect = [
        iter([{"tweet_id": "T1001", "cleaned_text": "Flood info length ok"}]),
        iter([])
    ]
    
    # This is the object returned by find()
    mock_find_result = MagicMock()
    # When .limit() is called on it, return the final cursor
    mock_find_result.limit.return_value = mock_cursor_final
    
    # When find() is called, return the intermediate object
    mock_tweet_col.find.return_value = mock_find_result
    
    # 2. Setup: Mock existing check to return empty (not processed yet)
    mock_misinfo_col.distinct.return_value = []

    # 3. Setup: Mock Classifier result
    mock_classifier.return_value = {
        "tweet_id": "T1001",
        "check_label": "AUTHENTIC",
        "confidence": 0.95,
        "reasoning": "Test reasoning",
        "classification_justification": "Test just",
        "timestamp": 123456
    }

    # 4. Action
    try:
        await asyncio.wait_for(run_classification_job(), timeout=5.0)
    except asyncio.TimeoutError:
        pytest.fail("Test timed out! Infinite loop detected in run_classification_job.")

    # 5. Assertion
    # Verify insert_many was called
    assert mock_misinfo_col.insert_many.called
    
    # Verify data stored
    args, _ = mock_misinfo_col.insert_many.call_args
    inserted_docs = args[0]
    
    assert len(inserted_docs) == 1
    assert inserted_docs[0]['tweet_id'] == "T1001"
    print("\n✅ IT-03-004 Passed: Classified tweet successfully stored in DB.")


# IT-03-005 & IT-03-006: OpenAI Integration & Label Validation
@pytest.mark.asyncio
@patch.object(main_misinfoClassifier, 'aclient')
async def test_it_03_005_and_006_ai_parsing(mock_aclient):
    """
    IT-03-005 & IT-03-006: Verify OpenAI response parsing and Label validation.
    """
    # Setup: Mock the Parsed Object
    mock_parsed_obj = MagicMock()
    mock_parsed_obj.check_label = "MISINFORMATION"
    mock_parsed_obj.confidence_score = 0.88
    mock_parsed_obj.reasoning = "Reasoning"
    mock_parsed_obj.justification = "Justification"

    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(parsed=mock_parsed_obj))
    ]
    
    # Mock the new beta parse path
    mock_aclient.beta.chat.completions.parse = AsyncMock(return_value=mock_completion)
    
    tweet = {"tweet_id": "T67890", "cleaned_text": "Landslide fake news detected"}
    sem = asyncio.Semaphore(1)

    # Action
    result = await classify_tweet_async(tweet, sem)

    # Assertion
    assert result is not None
    assert result['tweet_id'] == "T67890"
    assert result['check_label'] == "MISINFORMATION"
    assert result['confidence'] == 0.88
    
    print("\n✅ IT-03-005 & 006 Passed: AI response correctly parsed and validated.")