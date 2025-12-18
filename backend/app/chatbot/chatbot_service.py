import os
import json
import openai
from elasticsearch import Elasticsearch

# Inside Docker, use 'elasticsearch' as the host
es = Elasticsearch("http://elasticsearch:9200")

def get_historical_disasters(location=None, disaster_type=None, month=None):
    query = {"bool": {"must": []}}
    must_clauses = []
    
    # 1. Handle Location (Ignore 'Malaysia' to prevent empty results)
    if location and location.lower() != "malaysia":
        must_clauses.append({
            "multi_match": {
                "query": location, 
                "fields": ["location_state", "location_district", "location.state", "location.district"]
            }
        })
    if disaster_type:
        query["bool"]["must"].append({"term": {"classification_type": disaster_type.lower()}})
    if month:
        # Matches ISO date format synced from Mongo
        month_map = {"july": "07", "august": "08", "january": "01", "february": "02",
                     "march": "03", "april": "04", "may": "05", "june": "06",
                     "september": "09", "october": "10", "november": "11", "december": "12"}
        m_code = month_map.get(month.lower(), "01")
        query["bool"]["must"].append({"wildcard": {"start_time": f"*-{m_code}-*"}})

    res = es.search(
        index="disaster_events", 
        query=query, 
        size=5,
        sort=[{"start_time": {"order": "desc"}}] 
    )
    return [hit["_source"] for hit in res["hits"]["hits"]]

async def chatbot_response(user_text):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    messages = [
        {"role": "system", "content": "You are DisasterLens Assistant. Use the historical search tool to answer questions. Answer in the user's language (English or Bahasa Melayu)."},
        {"role": "user", "content": user_text}
    ]

    tools = [{
        "type": "function",
        "function": {
            "name": "get_historical_disasters",
            "description": "Search the database for disaster events by location, month, or type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "disaster_type": {"type": "string"},
                    "month": {"type": "string"}
                }
            }
        }
    }]

    # AI determines search parameters
    response = client.chat.completions.create(model="gpt-4o", messages=messages, tools=tools)
    
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        
        # Search ES
        data = get_historical_disasters(**args)
        
        # Final response
        messages.append(response.choices[0].message)
        messages.append({"tool_call_id": tool_call.id, "role": "tool", "content": json.dumps(data)})
        
        final = client.chat.completions.create(model="gpt-4o", messages=messages)
        return final.choices[0].message.content
    
    return response.choices[0].message.content

async def chatbot_response_with_data(user_input):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    messages = [
        {"role": "system", "content": "You are DisasterLens AI..."},
        {"role": "user", "content": user_input}
    ]

    tools = [{
        "type": "function",
        "function": {
            "name": "get_historical_disasters",
            "description": "Search the database for disaster events by location, month, or type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "disaster_type": {"type": "string"},
                    "month": {"type": "string"}
                }
            }
        }
    }]

    # ... (Step 1: OpenAI Tool Call logic) ...
    
    raw_data = [] # Initialize empty list for tracking
    response = client.chat.completions.create(model="gpt-4o", messages=messages, tools=tools)
    
    if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        
        # This function returns a LIST, so we DO NOT use await here
        raw_data = get_historical_disasters(**args) 
        
        # Append tool results for OpenAI to read
        messages.append(response.choices[0].message)
        messages.append({"tool_call_id": tool_call.id, "role": "tool", "content": json.dumps(raw_data)})
        
        # Final AI generation
        final_response = client.chat.completions.create(model="gpt-4o", messages=messages)
        ai_reply = final_response.choices[0].message.content
        
        return ai_reply, raw_data # Return both as a tuple
    
    return response.choices[0].message.content, [] # Return empty list if no tool called