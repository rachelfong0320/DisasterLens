import asyncio
import json
import logging
import time
import ssl
from typing import Dict, Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SSL_CONFIG

# --- AI Classifiers ---
from core.scrapers.TweetDataScraper.main_misinfoClassifier import classify_tweet_async
from core.scrapers.InstagramDataScraper.main_misinfoClassifier import classify_instagram_post

# --- Geo Resolver ---
from core.scrapers.TweetDataScraper.main_dataCombine import get_geo_data_safe


# =========================
# LOGGING (Docker-safe)
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
    force=True
)
logger = logging.getLogger("MisinfoCombineWorker")


# =========================
# GLOBALS
# =========================
CLASSIFY_TIMEOUT = 45  # seconds
MAX_CONCURRENT_CLASSIFIERS = 20
sem = asyncio.Semaphore(MAX_CONCURRENT_CLASSIFIERS)


# =========================
# MESSAGE PROCESSOR
# =========================
async def process_message(data: Dict[str, Any], producer: AIOKafkaProducer):
    platform = data.get("platform")
    logger.info(f"Processing message from platform={platform}")

    # --------------------------
    # 1. MISINFO CLASSIFICATION
    # --------------------------
    try:
        try:
            if platform == "twitter":
                result = await asyncio.wait_for(
                    classify_tweet_async(data, sem),
                    timeout=CLASSIFY_TIMEOUT
                )
            else:
                result = await asyncio.wait_for(
                    classify_instagram_post(data, sem),
                    timeout=CLASSIFY_TIMEOUT
                )
        except asyncio.TimeoutError:
            logger.warning("Classifier timeout — dropping message")
            return

        is_authentic = result and result.get("check_label") == "AUTHENTIC"
        if not is_authentic:
            logger.info("MISINFO filtered out")
            return

        # --------------------------
        # 2. GEO FIX
        # --------------------------
        lat = data.get("latitude")
        lng = data.get("longitude")
        location_str = data.get("location") or data.get("location_name") or ""

        address = data.get("address")
        city = data.get("city")

        if lat is None or lng is None:
            logger.info(f"Resolving geo for location='{location_str}'")
            try:
                address, city, lat, lng = get_geo_data_safe(location_str)
            except Exception as geo_err:
                logger.warning(f"Geo resolution failed: {geo_err}")

        # --------------------------
        # 3. UNIFIED SCHEMA
        # --------------------------
        unified_payload = {
            "postId": data.get("tweet_id") or data.get("ig_post_id"),
            "postText": (
                data.get("translated_text")
                or data.get("cleaned_text")
                or data.get("cleaned_description")
                or data.get("description")
                or data.get("raw_text")
            ),
            "createdAt": data.get("tweet_created_at") or data.get("created_at"),
            "hashtags": data.get("tweet_hashtags") or data.get("hashtags") or [],
            "location": location_str,
            "address": address,
            "city": city,
            "latitude": lat,
            "longitude": lng,
            "author_id": data.get("user_id") or data.get("author_id"),
            "author_name": (
                data.get("user_name")
                or data.get("author_username")
                or ""
            ),
            "processedAt": time.time(),
            "source": platform.capitalize() if platform else "Unknown"
        }

        # --------------------------
        # 4. PRODUCE
        # --------------------------
        await producer.send_and_wait(
            topic="authentic_posts",
            value=unified_payload
        )

        # Log produced message for debugging
        logger.info(">>> PRODUCED MESSAGE <<<\n%s", json.dumps(unified_payload, indent=2))
        logger.info(f"AUTHENTIC post published | id={unified_payload['postId']}")

    except Exception as e:
        logger.exception(f"Message processing failed: {e}")


# =========================
# MAIN RUNNER
# =========================
async def run():
    logger.info("MISINFO COMBINE WORKER BOOTING")

    # --------------------------
    # SSL CONTEXT
    # --------------------------
    logger.info("Initializing SSL context")
    ssl_context = ssl.create_default_context(
        cafile=KAFKA_SSL_CONFIG["ssl_cafile"]
    )
    ssl_context.load_cert_chain(
        certfile=KAFKA_SSL_CONFIG["ssl_certfile"],
        keyfile=KAFKA_SSL_CONFIG["ssl_keyfile"],
    )
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED

    # --------------------------
    # CONSUMER
    # --------------------------
    consumer = AIOKafkaConsumer(
        "raw_social_data",
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="misinfo-gatekeeper-group-debug",
        security_protocol="SSL",
        ssl_context=ssl_context,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        max_poll_interval_ms=600_000,
    )

    # --------------------------
    # PRODUCER
    # --------------------------
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        security_protocol="SSL",
        ssl_context=ssl_context,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    # --------------------------
    # START
    # --------------------------
    logger.info("Starting Kafka consumer...")
    await consumer.start()
    logger.info("Kafka consumer started")

    logger.info("Starting Kafka producer...")
    await producer.start()
    logger.info("Kafka producer started")

    try:
        logger.info("Listening for messages on topic: raw_social_data")

        async for message in consumer:
            # Log consumed message
            logger.info(">>> CONSUMED MESSAGE <<<\n%s", json.dumps(message.value, indent=2))
            await process_message(message.value, producer)

    except Exception as e:
        logger.exception(f"Fatal consumer loop error: {e}")

    finally:
        logger.info("Shutting down Kafka clients")
        await consumer.stop()
        await producer.stop()


# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    asyncio.run(run())
