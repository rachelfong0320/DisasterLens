import pytest
import sys
import os
import json
from unittest.mock import MagicMock, patch, AsyncMock

# --- SETUP: MOCK MODULES BEFORE IMPORT ---
# 1. Mock Elasticsearch client instance used at module level
mock_es_client = MagicMock()
sys.modules["elasticsearch"] = MagicMock()
sys.modules["elasticsearch"].Elasticsearch.return_value = mock_es_client

# 2. Mock OpenAI
sys.modules["openai"] = MagicMock()

# 3. Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 4. Import code under test
from app.chatbot.chatbot_service import get_historical_disasters, chatbot_response, chatbot_response_with_data
from app.routes.chatbot_route import router
from fastapi import FastAPI
from fastapi.testclient import TestClient

# 5. Setup FastAPI Client
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# --- FIXTURE: RESET MOCKS BEFORE EVERY TEST ---
@pytest.fixture(autouse=True)
def reset_mocks():
    """Automatically resets mock history before each test function."""
    mock_es_client.reset_mock()

# --- UT-08-001: Verify Query Parsing (Location & Type) ---
@patch("app.chatbot.chatbot_service.openai.OpenAI")
def test_ut_08_001_query_parsing(mock_openai_class):
    """
    Verify the NLP engine extracts location and type correctly via Tool Calling.
    """
    # Setup: Mock OpenAI to return a 'tool_calls' response asking for function execution
    mock_client = mock_openai_class.return_value
    
    # Mock the first response (The tool call)
    tool_call_msg = MagicMock()
    tool_call_msg.tool_calls = [
        MagicMock(
            function=MagicMock(arguments=json.dumps({"location": "Johor", "disaster_type": "flood"}))
        )
    ]
    
    # Mock the second response (The final answer after tool execution)
    final_answer_msg = MagicMock()
    final_answer_msg.tool_calls = None
    final_answer_msg.content = "I found floods in Johor."

    # Chain the responses
    mock_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=tool_call_msg)]), # 1st call: AI decides to use tool
        MagicMock(choices=[MagicMock(message=final_answer_msg)]) # 2nd call: AI summarizes result
    ]

    # Mock ES to return some dummy data
    mock_es_client.search.return_value = {"hits": {"hits": []}}

    # Action
    import asyncio
    result = asyncio.run(chatbot_response("Tell me about floods in Johor"))

    # Assertion
    assert "I found floods in Johor" in result
    
    # Verify ES was called with correct filter (via get_historical_disasters)
    args, kwargs = mock_es_client.search.call_args
    body = kwargs['body']
    must_clauses = body['query']['bool']['must']
    
    # Verify Location Clause
    location_clause = next((c for c in must_clauses if "multi_match" in c), None)
    assert location_clause is not None
    assert location_clause['multi_match']['query'] == "Johor"
    
    # Verify Type Clause
    type_clause = next((c for c in must_clauses if "term" in c), None)
    assert type_clause is not None
    assert type_clause['term']['classification_type'] == "flood"


# --- UT-08-002: Verify Historical Data Retrieval (Date Logic) ---
def test_ut_08_002_historical_data_logic():
    """
    Verify get_historical_disasters constructs the correct Date/Month query.
    """
    # Action: Search for "October"
    get_historical_disasters(month="October")
    
    # Assertion
    args, kwargs = mock_es_client.search.call_args
    body = kwargs['body']
    must_clauses = body['query']['bool']['must']
    
    # Look for wildcard date search
    date_clause = next((c for c in must_clauses if "wildcard" in c), None)
    
    assert date_clause is not None
    # "October" should map to "10"
    assert date_clause['wildcard']['start_time'] == "*-10-*"


# --- UT-08-004 & UT-08-005: Multi-language Response ---
@patch("app.chatbot.chatbot_service.openai.OpenAI")
def test_ut_08_004_multilanguage(mock_openai_class):
    """
    Verify the chatbot returns the string provided by the AI (Language agnostic).
    """
    mock_client = mock_openai_class.return_value
    
    # Scenario: Malay Input
    malay_response = MagicMock()
    malay_response.tool_calls = None
    malay_response.content = "Banjir di Kuala Lumpur terkawal."
    
    mock_client.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=malay_response)])
    
    import asyncio
    result = asyncio.run(chatbot_response("Apakah status banjir?"))
    
    assert result == "Banjir di Kuala Lumpur terkawal."


# --- UT-08-006: Verify Handling of Ambiguous Queries ---
@patch("app.chatbot.chatbot_service.openai.OpenAI")
def test_ut_08_006_ambiguous_query(mock_openai_class):
    """
    Verify that if AI does NOT call a tool (no clear intent), it returns text directly.
    """
    mock_client = mock_openai_class.return_value
    
    # AI just chats back
    chat_response = MagicMock()
    chat_response.tool_calls = None
    chat_response.content = "How can I help you today?"
    
    mock_client.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=chat_response)])
    
    import asyncio
    result = asyncio.run(chatbot_response("hello"))
    
    assert result == "How can I help you today?"
    # Verify ES was NOT called (optimization check)
    mock_es_client.search.assert_not_called()


# --- UT-08-007: Verify Response Formatting (API Endpoint) ---
@patch("app.routes.chatbot_route.chatbot_response_with_data")
def test_ut_08_007_api_formatting(mock_service_func):
    """
    Verify the /chatbot_debug endpoint returns the correct JSON structure.
    """
    # Setup: Mock service return values (Tuple: reply, debug_list)
    mock_service_func.return_value = ("Flood alert in Johor", [{"event_id": "1", "type": "flood"}])
    
    payload = {"message": "Debug this"}
    
    # Action
    response = client.post("/chatbot_debug", json=payload)
    
    # Assertion
    assert response.status_code == 200
    json_resp = response.json()
    
    # Check structure
    assert "reply" in json_resp
    assert "debug_data" in json_resp
    assert json_resp["reply"] == "Flood alert in Johor"
    assert json_resp["debug_data"][0]["type"] == "flood"