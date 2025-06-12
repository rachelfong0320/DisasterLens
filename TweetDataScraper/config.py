import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# MongoDB
MONGO_URI = "mongodb+srv://s2178502:Z03b4XXDF7VzV7hG@tweetdata.aqndcld.mongodb.net/retryWrites=true&w=majority&appName=TweetData"
DB_NAME = "TweetData"
COLLECTION_NAME = "CleanedTweets"

# Twitter API
RAPID_API_URL = "https://twitter241.p.rapidapi.com/search-v2"
HEADERS = {
    "X-RapidAPI-Key": "c7d63f413cmshf2851df4a5e42d1p1ed1bejsn092d86a02e69",
    "X-RapidAPI-Host": "twitter241.p.rapidapi.com"
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
