import logging
import re
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from core.jobs.schemas import LocationExtraction
from openai import OpenAI
from shapely.geometry import shape, Point
from core.jobs.prompts import LOCATION_AUDITOR_PROMPT
from pymongo import UpdateOne
from core.config import (
    OPEN_CAGE_KEY, 
    OPENAI_API_KEY,
    MALAYSIA_BOUNDING_BOX, 
    MALAYSIA_STATES_WHITELIST, 
    STATE_DISPLAY_NAME_MAP,
    MALAYSIA_STATE_DISTRICT_MAP
)

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize OpenCage Geocoder
try: 
    from opencage.geocoder import OpenCageGeocode 
    geocoder = OpenCageGeocode(OPEN_CAGE_KEY)
except Exception:
    class _StubGeocoder:
        def reverse_geocode(self, *args, **kwargs): return None
        def geocode(self, *args, **kwargs): return None
    geocoder = _StubGeocoder()

# Flatten the map for instant keyword matching
LOCATION_LOOKUP = {}
for state, districts in MALAYSIA_STATE_DISTRICT_MAP.items():
    LOCATION_LOOKUP[state.lower()] = (state, "Unknown District")
    for d in districts:
        LOCATION_LOOKUP[d.lower()] = (state, d)

# Compile a single regex pattern for all Malaysian locations
LOCATION_PATTERN = re.compile(r'\b(' + '|'.join(map(re.escape, LOCATION_LOOKUP.keys())) + r')\b', re.IGNORECASE)

# --- SPATIAL DATA PRE-LOADING ---
# 1. Absolute path inside Docker (Because /backend is mapped to /app)
GADM_PATH = Path("/app/data/gadm41_MYS_2.json")

# 2. Local Fallback (If running outside Docker)
if not GADM_PATH.exists():
    GADM_PATH = Path(__file__).resolve().parents[2] / "data" / "gadm41_MYS_2.json"

logging.info(f"GEOPROCESSOR: Searching for GADM at {GADM_PATH}")

try:
    with open(GADM_PATH, encoding='utf-8') as f:
        MALAYSIA_GADM = json.load(f)
        logging.info(f"✅ SUCCESS: GADM file loaded. Total shapes: {len(MALAYSIA_GADM.get('features', []))}")
except FileNotFoundError:
    logging.error(f"FATAL: GADM file not found at {GADM_PATH}. Layer 1 (GPS) will fail.")
    MALAYSIA_GADM = {"features": []}
except Exception as e:
    logging.error(f"ERROR: Could not parse GADM JSON: {e}")
    MALAYSIA_GADM = {"features": []}

# --- PILLAR 1: THE AI AUDITOR ---
def pillar1_openai_auditor(text: str, keywords: Any) -> Optional[LocationExtraction]:
    """Uses Structured Outputs to extract clean location intent."""
    try:
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": LOCATION_AUDITOR_PROMPT},
                {"role": "user", "content": f"Text: {text}\nKeywords: {keywords}"}
            ],
            response_format=LocationExtraction,
        )
        logging.info(f"OpenAI Auditor Result: {completion.choices[0].message.parsed}")
        return completion.choices[0].message.parsed
    except Exception as e:
        logging.error(f"OpenAI Error: {e}")
        return None
    
# --- PILLAR 2: THE OPENCAGE BRIDGE ---
def pillar2_opencage_bridge(search_str: str) -> Optional[Dict]:
    """Forward geocoding: Keywords -> Coordinates."""
    if not search_str or len(search_str) < 3: return None
    time.sleep(1.1) # OpenCage Free Tier rate limit
    try:
        res = geocoder.geocode(search_str, limit=1, countrycode='my')
        if res:
            return {'lat': res[0]['geometry']['lat'], 'lon': res[0]['geometry']['lng']}
    except Exception as e:
        logging.error(f"OpenCage Error: {e}")
    return None

# --- PILLAR 3: THE GADM JUDGE ---
def pillar3_gadm_judge(lat: float, lon: float) -> Optional[Dict]:
    """Spatial verification using local GeoJSON polygons."""
    point = Point(lon, lat) # GeoJSON is [Longitude, Latitude]
    for feature in MALAYSIA_GADM.get('features', []):
        polygon = shape(feature['geometry'])
        if polygon.contains(point):
            logging.info(f"GADM Match: {feature['properties'].get('NAME_1')}, {feature['properties'].get('NAME_2')}")
            return {
                'state': feature['properties'].get('NAME_1'),
                'district': feature['properties'].get('NAME_2'),
            }
    return None

def is_in_malaysia(lat: Optional[float], lon: Optional[float]) -> bool:
    """LAYER 0: Spatial Integrity Check."""
    if lat is None or lon is None: return False
    try:
        lat_f, lon_f = float(lat), float(lon)
        min_lat, max_lat = MALAYSIA_BOUNDING_BOX["lat"]
        min_lon, max_lon = MALAYSIA_BOUNDING_BOX["lon"]
        return (min_lat <= lat_f <= max_lat) and (min_lon <= lon_f <= max_lon)
    except (ValueError, TypeError):
        return False
    
