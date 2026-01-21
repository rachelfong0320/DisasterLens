import time
import random
import json
from datetime import datetime
from kafka import KafkaProducer
from core.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_SSL_CONFIG
from core.scrapers.InstagramDataScraper.dbConnection import DatabaseConnection

# Import the template from your new file
from core.scrapers.InstagramDataScraper.mock_data import MOCK_INSTAGRAM_POSTS

def run_mock_streaming():
    db = DatabaseConnection()
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        **KAFKA_SSL_CONFIG,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    print("--- INSTAGRAM SCRAPER STARTED ---")

    while True:
        # Pick a random template from your new data file
        template = random.choice(MOCK_INSTAGRAM_POSTS)
        
        doc = template.copy()
        doc["ig_post_id"] = str(random.randint(10**18, 10**19))
        doc["created_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Insert to DB so it shows up in your history/maps
        db.collection.insert_one(doc)
        
        # Prepare for Kafka topic 'raw_social_data'
        doc.pop('_id', None)
        doc['platform'] = 'instagram'
        doc['raw_text'] = doc.get('description', '') 
        
        producer.send('raw_social_data', value=doc)
        print(f"Sent new post {doc['ig_post_id']} to pipeline...")
        
        time.sleep(20) # Wait 20 seconds for the next one

if __name__ == "__main__":
    run_mock_streaming()