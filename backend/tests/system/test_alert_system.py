import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
from bson import ObjectId
from core.jobs import alert_generator

# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture
def mock_db_system():
    """Mocks the database for the Alert System."""
    db = MagicMock()
    db.disaster_events_collection = MagicMock()
    db.subscriber_collection = MagicMock()
    return db

@pytest.fixture
def new_flood_event():
    """
    Test Data: A new Flood event in Johor (Urgent).
    Corresponds to Step 1: Inject classified disaster record.
    """
    return {
        "_id": ObjectId(),
        "event_id": "evt_flood_johor_001",
        "classification_type": "flood",
        "location_state": "johor",
        "location_district": "Segamat",
        "severity": "Urgent", # As per test case pre-condition
        "start_time": datetime.now(timezone.utc),
        "last_alert_sent": None, # Never alerted
        "alert_cooldown_mins": 60
    }

@pytest.fixture
def subscriber_tester():
    """
    Test Data: User tester@example.com subscribed to Johor.
    Corresponds to Pre-condition 1.
    """
    return {
        "email": "tester@example.com",
        "locations": ["johor"], # Matches event location
        "preferences": {"severity": "Urgent"} # Optional matching logic
    }

# ==========================================
# TEST CASE: ST-07-001
# ==========================================

def test_st_07_001_end_to_end_alert_flow(mock_db_system, new_flood_event, subscriber_tester):
    """
    Test Case ID: ST-07-001
    Scenario: End-to-End Alert Flow (Successful Match)
    Pre-conditions: User subscribed to 'Johor', 'Urgent'.
    Test Steps:
      1. Inject Event (Simulated by mock_db return value).
      2. Worker Scans (Simulated by calling process_event_for_alerts).
      3. Verify Match (Check if subscriber was fetched and email sent).
    """
    
    # ----------------------------------------------------
    # 1. SETUP MOCKS (Simulate Database State)
    # ----------------------------------------------------
    
    # Step 1 (Implicit): The event exists in the DB
    mock_db_system.disaster_events_collection.find_one.return_value = new_flood_event
    
    # Step 3 (Implicit): The system searches for subscribers matching 'johor'
    # We return our tester user
    mock_db_system.subscriber_collection.find.return_value = [subscriber_tester]

    # Mock SMTP to verify the "Email Received" step
    with patch("core.jobs.alert_generator.db_connection", mock_db_system), \
         patch("smtplib.SMTP") as mock_smtp_cls:
        
        # Setup SMTP Mock
        mock_smtp_instance = MagicMock()
        mock_smtp_cls.return_value = mock_smtp_instance

        # ----------------------------------------------------
        # 2. TRIGGER WORKER (Step 2)
        # ----------------------------------------------------
        # In a real system, Kafka triggers this. Here, we call the logic directly.
        emails_sent_count = alert_generator.process_event_for_alerts("evt_flood_johor_001")

        # ----------------------------------------------------
        # 3. VERIFY RESULTS (Actual vs Expected)
        # ----------------------------------------------------
        
        # Verification 1: System identified the match
        # It should have found the subscriber based on location
        mock_db_system.subscriber_collection.find.assert_called()
        call_args = mock_db_system.subscriber_collection.find.call_args
        assert call_args[0][0]["locations"] == "johor"

        # Verification 2: Email sent to tester@example.com (Step 4)
        assert emails_sent_count == 1
        mock_smtp_instance.sendmail.assert_called_once()
        
        # Check recipients in the sendmail call
        # sendmail(from, to, msg)
        smtp_args = mock_smtp_instance.sendmail.call_args[0]
        recipient = smtp_args[1]
        email_content = str(smtp_args[2])
        
        assert recipient == "tester@example.com"
        assert "Flood" in email_content
        assert "Johor" in email_content
        assert "Urgent" in email_content or "ALERT" in email_content

        # Verification 3: DB Updated (Last Alert Sent)
        # The system must update the event to prevent duplicate alerts
        mock_db_system.disaster_events_collection.update_one.assert_called_once()
        assert "$set" in mock_db_system.disaster_events_collection.update_one.call_args[0][1]

        # Capture the email content from the mock
        smtp_args = mock_smtp_instance.sendmail.call_args[0]
        email_content = str(smtp_args[2])