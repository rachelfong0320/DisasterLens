import sys
import os
import logging
from datetime import datetime
from bson.objectid import ObjectId

# Add the parent directory to the path to import application modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Import the function from the core module
from core.jobs.alert_generator import _send_notification_email
# Note: process_event_for_alerts uses DB, so we test the inner function directly

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def manual_email_test():
    """
    Simulates a disaster event and calls the email sending function directly.
    """
    
    # 1. Mock Subscriber Data (The person who will receive the email)
    TEST_RECIPIENT_EMAIL = "rachelfong.tw@gmail.com" 

    # 2. Mock Disaster Event Data (Simulating what comes from consolidation)
    mock_event_data = {
        # This ObjectId is just for structure, the DB isn't hit for _send_notification_email
        "_id": ObjectId("694005831998c908d01ab442"), 
        "event_id": "LANDSLIDE-TEST-20251215-110000",
        "classification_type": "landslide",
        "location_district": "Kedah",
        "start_time": datetime.utcnow(),
        "geometry": {"type": "Point", "coordinates": [101.69, 3.14]},
        "related_post_ids": ["1234567890"]
    }
    
    # Check if SMTP details are available before attempting to send
    smtp_host = os.getenv("SMTP_HOST")
    smtp_user = os.getenv("SMTP_EMAIL")

    if not smtp_host or not smtp_user:
        logging.error("Missing SMTP_HOST or SMTP_EMAIL in environment variables. Check your .env file.")
        return

    logging.info(f"Attempting to send test email from {smtp_user} via {smtp_host}:{os.getenv('SMTP_PORT')} to {TEST_RECIPIENT_EMAIL}")
    
    try:
        _send_notification_email(TEST_RECIPIENT_EMAIL, mock_event_data)
        logging.info("Test execution complete. Check your inbox (and spam folder) for the test email.")
        logging.info("If successful, proceed to test the full `process_event_for_alerts` function.")
    except Exception as e:
        logging.critical(f"Email sending failed at the trigger level: {e}")

if __name__ == "__main__":
    manual_email_test()