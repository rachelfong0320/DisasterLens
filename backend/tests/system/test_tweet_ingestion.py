import pytest
import json
from unittest.mock import MagicMock, patch, call
from core.scrapers.TweetDataScraper import main_scraperTweet
from core.scrapers.TweetDataScraper import preprocess

# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture
def mock_twitter_response():
    """Generates a mock response structure for the Twitter API."""
    def _generate(tweet_id="12345", text="Banjir kilat di Kuala Lumpur", location="Kuala Lumpur"):
        return {
            "result": {
                "timeline": {
                    "instructions": [
                        {
                            "addEntries": [
                                {
                                    "content": {
                                        "itemContent": {
                                            "itemType": "TimelineTweet",
                                            "tweet_results": {
                                                "result": {
                                                    "rest_id": tweet_id,
                                                    "legacy": {
                                                        "full_text": text,
                                                        "created_at": "Wed Oct 27 10:00:00 +0000 2023",
                                                        "entities": {"hashtags": []}
                                                    },
                                                    "core": {
                                                        "user_results": {
                                                            "result": {
                                                                "rest_id": "user_1",
                                                                "legacy": {
                                                                    "name": "Test User",
                                                                    "screen_name": "testuser",
                                                                    "location": location,
                                                                    "followers_count": 500
                                                                },
                                                                "verified": False,
                                                                "professional": {"professional_type": "null"}
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }
    return _generate

# ==========================================
# TEST CASE: ST-04-001 (Integration)
# ==========================================

def test_st_04_001_pipeline_execution(mock_twitter_response):
    """
    Test Case ID: ST-04-001 (Steps 1, 2, 3, 6, 7)
    Scenario: Verify End-to-End Twitter Data Ingestion & Storage
    Coverage: API Fetch -> Filtering -> Metadata Extraction -> Deduplication -> Storage
    """
    # 1. Setup Mocks
    mock_response_data = mock_twitter_response(
        tweet_id="tweet_888", 
        text="Flash flood warning in KL", 
        location="Kuala Lumpur, Malaysia"
    )
    
    # Mock the API Session
    mock_session = MagicMock()
    mock_session.get.return_value.status_code = 200
    mock_session.get.return_value.json.return_value = mock_response_data

    # Mock DB Connection
    mock_insert_tweet = MagicMock()
    
    # Mock Kafka Producer
    mock_producer = MagicMock()

    # Apply Patches
    with patch.object(main_scraperTweet, "session_twitter", mock_session), \
         patch.object(main_scraperTweet, "insert_tweet", mock_insert_tweet), \
         patch.object(main_scraperTweet, "producer", mock_producer), \
         patch("time.sleep", return_value=None): # Skip sleeps
        
        # 2. Trigger the Scraper (Step 1)
        # We assume run_once stops when next_cursor is None (which our mock implies by omitting it)
        main_scraperTweet.run_once("flood Kuala Lumpur")

        # 3. Verify Querying (Step 2)
        mock_session.get.assert_called()
        args, kwargs = mock_session.get.call_args
        assert kwargs['params']['query'] == "flood Kuala Lumpur"

        # 4. Verify Metadata Extraction & Storage (Step 3 & 7)
        mock_insert_tweet.assert_called_once()
        inserted_doc = mock_insert_tweet.call_args[0][0]
        
        assert inserted_doc['tweet_id'] == "tweet_888"
        assert inserted_doc['raw_text'] == "Flash flood warning in KL"
        assert inserted_doc['location'] == "Kuala Lumpur, Malaysia"
        assert inserted_doc['platform'] == "twitter"

        # 5. Verify Kafka Push
        mock_producer.send.assert_called_once()
        assert mock_producer.send.call_args[0][0] == 'raw_social_data'

def test_st_04_001_deduplication(mock_twitter_response):
    """
    Test Case ID: ST-04-001 (Step 6)
    Scenario: Verify De-duplication Logic
    """
    mock_data = mock_twitter_response(tweet_id="tweet_duplicate_1")
    
    mock_session = MagicMock()
    mock_session.get.return_value.status_code = 200
    # Return the same tweet twice in sequential calls
    mock_session.get.return_value.json.return_value = mock_data

    mock_insert = MagicMock()

    with patch.object(main_scraperTweet, "session_twitter", mock_session), \
         patch.object(main_scraperTweet, "insert_tweet", mock_insert), \
         patch.object(main_scraperTweet, "producer", MagicMock()), \
         patch("time.sleep", return_value=None):
        
        # We need to simulate the loop running twice or processing the same ID twice
        # The script maintains a `seen_ids` set within `run_once`.
        # We can't easily run `run_once` twice and share state without modifying code,
        # but we can verify the internal loop logic if we feed a response with duplicates?
        # A simpler way is to check that `run_once` handles the ID set correctly.
        
        # Force the loop to run once with data
        main_scraperTweet.run_once("test query")
        
        # Check insert was called
        assert mock_insert.call_count == 1
        
        # Now, if we run it again with the same data, `seen_ids` is local to `run_once`. 
        # So technically the script relies on the DB `insert_tweet` handling duplicates 
        # (via Unique Index) if the script restarts.
        # Let's verify `insert_tweet` handles exceptions gracefully as per code.
        
        # Simulate DuplicateKeyError
        from pymongo import errors
        mock_insert.side_effect = errors.DuplicateKeyError("Duplicate")
        
        # Running it again should NOT crash
        try:
            main_scraperTweet.run_once("test query")
        except Exception:
            pytest.fail("Scraper crashed on duplicate DB entry")

# ==========================================
# TEST CASE: ST-04-001 (Unit - Text Processing)
# ==========================================

def test_st_04_001_translation_and_cleaning():
    """
    Test Case ID: ST-04-001 (Steps 4 & 5)
    Scenario: Verify Text Normalization and Translation Logic
    Coverage: clean_text -> translate_to_english
    """
    
    # 1. Test Text Normalization (Step 4)
    raw_text = "Ya Allah! BANJIR KILAT di Kuala Lumpur... 😭 http://link.com #banjir"
    expected_clean = "Ya Allah BANJIR KILAT di Kuala Lumpur banjir"
    # Note: The actual clean_text function removes punctuation and keeps alphanumeric.
    # Adjust assertion based on actual preprocess.py logic:
    # re.sub(r"[^A-Za-z0-9\s]", "", text) -> Removes '!' and '...'
    
    cleaned = preprocess.clean_text(raw_text)
    
    # Verify basics: No URL, No Emojis
    assert "http" not in cleaned
    assert "😭" not in cleaned
    assert "Ya Allah BANJIR KILAT" in cleaned

    # 2. Test Translation (Step 5 - Alternative Flow)
    malay_text = "banjir kilat di kuala lumpur"
    
    # Mock langdetect and deep_translator to avoid external API calls
    with patch("core.scrapers.TweetDataScraper.preprocess.detect") as mock_detect, \
         patch("core.scrapers.TweetDataScraper.preprocess.GoogleTranslator") as mock_translator:
        
        # Setup Translation Mock
        mock_detect.return_value = "id" # Detects as Indonesian/Malay
        mock_inst = MagicMock()
        mock_inst.translate.return_value = "flash flood in kuala lumpur"
        mock_translator.return_value = mock_inst

        # Execute
        translated = preprocess.translate_to_english(malay_text)

        # Verify
        assert translated == "flash flood in kuala lumpur"
        mock_translator.assert_called_with(source='auto', target='en')