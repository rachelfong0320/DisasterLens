# Used processed data to classify incident type, refine geo, consolidate events, and produce to incidents topic

import asyncio
import json
import logging
import ssl
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
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
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            logger.error(f"Failed to parse data string: {e}")
            return
        
    post_id = data.get("postId")
    
    # FIX: Access the internal PyMongo database object from your custom class
    # In your Database class, 'self.combined_db' is the actual PyMongo Database
    db = db_connection.combined_db 
    
    loop = asyncio.get_event_loop()

    try:
        logger.info(f"Finalizing Incident & Geo for Post: {post_id}")

        # 1. GEO REFINEMENT
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
        incident_res = await classify_incident_async(data, sem)
        data['incident'] = incident_res

        # 3. SAVE TO post_data
        # We use the 'db' PyMongo object we got above
        db[POSTS_COLLECTION].update_one(
            {"postId": post_id}, 
            {"$set": data}, 
            upsert=True
        )

        # 4. CONSOLIDATION
        # Pass the actual PyMongo database object to the consolidator
        event_id = await loop.run_in_executor(None, run_event_consolidation, db, data)

        if event_id:
           await producer.send_and_wait('incidents', {"event_id": str(event_id), "postId": post_id})
        
        logger.info(f"Post {post_id} successfully integrated.")

    except Exception as e:
        logger.error(f"Final stage failed for {post_id}: {e}")

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
        group_id='incident-finalizer-group',
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
        ssl_context=context  # Pass the object we created above
    )

    await consumer.start()
    await producer.start()
    
    try:
        logger.info("Incident Worker active. Waiting for AI-enriched data...")
        async for message in consumer:
            await process_final_stage(message.value, producer)
    finally:
        await consumer.stop()
        await producer.stop()


if __name__ == "__main__":
    asyncio.run(run())