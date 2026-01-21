import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Ensure backend path is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.chatbot.chatbot_service import chatbot_response_with_data

# System Test ST-08-001: Successful Real-Time Disaster Query
@pytest.mark.asyncio
@patch('app.chatbot.chatbot_service.openai.OpenAI')
@patch('app.chatbot.chatbot_service.es')
async def test_st_08_001_real_time_disaster_query(mock_es, mock_openai_class):
    """
    ST-08-001: Verify that asking for 'flood in Johor' triggers the correct 
    search parameters and returns location data for the map.
    """
    # --- 1. PRE-CONDITIONS (Setup Mocks) ---
    
    # Mock Elasticsearch to return "classified incident data for Johor"
    mock_es_response = {
        "hits": {
            "hits": [
                {
                    "_source": {
                        "event_id": "evt_johor_01",
                        "classification_type": "flood",
                        "location_state": "Johor",
                        "location_district": "Segamat",
                        "lat": 2.5,  # Coordinates needed for the map
                        "lon": 102.8,
                        "start_time": "2024-12-01T10:00:00"
                    }
                }
            ]
        }
    }
    mock_es.search.return_value = mock_es_response

    # Mock OpenAI to simulate "Smart" extraction
    mock_client = mock_openai_class.return_value
    
    # First call: AI decides to call the tool 'get_historical_disasters'
    first_call_response = MagicMock()
    first_call_response.choices[0].message.tool_calls = [
        MagicMock(
            function=MagicMock(
                name='get_historical_disasters',
                arguments='{"location": "Johor", "disaster_type": "flood"}'
            )
        )
    ]
    first_call_response.choices[0].message.content = None 

    # Second call: AI generates the natural language summary
    second_call_response = MagicMock()
    second_call_response.choices[0].message.tool_calls = None
    second_call_response.choices[0].message.content = "There is currently a flood reported in Segamat, Johor."

    # Chain the responses
    mock_client.chat.completions.create.side_effect = [first_call_response, second_call_response]

    # --- 2. TEST STEPS ---
    
    user_query = "Show me the current flood in Johor."
    
    # We use 'with_data' because ST-08-001 requires checking if the MAP gets data.
    ai_reply, raw_data = await chatbot_response_with_data(user_query)

    # --- 3. VERIFY EXPECTED RESULTS ---

    # 3a. Verify Natural Language Response
    assert "flood" in ai_reply.lower()
    assert "Johor" in ai_reply
    print(f"\n✅ Chatbot Reply: {ai_reply}")

    # 3b. Verify Map Data Integrity
    assert len(raw_data) > 0, "No data returned for the map to render"
    event = raw_data[0]
    
    assert event['location_state'] == "Johor"
    assert event['classification_type'] == "flood"
    
    # Verify coordinates exist
    assert 'lat' in event and 'lon' in event
    
    # 3c. Verify the Logic (Fixing the Argument Extraction)
    assert mock_es.search.called
    
    call_args = mock_es.search.call_args
    # call_args is a tuple: (args, kwargs)
    # Your code uses es.search(index=..., body=...) -> Keyword Arguments (kwargs)
    
    # Check kwargs first (Robust method)
    kwargs = call_args[1]
    if 'body' in kwargs:
        search_body = kwargs['body']
    else:
        # Fallback to positional if implementation changes
        search_body = call_args[0][1]

    # Verify the query structure
    print(f"\n✅ ES Query Sent: {search_body}")
    
    # Check if we filtered by location "Johor"
    # The structure is deeply nested, so we check for presence of the string
    import json
    body_str = json.dumps(search_body)
    assert "Johor" in body_str
    assert "flood" in body_str.lower()