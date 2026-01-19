import pytest
import sys
import os
from unittest.mock import MagicMock, patch


# --- SETUP: MOCK DATABASE BEFORE IMPORT ---
# 1. Define a real class for DuplicateKeyError so Python accepts it in 'try/except' blocks
class MockDuplicateKeyError(Exception):
    pass

# 2. Create the mocks
mock_pymongo = MagicMock()
mock_errors = MagicMock()

# 3. Assign our custom exception class to the mock's attribute
mock_errors.DuplicateKeyError = MockDuplicateKeyError

# 4. CRITICAL FIX: Link mock_errors to mock_pymongo so "from pymongo import errors" works
mock_pymongo.errors = mock_errors

# 5. Apply to sys.modules
sys.modules["pymongo"] = mock_pymongo
sys.modules["pymongo.errors"] = mock_errors

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import your modules (now that mocks are ready)
from core.scrapers.TweetDataScraper.preprocess import clean_text, translate_to_english, tokenize_and_clean
from core.scrapers.TweetDataScraper.dbConnection import insert_tweet

# --- UT-02-001: Clean Text ---
@pytest.mark.parametrize("input_text, expected_output", [
    ("Flood in Selangor! http://bit.ly/123", "Flood in Selangor"),
    ("http://bit.ly/123 Flood in Selangor!", "Flood in Selangor"),
    ("Flood in http://bit.ly/123 Selangor!", "Flood in Selangor"),
    ("Flood in Selangor! @Lim123", "Flood in Selangor"),
    ("@Lim123 Flood in Selangor!", "Flood in Selangor"),
    ("Flood in @Lim123 Selangor!", "Flood in Selangor"),
    ("Forest fire in Kampung Batu 🔥🔥🔥", "Forest fire in Kampung Batu"),
    ("Forest fire!!!! OMGGG in Kampung Batu", "Forest fire OMGGG in Kampung Batu"),
    ("Forest fire OMGGG in Kampung Batu", "Forest fire OMGGG in Kampung Batu"),
    ("Flood        in Selangor!!!!!!", "Flood in Selangor"),
])
def test_ut_02_001_clean_text(input_text, expected_output):
    """
    Verify that the system correctly cleans tweet text by removing URLs, 
    mentions, emojis, and special characters.
    """
    assert clean_text(input_text) == expected_output


# --- UT-02-002: Translation ---
@patch("core.scrapers.TweetDataScraper.preprocess.detect")
@patch("core.scrapers.TweetDataScraper.preprocess.GoogleTranslator")
def test_ut_02_002_translation(mock_translator_class, mock_detect):
    """
    Verify translation logic. We mock the API so we don't actually hit Google Translate.
    """
    # Setup: Mock language detection to return 'ms' (Malay)
    mock_detect.return_value = "ms"
    
    # Setup: Mock the translator instance and its translate method
    mock_translator_instance = mock_translator_class.return_value
    mock_translator_instance.translate.return_value = "Flash flood occurring in Kuala Lumpur now."

    input_text = "Banjir kilat berlaku di Kuala Lumpur sekarang."
    
    # Action
    result = translate_to_english(input_text)
    
    # Assertion
    assert result == "Flash flood occurring in Kuala Lumpur now."
    mock_detect.assert_called_with(input_text)
    mock_translator_class.assert_called()


# --- UT-02-003: Tokenization & Stopwords ---
def test_ut_02_003_tokenization():
    """
    Verify that the system correctly tokenizes cleaned tweet text and removes common stopwords.
    """
    input_text = "the flood is at kuala lumpur"
    expected_output = ["flood", "kuala", "lumpur"]
    
    # Action
    result = tokenize_and_clean(input_text)
    
    # Assertion
    assert result == expected_output


# --- UT-02-004: DB Storage (Success) ---
@patch("core.scrapers.TweetDataScraper.dbConnection.tweet_collection")
def test_ut_02_004_db_storage_success(mock_collection):
    """
    Verify that processed tweet data is stored in the database in a structured format.
    """
    # Setup
    mock_tweet = {
        "tweet_id": "123",
        "text": "Flood alert",
        "created_at": "2024-01-01",
        "location": "Johor"
    }

    # Action
    insert_tweet(mock_tweet)

    # Assertion
    mock_collection.insert_one.assert_called_once_with(mock_tweet)


# --- UT-02-005: DB Duplicate Handling ---
@patch("core.scrapers.TweetDataScraper.dbConnection.tweet_collection")
def test_ut_02_005_db_prevent_duplicates(mock_collection):
    """
    Verify that the system prevents duplicate tweets from being stored based on tweet ID.
    """
    # Setup: Make insert_one raise our custom MockDuplicateKeyError
    # This matches the class we injected into sys.modules earlier
    mock_collection.insert_one.side_effect = MockDuplicateKeyError("Duplicate")
    
    mock_tweet = {"tweet_id": "1935556522840650175", "text": "Duplicate Tweet"}

    # Action: Call insert_tweet
    try:
        insert_tweet(mock_tweet)
    except Exception as e:
        pytest.fail(f"insert_tweet raised an exception instead of handling it gracefully: {e}")

    # Assertion: Should have tried to insert, failed, and caught the error (skipping crash)
    mock_collection.insert_one.assert_called_once()
    print("\n✅ UT-02-005 Passed: Duplicate tweet gracefully handled")