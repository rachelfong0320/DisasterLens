from fastapi import APIRouter, HTTPException, status
from starlette.concurrency import run_in_threadpool
from starlette.background import BackgroundTasks
from core.run_root_pipeline import run_master_pipeline 
from core.processor.stats_pipeline import run_stats_pipeline


router = APIRouter(tags=["Pipeline Operations"])
ROOT_PIPELINE_MODULE = "core.run_root_pipeline" 
STATS_PIPELINE_MODULE = "core.processor.stats_pipeline"
    
def run_script_in_background(module_name: str):
    """Executes the script as a module using 'python -m'."""
    import subprocess
    import logging
    logger = logging.getLogger(__name__)
    try:
        # Use 'python -m' to execute the script as a module
        subprocess.Popen(["python", "-m", module_name])
        logger.info(f"Started background process for module: {module_name}")
    except Exception as e:
        logger.error(f"Failed to start process for module {module_name}: {e}")
    
@router.post("/run_master_pipeline", response_description="Run the entire data pipeline (Scrape, Classify, Combine)")
async def trigger_master_pipeline(background_tasks: BackgroundTasks, batch_size: int = 100):
    """
    Triggers the full, resource-intensive master pipeline in the background.
    """
    background_tasks.add_task(run_script_in_background, ROOT_PIPELINE_MODULE)
    
    return {"message": "Master pipeline execution initiated in the background.", 
            "status": "Accepted", 
            "note": "Check logs for progress. This may take several minutes."}

@router.post("/trigger/stats-cache-update", status_code=status.HTTP_202_ACCEPTED) 
def trigger_stats_pipeline_manual(background_tasks: BackgroundTasks):
    """
    Manually triggers the low-frequency analytics and caching pipeline (fixes 404 on /global).
    """
    # This is now CORRECT: It passes the STRING PATH to the non-blocking runner
    background_tasks.add_task(run_script_in_background, STATS_PIPELINE_MODULE)
    return {
        "message": "Stats Cache Update Pipeline started in the background.",
        "fix": "Run this once to fix the 404 error on your Global Analytics dashboard."
    }
    
# @router.get("/tweets", response_description="List all tweets")
# async def get_tweets(limit: int = 50):
#     try:
#         # Access the collection directly using your existing logic
#         tweets = list(db_connection.tweet_collection.find().limit(limit))
        
#         # Convert ObjectId to string for JSON compatibility
#         for tweet in tweets:
#             tweet["_id"] = str(tweet["_id"])
            
#         return tweets
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/instagram", response_description="List all IG posts")
# async def get_ig_posts(limit: int = 50):
#     try:
#         posts = list(db_connection.ig_collection.find().limit(limit))
#         for post in posts:
#             post["_id"] = str(post["_id"])
#         return posts
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    

    