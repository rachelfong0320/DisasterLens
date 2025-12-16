from pymongo import MongoClient
from pymongo.database import Database
from typing import Generator
from dotenv import load_dotenv
from core.config import MONGO_URI, COMBINED_DB_NAME

load_dotenv()

client = MongoClient(MONGO_URI)

def get_db() -> Generator[Database, None, None]:
    """
    FastAPI dependency function to inject the combined database object into route handlers.
    """
    try:
        # Yields the database object for the route to use
        yield client[COMBINED_DB_NAME] 
    finally:
        # The connection pool handles closing, so we just allow the yield to finish
        pass