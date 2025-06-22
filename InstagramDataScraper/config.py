import os
import re
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_KEY = os.getenv("RAPIDAPI_IG_KEY").strip()
API_HOST = "instagram-social-api.p.rapidapi.com"
BASE_URL = "https://instagram-social-api.p.rapidapi.com/v1/search_posts"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST
}

# MongoDB Configuration
MONGO_USERNAME = os.getenv("MONGO_USERNAME").strip()
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD").strip()
MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@disasterlens.cnayord.mongodb.net/?retryWrites=true&w=majority&appName=DisasterLens"
DB_NAME = "Instagram"
COLLECTION_NAME = "cleaned_posts"

# malaysia_keywords is used for API query construction (broad match)
# malaysia_locations is used for post-filtering (detailed city/location match)
# Search Keywords
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


