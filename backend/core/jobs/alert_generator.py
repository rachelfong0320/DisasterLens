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
SMTP_USERNAME = os.getenv("SMTP_EMAIL") 
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SENDER_ADDRESS = SMTP_USERNAME


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

    post_link = f"http://localhost:3000"  # Link to the system dashboard or event details
    unsubscribe_url = f"http://localhost:8000/api/v1/unsubscribe?email={subscriber_email}"

    # 1. Build the email content
    subject = f"ALERT: {event_type.upper()} Detected in {location}"
    html_content = f"""\
    <html>
  <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; margin: 0; padding: 0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
      <!-- Header -->
      <tr>
        <td style="background: linear-gradient(135deg, #1c50a7 70%, #ffffff 100%); color: #ffffff; padding: 20px; text-align: center;">
          <h1 style="margin: 0; font-size: 24px;">DisasterLens</h1>
          <p style="margin: 5px 0 0; font-size: 16px;">New {event_type.title()} Event Detected</p>
        </td>
      </tr>

      <!-- Body -->
      <tr>
        <td style="padding: 20px; color: #333333; line-height: 1.5;">
          <p>A significant <strong>{event_type}</strong> event has been detected in <strong>{location}</strong>.</p>

          <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 10px; border-collapse: collapse;">
            <tr>
              <td style="padding: 8px; border: 1px solid #dddddd;"><strong>Event ID:</strong></td>
              <td style="padding: 8px; border: 1px solid #dddddd;">{event_id}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border: 1px solid #dddddd;"><strong>First Reported:</strong></td>
              <td style="padding: 8px; border: 1px solid #dddddd;">{event_data.get('start_time').strftime('%Y-%m-%d %H:%M:%S UTC')}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border: 1px solid #dddddd;"><strong>Location State:</strong></td>
              <td style="padding: 8px; border: 1px solid #dddddd;">{event_data.get('location_state')}</td>
            </tr>
          </table>

          <p style="margin-top: 15px;">For more details, please check the system dashboard:</p>
          <p style="text-align: center;">
            <a href="{post_link}" style="display: inline-block; background-color:#1c50a7; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 4px; font-weight: bold;">View Dashboard</a>
          </p>

          <p style="font-size: 12px; color: #777777; margin-top: 20px;">
            You are receiving this alert because you subscribed to notifications for {location}.  
            To change your preferences, please visit your subscription page.
          </p>

          <p style="font-size: 12px; color: #777777;">
            If you wish to stop receiving these alerts, <a href="{unsubscribe_url}" style="color: #ff4d4f; text-decoration: none;">unsubscribe here</a>.
          </p>
        </td>
      </tr>

      <!-- Footer -->
      <tr>
        <td style="background-color: #f0f0f0; text-align: center; padding: 15px; font-size: 12px; color: #999999;">
          &copy; 2025 DisasterLens. All rights reserved.
        </td>
      </tr>
    </table>
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


def process_event_for_alerts(event_id: str) -> int:
    """
    Checks the event's alert cooldown and triggers emails to matching subscribers.
    """
    events_collection = db_connection.disaster_events_collection #
    subscribers_collection = db_connection.subscriber_collection #

    # 1. Fetch the latest event data
    event = events_collection.find_one({"event_id": event_id})
    
    if not event:
        logger.error(f"Event ID {event_id} not found for alerting.")
        return 0

    event_location = event.get("location_state")
    logger.info(
    f"[ALERT DEBUG] Event ID={event.get('event_id')} | "
    f"location_state={event_location} | "
    f"type={type(event_location)}"
)
    
    if not event_location:
        logger.warning(f"Event {event['event_id']} has no location, skipping alert generation.")
        return 0

    # 2. Spam Prevention Check (CoOLDOWN LOGIC)
    raw_last_alert_sent = event.get("last_alert_sent")

    if raw_last_alert_sent is None:
        last_alert_sent = datetime.min.replace(tzinfo=timezone.utc)
    elif raw_last_alert_sent.tzinfo is None:
        # MongoDB naive datetime → assume UTC
        last_alert_sent = raw_last_alert_sent.replace(tzinfo=timezone.utc)
    else:
        last_alert_sent = raw_last_alert_sent

    cooldown_mins: int = event.get(
        "alert_cooldown_mins",
        DEFAULT_COOLDOWN_MINUTES
    )

    cooldown_expiry = last_alert_sent + timedelta(minutes=cooldown_mins)
    current_time = datetime.now(timezone.utc)
    if current_time < cooldown_expiry:
        logger.info(
            f"Event {event['event_id']} on cooldown until {cooldown_expiry}."
        )
        return 0
    
    # 3. Find matching subscribers
    subscribers = subscribers_collection.find({
        "locations": event_location
    })

    emails_sent = 0
    
    # 4. Send notifications
    for subscriber in subscribers:
        subscriber_email = subscriber.get("email") 
        logger.info(
        f"[ALERT DEBUG] Sending alert to subscriber email={subscriber.get('email')}"
    )
        if subscriber_email:
            _send_notification_email(subscriber_email, event)
            emails_sent += 1

    # 5. If alerts were sent, update the disaster event to reset the cooldown timer
    if emails_sent > 0:
        events_collection.update_one(
            {"_id": event_id},
            {"$set": {"last_alert_sent": current_time}}
        )
        logger.info(f"Cooldown reset for event {event['event_id']}.")
        
    return emails_sent