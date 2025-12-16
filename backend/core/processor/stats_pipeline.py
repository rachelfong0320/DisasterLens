import logging
from datetime import datetime, timezone
from pymongo.database import Database
from typing import Dict, Any, List
from core.db.disaster_event_saver import get_mongo_client
from core.config import (
    COMBINED_DB_NAME, 
    DISASTER_EVENTS_COLLECTION, 
    DISASTER_POSTS_COLLECTION, 
    ANALYTICS_COLLECTION
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _calculate_event_analytics(db: Database) -> Dict[str, Any]:
    """Calculates frequency, district counts, and monthly trends from consolidated events."""
    logger.info("  -> Calculating Event Aggregations (Frequency, Districts, Monthly)...")
    
    event_collection = db[DISASTER_EVENTS_COLLECTION]
    
    pipeline = [
            {
            #Filter out unwanted data at the start.
            "$match": {
                # Filter 1: Exclude "Unknown District" (Uses 'location_district' as confirmed)
                "location_district": { "$nin": ["Unknown District","unknown district", "unknown", "", None ] }, 
                # Filter 2: Exclude "none" classification type
                "classification_type": { "$ne": "none" }
                }
            }, 
            {
                "$facet": {
                    # 1. Disaster Type Frequency Chart
                    "type_counts": [
                        { "$group": { "_id": "$classification_type", "count": { "$sum": 1 } } },
                        { "$project": { "_id": 0, "type": "$_id", "frequency": "$count" } }
                    ],
                    
                    # 2. Top 5 Affected Districts Chart
                    "district_ranking": [
                        { "$group": { "_id": "$location_district", "count": { "$sum": 1 } } },
                        { "$sort": { "count": -1 } },
                        { "$limit": 5 },
                        { "$project": { "_id": 0, "district": "$_id", "event_count": "$count" } }
                    ],
                    
                    # 3. Events by Month Chart (Historical Trend)
                    "monthly_events": [
                        {
                            "$group": {
                                "_id": {
                                    "year": { "$year": "$start_time" },
                                    "month": { "$month": "$start_time" }
                                },
                                "total_events": { "$sum": 1 }
                            }
                        },
                        # Sort oldest to newest for chart display
                        { "$sort": { "_id.year": 1, "_id.month": 1 } }
                    ]
                }
            }
        ]

    result = list(event_collection.aggregate(pipeline))
    
    # $facet always returns one document with the results arrays inside
    return result[0] if result else {}


def _calculate_post_analytics(db: Database) -> Dict[str, Any]:
    """Calculates sentiment analysis counts from the individual posts."""
    logger.info("  -> Calculating Post Aggregations (Sentiment Counts)...")
    
    post_collection = db[DISASTER_POSTS_COLLECTION]
    
    # 1. Sentiment Analysis Count (Urgent, Warning, Informational)
    # Assumes your Event Creator adds a field named 'sentiment_label'
    sentiment_pipeline = [
        {
            # Group by the sentiment classification label
            "$group": {
                "_id": "$sentiment.label", 
                "count": { "$sum": 1 }
            }
        },
        { 
            "$project": { 
                "_id": 0, 
                "label": "$_id", 
                "count": 1 
            } 
        }
    ]
    
    sentiment_results = list(post_collection.aggregate(sentiment_pipeline))
    
    return {"sentiment_counts": sentiment_results}


def run_stats_pipeline():
    """Master function to run all analytics and save them to the ANALYTICS_COLLECTION."""
    logger.info("==============================================")
    logger.info("STARTING MASTER STATISTICS PIPELINE")
    logger.info("==============================================")
    
    client = get_mongo_client()
    if not client: 
        logger.error("Failed to connect to MongoDB for statistics.")
        return False
    
    db = client[COMBINED_DB_NAME]
    
    try:
        # Step 1: Calculate Event-based analytics
        event_analytics = _calculate_event_analytics(db)
        
        # Step 2: Calculate Post-based analytics
        post_analytics = _calculate_post_analytics(db)
        
        # Step 3: Combine all results into one document for the UI
        final_analytics_document = {
            # Use a fixed _id so we can always update the same document
            "_id": "master_dashboard_analytics", 
            "timestamp": datetime.now(timezone.utc),
            **event_analytics,
            **post_analytics,
        }
        
        # Step 4: Save the final document to the dedicated analytics collection
        analytics_collection = db[ANALYTICS_COLLECTION]
        
        # Use replace_one with upsert=True to either update the existing document or create it
        analytics_collection.replace_one(
            {"_id": "master_dashboard_analytics"},
            final_analytics_document,
            upsert=True
        )
        
        logger.info("Successfully calculated and saved all master analytics.")
        return True
        
    except Exception as e:
        logger.error(f"CRITICAL FAILED: Statistics Pipeline failed: {e}")
        return False
        
    finally:
        if client: client.close()


if __name__ == '__main__':
    # Simple test run if executed directly
    run_stats_pipeline()