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
@patch('core.scrapers.TweetDataScraper.preprocess.GoogleTranslator') # Mock External API
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.producer') # Mock Kafka
def test_it_02_001_translation_flow(mock_producer, mock_translator_class, mock_session):
    """
    IT-02-001: Verify that non-English tweets are passed from the scraper 
    to the translation API (via preprocess) and returned as English.
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

    # 2. Setup: Mock Translator logic inside 'preprocess.py'
    # The scraper calls preprocess.clean_and_translate -> calls GoogleTranslator
    mock_translator_instance = mock_translator_class.return_value
    mock_translator_instance.translate.return_value = "Big flood in Kelantan" 

    # 3. Setup: Spy on the DB Insertion to see the final object
    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet') as mock_insert:
        # Mock helper to allow "Kelantan"
        with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=True):
            try:
                run_once("flood")
            except:
                pass

        # 4. Assertion
        # Verify Scraper -> Preprocessor Integration
        assert mock_insert.called
        args, _ = mock_insert.call_args
        saved_data = args[0]

        # The 'text' field should now contain the English translation
        # (Assuming your scraper overwrites 'text' or saves it in 'cleaned_text')
        # We check that the Malay text was replaced or accompanied by the English one.
        print(f"DEBUG: Saved Text: {saved_data.get('text')}")
        
        # Verify translation integration
        assert "Big flood in Kelantan" in saved_data['text']
        
        # Verify Preprocessor was actually used
        mock_translator_instance.translate.assert_called()
        print("\n✅ IT-02-001 Passed: Malay tweet correctly translated to English before storage.")


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

    # 2. Setup: Use a REAL Mock for the DB Collection (Spying on the module level object)
    # We patch the collection inside dbConnection to intercept the 'insert_one' call
    mock_collection = MagicMock()
    with patch.object(dbConnection, 'tweet_collection', mock_collection):
        
        # Mock helper
        with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=True):
            try:
                run_once("flood")
            except:
                pass

        # 3. Assertion
        # Verify insert_one was called on the collection
        assert mock_collection.insert_one.called
        
        # Inspect the document stored
        args, _ = mock_collection.insert_one.call_args
        document = args[0]
        
        # Verify Schema/Metadata
        assert document['tweet_id'] == "INT_02_002"
        assert "cleaned_text" in document or "text" in document
        assert "hashtags" in document
        assert "created_at" in document
        assert "location" in document
        
        # Verify Hashtag Extraction
        assert "disaster" in document['hashtags'] or "#disaster" in document['hashtags']
        
        print("\n✅ IT-02-002 Passed: Full pipeline successfully stored cleaned metadata to DB.")