def _format_keywords_to_string(keywords_data: Any) -> str:
    """Standardizes keywords/topics into a clean string for OpenCage."""
    if not keywords_data: 
        return ""
    if isinstance(keywords_data, str): 
        return keywords_data.strip()
    if isinstance(keywords_data, dict):
        topic = keywords_data.get('topic')
        if topic:
            return ", ".join(topic) if isinstance(topic, list) else str(topic).strip()
        return ", ".join([str(v) for v in keywords_data.values() if v])
    if isinstance(keywords_data, list): 
        return ", ".join([str(k) for k in keywords_data if k])
    return str(keywords_data)    
    
# --- THE ORCHESTRATOR ---
def reverse_geocode_coordinates(lat: Any, lon: Any, post_text: str, keywords: Any) -> Dict[str, Any]:
    """
    Implements Path A (GPS Validation) and Path B (AI Rescue).
    Keeps the exact geo_data structure required for dashboard.
    """
    res = {
        'state': 'Unknown State', 'district': 'Unknown District', 
        'lat': lat, 'lon': lon, 'is_malaysia': False,
        'confidence_score': 0, 'inference': 'none'
    }

    try:
        # 1. Audit Human Intent (Pillar 1)
        ai_intent = pillar1_openai_auditor(post_text, keywords)
        
        # Path A: If GPS Coordinates Exist
        if lat and lon and is_in_malaysia(lat, lon):
            res['is_malaysia'] = True
            gadm_initial = pillar3_gadm_judge(float(lat), float(lon))
            
            # Match Verification
            if gadm_initial and ai_intent and gadm_initial['state'].lower() == ai_intent.state.lower():
                logging.info(f"✅ [PATH A] GPS matches Text Intent: {ai_intent.state}")
                res.update(gadm_initial)
                res.update({'confidence_score': 1.0, 'inference': 'gps_verified_by_ai'})
                return res
        
        # Path B: Conflict Resolution or No GPS (Rescue)
        if ai_intent and ai_intent.state != "Unknown":
            logging.info(f"🚀 [PATH B] Rescuing via OpenCage for: {ai_intent.search_string}")
            search_query = ai_intent.search_string if ai_intent.search_string else _format_keywords_to_string(keywords)
            # Use OpenCage to find the intended location
            bridge_coords = pillar2_opencage_bridge(search_query)
            if bridge_coords:
                # Final Spatial Judge
                final_gadm = pillar3_gadm_judge(bridge_coords['lat'], bridge_coords['lon'])
                if final_gadm:
                    logging.info(f"✨ [RESCUED] Successfully pinned to {final_gadm['district']}, {final_gadm['state']}")
                    res.update(final_gadm)
                    res.update(bridge_coords)
                    res.update({'is_malaysia': True, 'confidence_score': 0.8, 'inference': 'ai_opencage_rescue'})
                    return res
                else:
                    logging.info(f"⚠️ [CONFLICT] GPS says {gadm_initial['state'] if gadm_initial else 'Unknown'}, but Text says {ai_intent.state if ai_intent else 'Unknown'}. Shifting to Path B.")

        # Fallback: GPS Only (if path A didn't verify but GADM found it)
        if lat and lon and is_in_malaysia(lat, lon):
            logging.info("📡 [FALLBACK] Using original GPS metadata only.")
            gadm_fallback = pillar3_gadm_judge(float(lat), float(lon))
            if gadm_fallback:
                res.update(gadm_fallback)
                res.update({'confidence_score': 0.6, 'inference': 'gps_only'})

    except Exception as e:
        logging.error(f"Geoprocessing Error: {e}")
        
    return res

# --- THE SWEEP ENGINE ---
def run_geo_processing_sweep(db_instance: Any, batch_size: int = 50) -> int:
    posts_collection = db_instance.posts_collection
    total_processed = 0
    
    # Query targets records that need cleaning or rescue
    query = {
        "$or": [
            {"geo_processed": {"$ne": True}}, 
            {"geo_data.state": "Unknown State"},
            {"geo_data.confidence_score": {"$lt": 0.3}}
        ]
    }

    total_to_do = posts_collection.count_documents(query)
    print(f"🚀 Starting sweep... Target: {total_to_do} records.", flush=True)

    while True:

        posts = list(posts_collection.find(query).sort("_id", 1).limit(batch_size))
        if not posts: 
            print("🏁 Finished! All records processed.") 
            break
        
        updates = []
        for p in posts:
            raw_lat = p.get('raw_geo', {}).get('latitude') or p.get('latitude')
            raw_lon = p.get('raw_geo', {}).get('longitude') or p.get('longitude')

            current_id = str(p.get('_id'))

            logging.info(f"🔍 [ANALYSING] GIS for {current_id}...")
            
            geo_result = reverse_geocode_coordinates(raw_lat, raw_lon, p.get('postText', ''), p.get('keywords'))
            
            update_op = {
                '$set': {
                    'geo_data': geo_result, 
                    'geo_processed': True,
                    'last_processed_at': time.time()
                }
            }
            
            # Data Migration for root fields to raw_geo
            rename_map = {}
            for field in ['latitude', 'longitude', 'location', 'address', 'city']:
                if field in p: rename_map[field] = f'raw_geo.{field}'
            if rename_map: update_op['$rename'] = rename_map

            updates.append(UpdateOne({'_id': p['_id']}, update_op))
        
        if updates:
            posts_collection.bulk_write(updates)
            total_processed += len(updates)
            print(f"Sweep Progress: {total_processed} records processed...")
            
    return total_processed
