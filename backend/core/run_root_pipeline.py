import sys
import os
import logging
import time
from typing import Dict, Any

from core.processor.event_creator import run_event_creator_pipeline
from core.processor.event_consolidator import run_master_event_consolidator

# 1. Setup path for import resolution 
# Import the specific scraper pipeline runners
try:
    from .scrapers.TweetDataScraper import run_pipeline as twitter_scraper_runner
    from .scrapers.InstagramDataScraper import run_pipeline as instagram_scraper_runner

    # Import the shared analytics pipeline from the jobs directory
    from .jobs.run_pipeline import run_all_analytics_jobs 
except ImportError as e:
    logging.error(f"CRITICAL: Failed to import necessary job modules. Check paths/names: {e}")
    sys.exit(1)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_master_pipeline(analytics_batch_size: int = 100) -> Dict[str, Any]:
    """
    The ROOT pipeline: Executes all data ingestion (Scrapers) followed by 
    the full suite of analytical processing jobs (Shared Jobs).
    """
    start_time = time.time()
    logging.info("==============================================")
    logging.info("STARTING MASTER ROOT DATA PIPELINE")
    logging.info("==============================================")

    results = {}
    
    # --- STEP 1: DATA INGESTION (Scrapers) ---
    logging.info("--- 1a. EXECUTING TWITTER SCRAPER ---")
    try:
        twitter_results = twitter_scraper_runner.run_pipeline() 
        results['twitter_scraper'] = f"Success: {twitter_results} posts ingested."
        logging.info(f"Twitter Scraper Result: {results['twitter_scraper']}")
    except Exception as e:
        results['twitter_scraper'] = f"FAILED: Twitter Scraper failed: {e}"
        logging.error(results['twitter_scraper'])


    logging.info("--- 1b. EXECUTING INSTAGRAM SCRAPER ---")
    try:
        instagram_results = instagram_scraper_runner.run_pipeline() 
        results['instagram_scraper'] = f"Success: {instagram_results} posts ingested."
        logging.info(f"Instagram Scraper Result: {results['instagram_scraper']}")
    except Exception as e:
        results['instagram_scraper'] = f"FAILED: Instagram Scraper failed: {e}"
        logging.error(results['instagram_scraper'])

    
    # --- STEP 2: ANALYTICAL PROCESSING (Shared Jobs) ---
    logging.info("--- 2. EXECUTING SHARED ANALYTICAL JOBS ---")
    try:
        analysis_results = run_all_analytics_jobs(batch_size=analytics_batch_size)
        results.update(analysis_results) 
    except Exception as e:
        results['analytics_sweep'] = f"CRITICAL FAILED: Analytics sweep failed: {e}"
        logging.error(results['analytics_sweep'])

    logging.info("--- 2b. EXECUTING EVENT CREATOR (POST-LEVEL SAVE) ---")
    try:
        creation_report = run_event_creator_pipeline()
        results['post_creation'] = creation_report
        logging.info(f"Event Creator Result: {results['post_creation']}")
    except Exception as e:
        results['post_creation'] = f"CRITICAL FAILED: Post Creation failed: {e}"
        logging.error(results['post_creation']) 

    # --- STEP 3: MASTER EVENT CONSOLIDATION (EVENT-LEVEL AGGREGATION) ---
    logging.info("--- 3. START MASTER EVENT CONSOLIDATION JOB ---")
    try:
        consolidation_count = run_master_event_consolidator()
        results['event_consolidation'] = f"Success: Consolidated {consolidation_count} posts into unique events."
        logging.info(f"Consolidation Result: {results['event_consolidation']}")
    except Exception as e:
        results['event_consolidation'] = f"CRITICAL FAILED: Master Consolidation failed: {e}"
        logging.error(results['event_consolidation'])

    # --- FINAL REPORT ---
    end_time = time.time()
    total_duration = end_time - start_time
    
    logging.info("==============================================")
    logging.info(f"MASTER ROOT PIPELINE COMPLETE in {total_duration:.2f} seconds.")
    logging.info("==============================================")
    
    return results

if __name__ == "__main__":
    logging.info("Master Root Pipeline running via command line entry point.")
    final_report = run_master_pipeline(analytics_batch_size=100)
    print("\nFINAL MASTER PIPELINE REPORT:")
    for key, value in final_report.items():
        print(f"  - {key}: {value}")



            #  # --- STEP 3: EVENT CONSOLIDATION ---
    # logging.info("--- 3. START FINAL EVENT CONSOLIDATION JOB ---")
    # try:
    #     consolidation_report = run_event_creator_pipeline()
    #     results['event_consolidation'] = consolidation_report
    #     logging.info(f"Consolidation Result: {results['event_consolidation']}")
    # except Exception as e:
    #     results['event_consolidation'] = f"CRITICAL FAILED: Event Consolidation failed: {e}"
    #     logging.error(results['event_consolidation'])   