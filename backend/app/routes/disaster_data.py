# app/routes/disaster_data.py

from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database
from core.config import MALAYSIA_STATE_DISTRICT_MAP, ANALYTICS_COLLECTION, DISASTER_POSTS_COLLECTION

from app.db.connection import get_db 
from app.models.data_models import (
    DisasterEvent, 
    GlobalAnalytics,
    KeywordTrend
) 

router = APIRouter(tags=["Disaster Data Service"])

# --- CORE HELPER FUNCTIONS ---

def _get_time_aware_datetime(dt: date, is_end: bool = False) -> datetime:
    time_part = datetime.max.time() if is_end else datetime.min.time()
    return datetime.combine(dt, time_part).replace(tzinfo=timezone.utc)

def _get_sentiment_pipeline(
    start_dt: datetime, 
    end_dt: datetime, 
    disaster_type: Optional[str] = None 
) -> List[Dict[str, Any]]:
    """Builds the aggregation pipeline for sentiment counts on posts, now including type filter."""
    
    match_query = {
        "start_time": { "$gte": start_dt, "$lte": end_dt }
    }
    
    if disaster_type:
        # NOTE: Using 'disaster_type' field from combined_disaster_posts collection
        match_query["disaster_type"] = disaster_type.lower()
        
    return [
        {
            "$match": match_query # Filter by time and type
        },
        # FIX: Unwind the nested 'sentiment' object for grouping
        { "$unwind": "$sentiment" },
        # FIX: Group by the actual label inside the sentiment object
        { "$group": { "_id": "$sentiment.label", "count": { "$sum": 1 } } }, 
        # FIX: Rename the fields for clean output
        { "$project": { "_id": 0, "label": "$_id", "frequency": "$count" } } 
    ]

# =======================================================
# 1. MAP FILTERING ENDPOINT (/events/filtered)
# =======================================================

@router.get(
    "/events/filtered", 
    response_model=List[DisasterEvent],
    summary="Retrieve consolidated events filtered by date, type, and location for the GIS map and Chatbot."
)
async def get_filtered_events(
    db: Database = Depends(get_db),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    disaster_type: Optional[str] = Query(None, description="Disaster type (e.g., flood)"),
    state: Optional[str] = Query(None, description="Malaysian State (e.g., selangor)")
):
    
    collection = db["disaster_events"]
    query_filter = {}

    # --- Build Query Filter (Date, Type, Location) ---
    if start_date or end_date:
        time_query = {}
        if start_date:
            time_query["$gte"] = _get_time_aware_datetime(start_date, is_end=False)
        if end_date:
            time_query["$lte"] = _get_time_aware_datetime(end_date, is_end=True)
            
        if time_query:
            query_filter["most_recent_report"] = time_query

    if disaster_type:
        query_filter["classification_type"] = disaster_type.lower() 

    unknown_terms = ["unknown district", "unknown state", "unknown", ""]

    if state:
        # Set the state equality filter
        query_filter["location_state"] = {"$eq": state.lower(), "$nin": unknown_terms}
        
        # Add districts if they exist in your map
        districts = MALAYSIA_STATE_DISTRICT_MAP.get(state.lower())
        if districts:
            query_filter["location_district"] = {"$in": districts, "$nin": unknown_terms}
    else:
        # Default global "Unknown" filtering
        query_filter["location_state"] = {"$nin": unknown_terms, "$exists": True}
        query_filter["location_district"] = {"$nin": unknown_terms, "$exists": True}

    # 4. Aggregation Pipeline
    pipeline = [
        { "$match": query_filter },
        { "$project": {
            "_id": 0,
            "total_posts_count": { "$size": "$related_post_ids" },            
            "event_id": 1,
            "classification_type": 1,
            "location_district": 1,
            "location_state": 1,
            "start_time": 1,
            "most_recent_report": 1,
            "geometry": 1,
            "related_post_ids": 1
        }}
    ]

    events = []
    cursor = collection.aggregate(pipeline) 
    for doc in cursor:
        events.append(DisasterEvent(**doc))
        
    return events

# =======================================================
# 2. GLOBAL ANALYTICS ENDPOINT (/analytics/global)
# =======================================================

@router.get(
    "/analytics/global",
    response_model=GlobalAnalytics,
    summary="Retrieve all global pre-calculated chart data (All-Time Historical)."
)
async def get_global_analytics(db: Database = Depends(get_db)):
    
    analytics_collection = db[ANALYTICS_COLLECTION] 
    analytics_doc = analytics_collection.find_one({"_id": "master_dashboard_analytics"})
    
    if not analytics_doc:
        raise HTTPException(status_code=404, detail="Analytics data has not been calculated yet.")
    
    transformed_monthly_events = []
    if 'monthly_events' in analytics_doc:
        for event in analytics_doc['monthly_events']:
            # Take the year and month from the nested '_id'
            year_month_data = event.pop('_id') 
            
            # Create the new, flat structure expected by Pydantic
            transformed_monthly_events.append({
                "year": year_month_data['year'],
                "month": year_month_data['month'],
                "total_events": event['total_events']
            })
            
    # 2. Update the master document with the transformed data
    analytics_doc['monthly_events'] = transformed_monthly_events
    
    # 3. Clean up and return
    analytics_doc.pop('_id', None)
    return analytics_doc

