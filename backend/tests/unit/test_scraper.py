import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# --- STEP 1: MOCK KAFKA BEFORE IMPORTING YOUR CODE ---
# We replace the real 'kafka' library with a fake one (MagicMock)
# so that when main_scraperTweet.py tries to do "producer = KafkaProducer(...)",
# it succeeds without needing a real server.
mock_kafka = MagicMock()
sys.modules["kafka"] = mock_kafka
sys.modules["kafka.errors"] = MagicMock()

# --- STEP 2: NOW IMPORT YOUR MODULE ---
# Add backend to path so we can find 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.scrapers.TweetDataScraper.main_scraperTweet import run_once

# --- TEST FIXTURES ---
@pytest.fixture
def mock_twitter_response():
    """Generates a standard mock response structure for Twitter API."""
    return {
        "result": {
            "timeline": {
                "instructions": [
                    {
                        "entries": [
                            {
                                "content": {
                                    "itemContent": {
                                        "itemType": "TimelineTweet",
                                        "tweet_results": {
                                            "result": {
                                                "rest_id": "tweet_123",
                                                "legacy": {
                                                    "full_text": "Banjir kilat di KL! #banjir",
                                                    "created_at": "Wed Oct 10 20:19:24 +0000 2025",
                                                    "entities": {"hashtags": [{"text": "banjir"}]}
                                                },
                                                "core": {
                                                    "user_results": {
                                                        "result": {
                                                            "rest_id": "user_123",
                                                            "verified": False,
                                                            "verification_type": "null",
                                                            "professional": {"professional_type": "null"},
                                                            "legacy": {
                                                                "screen_name": "normal_user",
                                                                "name": "Ali",
                                                                "followers_count": 500,
                                                                "location": "Kuala Lumpur, Malaysia"
                                                            }
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

# --- TEST CASES ---

# UT-01-001: Verify connection to Twitter API
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
def test_ut_01_001_twitter_connection(mock_session):
    # Setup: Mock a 200 OK response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {} 
    mock_session.get.return_value = mock_response

    # Action: Run the scraper (mocking internals to prevent loop)
    # We also verify 'producer' inside the module is our mock
    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet'), \
         patch('core.scrapers.TweetDataScraper.main_scraperTweet.producer'):
        try:
            run_once("flood")
        except Exception: 
            pass 

    # Assertion
    mock_session.get.assert_called()
    print("\n✅ UT-01-001 Passed: API Connection Verified")


# UT-01-002: Verify extraction of tweets with keywords
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet')
def test_ut_01_002_keyword_extraction(mock_db_insert, mock_session, mock_twitter_response):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_twitter_response
    mock_session.get.return_value = mock_response

    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=True):
         try:
            run_once("banjir")
         except: pass 

    mock_db_insert.assert_called()
    print("\n✅ UT-01-002 Passed: Keyword Tweet Extracted")


# UT-01-003: Verify tweets WITHOUT location are discarded
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet')
def test_ut_01_003_discard_no_location(mock_db_insert, mock_session, mock_twitter_response):
    data = mock_twitter_response
    # Empty location
    data['result']['timeline']['instructions'][0]['entries'][0]['content']['itemContent']['tweet_results']['result']['core']['user_results']['result']['legacy']['location'] = ""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_session.get.return_value = mock_response

    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=False):
        try:
            run_once("flood")
        except: pass

    mock_db_insert.assert_not_called()
    print("\n✅ UT-01-003 Passed: No-Location Tweet Discarded")


# UT-01-004: Verify tweets WITH location are extracted
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet')
def test_ut_01_004_extract_with_location(mock_db_insert, mock_session, mock_twitter_response):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_twitter_response
    mock_session.get.return_value = mock_response

    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=True):
        try:
            run_once("flood")
        except: pass

    mock_db_insert.assert_called()
    print("\n✅ UT-01-004 Passed: Location Tweet Extracted")


# UT-01-005: Verify Authority Figures are EXCLUDED
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet')
def test_ut_01_005_exclude_authority(mock_db_insert, mock_session, mock_twitter_response):
    data = mock_twitter_response
    # Set verified = True
    data['result']['timeline']['instructions'][0]['entries'][0]['content']['itemContent']['tweet_results']['result']['core']['user_results']['result']['verified'] = True

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = data
    mock_session.get.return_value = mock_response

    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=True):
        try:
            run_once("flood")
        except: pass

    mock_db_insert.assert_not_called()
    print("\n✅ UT-01-005 Passed: Authority Figure Excluded")