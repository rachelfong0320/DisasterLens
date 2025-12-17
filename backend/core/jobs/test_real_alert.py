import sys
import os
from bson.objectid import ObjectId
import logging

# Fix path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from core.jobs.alert_generator import process_event_for_alerts

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    EVENT_ID = ObjectId("69415fdf9b49acef0c093a83")

    sent = process_event_for_alerts(EVENT_ID)

    print(f"Emails sent: {sent}")
