import pytest
import asyncio
from unittest.mock import MagicMock, patch, ANY
from datetime import datetime, timedelta, timezone
from bson import ObjectId

# Import the functions to be tested
from app.routes.alert_routes import subscribe_user, unsubscribe, SubscriberModel
from core.jobs import alert_generator
from core.jobs.alert_generator import process_event_for_alerts

# ==========================================
# TEST FIXTURES
# ==========================================

@pytest.fixture
def mock_db_connection():
    """Mocks the shared database connection object."""
    mock_db = MagicMock()
    # Mock collections
    mock_db.subscriber_collection = MagicMock()
    mock_db.disaster_events_collection = MagicMock()
    return mock_db

@pytest.fixture
def sample_subscriber_data():
    return SubscriberModel(
        email="user@example.com", 
        locations=["johor", "selangor"]
    )

@pytest.fixture
def sample_event_doc():
    """Returns a fresh event document suitable for alerting."""
    return {
        "_id": ObjectId(),
        "event_id": "event_123",
        "classification_type": "flood",
        "location_state": "johor",
        "location_district": "Johor Bahru",
        "start_time": datetime.now(timezone.utc),
        "last_alert_sent": None, # Never alerted
        "alert_cooldown_mins": 60
    }

# ==========================================
# TEST CASE: IT-07-001 & IT-07-004
# ==========================================

@pytest.mark.asyncio
async def test_it_07_001_and_004_subscription_upsert(mock_db_connection, sample_subscriber_data):
    """
    Test Case ID: IT-07-001 & IT-07-004
    Test Scenario: Subscription Workflow & Upsert Logic
    Coverage: Backend Route <-> Database Storage (Upsert)
    """
    # Patch the db_connection used in alert_routes
    with patch("app.routes.alert_routes.db_connection", mock_db_connection):
        
        # 1. Execute Subscribe Action
        response = await subscribe_user(sample_subscriber_data)
        
        # 2. Verify Response
        assert response["message"] == "Subscription successful"
        assert response["data"] == sample_subscriber_data

        # 3. Verify Database Interaction (Upsert Logic)
        # Expected: update_one called with upsert=True
        mock_db_connection.subscriber_collection.update_one.assert_called_once()
        
        call_args = mock_db_connection.subscriber_collection.update_one.call_args
        filter_arg = call_args[0][0]
        update_arg = call_args[0][1]
        kwargs = call_args[1]

        # Check Filter (Email)
        assert filter_arg == {"email": "user@example.com"}
        
        # Check Upsert Flag (IT-07-004 requirement)
        assert kwargs.get("upsert") is True
        
        # Check Update Payload
        assert "$set" in update_arg
        assert update_arg["$set"]["locations"] == ["johor", "selangor"]
        assert "updatedAt" in update_arg["$set"]
        
        # Check Insert-Only Fields
        assert "$setOnInsert" in update_arg
        assert "createdAt" in update_arg["$setOnInsert"]

# ==========================================
# TEST CASE: IT-07-002
# ==========================================

def test_it_07_002_alert_triggering_success(mock_db_connection, sample_event_doc):
    """
    Test Case ID: IT-07-002 (Part 1)
    Test Scenario: Alert Triggering (Fresh Event)
    Coverage: Data Detection <-> Match Logic
    """
    event_id = "event_123"
    
    # Setup Mocks
    mock_db_connection.disaster_events_collection.find_one.return_value = sample_event_doc
    
    # Mock finding 1 subscriber for "johor"
    mock_db_connection.subscriber_collection.find.return_value = [
        {"email": "subscriber@test.com", "locations": ["johor"]}
    ]

    # Patch DB and SMTP
    with patch("core.jobs.alert_generator.db_connection", mock_db_connection), \
         patch("smtplib.SMTP") as mock_smtp_cls:
        
        # Setup SMTP Mock Instance
        mock_smtp_instance = MagicMock()
        mock_smtp_cls.return_value = mock_smtp_instance

        # 1. Execute Alert Process
        emails_sent = process_event_for_alerts(event_id)

        # 2. Verify Email Sending
        assert emails_sent == 1
        mock_smtp_instance.sendmail.assert_called_once()
        
        # Verify the recipient in the sendmail call
        args = mock_smtp_instance.sendmail.call_args[0]
        assert args[1] == "subscriber@test.com" # Recipient

        # 3. Verify Cooldown Reset (Database Update)
        mock_db_connection.disaster_events_collection.update_one.assert_called_once()
        update_call = mock_db_connection.disaster_events_collection.update_one.call_args
        
        # Ensure we updated the specific event
        assert update_call[0][0] == {"_id": event_id}
        # Ensure we set 'last_alert_sent'
        assert "$set" in update_call[0][1]
        assert "last_alert_sent" in update_call[0][1]["$set"]


