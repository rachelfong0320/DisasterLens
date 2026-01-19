import pytest
import sys
import os
import asyncio
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

# --- SETUP: PATHS ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# --- IMPORTS ---
from core.consumers import analytics_worker
from core.consumers import incident_worker
from core.jobs import alert_generator

# --- INTEGRATION TESTS ---

# IT-04-001: End-to-End Processing (Scraper -> Analytics -> DB)
@pytest.mark.asyncio
@patch.object(analytics_worker, 'analyze_sentiment_async') # Mock AI
@patch.object(analytics_worker, 'generate_main_topic_async') # Mock Topic Gen
async def test_it_04_001_end_to_end_processing(mock_topic_gen, mock_sentiment):
    """
    IT-04-001: Verify end-to-end processing of a real-time message.
    """
    # 1. Setup: Mock Data
    raw_message = {
        "postId": "RT_001",
        "postText": "Flash flood warning in Johor!",
        "timestamp": 1234567890
    }

    # 2. Setup: Mock AI Responses
    mock_sentiment.return_value = {
        "sentiment_label": "Urgent",
        "confidence_score": 0.95
    }
    mock_topic_gen.return_value = "Flood in Johor"
    
    # Mock Kafka Producer
    mock_producer = MagicMock()
    mock_producer.send_and_wait = AsyncMock()

    # 3. Action: Process the message
    await analytics_worker.process_analytics(raw_message, mock_producer)

    # 4. Verification
    mock_sentiment.assert_called_once()
    
    assert mock_producer.send_and_wait.called
    
    # FIX: Robust argument extraction
    call_args = mock_producer.send_and_wait.call_args
    # call_args can be (args, kwargs) or just args depending on python version/mock
    
    # Try to get arguments from positional args first
    if len(call_args[0]) >= 2:
        topic_sent = call_args[0][0]
        data_sent = call_args[0][1]['value'] # Assuming the second arg is the dict with 'value'
    else:
        # Fallback if passed as kwargs or different structure (e.g. topic="...", value=...)
        # Based on your log, it seems likely it's passed positionally but let's check kwargs too
        topic_sent = call_args.kwargs.get('topic') or call_args[0][0]
        full_payload = call_args.kwargs.get('value') or call_args[0][1]
        # Your worker logs show it sends a dict, check if it's wrapped in 'value' key or raw
        data_sent = full_payload.get('value') if isinstance(full_payload, dict) and 'value' in full_payload else full_payload

    # Verify Payload Content
    assert topic_sent == "processed_data"
    assert data_sent['postId'] == "RT_001"
    assert data_sent['analytics_status'] == "enriched"
    assert data_sent['sentiment']['sentiment_label'] == "Urgent"
    
    print("\n✅ IT-04-001 Passed: Real-time message processed and forwarded to next stage.")


# IT-04-002: End-to-End Alert Generation (Incident Worker -> DB -> Alert)
# Removed @pytest.mark.asyncio because this test function is synchronous (def test_...)
@patch.object(alert_generator, 'smtplib')
@patch.object(alert_generator, 'db_connection')
@patch.object(incident_worker, 'db_connection')
def test_it_04_002_end_to_end_alerting(mock_incident_db, mock_alert_db, mock_smtplib):
    """
    IT-04-002: Verify end-to-end alert generation from a real-time event.
    """
    # ----------------------------------------------------------------
    # PHASE 1: Incident Worker (Simulate detection)
    # ----------------------------------------------------------------
    event_id = "EVT_KL_01"
    mock_event_doc = {
        "event_id": event_id,
        "classification_type": "Flood",
        "location_state": "Kuala Lumpur",
        "start_time": datetime.now(timezone.utc),
        "last_alert_sent": None 
    }

    # ----------------------------------------------------------------
    # PHASE 2: Alert Generator (Simulate periodic job)
    # ----------------------------------------------------------------

    # 2. Setup Alert Generator Mocks
    mock_alert_db.disaster_events_collection.find_one.return_value = mock_event_doc
    
    mock_subscriber = {
        "email": "subscriber@test.com", 
        "locations": ["Kuala Lumpur"],
        "preferences": ["Flood"]
    }
    mock_alert_db.subscriber_collection.find.return_value = [mock_subscriber]

    # 3. Setup Email Server Mock
    mock_smtp_instance = MagicMock()
    mock_smtplib.SMTP.return_value = mock_smtp_instance

    # 4. Action: Run the alert logic
    with patch.dict(os.environ, {
        "SMTP_HOST": "smtp.test.com", 
        "SMTP_EMAIL": "alert@test.com", 
        "SMTP_PASSWORD": "123"
    }):
        alert_generator.process_event_for_alerts(event_id)

    # 5. Verification
    mock_smtplib.SMTP.assert_called()
    mock_smtp_instance.sendmail.assert_called()
    
    call_args = mock_smtp_instance.sendmail.call_args
    recipient = call_args[0][1] 
    message_body = str(call_args[0][2])
    
    assert recipient == "subscriber@test.com"
    assert "Kuala Lumpur" in message_body
    
    print("\n✅ IT-04-002 Passed: Disaster Event triggered correct Email Alert to subscriber.")