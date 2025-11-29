# app/routes.py
from fastapi import APIRouter, HTTPException
from app.database import db_connection 
from typing import List

router = APIRouter()

@router.get("/tweets", response_description="List all tweets")
async def get_tweets(limit: int = 50):
    try:
        # Access the collection directly using your existing logic
        tweets = list(db_connection.tweet_collection.find().limit(limit))
        
        # Convert ObjectId to string for JSON compatibility
        for tweet in tweets:
            tweet["_id"] = str(tweet["_id"])
            
        return tweets
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instagram", response_description="List all IG posts")
async def get_ig_posts(limit: int = 50):
    try:
        posts = list(db_connection.ig_collection.find().limit(limit))
        for post in posts:
            post["_id"] = str(post["_id"])
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))