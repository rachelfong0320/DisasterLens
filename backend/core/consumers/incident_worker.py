import asyncio
import json
import logging
import ssl
from datetime import datetime, timezone
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SSL_CONFIG, COMBINED_DB_NAME, POSTS_COLLECTION, DISASTER_POSTS_COLLECTION
from app.database import db_connection

# --- Import Final Stage Logic ---
from core.jobs.main_geoProcessor import reverse_geocode_coordinates 
from core.jobs.main_incidentClassifier import classify_incident_async
from core.processor.event_consolidator import run_event_consolidation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("IncidentWorker")

# Semaphore for AI Rate Limiting
sem = asyncio.Semaphore(20)

async def process_final_stage(data, producer):
    # 1. Ensure data is a dict
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            logger.error("Failed to parse data string into dictionary")
            return

    post_id = data.get("postId") or data.get("post_id")
    
    # 2. Extract Keyword Text safely
    raw_keywords = data.get('keywords')
    if isinstance(raw_keywords, dict):
        keyword_text = raw_keywords.get('topic', '')
    else:
        keyword_text = str(raw_keywords or '')

    db = db_connection.combined_db 
    loop = asyncio.get_event_loop()

    try:
        logger.info(f"--- STARTING FINAL STAGE FOR POST: {post_id} ---")

        # 3. Geo Processing (OpenCage Logic)
        geo_res = await loop.run_in_executor(
            None, 
            reverse_geocode_coordinates,
            data.get('latitude'),
            data.get('longitude'),
            data.get('postText', ''),
            data.get('location', ''),
            keyword_text
        )
        logger.info(f"🌍 Geo Processing Result for {post_id}: {geo_res}")
        data['geo_data'] = geo_res
        data['geo_processed'] = True

        # 4. Incident Classification
        incident_res = await classify_incident_async(data, sem)

        # Ensure incident_res is a dict for consistency
        if isinstance(incident_res, str):
            data['incident'] = {"classification_type": incident_res, "confidence_score": 1.0}
        else:
            data['incident'] = incident_res

        # 5. Save RAW Data to MongoDB
        db[POSTS_COLLECTION].update_one(
            {"postId": post_id}, 
            {"$set": data}, 
            upsert=True
        )

        # ---------------------------------------------------------
        # 6. TRANSFORM: Assembly Logic (Moved from Event Creator)
        # ---------------------------------------------------------
        # This builds the exact format the Consolidator expects to group by location
        clean_event_point = {
            "post_id": post_id,
            "classification_status": "Confirmed",
            "disaster_type": data['incident'].get("classification_type"),
            "start_time": data.get("createdAt"),
            "location": {
                "state": geo_res.get("state"),
                "district": geo_res.get("district"),
                "lat_lon": [data.get("longitude"), data.get("latitude")], 
            },
            "post_text": data.get("postText"),
            "keywords": keyword_text,
            "sentiment": data.get("sentiment", {}) # From Analytics Worker
        }

        db[DISASTER_POSTS_COLLECTION].update_one(
            {"post_id": post_id}, 
            {"$set": clean_event_point}, 
            upsert=True
        )
        logger.info(f"📤 Saved to {DISASTER_POSTS_COLLECTION} for FE display")

        # ---------------------------------------------------------
        # 7. CONSOLIDATE: Grouping posts into Events
        # ---------------------------------------------------------
        logger.info(f"🔄 Grouping {post_id} into Disaster Events...")
        event_id = await loop.run_in_executor(
            None, 
            run_event_consolidation, 
            db, 
            clean_event_point
        )

        # 8. Produce Result to Kafka
        if event_id:
            await producer.send_and_wait(
                'incidents', 
                {"event_id": str(event_id), "postId": post_id}
            )
        
        logger.info(f"✅ Success: Post {post_id} integrated into Event {event_id}")

    except Exception as e:
        logger.error(f"❌ Final stage failed for {post_id}: {e}", exc_info=True)

async def run():
    # 1. Create the SSL context manually using paths from your config
    # We pull the paths OUT of the dictionary so we don't pass the dictionary itself
    context = ssl.create_default_context(cafile=KAFKA_SSL_CONFIG['ssl_cafile'])
    context.load_cert_chain(
        certfile=KAFKA_SSL_CONFIG['ssl_certfile'], 
        keyfile=KAFKA_SSL_CONFIG['ssl_keyfile']
    )
    context.check_hostname = False 
    context.verify_mode = ssl.CERT_REQUIRED

    # 2. Setup Consumer
    consumer = AIOKafkaConsumer(
        'processed_data',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        # group_id='incident-finalizer-group',
        group_id='incident-worker-debug-v1',  # Change this to a new name
        auto_offset_reset='earliest',
        # Ensure it decodes bytes to string, then loads to dict
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        security_protocol='SSL',
        ssl_context=context
    )
    
    # 3. Setup Producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        security_protocol='SSL',
        ssl_context=context
    )

    await consumer.start()
    await producer.start()
    
    try:
        logger.info("Incident Worker active. Waiting for AI-enriched data...")
        async for message in consumer:
            logger.info("-" * 30)
            logger.info(f"📥 Received from Kafka: Offset {message.offset}")
            await process_final_stage(message.value, producer)
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(run())