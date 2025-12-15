# app/routes.py
from fastapi import APIRouter, HTTPException
from app.database import db_connection 
from typing import List
from starlette.concurrency import run_in_threadpool
from starlette.background import BackgroundTasks

from core.run_root_pipeline import run_master_pipeline

router = APIRouter()

# Helper function to run the pipeline synchronously in a thread
def run_pipeline_sync(batch_size: int):
    """Placeholder for the synchronous execution of the master pipeline."""
    try:
        # Calls the master function we imported
        results = run_master_pipeline(analytics_batch_size=batch_size)
        return results
    except Exception as e:
        # You can log or handle this error as needed
        raise e
    
@router.post("/run_master_pipeline", response_description="Run the entire pipeline (Scrape, Classify, Combine)")
async def trigger_master_pipeline(background_tasks: BackgroundTasks, batch_size: int = 100):
    """
    Triggers the full, resource-intensive master pipeline in the background.
    Execution may take a long time and should not block the server.
    """
    # Use BackgroundTasks to run the synchronous threadpool job
    background_tasks.add_task(run_in_threadpool, run_pipeline_sync, batch_size)
    
    return {"message": "Master pipeline execution initiated in the background.", 
            "status": "Accepted", 
            "note": "Check logs for progress. This may take several minutes."}
    
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
    

    