import pytest
import sys
import os
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

# --- SETUP: MOCK DEPENDENCIES BEFORE IMPORT ---
mock_aiokafka = MagicMock()
sys.modules["aiokafka"] = mock_aiokafka
sys.modules["aiokafka.errors"] = MagicMock()

# Mock OpenAI
sys.modules["openai"] = MagicMock()

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import modules to test
from core.consumers.analytics_worker import process_analytics
from core.jobs.main_sentimentAnalysis import analyze_sentiment_async

# --- UT-04-001: Verify Worker Consumes & Processes Messages ---
@pytest.mark.asyncio
@patch("core.consumers.analytics_worker.analyze_sentiment_async")
@patch("core.consumers.analytics_worker.generate_main_topic_async")
async def test_ut_04_001_worker_consumes_message(mock_topic_gen, mock_sentiment):
    """
    Verify the worker can consume a message, process it, and produce the result
    without dropping the connection.
    """
    # 1. Setup Mocks for the dependent jobs
    mock_sentiment.return_value = {"sentiment": "Urgent"}
    mock_topic_gen.return_value = "Flood in Johor"

    # 2. Setup Mock Producer
    mock_producer = AsyncMock()
    
    # 3. Create a mock message payload (what Kafka would deliver)
    message_data = {
        "postId": "msg_123",
        "postText": "Flash flood in Johor",
        "timestamp": 1234567890
    }

    # 4. Action: Call the processing function directly
    await process_analytics(message_data, mock_producer)

    # 5. Assertions
    # Ensure dependencies were called
    mock_sentiment.assert_called_once()
    mock_topic_gen.assert_called_once()
    
    # Ensure result was produced to 'processed_data' topic
    mock_producer.send_and_wait.assert_called_once()
    call_args = mock_producer.send_and_wait.call_args
    assert call_args[0][0] == "processed_data"
    assert call_args[1]['value']['analytics_status'] == "enriched"
    assert call_args[1]['value']['sentiment'] == {"sentiment": "Urgent"}


# --- UT-04-002: Verify Processing Logic (Sentiment Analysis) ---
@pytest.mark.asyncio
@patch("core.jobs.main_sentimentAnalysis.aclient")
async def test_ut_04_002_processing_logic(mock_aclient):
    """
    Verify message is processed correctly by the worker logic (Sentiment Analysis).
    """
    # Setup: Mock OpenAI response to return a valid JSON string
    # FIXED: Changed 'sentiment_label' to 'sentiment' to match the Pydantic validation_alias
    mock_response_content = json.dumps({
        "sentiment": "Urgent",  
        "confidence_score": 0.95,
        "reasoning": "Life threatening flood detected."
    })
    
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content=mock_response_content))
    ]
    
    mock_aclient.chat.completions.create = AsyncMock(return_value=mock_completion)

    post_data = {
        "postId": "123",
        "postText": "Help! The water is rising fast and we are trapped on the roof!"
    }
    sem = asyncio.Semaphore(1)

    # Action
    result = await analyze_sentiment_async(post_data, sem)

    # Assertion
    assert result is not None
    assert result["sentiment_label"] == "Urgent" # The output dictionary uses the mapped name
    assert result["confidence_level"] == 0.95
    assert result["post_id"] == "123"


# --- UT-04-003: Verify Error Handling (Invalid Input) ---
@pytest.mark.asyncio
async def test_ut_04_003_error_handling_invalid_input():
    """
    Verify worker handles missing or empty text gracefully.
    """
    # Setup: Invalid Inputs
    invalid_post_1 = {"postId": "err_001", "postText": ""} # Empty
    invalid_post_2 = {"postId": "err_002", "postText": None} # None
    
    sem = asyncio.Semaphore(1)

    # Action
    result_1 = await analyze_sentiment_async(invalid_post_1, sem)
    result_2 = await analyze_sentiment_async(invalid_post_2, sem)

    # Assertion: Should return None, not crash
    assert result_1 is None
    assert result_2 is None


# --- UT-04-003 (Part 2): Verify Worker Exception Handling ---
@pytest.mark.asyncio
@patch("core.consumers.analytics_worker.analyze_sentiment_async")
async def test_ut_04_003_worker_exception_handling(mock_sentiment, caplog):
    """
    Verify process_analytics catches exceptions and logs errors instead of crashing.
    """
    # Setup: Make sentiment analysis raise an unexpected exception
    mock_sentiment.side_effect = Exception("Unexpected API Failure")

    mock_producer = AsyncMock()
    message_data = {"postId": "crash_test", "postText": "boom"}

    # Action
    await process_analytics(message_data, mock_producer)

    # Assertion
    # 1. Producer should NOT have sent anything
    mock_producer.send_and_wait.assert_not_called()
    
    # 2. Check logs for the specific error message
    # "Analytics enrichment failed for post crash_test" is expected from analytics_worker.py
    assert "Analytics enrichment failed for post crash_test" in caplog.text