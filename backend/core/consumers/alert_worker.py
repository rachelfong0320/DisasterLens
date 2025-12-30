import json
import logging
from kafka import KafkaConsumer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SSL_CONFIG
from core.jobs.alert_generator import process_event_for_alerts

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AlertWorker")

def run():
    # 1. Initialize Kafka Consumer
    # We listen to the 'incidents' topic which now carries Event IDs
    consumer = KafkaConsumer(
        'incidents',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        **KAFKA_SSL_CONFIG,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='alert-worker-group',
        request_timeout_ms=30000
    )

    logger.info("Alert Worker is active. Monitoring for disaster events...")

    for message in consumer:
        event_data = message.value
        event_id = event_data.get('event_id')
        
        if not event_id:
            continue

        try:
            logger.info(f"📬 Processing alerts for Event: {event_id}")
            
            # 2. TRIGGER YOUR ORIGINAL ALERT LOGIC
            # This function checks for matching subscribers and sends emails via SMTP
            process_event_for_alerts(event_id)
            
            logger.info(f"Alert processing finished for {event_id}")

        except Exception as e:
            logger.error(f"Failed to send alerts for {event_id}: {e}")

if __name__ == "__main__":
    run()