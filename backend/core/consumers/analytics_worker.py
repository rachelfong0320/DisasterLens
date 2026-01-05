#take authentic posts to run sentiment & keywords (authentic_posts -> processed_data)

import asyncio
import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SSL_CONFIG

# --- Import Shared AI Jobs ---
from core.jobs.main_sentimentAnalysis import analyze_sentiment_async
from core.jobs.main_keywordTracking import generate_main_topic_async

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnalyticsWorker")

# Global semaphore to control OpenAI rate limits
sem = asyncio.Semaphore(20)

async def process_analytics(combined_data, producer):
    post_id = combined_data.get("postId")
    try:
        logger.info(f"Running AI Enrichment for Post: {post_id}")

        # 1. RUN AI JOBS IN PARALLEL
        # We use the unified 'postText' created in Step 2
        sentiment_task = analyze_sentiment_async(combined_data, sem)
        keyword_task = generate_main_topic_async(combined_data)

        # Execute both tasks at the same time to save time/cost
        sentiment_res, keyword_res = await asyncio.gather(sentiment_task, keyword_task)

        # 2. ATTACH RESULTS
        # keyword_res contains the 'topic' used by your later geo logic
        combined_data['sentiment'] = sentiment_res
        combined_data['keywords'] = keyword_res  
        combined_data['analytics_status'] = "enriched"

        # 3. PRODUCE TO TOPIC: processed_data
        # This data is now enriched with AI results, ready for Incident Classification
        producer.send('processed_data', value=combined_data)
        producer.flush()
        
        logger.info(f"AI Enrichment complete for {post_id}. Forwarding...")

    except Exception as e:
        logger.error(f"Analytics enrichment failed for {post_id}: {e}")

async def run():
    consumer = KafkaConsumer(
        'authentic_posts',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        **KAFKA_SSL_CONFIG,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='analytics-worker-group',
        request_timeout_ms=30000,
        max_poll_interval_ms=600000,  # 10 minutes (adjust as needed)
        max_poll_records=1             # optional: process 1 message at a time
    )
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        **KAFKA_SSL_CONFIG,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        request_timeout_ms=30000
    )

    logger.info("Analytics Worker active. Listening for authentic posts...")
    for message in consumer:
        await process_analytics(message.value, producer)

if __name__ == "__main__":
    asyncio.run(run())