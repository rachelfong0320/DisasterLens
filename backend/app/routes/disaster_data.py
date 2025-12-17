# app/routes/disaster_data.py
import csv
import io
import json
import pandas as pd
from fastapi.responses import StreamingResponse
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

    if state:
        districts = MALAYSIA_STATE_DISTRICT_MAP.get(state.lower())
        if districts:
            query_filter["location_district"] = {"$in": districts}

    # Filter out 'Unknown' districts/states (using $nin for not in)
    unknown_terms = ["unknown district", "unknown state", "unknown", ""]
    
    query_filter["location_district"] = {
        **query_filter.get("location_district", {}), # Preserve existing district filters (if 'state' was provided)
        "$nin": unknown_terms,
        "$exists": True
    }
    
    query_filter["location_state"] = {
        **query_filter.get("location_state", {}), # Preserve existing state filters (though none are currently applied directly)
        "$nin": unknown_terms,
        "$exists": True
    }

    # Execute the query
    events = []
    # FIX: Since we need to project the size of related_post_ids for accuracy, 
    # we should use an aggregation pipeline here instead of .find()
    
    pipeline = [
        { "$match": query_filter },
        
        # Stage 2: Project the final document, calculating the accurate total_posts_count
        { "$project": {
            "_id": 0,
            "total_posts_count": { "$size": "$related_post_ids" },            
            "event_id": "$event_id",
            "classification_type": "$classification_type",
            "location_district": "$location_district",
            "location_state": "$location_state",
            "start_time": "$start_time",
            "most_recent_report": "$most_recent_report",
            "geometry": "$geometry",
            "related_post_ids": "$related_post_ids"
        }}
    ]

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

@router.get(
    "/events/export",
    response_model=None,
)
async def export_disaster_events(
    db: Database = Depends(get_db),
    format: str = Query(..., description="Export format: csv, excel, json, or raw"),
    limit: Optional[int] = Query(None, description="Limit the number of records (Amount)"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    location: Optional[str] = Query(None, description="Malaysian State (e.g., selangor)"),
    category: Optional[str] = Query(None, description="Category of disaster (e.g., flood)"),
    severity: Optional[str] = Query(None, description="Severity level (e.g., Urgent, Informational, Warning)"),
    keyword: Optional[str] = Query(None, description="Search keyword in title or description"),
):
    # 1. Build the MongoDB Query
    query = {}

    # Filter by Date Range
    if start_date or end_date:
        date_query = {}
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00').split('T')[0])
                date_query["$gte"] = start_dt
            except ValueError:
                pass 
        if end_date:
            try:
                end_dt_str = end_date.replace('Z', '+00:00').split('T')[0]
                end_dt = datetime.fromisoformat(end_dt_str).replace(hour=23, minute=59, second=59)
                date_query["$lte"] = end_dt
            except ValueError:
                pass
        if date_query:
            query["start_time"] = date_query

    # Filter by Location
    if location:
        query["$or"] = [
            {"location.state": {"$regex": location, "$options": "i"}},
            {"location.district": {"$regex": location, "$options": "i"}}
        ]

    # Filter by Category
    if category and category.lower() != "all":
        query["disaster_type"] = {"$regex": category, "$options": "i"}

    # Filter by Severity
    if severity and severity.lower() != "all":
        query["sentiment.label"] = {"$regex": severity, "$options": "i"}

    # Filter by Keyword
    if keyword:
        keyword_filter = [
            {"post_text": {"$regex": keyword, "$options": "i"}},
            {"keywords": {"$regex": keyword, "$options": "i"}}
        ]
        
        if "$or" in query:
            query["$and"] = [
                {"$or": query.pop("$or")},
                {"$or": keyword_filter}
            ]
        else:
            query["$or"] = keyword_filter

    # 2. Fetch Data (Synchronous)
    try:
        collection = db[DISASTER_POSTS_COLLECTION]

        # Use synchronous find and sort
        cursor = collection.find(query).sort("start_time", -1)
        
        if limit and limit > 0:
            cursor = cursor.limit(limit)
            
        # Synchronously convert cursor to list
        documents = list(cursor)
        
    except Exception as e:
        print(f"Export Database Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # 3. Process Data for Export
    data_list = []
    for doc in documents:
        flat_doc = {}
        
        # ID and Metadata
        flat_doc["id"] = str(doc.get("_id", ""))
        flat_doc["post_id"] = doc.get("post_id", "")
        flat_doc["status"] = doc.get("classification_status", "")
        flat_doc["disaster_type"] = doc.get("disaster_type", "none")
        
        # Time
        st = doc.get("start_time")
        if isinstance(st, datetime):
            flat_doc["start_time"] = st.isoformat()
        else:
            flat_doc["start_time"] = str(st) if st else ""

        # Content
        flat_doc["post_text"] = doc.get("post_text", "")
        
        # Flatten Location
        loc = doc.get("location", {})
        if isinstance(loc, dict):
            flat_doc["state"] = loc.get("state", "")
            flat_doc["district"] = loc.get("district", "")
            lat_lon = loc.get("lat_lon", [])
            if isinstance(lat_lon, list) and len(lat_lon) >= 2:
                flat_doc["longitude"] = lat_lon[0]
                flat_doc["latitude"] = lat_lon[1]
        
        # Flatten Sentiment
        sent = doc.get("sentiment", {})
        if isinstance(sent, dict):
            flat_doc["sentiment_label"] = sent.get("label", "")
            flat_doc["sentiment_confidence"] = sent.get("confidence", "")
            flat_doc["sentiment_reasoning"] = sent.get("reasoning", "")

        flat_doc["keywords"] = doc.get("keywords", "")

        if format in ["json", "raw"]:
            clean_doc = doc.copy()
            clean_doc["_id"] = str(clean_doc["_id"])
            if isinstance(clean_doc.get("start_time"), datetime):
                clean_doc["start_time"] = clean_doc["start_time"].isoformat()
            data_list.append(clean_doc)
        else:
            data_list.append(flat_doc)

    if not data_list:
        if format in ["json", "raw"]:
            data_list = [{"message": "No data found"}]
        else:
            data_list = [] 

    filename_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 4. Generate File
    if format in ["json", "raw"]:
        json_str = json.dumps(data_list, default=str, indent=2)
        return StreamingResponse(
            io.StringIO(json_str),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=disaster_data_{filename_timestamp}.json"}
        )

    elif format == "csv":
        df = pd.DataFrame(data_list)
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        return StreamingResponse(
            iter([stream.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=disaster_data_{filename_timestamp}.csv"}
        )

    elif format == "excel":
        df = pd.DataFrame(data_list)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Disaster Data')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=disaster_data_{filename_timestamp}.xlsx"}
        )

    raise HTTPException(status_code=400, detail="Invalid format specified")
