import asyncio
import json
import logging
import ssl
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SSL_CONFIG
from core.jobs.main_sentimentAnalysis import analyze_sentiment_async
from core.jobs.main_keywordTracking import generate_main_topic_async
import pprint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AnalyticsWorker")

sem = asyncio.Semaphore(20)
AI_TIMEOUT = 45  # max seconds per AI call

async def process_analytics(data, producer):
    post_id = data.get("postId")
    logger.info(">>> CONSUMED MESSAGE <<<\n%s", pprint.pformat(data))

    try:
        sentiment_task = asyncio.wait_for(analyze_sentiment_async(data, sem), timeout=AI_TIMEOUT)
        keyword_task = asyncio.wait_for(generate_main_topic_async(data), timeout=AI_TIMEOUT)

        sentiment_res, keyword_res = await asyncio.gather(sentiment_task, keyword_task)

        data['sentiment'] = sentiment_res
        data['keywords'] = keyword_res
        data['analytics_status'] = "enriched"
        data['processedAt'] = asyncio.get_event_loop().time()

        # Produce to Kafka
        await producer.send_and_wait('processed_data', value=data)
        logger.info(">>> PRODUCED MESSAGE <<<\n%s", pprint.pformat(data))
        logger.info(f"AI Enrichment complete for post {post_id}")

    except asyncio.TimeoutError:
        logger.warning(f"AI enrichment timed out for post {post_id}")
    except Exception as e:
        logger.exception(f"Analytics enrichment failed for post {post_id}: {e}")

async def run():
    ssl_context = ssl.create_default_context(cafile=KAFKA_SSL_CONFIG['ssl_cafile'])
    ssl_context.load_cert_chain(KAFKA_SSL_CONFIG['ssl_certfile'], KAFKA_SSL_CONFIG['ssl_keyfile'])
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    consumer = AIOKafkaConsumer(
        'authentic_posts',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id='analytics-worker-group',
        security_protocol='SSL',
        ssl_context=ssl_context,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        max_poll_interval_ms=600_000,
        auto_offset_reset='earliest'
    )

    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        security_protocol='SSL',
        ssl_context=ssl_context,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    await consumer.start()
    await producer.start()
    logger.info("Analytics Worker active. Listening for authentic posts...")

    try:
        async for message in consumer:
            await process_analytics(message.value, producer)
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(run())
