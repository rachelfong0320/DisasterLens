import os
import re
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv("IG_OPENAI_API_KEY").strip()
MONGO_USERNAME = os.getenv("MONGO_USERNAME").strip()
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD").strip()
MONGO_URI = f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@disasterlens.cnayord.mongodb.net/?retryWrites=true&w=majority&appName=DisasterLens"
