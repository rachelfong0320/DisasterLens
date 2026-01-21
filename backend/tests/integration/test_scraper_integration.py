import pytest
import sys
import os
from unittest.mock import MagicMock, patch, ANY

# --- SETUP: PATHS ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import the modules we are integrating
from core.scrapers.TweetDataScraper.main_scraperTweet import run_once
from core.scrapers.TweetDataScraper import dbConnection

# --- INTEGRATION TESTS ---

# IT-01-001: Verify Scraper -> Preprocessing -> DB Pipeline
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.producer') # Mock Kafka to focus on DB
def test_it_01_001_scraper_data_flow(mock_producer, mock_session):
    """
    IT-01-001: Verify that scraped tweets are processed (cleaned) and passed 
    to the database with the new 'cleaned_text' field.
    """
    # 1. Setup: Mock Twitter API Response (Valid Tweet)
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
                                        "rest_id": "INT_001",
                                        "legacy": {
                                            "full_text": "Floods in Johor Bahru! #banjir http://link.com",
                                            "created_at": "Mon Oct 10 20:00:00 +0000 2025",
                                            "entities": {"hashtags": []}
                                        },
                                        "core": {
                                            "user_results": {
                                                "result": {
                                                    "legacy": {"screen_name": "user1", "location": "Johor"}
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

    # 2. Setup: Mock Database Collection to capture the insertion/update
    # We use a real-ish flow by patching the collection object imported in main_scraperTweet
    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet') as mock_insert:
        # 3. Action: Run the Scraper
        # We assume helpers.is_location_in_malaysia returns True for "Johor"
        with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=True):
            try:
                run_once("flood")
            except Exception:
                pass # Ignore loop break

        # 4. Assertion: Check what was sent to the DB
        # The scraper calls 'insert_tweet(tweet_info)'
        assert mock_insert.called
        args, _ = mock_insert.call_args
        data_passed_to_db = args[0]

        # Verify Data Processing happened (Preprocess.py integration)
        # Raw text had URL; Cleaned text should NOT have URL
        assert "http://link.com" not in data_passed_to_db['cleaned_text']
        assert "Floods in Johor Bahru" in data_passed_to_db['cleaned_text']
        
        # Verify it went to DB
        print("\n✅ IT-01-001 Passed: Scraped data was cleaned and sent to DB function.")


# IT-01-002: Verify DB Configuration Integration
def test_it_01_002_db_configuration():
    """
    IT-01-002: Verify that the database configuration is correctly loaded 
    and passed to the scraper module.
    """
    # 1. Action: Access the connection object from the module
    collection = dbConnection.tweet_collection
    
    # 2. Assertion
    # If the connection failed or config was missing, this would be None or raise error
    assert collection is not None
    
    # Verify it is a valid Mongo Collection object (or Mock if in test env)
    # This proves the scraper module has access to the DB config
    assert hasattr(collection, 'insert_one') or hasattr(collection, 'update_one')
    print("\n✅ IT-01-002 Passed: Database configuration loaded and accessible.")


# IT-01-003: Verify Helper Integration (Malaysia Keyword/Filter)
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.session_twitter')
@patch('core.scrapers.TweetDataScraper.main_scraperTweet.producer')
def test_it_01_003_helper_integration(mock_producer, mock_session):
    """
    IT-01-003: Verify that the helper file is able to pass the Malaysia keyword/filter
    to the scraper.
    """
    # 1. Setup: Mock API to return a tweet from "London"
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
                                        "rest_id": "INT_003",
                                        "legacy": {
                                            "full_text": "Rain in London",
                                            "created_at": "Mon Oct 10 20:00:00 +0000 2025"
                                        },
                                        "core": {
                                            "user_results": {
                                                "result": {
                                                    "legacy": {"screen_name": "uk_user", "location": "London, UK"}
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

    # 2. Setup: Spy on the Helper Function
    # FIXED: Patch 'main_scraperTweet.is_location_in_malaysia' (Where it is used)
    # NOT 'helpers.is_location_in_malaysia' (Where it is defined)
    with patch('core.scrapers.TweetDataScraper.main_scraperTweet.is_location_in_malaysia', return_value=False) as mock_helper:
        with patch('core.scrapers.TweetDataScraper.main_scraperTweet.insert_tweet') as mock_insert:
            try:
                run_once("flood")
            except:
                pass

            # 3. Assertion
            # Verify the helper was integrated and consulted
            mock_helper.assert_called() 
            
            # Verify the logic worked: London should NOT be inserted
            mock_insert.assert_not_called()
            
            print("\n✅ IT-01-003 Passed: Helper module correctly integrated for Malaysia location filtering.")