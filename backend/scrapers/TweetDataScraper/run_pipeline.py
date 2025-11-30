# run_pipeline.py
import asyncio
import logging
from main_scraperTweet import start_scraping_job
from main_misinfoClassifier import run_classification_job
from main_dataCombine import run_enrichment_pipeline

# ---------------------------------------------------------
# SILENCE NOISY LOGS
# This stops OpenAI and HTTP libraries from printing every request
# ---------------------------------------------------------
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Only allow your own logs (optional, if you want your own logs to show)
logging.basicConfig(level=logging.INFO, format='%(message)s')

def run_pipeline():
    # 1. Run Scraper (Synchronous)
    print("\n" + "="*40)
    print("STEP 1: SCRAPING TWEETS")
    print("="*40 + "\n")
    
    try:
        start_scraping_job()
    except KeyboardInterrupt:
        print("Scraping stopped manually. Proceeding to classification...")
    except Exception as e:
        print(f"Scraper Error: {e}")

    # 2. Run Classifier (Asynchronous)
    print("\n" + "="*40)
    print("STEP 2: CLASSIFYING MISINFORMATION")
    print("="*40 + "\n")
    
    try:
        asyncio.run(run_classification_job())
    except Exception as e:
        print(f"Classifier Error: {e}")

    print("\n Pipeline Finished Successfully.")

    # 3. Run Data Enricher (Synchronous)
    print("\n" + "="*40)
    print("STEP 3: COOMBINE AUTHENTIC DATA")
    print("="*40 + "\n")
    
    try:
        run_enrichment_pipeline()
    except Exception as e:
        print(f"Enricher Error: {e}")

    print("\n Pipeline Finished Successfully.")

if __name__ == "__main__":
    run_pipeline()