def test_it_07_002_cooldown_enforcement(mock_db_connection, sample_event_doc):
    """
    Test Case ID: IT-07-002 (Part 2)
    Test Scenario: Cooldown Enforcement (Supress Duplicate)
    Coverage: Cooldown/Deduplication Logic
    """
    event_id = "event_123"
    
    # MODIFY SCENARIO: Event was alerted 5 minutes ago
    sample_event_doc["last_alert_sent"] = datetime.now(timezone.utc) - timedelta(minutes=5)
    sample_event_doc["alert_cooldown_mins"] = 60 # Cooldown is 60 mins
    
    # Setup DB Mock
    mock_db_connection.disaster_events_collection.find_one.return_value = sample_event_doc
    
    # Even if subscribers exist...
    mock_db_connection.subscriber_collection.find.return_value = [
        {"email": "subscriber@test.com", "locations": ["johor"]}
    ]

    with patch("core.jobs.alert_generator.db_connection", mock_db_connection), \
         patch("smtplib.SMTP") as mock_smtp_cls:
        
        mock_smtp_instance = MagicMock()
        mock_smtp_cls.return_value = mock_smtp_instance

        # 1. Execute Alert Process
        emails_sent = process_event_for_alerts(event_id)

        # 2. Verify NO Email Sent
        assert emails_sent == 0
        mock_smtp_instance.sendmail.assert_not_called()

        # 3. Verify NO DB Update (Cooldown not reset)
        mock_db_connection.disaster_events_collection.update_one.assert_not_called()

# ==========================================
# TEST CASE: IT-07-003
# ==========================================

@pytest.mark.asyncio
async def test_it_07_003_unsubscribe_workflow(mock_db_connection):
    """
    Test Case ID: IT-07-003
    Test Scenario: Unsubscribe Workflow and Database Cleanup
    Coverage: Backend Route <-> Database Deletion
    """
    email_to_remove = "test@example.com"
    
    # Setup Mock Result for delete_one
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 1 # Simulate successful deletion
    mock_db_connection.subscriber_collection.delete_one.return_value = mock_delete_result

    with patch("app.routes.alert_routes.db_connection", mock_db_connection):
        
        # 1. Execute Unsubscribe
        response = await unsubscribe(email=email_to_remove)
        
        # 2. Verify Database Deletion
        mock_db_connection.subscriber_collection.delete_one.assert_called_once_with(
            {"email": email_to_remove}
        )
        
        # 3. Verify HTML Response (Success Page)
        # The function returns a raw HTML string. We check for success keywords.
        assert "Unsubscribed Successfully" in response
        assert "You will no longer receive disaster alerts" in response

@pytest.mark.asyncio
async def test_it_07_003_unsubscribe_not_found(mock_db_connection):
    """
    Test Case ID: IT-07-003 (Edge Case)
    Test Scenario: Unsubscribe Email Not Found
    """
    email_to_remove = "missing@example.com"
    
    # Simulate email not found (deleted_count = 0)
    mock_delete_result = MagicMock()
    mock_delete_result.deleted_count = 0
    mock_db_connection.subscriber_collection.delete_one.return_value = mock_delete_result

    with patch("app.routes.alert_routes.db_connection", mock_db_connection):
        
        response = await unsubscribe(email=email_to_remove)
        
        # Check for specific "Not Found" HTML content
        assert "Email Not Found" in response