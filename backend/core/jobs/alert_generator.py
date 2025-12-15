import logging
import os
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from bson.objectid import ObjectId
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Ensure environment variables are loaded 
load_dotenv() 

# Import the database connection established in app/database.py
from app.database import db_connection 

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- CONFIGURATION for Alerting & SMTP ---
DEFAULT_COOLDOWN_MINUTES = 60 

# Load SMTP configuration directly from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
# We use the provided SMTP_EMAIL for both authentication and the sender address
SMTP_USERNAME = os.getenv("SMTP_EMAIL") 
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_ADDRESS = SMTP_USERNAME # The "From" address is the authenticated user
# -------------------------------------------


def _send_notification_email(subscriber_email: str, event_data: Dict[str, Any]):
    """
    Sends an email notification using SMTP with TLS encryption.
    """
    # Check if critical variables are loaded
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, SENDER_ADDRESS]):
        logger.error("SMTP configuration is incomplete. Cannot send email.")
        return

    event_type = event_data.get('classification_type', 'Disaster')
    location = event_data.get('location_district', 'Unknown Location')
    event_id = event_data.get('event_id', 'N/A')
    
    post_link = f"LINK_TO_POST_ID/{event_data.get('related_post_ids', ['N/A'])[0]}"

    # 1. Build the email content
    subject = f"ALERT: {event_type.upper()} Detected in {location}"
    html_content = f"""\
    <html>
      <body>
        <h2>Disaster Alert: New {event_type.title()} Event</h2>
        <p>A significant {event_type} event has been detected in <strong>{location}</strong>.</p>
        <ul>
          <li><strong>Event ID:</strong> {event_id}</li>
          <li><strong>First Reported:</strong> {event_data.get('start_time').strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
          <li><strong>Location Coordinates:</strong> {event_data.get('geometry', {}).get('coordinates')}</li>
        </ul>
        <p>For more details, please check the system dashboard.</p>
        <p><a href="{post_link}">View Original Post (Placeholder)</a></p>
        <p style="font-size: 0.8em; color: #777;">
            You are receiving this alert because you subscribed to notifications for {location}. 
            To change your preferences, please visit your subscription page.
        </p>
      </body>
    </html>
    """

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SENDER_ADDRESS 
    message["To"] = subscriber_email
    
    message.attach(MIMEText(html_content, "html"))

    # 2. Send email via SMTP
    context = ssl.create_default_context()
    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # SENDER_ADDRESS is used as the envelope sender and 'From' header
        server.sendmail(SENDER_ADDRESS, subscriber_email, message.as_string())
        logger.info(f"Successfully sent alert for {event_id} to {subscriber_email}")
        
    except smtplib.SMTPAuthenticationError:
        # Critical error message for the user if Gmail rejects the password
        logger.error(f"SMTP Authentication Error: Gmail requires an App Password. Please verify SMTP_PASSWORD environment variable for {SMTP_USERNAME}.")
    except Exception as e:
        logger.error(f"Failed to send email via SMTP: {e}")
    finally:
        if 'server' in locals() and server:
            server.quit()


def process_event_for_alerts(event_id: ObjectId) -> int:
    """
    Checks the event's alert cooldown and triggers emails to matching subscribers.
    """
    # TODO: Change DB once YONGJING sets up the proper collections
    events_collection = db_connection.disaster_events_collection #
    subscribers_collection = db_connection.subscriber_collection #

    # 1. Fetch the latest event data
    event = events_collection.find_one({"_id": event_id}) #
    
    if not event:
        logger.error(f"Event ID {event_id} not found for alerting.")
        return 0

    # TODO: Change 'location_district' to the appropriate field once DB is finalized
    event_location = event.get("location_district")
    
    if not event_location:
        logger.warning(f"Event {event['event_id']} has no location, skipping alert generation.")
        return 0

    # 2. Spam Prevention Check (CoOLDOWN LOGIC)
    last_alert_sent: datetime = event.get("last_alert_sent", datetime.min.replace(tzinfo=timezone.utc)) #
    cooldown_mins: int = event.get("alert_cooldown_mins", DEFAULT_COOLDOWN_MINUTES)
    cooldown_expiry = last_alert_sent + timedelta(minutes=cooldown_mins)
    current_time = datetime.now(timezone.utc)

    if current_time < cooldown_expiry:
        logger.info(f"Event {event['event_id']} on cooldown. Skipping alert.")
        return 0

    # 3. Find matching subscribers
    subscribers = subscribers_collection.find({
        "locations": event_location
    })

    emails_sent = 0
    
    # 4. Send notifications
    for subscriber in subscribers:
        subscriber_email = subscriber.get("email") # Get the recipient's email from the subscriber document
        if subscriber_email:
            _send_notification_email(subscriber_email, event) # Call send function
            emails_sent += 1

    # 5. If alerts were sent, update the disaster event to reset the cooldown timer
    if emails_sent > 0:
        events_collection.update_one(
            {"_id": event_id},
            {"$set": {"last_alert_sent": current_time}}
        )
        logger.info(f"Cooldown reset for event {event['event_id']}.")
        
    return emails_sent