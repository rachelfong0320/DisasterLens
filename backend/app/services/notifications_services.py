import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
import os
import time
from collections import Counter
from app.database import db_connection

load_dotenv()
# Email Config (Replace with env vars in production)
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def queue_incidents_for_subscribers(classified_incidents):
    """
    1. Takes a list of newly classified incidents.
    2. Finds subscribers interested in those locations.
    3. Pushes 'pending' records to the notification_queue.
    """
    queue_items = []
    
    for incident in classified_incidents:
        # Skip if invalid or irrelevant
        if not incident.get('incident_type') or incident.get('incident_type') == "None":
            continue

        # Get location from the incident data (assuming it's passed in or fetched)
        # Note: You might need to fetch the full post to get the "location" string if it's not in the incident object
        # specific_location = incident.get('location', 'Unknown Location') 
        
        # For this example, we query the main post to get the location string
        full_post = db_connection.posts_collection.find_one({"postId": incident['post_id']})
        if not full_post: 
            continue
            
        location_str = full_post.get('location') or full_post.get('city')
        if not location_str:
            continue

        # Find subscribers whose subscribed location is mentioned in the incident location
        # Uses regex for case-insensitive matching
        # Logic: If user subscribes to "Selangor", and tweet is from "Sungai Buloh, Selangor", notify them.
        cursor = db_connection.subscriber_collection.find({})
        
        for sub in cursor:
            user_locations = sub.get('locations', [])
            matched_location = None
            
            # Check if any of user's preferred locations are in the tweet's location
            for user_loc in user_locations:
                if user_loc.lower() in location_str.lower():
                    matched_location = user_loc
                    break
            
            if matched_location:
                queue_items.append({
                    "user_email": sub['email'],
                    "target_location": matched_location, # The general area (e.g. Los Angeles)
                    "incident_type": incident['incident_type'],
                    "incident_id": incident['post_id'],
                    "occurred_at": time.time(),
                    "status": "pending"
                })

    if queue_items:
        db_connection.notification_queue.insert_many(queue_items)
        print(f"Queued {len(queue_items)} notifications.")

def process_notification_queue():
    """
    1. Finds all 'pending' notifications.
    2. Groups them by User -> Location.
    3. Sends a summary email.
    4. Marks them as 'sent'.
    """
    # 1. Get all pending items
    pending = list(db_connection.notification_queue.find({"status": "pending"}))
    if not pending:
        return 0

    # 2. Group by User
    user_batches = {}
    for item in pending:
        email = item['user_email']
        if email not in user_batches:
            user_batches[email] = []
        user_batches[email].append(item)

    emails_sent = 0

    # 3. Process per User
    for email, items in user_batches.items():
        # Group by Location within the user's batch
        location_groups = {}
        for item in items:
            loc = item['target_location']
            if loc not in location_groups:
                location_groups[loc] = []
            location_groups[loc].append(item['incident_type'])

        # Generate Email Body
        msg_body = "DisasterLens Alert Summary:\n\n"
        
        for loc, types in location_groups.items():
            count = len(types)
            breakdown = Counter(types) # e.g. {'flood': 3, 'fire': 1}
            
            msg_body += f"🚨 {count} new alerts detected in {loc}:\n"
            for d_type, d_count in breakdown.items():
                msg_body += f"   - {d_count} {d_type}\n"
            msg_body += "\n"
            
        msg_body += "View full dashboard: http://localhost:3000/dashboard"

        # Send Email
        try:
            send_email(email, "New Disaster Alerts Summary", msg_body)
            
            # 4. Mark items as sent
            ids_to_update = [i['_id'] for i in items]
            db_connection.notification_queue.update_many(
                {"_id": {"$in": ids_to_update}},
                {"$set": {"status": "sent", "sent_at": time.time()}}
            )
            emails_sent += 1
        except Exception as e:
            print(f"Failed to send email to {email}: {e}")

    return emails_sent

def send_email(to, subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_EMAIL
    msg['To'] = to

    # Use generic SMTP or specific provider (Gmail example)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
        smtp.send_message(msg)