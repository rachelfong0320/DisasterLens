import sys
import os
import logging
import time
from typing import Dict, Any
from pymongo.errors import ConnectionFailure

# 1. Get the path to the directory containing 'backend' (The Project Root)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(project_root)

# 2. Add the 'backend' folder itself to the path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(backend_dir)


from app.database import db_connection 

from .main_incidentClassifier import sweep_incident_classification_job as run_incident_sweep
from .main_sentimentAnalysis import run_sentiment_job_sweep
from .main_keywordTracking import run_trend_analysis_sweep
from .main_geoProcessor import run_geo_processing_sweep

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_all_analytics_jobs(batch_size: int = 100) -> Dict[str, Any]:
    """
    SYNCHRONOUS ENTRY POINT: Runs the entire suite of analytical classifications 
    (Incident, Sentiment, and Keyword Tracking) in sequence.
    """
    start_time = time.time()
    logging.info("==============================================")
    logging.info("STARTING SHARED ANALYTICS PIPELINE SWEEP")
    logging.info("==============================================")

    # Dictionary to track results
    results = {}

    # reset_failed_geo_posts(db_connection)
    
    # --- 1. KEYWORD/TREND ANALYSIS ---
    try:
        # Keyword sweep returns total analyzed, which is the sum of new classifications 
        # and consolidation runs.
        keyword_analysis_result = run_trend_analysis_sweep(db_connection,batch_size) 
        results['keyword_tracking'] = f"Success: Trend analysis completed. {keyword_analysis_result} keywords updated."
    except Exception as e:
        results['keyword_tracking'] = f"FAILED: {e}"
        logging.error(f"Keyword Tracking FAILED: {e}")

    # --- 2. GEO-PROCESSING ---
    try:
        # Note: Set a smaller batch size here to avoid slamming the Nominatim/OpenCage API
        geo_count = run_geo_processing_sweep(db_connection, batch_size=50) 
        results['geo_processing'] = f"Success: {geo_count} posts geo-enriched."
    except Exception as e:
        results['geo_processing'] = f"FAILED: {e}"
        logging.error(f"Geo-Processing FAILED: {e}")

    # --- 1. INCIDENT CLASSIFICATION ---
    try:
        incident_count = run_incident_sweep(db_connection,batch_size)
        results['incident_classification'] = f"Success: {incident_count} posts classified."
    except Exception as e:
        results['incident_classification'] = f"FAILED: {e}"
        logging.error(f"Incident Classification FAILED: {e}")
        # Note: We continue to the next job even if one fails
        
    # --- 2. SENTIMENT ANALYSIS ---
    try:
        sentiment_count = run_sentiment_job_sweep(db_connection,batch_size)
        results['sentiment_analysis'] = f"Success: {sentiment_count} posts analyzed."
    except Exception as e:
        results['sentiment_analysis'] = f"FAILED: {e}"
        logging.error(f"Sentiment Analysis FAILED: {e}")

    # (Keyword sweep already executed above.)


    end_time = time.time()
    total_duration = end_time - start_time
    
    logging.info("==============================================")
    logging.info(f"ANALYTICS PIPELINE COMPLETE in {total_duration:.2f} seconds.")
    logging.info("==============================================")
    
    return results

if __name__ == "__main__":
# Example usage: You can now run the command: python backend/jobs/run_pipeline.py
    logging.info("Root Pipeline running via command line entry point.")
    results = run_all_analytics_jobs(batch_size=100)
    print("\nFinal Pipeline Report:", results)    