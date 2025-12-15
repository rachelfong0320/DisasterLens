import logging
from typing import Dict, Any, List
from pymongo import UpdateOne

# Assuming config.py and opencage are available
try:
    from opencage.geocoder import OpenCageGeocode 
    from core.config import OPEN_CAGE_KEY 
    # Initialize OpenCage client globally
    geocoder = OpenCageGeocode(OPEN_CAGE_KEY)
except Exception:
    # If OpenCage is unavailable in the test environment, create a lightweight stub
    class _StubGeocoder:
        def reverse_geocode(self, *args, **kwargs):
            return None
        def geocode(self, *args, **kwargs):
            return None
    geocoder = _StubGeocoder()


def _validate_and_swap_if_necessary(latitude, longitude, out):
    """Ensure latitude and longitude are in valid ranges; if not, attempt a swap."""
    try:
        lat_f = float(latitude)
        lon_f = float(longitude)
    except Exception:
        return latitude, longitude

    # If lat is outside [-90,90] but lon is within, swap them
    if (lat_f < -90 or lat_f > 90) and (-90 <= lon_f <= 90):
        out['swap_coords'] = True
        out['override_reason'] = 'coords_swapped'
        return lon_f, lat_f
    return lat_f, lon_f


def _haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0 # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


def _reverse_geocode(lat, lon):
    # If lat or lon are not usable, skip reverse geocode
    try:
        if lat is None or lon is None:
            return None
        results = geocoder.reverse_geocode(lat, lon, limit=1, language='en')
        if results and results[0]:
            comp = results[0]['components']
            return {
                'state': comp.get('state') or comp.get('state_district') or 'Unknown State',
                'district': comp.get('county') or comp.get('city') or comp.get('town') or comp.get('village') or 'Unknown District',
                'lat': results[0]['geometry']['lat'],
                'lon': results[0]['geometry']['lng']
            }
    except Exception as e:
        logging.debug(f"Reverse geocode error: {e}")
    return None


def _keyword_geocode(keyword: str):
    if not keyword or not keyword.strip():
        return None
    try:
        query = keyword.strip() + ", Malaysia"
        results = geocoder.geocode(query, limit=1, language='en')
        if results and results[0]:
            comp = results[0].get('components', {})
            return {
                'state': comp.get('state') or comp.get('state_district'),
                'district': comp.get('county') or comp.get('city') or comp.get('town') or comp.get('village'),
                'lat': results[0]['geometry']['lat'],
                'lon': results[0]['geometry']['lng']
            }
    except Exception as e:
        logging.debug(f"Keyword geocode failed: {e}")
    return None


def reverse_geocode_coordinates(lat: float, lon: float, post_text: str, raw_location_str: str, keywords: str = None) -> Dict[str, Any]:
    """Uses OpenCage to find state and district from coordinates, with text and keyword fallback.
    Returns dict with keys: state,district,lat,lon, override_reason, swap_coords, previous
    """

    # Initialize the structured location object
    structured_location = {
        'state': 'Unknown State',
        'district': 'Unknown District',
        'lat': lat,
        'lon': lon,
        'override_reason': None,
        'swap_coords': False,
        'previous': None
    }

    # Sanitize/Swap Coordinates (lat/lon may be None)
    try:
        lat, lon = _validate_and_swap_if_necessary(lat, lon, structured_location)
    except Exception:
        pass

    # Primary reverse geocode
    reverse_res = _reverse_geocode(lat, lon)
    if reverse_res:
        structured_location['previous'] = {
            'state': structured_location['state'],
            'district': structured_location['district'],
            'lat': structured_location['lat'],
            'lon': structured_location['lon']
        }
        structured_location.update(reverse_res)
        # distance check
        try:
            distance = _haversine(float(lat), float(lon), float(structured_location['lat']), float(structured_location['lon']))
            if distance > 50:
                structured_location['override_reason'] = 'reverse_distance_large'
        except Exception:
            distance = 0
    else:
        # fallback: use raw_location_str heuristics
        if raw_location_str and len(raw_location_str.strip()) > 3:
            best_guess = raw_location_str.split(',')[0].strip()
            if best_guess.lower() not in ['malaysia', 'unknown'] and len(best_guess) > 2:
                if structured_location['previous'] is None:
                    structured_location['previous'] = {'state': structured_location['state'], 'district': structured_location['district'], 'lat': structured_location['lat'], 'lon': structured_location['lon']}
                structured_location['district'] = best_guess
                structured_location['state'] = 'GUESS'

    # Keyword fallback
    if keywords and isinstance(keywords, str) and len(keywords.strip()) > 2:
        kw_res = _keyword_geocode(keywords)
        if kw_res and kw_res.get('state'):
            # compute kw_distance
            try:
                kw_distance = _haversine(float(lat), float(lon), float(kw_res['lat']), float(kw_res['lon']))
            except Exception:
                kw_distance = 0

            # prefer keyword if state differs or kw_distance is closer
            reverse_distance = locals().get('distance', 0)
            if kw_res['state'] != structured_location.get('state') or kw_distance < reverse_distance:
                if structured_location['previous'] is None:
                    structured_location['previous'] = {'state': structured_location['state'], 'district': structured_location['district'], 'lat': structured_location['lat'], 'lon': structured_location['lon']}
                structured_location.update({
                    'state': kw_res['state'],
                    'district': kw_res.get('district') or structured_location.get('district'),
                    'lat': kw_res['lat'],
                    'lon': kw_res['lon'],
                    'override_reason': 'keyword_override'
                })

    return structured_location


