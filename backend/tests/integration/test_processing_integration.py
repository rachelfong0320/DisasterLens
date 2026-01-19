import pytest
import sys
import os
from unittest.mock import MagicMock, patch

# --- SETUP: PATHS ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import modules
from core.scrapers.TweetDataScraper.main_scraperTweet import run_once
from core.scrapers.TweetDataScraper import dbConnection

# --- INTEGRATION TESTS ---

# IT-02-001: Scraper <-> Preprocessor <-> Translation API
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.clean_text') # FIXED: Patch 'clean_text' instead of 'clean_and_translate'
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.producer') # Mock Kafka
def test_it_02_001_translation_flow(mock_producer, mock_clean_func, mock_session):
    """
    IT-02-001: Verify that tweets passed from the scraper are processed 
    (cleaned/translated) and the result is used.
    """
    # 1. Setup: Mock Twitter API returning a Malay Tweet
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "timeline": {
                "instructions": [{
                    "entries": [{
                        "content": {
                            "itemContent": {
                                "itemType": "TimelineTweet",
                                "tweet_results": {
                                    "result": {
                                        "rest_id": "INT_02_001",
                                        "legacy": {
                                            "full_text": "Banjir besar di Kelantan", # Malay
                                            "created_at": "Mon Oct 10 20:00:00 +0000 2025",
                                            "entities": {"hashtags": []}
                                        },
                                        "core": {
                                            "user_results": {
                                                "result": {
                                                    "legacy": {"screen_name": "user_my", "location": "Kelantan"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }]
                }]
            }
        }
    }
    mock_session.get.return_value = mock_response

    # 2. Setup: Mock the Preprocessor Return Value
    # We simulate that the cleaning function returns the English translation
    # This proves the Scraper uses the output of the preprocessor.
    mock_clean_func.return_value = "Big flood in Kelantan"

    # 3. Setup: Spy on the DB Insertion
    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet') as mock_insert:
        with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=True):
            try:
                run_once("flood")
            except:
                pass

        # 4. Assertion
        assert mock_insert.called
        args, _ = mock_insert.call_args
        saved_data = args[0]

        # Verify the Scraper used the output from the Preprocessor
        print(f"DEBUG: Saved Text: {saved_data.get('cleaned_text')}")
        assert "Big flood in Kelantan" in saved_data['cleaned_text']
        
        # Verify Preprocessor was actually called with the raw text
        mock_clean_func.assert_called()
        print("\n✅ IT-02-001 Passed: Scraper correctly integrated with Preprocessor.")


# IT-02-002: Pipeline -> DB Storage Verification
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.producer')
def test_it_02_002_pipeline_storage(mock_producer, mock_session):
    """
    IT-02-002: Verify that processed tweets and metadata are correctly stored 
    in the database with all required fields.
    """
    # 1. Setup: Mock Twitter API (Standard English Tweet)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "result": {
            "timeline": {
                "instructions": [{
                    "entries": [{
                        "content": {
                            "itemContent": {
                                "itemType": "TimelineTweet",
                                "tweet_results": {
                                    "result": {
                                        "rest_id": "INT_02_002",
                                        "legacy": {
                                            "full_text": "Heavy rain causing floods #disaster",
                                            "created_at": "Mon Oct 10 20:00:00 +0000 2025",
                                            "entities": {"hashtags": [{"text": "disaster"}]}
                                        },
                                        "core": {
                                            "user_results": {
                                                "result": {
                                                    "legacy": {"screen_name": "tester", "location": "KL"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }]
                }]
            }
        }
    }
    mock_session.get.return_value = mock_response

    # 2. Setup: Mock DB Collection
    mock_collection = MagicMock()
    with patch.object(dbConnection, 'tweet_collection', mock_collection):
        with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=True):
            try:
                run_once("flood")
            except:
                pass

        # 3. Assertion
        assert mock_collection.insert_one.called
        args, _ = mock_collection.insert_one.call_args
        document = args[0]
        
        # Verify Schema/Metadata
        assert document['tweet_id'] == "INT_02_002"
        assert "cleaned_text" in document
        assert "tweet_created_at" in document
        assert "location" in document
        
        # Verify Hashtag Storage
        assert "tweet_hashtags" in document
        tags = document["tweet_hashtags"]
        assert "disaster" in str(tags)
        
        print("\n✅ IT-02-002 Passed: Full pipeline successfully stored cleaned metadata to DB.")