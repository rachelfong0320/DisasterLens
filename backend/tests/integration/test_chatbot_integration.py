import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from app.main import app 
from app.chatbot import chatbot_service

# Initialize the TestClient
client = TestClient(app)

# ==========================================
# MOCK DATA
# ==========================================

MOCK_ES_RESPONSE = {
    "hits": {
        "hits": [
            {
                "_source": {
                    "event_id": "evt_storm_1",
                    "classification_type": "storm",
                    "location_state": "Pahang",
                    "start_time": "2023-10-27T14:30:00",
                    "description": "Heavy storm detected in Kuantan."
                }
            }
        ]
    }
}

MOCK_OPENAI_TOOL_CALL = MagicMock()
MOCK_OPENAI_TOOL_CALL.message.tool_calls = [
    MagicMock(
        function=MagicMock(
            arguments='{"location": "Pahang", "disaster_type": "storm"}',
            name="get_historical_disasters"
        ),
        id="call_123"
    )
]
MOCK_OPENAI_TOOL_CALL.message.content = None

MOCK_OPENAI_FINAL_RESPONSE = MagicMock()
MOCK_OPENAI_FINAL_RESPONSE.message.tool_calls = None
MOCK_OPENAI_FINAL_RESPONSE.message.content = "There is a storm reported in Pahang on Oct 27th."

# ==========================================
# TEST CASE: IT-08-001 & IT-08-002
# ==========================================

def test_it_08_001_and_002_chatbot_success_flow():
    """
    Test Case ID: IT-08-001 & IT-08-002
    Scenario: End-to-End Chatbot Response & Data Retrieval
    Coverage: API Route -> Logic -> LLM (Mock) -> ES (Mock)
    """
    
    # 1. Mock Elasticsearch (The Database)
    with patch("app.chatbot.chatbot_service.es.search") as mock_es_search:
        mock_es_search.return_value = MOCK_ES_RESPONSE
        
        # 2. Mock OpenAI (The LLM)
        # We need to simulate the sequence: 
        #   Call 1 (Decides to use Tool) -> Call 2 (Summarizes Data)
        mock_openai_client = MagicMock()
        mock_openai_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MOCK_OPENAI_TOOL_CALL]),    # First call returns tool request
            MagicMock(choices=[MOCK_OPENAI_FINAL_RESPONSE]) # Second call returns final text
        ]

        with patch("openai.OpenAI", return_value=mock_openai_client):
            
            # 3. Simulate Frontend Request
            payload = {"message": "Is there a storm in Pahang?"}
            response = client.post("/api/v1/chat", json=payload)

            # 4. Verify API Response (IT-08-001)
            assert response.status_code == 200
            json_response = response.json()
            assert json_response["reply"] == "There is a storm reported in Pahang on Oct 27th."

            # 5. Verify Data Retrieval (IT-08-002)
            # Ensure the tool arguments were parsed correctly
            # Ensure ES was searched with the correct index
            mock_es_search.assert_called_once()
            call_args = mock_es_search.call_args
            assert call_args[1]['index'] == "disaster_events"
            
            # Check if the ES query body actually contained the filters we expect
            search_body = call_args[1]['body']
            must_clauses = search_body['query']['bool']['must']
            
            # Verify "Pahang" was in the search query
            location_match = any(
                c.get('multi_match', {}).get('query') == 'Pahang' 
                for c in must_clauses
            )
            assert location_match, "Elasticsearch query should filter by 'Pahang'"

# ==========================================
# TEST CASE: IT-08-003
# ==========================================

def test_it_08_003_external_api_failure():
    """
    Test Case ID: IT-08-003
    Scenario: Resilience to External API Downtime
    Coverage: External Service Integration <-> Error Handling
    """
    
    # Simulate OpenAI crashing (TimeOut or ConnectionError)
    with patch("openai.OpenAI", side_effect=Exception("OpenAI Connection Timeout")):
        
        payload = {"message": "Hello?"}
        response = client.post("/api/v1/chat", json=payload)
        
        # The backend code in chatbot_route.py catches Exception and raises 500
        assert response.status_code == 500
        assert response.json() == {"detail": "Failed to generate chatbot response"}

# ==========================================
# EXTRA: DEBUG ENDPOINT TEST
# ==========================================

def test_chatbot_debug_endpoint_structure():
    """
    Verifies the /chatbot_debug endpoint returns both reply and raw data.
    """
    with patch("app.chatbot.chatbot_service.es.search") as mock_es_search, \
         patch("openai.OpenAI") as MockOpenAI:
        
        # Setup Mocks
        mock_es_search.return_value = MOCK_ES_RESPONSE
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = [
            MagicMock(choices=[MOCK_OPENAI_TOOL_CALL]), 
            MagicMock(choices=[MOCK_OPENAI_FINAL_RESPONSE])
        ]
        MockOpenAI.return_value = mock_client

        # Call Endpoint
        payload = {"message": "Debug storm Pahang"}
        response = client.post("/api/v1/chatbot_debug", json=payload)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "reply" in data
        assert "debug_data" in data
        assert len(data["debug_data"]) == 1
        assert data["debug_data"][0]["event_id"] == "evt_storm_1"