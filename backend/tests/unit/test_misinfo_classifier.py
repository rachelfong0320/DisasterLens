import pytest
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# --- SETUP: MOCK DATABASE & OPENAI BEFORE IMPORT ---
mock_pymongo = MagicMock()
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = MagicMock()

# Mock OpenAI to prevent "api_key not found" errors during import
sys.modules["openai"] = MagicMock()

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your modules
from core.scrapers.TweetDataScraper.main_misinfoClassifier import classify_tweet_async
from core.scrapers.TweetDataScraper.prompts import MISINFO_SYSTEM_PROMPT

# --- UT-03-001: Verify Prompt Construction ---
@pytest.mark.asyncio
@patch("core.scrapers.TweetDataScraper.main_misinfoClassifier.aclient")
async def test_ut_03_001_prompt_construction(mock_aclient):
    """
    Verify that processed tweet text is sent to the OpenAI model 
    with the correct MISINFO_SYSTEM_PROMPT using the beta.parse method.
    """
    # Setup: Mock the OpenAI 'parse' response structure
    # The code expects: completion.choices[0].message.parsed
    mock_parsed_obj = MagicMock()
    mock_parsed_obj.check_label = "AUTHENTIC"
    mock_parsed_obj.confidence_score = 0.95
    mock_parsed_obj.reasoning = "Eyewitness account."
    mock_parsed_obj.justification = "Valid source."

    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(parsed=mock_parsed_obj))
    ]

    # CRITICAL FIX: Mock 'beta.chat.completions.parse' instead of 'chat.completions.create'
    # and ensure it is an AsyncMock so it can be awaited.
    mock_aclient.beta.chat.completions.parse = AsyncMock(return_value=mock_completion)

    tweet_data = {
        "tweet_id": "T12345",
        "translated_text": "Water is entering my porch in Taman Sri Muda",
        "location": "Shah Alam"
    }

    # Create a real semaphore for the test
    sem = asyncio.Semaphore(1)

    # Action
    await classify_tweet_async(tweet_data, sem)

    # Assertion
    # Check calls on the .parse method
    args, kwargs = mock_aclient.beta.chat.completions.parse.call_args
    
    # 1. Verify Model
    assert kwargs["model"] == "gpt-4o-mini"
    
    # 2. Verify System Prompt
    messages = kwargs["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == MISINFO_SYSTEM_PROMPT
    
    # 3. Verify User Content (The tweet)
    assert messages[1]["role"] == "user"
    assert "Water is entering my porch" in messages[1]["content"]