# get trending keywords
@router.get(
    "/analytics/keywords/global",
    response_model=List[KeywordTrend], # Use KeywordTrend if defined
    summary="Retrieve all-time trending keywords from the pre-calculated pipeline table (Instant Load)."
)
async def get_top_keywords_global(db: Database = Depends(get_db), limit: int = 10):
    
    analytics_collection = db["tracking_keyword"] 
    
    # Query only documents where the type is 'keyword'
    cursor = analytics_collection.find(
        {"type": "keyword"}
    ).sort("frequency", -1).limit(limit)
    
    results = []
    for doc in cursor:
        results.append(KeywordTrend(
            keyword=doc['term'],
            frequency=doc['frequency']
        ))
        
    return results


# =======================================================
# 3. FILTERED ANALYTICS ENDPOINT (/analytics/filtered)
# =======================================================

@router.get(
    "/analytics/filtered",
    # Returns a dynamic dictionary (not a static Pydantic model) because of the structure
    summary="Retrieve chart data calculated specifically for a provided date range and/or type filter."
)
async def get_filtered_analytics(
    db: Database = Depends(get_db),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    disaster_type: Optional[str] = Query(None, description="Optional filter by disaster type"),
):
    
    event_collection = db["disaster_events"]
    post_collection = db["combined_disaster_posts"] 
    
    start_dt = _get_time_aware_datetime(start_date, is_end=False)
    end_dt = _get_time_aware_datetime(end_date, is_end=True)
    
    # 1. Build the Event Match Filter (Date + Optional Type)
    event_match = {
        "$match": {
            "most_recent_report": { "$gte": start_dt, "$lte": end_dt }
        }
    }
    if disaster_type:
        event_match["$match"]["classification_type"] = disaster_type.lower()
    
    # 2. Event Aggregation Pipeline (Type, District, Monthly) - Using $facet
    analysis_pipeline = [
        event_match, 
        {
            "$facet": {
                # --- All aggregations now performed on filtered data ---               
                "type_counts": [ 
                    # FIX: Add $match to exclude the 'none' classification type
                    { "$match": { "classification_type": { "$ne": "none" } } },
                    
                    { "$group": { "_id": "$classification_type", "count": { "$sum": 1 } } }, 
                    { "$project": { "_id": 0, "type": "$_id", "frequency": "$count" } } 
                ],
                "district_ranking": [ 
                    # FIX: Filter out 'Unknown District' and null/empty districts
                    { "$match": { 
                        "location_district": { 
                            "$nin": ["Unknown District", "Unknown", "unknown district", None, ""],
                            "$exists": True
                        },
                    }},
                    { "$group": { "_id": "$location_district", "count": { "$sum": 1 } } }, 
                    { "$sort": { "count": -1 } }, 
                    { "$limit": 5 }, 
                    { "$project": { "_id": 0, "district": "$_id", "event_count": "$count" } } 
                ],
                
                "monthly_events": [ 
                    { "$group": { 
                        "_id": { "year": { "$year": "$start_time" }, "month": { "$month": "$start_time" } }, 
                        "total_events": { "$sum": 1 } 
                    }}, 
                    { "$sort": { "_id.year": 1, "_id.month": 1 } } 
                ]
            }
        }
    ]
    
    event_results = list(event_collection.aggregate(analysis_pipeline))
    
    # 3. Post Aggregation Pipeline (Sentiment Analysis)
    sentiment_pipeline = _get_sentiment_pipeline(start_dt, end_dt, disaster_type)
    sentiment_results = list(post_collection.aggregate(sentiment_pipeline))
    
    # 4. Combine and Return
    final_result = event_results[0] if event_results and event_results[0] else {}
    final_result["sentiment_counts"] = sentiment_results
    
    if not final_result:
        return { "type_counts": [], "district_ranking": [], "monthly_events": [], "sentiment_counts": [] }
        
    return final_result

@router.get(
    "/analytics/keywords/filtered",
    summary="Retrieve top N trending keywords filtered by date range and disaster type (Live Calc)."
)
async def get_top_keywords_filtered(
    db: Database = Depends(get_db),
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    disaster_type: Optional[str] = Query(None, description="Optional filter by disaster type (e.g., 'flood')"),
    limit: int = 10
):
    # Ensure start and end date are logically ordered
    if start_date > end_date:
        raise HTTPException(
            status_code=400, 
            detail="start_date cannot be after end_date."
        )
    
    # Collection: The final source of truth with the historical context and the new 'keywords' field
    post_collection = db[DISASTER_POSTS_COLLECTION] 
    
    start_dt = _get_time_aware_datetime(start_date, is_end=False)
    end_dt = _get_time_aware_datetime(end_date, is_end=True)
    
    # 1. Base Match Filter
    match_query = {
        # Filter by the correct historical time field
        "start_time": { "$gte": start_dt, "$lte": end_dt },
        "keywords": { "$ne": None, "$exists": True, "$ne": "" } 
    }
    
    if disaster_type:
        # Filter by the correct classification field
        match_query["disaster_type"] = disaster_type.lower()
    
    # 2. Aggregation Pipeline
    pipeline = [
        {"$match": match_query},
        
        # New Step 1: Clean the keyword string (remove commas, periods, etc.)
        {"$project": {
            "cleaned_keywords": {
                # 1. Convert to lowercase immediately
                "$toLower": "$keywords" 
            }
        }},
        # Step E: Group and count the individual words
        {
            "$group": {
                "_id": "$cleaned_keywords", # Already lowercased, no need for $toLower again
                "count": {"$sum": 1}
            }
        },
        
        # Step D: Sort and limit the results
        {"$sort": {"count": -1}},
        {"$limit": limit},
        
        # Step E: Reshape the output to match the expected model
        {"$project": {"_id": 0, "keyword": "$_id", "frequency": "$count"}}
    ]
    
    # This line is now safe from UnboundLocalError and uses the correct pipeline
    results = list(post_collection.aggregate(pipeline))
    
    return results
