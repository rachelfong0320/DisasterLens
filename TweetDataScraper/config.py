import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import os

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

# Logging
logging.basicConfig(filename='streaming.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

# HTTP Session
session = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)
