# run_pipeline.py
import asyncio
import logging
from main_dataCombine import run_enrichment_pipeline
from main_scraperIg import run_scraping_job
from main_misinfoClassifier import run_classification_job

# ---------------------------------------------
# Suppress noisy HTTP logs
# ---------------------------------------------
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def run_pipeline():
    """Run the instagram scrapper"""
    
    print("\n" + "="*50)
    print("STEP 1: SCRAPING INSTAGRAM POSTS")
    print("="*50 + "\n")

    try:
        asyncio.run(run_scraping_job())
    except KeyboardInterrupt:
        print(" Scraping interrupted manually — moving to classification.")
    except Exception as e:
        print(f"Scraper Error: {e}")

    # RUn misinformation classifier
    print("\n" + "="*50)
    print("STEP 2: CLASSIFYING MISINFORMATION")
    print("="*50 + "\n")

    try:
        asyncio.run(run_classification_job())
    except Exception as e:
        print(f"Classifier Error: {e}")

# STEP 3: DATA COMBINATION (Enrichment)
    print("\n" + "="*50)
    print("STEP 3: CONCURRENT DATA ENRICHMENT (Instagram)")
    print("="*50 + "\n")

    try:
        # Run the new synchronous enrichment pipeline using existing geo-data
        run_enrichment_pipeline() 
    except Exception as e:
        print(f"Data Combination Error: {e}")

    print("\nPipeline Finished Successfully.")

if __name__ == "__main__":
    run_pipeline()
