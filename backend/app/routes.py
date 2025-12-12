# app/routes.py
from fastapi import APIRouter, HTTPException
from app.database import db_connection 
from typing import List
from starlette.concurrency import run_in_threadpool

from jobs.main_incidentClassifier import run_incident_classification_batch
from jobs.main_incidentClassifier import sweep_incident_classification_job
from jobs.main_keywordTracking import run_trend_analysis_sweep
from jobs.main_sentimentAnalysis import run_sentiment_job_sweep

router = APIRouter()

# 1. Endpoint for all UNIFIED posts (Replaces /tweets and /instagram)
@router.get("/posts/unified", response_description="List all unified social media posts (Twitter + Instagram)")
async def get_unified_posts(limit: int = 50):
    try:
        # Queries the unified posts_data collection
        posts = list(db_connection.posts_collection.find().limit(limit))
        for post in posts:
            post["_id"] = str(post["_id"])
        return posts
    except Exception as e:
        # Use database connection from app/database.py
        raise HTTPException(status_code=500, detail=str(e))

# 2. Endpoint for Incident Classification results (Your Part - FR-023: Visualization)
@router.get("/analysis/incidents", response_description="List incident classification results")
async def get_incident_classifications(limit: int = 50):
    try:
        # Queries the centralized incident_classification table
        incidents = list(db_connection.incident_collection.find().limit(limit))
        for incident in incidents:
            incident["_id"] = str(incident["_id"])
        return incidents
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test/run_incident_classifier", response_description="Run Incident Classification on combined data")
async def trigger_incident_classifier(batch_size: int = 100, continuous: bool = False):
    """
    Trigger the incident classifier.
    - If `continuous` is False (default) this runs a single async batch and returns the number classified.
    - If `continuous` is True this runs the synchronous sweeping function in a threadpool until no more posts remain.
    """
    try:
        if continuous:
            # NOTE: The sweeping function is SYNCHRONOUS, so run it in a threadpool to avoid blocking.
            posts_classified = await run_in_threadpool(
                sweep_incident_classification_job, # The synchronous sweeping function
                batch_size                         # Pass the batch size argument
            )
            return {"message": f"Incident Classification sweep completed. {posts_classified} total posts classified."}

        # Default / preferred path: run a single async batch inside the FastAPI event loop.
        posts_classified = await run_incident_classification_batch(batch_size)
        return {"message": f"Incident Classification batch completed. {posts_classified} posts classified."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification job failed: {e}")

@router.post("/test/run_trend_analysis", response_description="Run Trend Analysis (Topic Generation & Consolidation)")
async def trigger_trend_analysis(batch_size: int = 50):
    try:
        # Run the full synchronous sweeping function in a threadpool
        posts_processed = await run_in_threadpool(run_trend_analysis_sweep, batch_size) 
        return {"message": f"Trend Analysis Sweep completed. Processed {posts_processed} posts and updated analytics tables."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend Analysis job failed: {e}")  

@router.post("/test/run_sentiment_analysis", response_description="Run Sentiment Analysis Sweep on combined data")
async def trigger_sentiment_analysis(batch_size: int = 100):
    """Triggers the full sentiment analysis sweep job."""
    try:
        # Run the synchronous sweep function in a threadpool
        posts_analyzed = await run_in_threadpool(run_sentiment_job_sweep, batch_size) 
        return {"message": f"Sentiment Analysis job completed. {posts_analyzed} total posts analyzed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment Analysis job failed: {e}")          
       
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
    

    