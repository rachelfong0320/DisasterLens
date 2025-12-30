# Used processed data to classify incident type, refine geo, consolidate events, and produce to incidents topic

import asyncio
import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SSL_CONFIG, COMBINED_DB_NAME, POSTS_COLLECTION
from app.database import db_connection

# --- Import Final Stage Logic ---
from core.jobs.main_geoProcessor import reverse_geocode_coordinates # High-quality OpenCage logic
from core.jobs.main_incidentClassifier import classify_incident_async
from core.processor.event_consolidator import run_event_consolidation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IncidentWorker")

# Semaphore for AI Rate Limiting
sem = asyncio.Semaphore(20)

async def process_final_stage(data, producer):
    post_id = data.get("postId")
    db = db_connection[COMBINED_DB_NAME]
    loop = asyncio.get_event_loop()

    try:
        logger.info(f"Finalizing Incident & Geo for Post: {post_id}")

        # 1. HIGH-QUALITY GEO REFINEMENT
        # We now pass 'keywords' generated in Step 3 as a fallback.
        # This function uses your OpenCage logic to get State/District.
        geo_res = await loop.run_in_executor(
            None, 
            reverse_geocode_coordinates,
            data.get('latitude'),
            data.get('longitude'),
            data.get('postText', ''),
            data.get('location', ''),
            data.get('keywords') 
        )
        data['geo_data'] = geo_res
        data['geo_processed'] = True

        # 2. INCIDENT CLASSIFICATION
        # Determines if it's a Flood, Landslide, etc.
        incident_res = await classify_incident_async(data, sem)
        data['incident'] = incident_res

        # 3. SAVE TO FINAL MONGODB COLLECTION (posts_data)
        # This is the "DataCombine" result you showed me earlier.
        db[POSTS_COLLECTION].update_one(
            {"postId": post_id}, 
            {"$set": data}, 
            upsert=True
        )

        # 4. CONSOLIDATE INTO DISASTER EVENTS
        # Groups this post with others in the same area/time to create a master event
        event_id = await loop.run_in_executor(None, run_event_consolidation, db, data)

        # 5. PRODUCE TO TOPIC: incidents
        # We send the Event ID to trigger alerts in Step 5
        if event_id:
            producer.send('incidents', value={"event_id": str(event_id), "postId": post_id})
            producer.flush()
        
        logger.info(f"Post {post_id} fully integrated into Event {event_id}")

    except Exception as e:
        logger.error(f"Final stage failed for {post_id}: {e}")

async def run():
    consumer = KafkaConsumer(
        'processed_data',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        **KAFKA_SSL_CONFIG,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='incident-finalizer-group',
        request_timeout_ms=30000
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        **KAFKA_SSL_CONFIG,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        request_timeout_ms=30000
    )

    logger.info("Incident Worker active. Waiting for AI-enriched data...")
    for message in consumer:
        await process_final_stage(message.value, producer)

if __name__ == "__main__":
    asyncio.run(run())