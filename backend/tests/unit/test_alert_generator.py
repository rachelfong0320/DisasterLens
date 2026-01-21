import pytest
import sys
import os
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, ANY

# --- SETUP: MOCK DATABASE & MODULES BEFORE IMPORT ---
# 1. Mock the database connection object used in both files
mock_db_conn = MagicMock()
mock_db_conn.disaster_events_collection = MagicMock()
mock_db_conn.subscriber_collection = MagicMock()

# 2. Mock the 'app.database' module so imports work
mock_app_db = MagicMock()
mock_app_db.db_connection = mock_db_conn
sys.modules["app.database"] = mock_app_db

# 3. Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 4. Import the code under test
from core.jobs.alert_generator import process_event_for_alerts, _send_notification_email
from app.routes.alert_routes import router
from fastapi import FastAPI
from fastapi.testclient import TestClient

# 5. Setup FastAPI Test Client
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# --- FIXTURE: RESET MOCKS BEFORE EVERY TEST ---
@pytest.fixture(autouse=True)
def reset_mocks():
    """Automatically resets mock history before each test function."""
    mock_db_conn.reset_mock()
    mock_db_conn.disaster_events_collection.reset_mock()
    mock_db_conn.subscriber_collection.reset_mock()

# --- UT-07-001: Alert Generation for Subscribed Locations ---
@patch("core.jobs.alert_generator.smtplib") # Mock email server
def test_ut_07_001_alert_generation(mock_smtplib):
    """
    Verify alert generation logic:
    1. Alert sent if user is subscribed to location.
    2. Alert NOT sent if user is subscribed to different location.
    """
    # Setup: Mock Event (Johor)
    event_id = "event_johor_01"
    mock_event = {
        "event_id": event_id,
        "classification_type": "Flood",
        "location_state": "Johor",
        "location_district": "Johor Bahru",
        "start_time": datetime.now(timezone.utc),
        "last_alert_sent": None
    }
    mock_db_conn.disaster_events_collection.find_one.return_value = mock_event

    # Scenario A: User subscribed to Johor
    # Mock find() to return a list of subscribers
    mock_subscriber_johor = {"email": "johor_user@test.com", "locations": ["Johor"]}
    mock_db_conn.subscriber_collection.find.return_value = [mock_subscriber_johor]

    # Force Env vars for email to be present
    with patch.dict(os.environ, {"SMTP_HOST": "smtp.test.com", "SMTP_EMAIL": "me", "SMTP_PASSWORD": "123"}):
        sent_count = process_event_for_alerts(event_id)

    assert sent_count == 1
    # Verify DB query looked for subscribers in "Johor"
    mock_db_conn.subscriber_collection.find.assert_called_with({"locations": "Johor"})

    # Scenario B: User subscribed to Pahang (Mock DB returns empty for "Johor" query)
    mock_db_conn.subscriber_collection.find.return_value = []
    
    with patch.dict(os.environ, {"SMTP_HOST": "smtp.test.com", "SMTP_EMAIL": "me", "SMTP_PASSWORD": "123"}):
        sent_count_empty = process_event_for_alerts(event_id)
        
    assert sent_count_empty == 0


# --- UT-07-002: Duplicate Alert Prevention (Cooldown) ---
@patch("core.jobs.alert_generator.smtplib")
def test_ut_07_002_cooldown_logic(mock_smtplib):
    """
    Verify that if an alert was sent recently (within cooldown), 
    no new alert is generated.
    """
    event_id = "event_cooldown_01"
    
    # Setup: Event sent 10 minutes ago (Cooldown is 60 mins default)
    ten_mins_ago = datetime.now(timezone.utc) - timedelta(minutes=10)
    
    mock_event = {
        "event_id": event_id,
        "classification_type": "Flood",
        "location_state": "Johor",
        "start_time": datetime.now(timezone.utc),
        "last_alert_sent": ten_mins_ago
    }
    
    mock_db_conn.disaster_events_collection.find_one.return_value = mock_event

    # Action
    sent_count = process_event_for_alerts(event_id)

    # Assertion
    assert sent_count == 0
    # Ensure we didn't even query subscribers (optimization check)
    mock_db_conn.subscriber_collection.find.assert_not_called()


