import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import os

"""
This script sets up the environment and session configuration for streaming disaster-related tweets 
using the Twitter API (via RapidAPI), with built-in support for retries, logging, and MongoDB connection setup.

Key features:
- Loads API keys and MongoDB URI from a .env file for security and configuration flexibility.
- Initializes a MongoDB database connection to store cleaned tweet data.
- Configures an HTTP session with retry logic to handle common network issues (e.g., rate limits, server errors).
- Sets up logging to track script activity and potential errors.

Note:
- Actual tweet processing and data ingestion logic should be implemented separately using the configured session and DB.
"""


load_dotenv()

# MongoDB
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "TweetData"
COLLECTION_NAME = "CleanedTweets"

# Twitter API
RAPID_API_URL = "https://twitter241.p.rapidapi.com/search-v2"
HEADERS = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": os.getenv("RAPIDAPI_HOST")
}

# Logging (to console, not file — so it shows in GitHub Actions)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]  # Send to stdout
)

# HTTP Session
session = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)


logging.info("✅ Session and API configuration initialized successfully.")