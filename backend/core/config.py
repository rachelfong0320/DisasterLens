import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from openai import AsyncOpenAI
import re

# Load all environment variables from .env file
load_dotenv()

# =================================================================
# 1. SHARED KEYS AND ENVIRONMENT SETUP
# =================================================================

# Load general keys for various services
OPENAI_API_KEY = os.getenv("IG_OPENAI_API_KEY").strip()
OPEN_CAGE_KEY = os.getenv("OPEN_CAGE_KEY").strip()

# MongoDB Connection String (Using the IG format as it looks like a secure Atlas connection)
MONGO_USERNAME = os.getenv("MONGO_USERNAME").strip()
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD").strip()
MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@disasterlens.cnayord.mongodb.net/?retryWrites=true&w=majority&appName=DisasterLens"

# =================================================================
# 2. DATABASE NAMES AND COLLECTIONS
# =================================================================
# Central Database Names used across the project
DB_TWEET = "TweetData"
DB_INSTAGRAM = "Instagram"
COMBINED_DB_NAME = "SocialMediaPosts"

# Collection Names
TWEET_COLLECTION = "CleanedTweet"
IG_COLLECTION = "cleaned_posts"
TWEET_MISINFO_COLLECTION = "misinfo_classific"
IG_MISINFO_COLLECTION = "misinfo_classific_data" # Renamed to avoid IG/Tweet conflict
POSTS_COLLECTION = "posts_data"
SENTIMENT_COLLECTION = "sentiment_check"
INCIDENT_COLLECTION = "incident_classification"
DISASTER_EVENTS_COLLECTION = "disaster_events"

# =================================================================
# 3. TWITTER/RAPID API SETUP (from Tweet config)
# =================================================================
RAPID_API_URL_TWITTER = "https://twitter241.p.rapidapi.com/search-v2"
HEADERS_TWITTER = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_KEY"),
    "X-RapidAPI-Host": os.getenv("RAPIDAPI_HOST")
}

# HTTP Session (shared object for API calls)
session_twitter = requests.Session()
retries = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retries)
session_twitter.mount("https://", adapter)
session_twitter.mount("http://", adapter)

# =================================================================
# 4. INSTAGRAM API SETUP (from Instagram config)
# =================================================================
RAPID_API_URL_IG = "https://instagram-social-api.p.rapidapi.com/v1/search_posts"
HEADERS_IG = {
    "X-RapidAPI-Key": os.getenv("RAPIDAPI_IG_KEY").strip(),
    "X-RapidAPI-Host": os.getenv("RAPID_API_IG_HOST").strip()
}

# =================================================================
# 5. SHARED CLIENTS
# =================================================================
ACLIENT = AsyncOpenAI(api_key=OPENAI_API_KEY)

# =================================================================
# 6. KEYWORDS (from Instagram config, as they are shared logic)
# =================================================================
disasters = [
    "banjir", "tanah runtuh", "ribut", "jerebu",
    "kebakaran hutan", "mendapan tanah", "gempa bumi", "tsunami",
    "flood", "landslide", "storm", "haze",
    "forest fire", "sinkhole", "earthquake"
]

malaysia_keywords = [
    "malaysia", "kuala lumpur", "selangor", "johor", "penang", "pulau pinang",
    "perak", "kedah", "pahang", "terengganu", "kelantan", "melaka", "negeri sembilan",
    "sabah", "sarawak", "labuan", "putrajaya", "cyberjaya", "langkawi", "ipoh", "alor setar",
    "george town", "kuantan", "kuching", "kota kinabalu", "bintulu", "sibu", "miri"
]

# Location validation
malaysia_locations = [
    "malaysia",
    "kuala lumpur", "putrajaya", "labuan",
    "johor", "kedah", "kelantan", "melaka", "negeri sembilan", "pahang", "pulau pinang",
    "penang", "perak", "perlis", "sabah", "sarawak", "selangor", "terengganu",
    # Major Cities
    "johor bahru", "malacca city", "alor setar", "ipoh", "kuantan","cyberjaya","langkawi","george town",
    "kuala terengganu", "putrajaya", "iskandar puteri", "sungai petani",
    "sandakan", "miri", "tawau", "butterworth", "shah alam", "petaling jaya",
    "klang", "subang jaya", "taiping", "bintulu", "sibu"
]

# Generate search keywords combinations
# keywords = [f"{d} {s}" for d in disasters for s in malaysia_keywords]
malaysia_keywords_clean = [re.sub(r'[\r\n]', '', s).strip() for s in malaysia_keywords]
disasters_clean = [re.sub(r'[\r\n]', '', d).strip() for d in disasters]

keywords = [f"{d} {s}" for d in disasters_clean for s in malaysia_keywords_clean]