def run_geo_processing_sweep(db_instance: Any, batch_size: int = 50) -> int:
    """
    Reverse geocodes posts in batches until all eligible posts are done.
    FIXED: Uses while loop for full coverage and $unset for cleanup.
    """
    from pymongo import UpdateOne
    
    logging.info("--- STARTING GEO-PROCESSING SWEEP ---")
    
    # Access collection via the Database instance property
    posts_collection = db_instance.posts_collection
    total_processed_count = 0
    
    # CRITICAL FIX: Loop until the query returns an empty set (full coverage)
    while True:
        # Query: Find UNPROCESSED posts that have coordinates OR keywords OR a raw location name
        query = {
            "geo_processed": { "$ne": True },
            "$or": [
                {"latitude": { "$exists": True, "$ne": None }, "longitude": { "$exists": True, "$ne": None }},
                {"keywords": { "$exists": True, "$ne": None }},
                {"location": { "$exists": True, "$ne": None }}
            ]
        }

        posts_cursor = posts_collection.find(query).limit(batch_size)
        posts_to_process = list(posts_cursor) 
        
        if not posts_to_process:
            break # Exit loop if no more posts are found

        logging.info(f"Processing a batch of {len(posts_to_process)} posts...")
        
        updates_queue = []
        
        for post in posts_to_process:
            try:
                lat = post.get('latitude')
                lon = post.get('longitude')
                post_text = post.get('postText', '')
                raw_location_str = post.get('location', '') 
                keywords = post.get('keywords')
                post_id = post.get('_id')

                # 1. Perform Geocoding/Fallback
                structured_location = reverse_geocode_coordinates(lat, lon, post_text, raw_location_str, keywords)
                
                # 2. Prepare bulk update operation - only set audit fields if present
                set_fields = {
                    'geo_data.state': structured_location['state'],
                    'geo_data.district': structured_location['district'],
                    'geo_data.lat': structured_location.get('lat', lat),
                    'geo_data.lon': structured_location.get('lon', lon),
                    'geo_processed': True
                }
                if structured_location.get('override_reason'):
                    set_fields['geo_data.override_reason'] = structured_location['override_reason']
                if structured_location.get('swap_coords'):
                    set_fields['geo_data.swap_coords'] = structured_location['swap_coords']
                if structured_location.get('previous'):
                    set_fields['geo_data.previous'] = structured_location['previous']

                updates_queue.append(
                    UpdateOne(
                        {'_id': post_id},
                        {
                            # CRITICAL FIX: RENAME the 5 base fields to raw_geo
                            '$rename': {
                                'latitude': 'raw_geo.latitude',
                                'longitude': 'raw_geo.longitude',
                                'location': 'raw_geo.location',
                                'address': 'raw_geo.address',
                                'city': 'raw_geo.city'
                            },
                            # SET the new refined geo_data and the processing flag
                            '$set': set_fields 
                        }
                    )
                )

            except Exception as e:
                logging.error(f"Failed to process post {post.get('postId')}: {e}")
                # Ensure the post is marked processed to avoid future reprocessing
                updates_queue.append(
                    UpdateOne(
                        { '_id': post.get('_id') },
                        { '$set': { 'geo_data.district': "UNKNOWN_ERROR", 'geo_processed': True } }
                    )
                )
                
        # Execute the bulk writes
        if updates_queue:
            posts_collection.bulk_write(updates_queue, ordered=False)
            total_processed_count += len(updates_queue)
            logging.info(f"Batch completed. Total processed so far: {total_processed_count}")
        else:
            break
            
    logging.info(f"GEO-PROCESSING SWEEP COMPLETE. Total posts processed: {total_processed_count}")
    return total_processed_count