# --- UT-07-003: Verify Email Content ---
@patch("core.jobs.alert_generator.smtplib")
def test_ut_07_003_email_content(mock_smtplib):
    """
    Verify the constructed email contains the necessary details.
    """
    mock_server = MagicMock()
    mock_smtplib.SMTP.return_value = mock_server
    
    subscriber_email = "test@example.com"
    event_data = {
        "event_id": "EVT_123",
        "classification_type": "Fire",
        "location_district": "Pahang",
        "location_state": "Pahang",
        "start_time": datetime(2026, 1, 10, 20, 0, 0, tzinfo=timezone.utc)
    }

    # Force Env vars
    with patch.dict(os.environ, {"SMTP_HOST": "smtp.test.com", "SMTP_EMAIL": "sender@test.com", "SMTP_PASSWORD": "123"}):
        _send_notification_email(subscriber_email, event_data)

    # Verify sendmail was called
    mock_server.sendmail.assert_called_once()
    
    # Inspect arguments: (from_addr, to_addrs, msg_string)
    args, _ = mock_server.sendmail.call_args
    msg_content = args[2] # The email body string
    
    # Assertions
    assert "Fire" in msg_content
    assert "Pahang" in msg_content
    assert "EVT_123" in msg_content


# --- UT-07-004: Performance Latency Check ---
@patch("core.jobs.alert_generator.smtplib")
def test_ut_07_004_latency(mock_smtplib):
    """
    Verify that processing a single event for alerting takes less than 3 seconds.
    """
    # Setup
    mock_db_conn.disaster_events_collection.find_one.return_value = {
        "event_id": "perf_test",
        "location_state": "Perak",
        "start_time": datetime.now(timezone.utc),
        "last_alert_sent": None
    }
    mock_db_conn.subscriber_collection.find.return_value = [{"email": "u1@test.com", "locations": ["Perak"]}]

    # Action (with Timer)
    start_time = time.time()
    with patch.dict(os.environ, {"SMTP_HOST": "smtp.test.com", "SMTP_EMAIL": "me", "SMTP_PASSWORD": "123"}):
        process_event_for_alerts("perf_test")
    end_time = time.time()
    
    duration = end_time - start_time
    
    # Assertion
    assert duration < 3.0, f"Alert processing took too long: {duration} seconds"


# --- UT-07-005: API Subscription Selection ---
def test_ut_07_005_api_subscription_success():
    """
    Verify user can subscribe via API with valid data.
    """
    payload = {
        "email": "user@test.com",
        "locations": ["Selangor"]
    }
    
    # Action
    response = client.post("/subscribe", json=payload)
    
    # Assertion
    assert response.status_code == 200
    assert response.json()["message"] == "Subscription successful"
    
    # Verify DB update was called
    mock_db_conn.subscriber_collection.update_one.assert_called_with(
        {"email": "user@test.com"},
        ANY,
        upsert=True
    )


# --- UT-07-006: API Empty Location Validation ---
def test_ut_07_006_api_empty_location():
    """
    Verify backend validation rejects empty location lists.
    """
    payload = {
        "email": "user@test.com",
        "locations": [] # Empty
    }
    
    # Action
    response = client.post("/subscribe", json=payload)
    
    # Assertion
    assert response.status_code == 400
    assert "At least one location is required" in response.json()["detail"]


# --- UT-07-007: API Email Validation ---
@pytest.mark.parametrize("invalid_email", ["user@com", "usercom", ""])
def test_ut_07_007_api_email_validation(invalid_email):
    """
    Verify API rejects invalid email formats (handled by Pydantic).
    """
    payload = {
        "email": invalid_email,
        "locations": ["Selangor"]
    }
    
    # Action
    response = client.post("/subscribe", json=payload)
    
    # Assertion
    # Pydantic returns 422 Unprocessable Entity for schema violations
    assert response.status_code == 422