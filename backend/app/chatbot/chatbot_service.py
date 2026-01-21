import os
import json
import openai
from elasticsearch import Elasticsearch

# Inside Docker, use 'elasticsearch' as the host
es = Elasticsearch("http://elasticsearch:9200")

def get_historical_disasters(location=None, disaster_type=None, month=None, year=None,latest=False):
    # FIXED: We use a single list 'must_clauses' to collect ALL filters
    must_clauses = []
    
    # 1. Handle Location (Ignore 'Malaysia' to prevent empty results)
    if location and location.lower() != "malaysia":
        must_clauses.append({
            "multi_match": {
                "query": location, 
                "fields": ["location_state", "location_district", "location.state", "location.district"],
                "fuzziness": "AUTO"
            }
        })
    
    # 2. Handle Disaster Type
    if disaster_type:
        # FIXED: Append to must_clauses, not a separate 'query' dict
        must_clauses.append({"term": {"classification_type": disaster_type.lower()}})
        
    # 3. Handle Month (UPDATED)
    if month:
        # CLEANUP: If AI sends "November 2025", split it to get just "November"
        clean_month = month.split(" ")[0].lower()
        
        month_map = {
            "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
            "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        target_m = month_map.get(clean_month) # Use clean_month here
        
        if target_m:
            must_clauses.append({
                "script": {
                    "script": {
                        "source": "doc['start_time'].size() > 0 && doc['start_time'].value.monthValue == params.m",
                        "params": {"m": target_m}
                    }
                }
            })

    # 4. Handle Year (NEW)
    if year:
        try:
            target_y = int(year)
            must_clauses.append({
                "script": {
                    "script": {
                        "source": "doc['start_time'].size() > 0 && doc['start_time'].value.year == params.y",
                        "params": {"y": target_y}
                    }
                }
            })
        except ValueError:
            pass # Ignore invalid years

    # DYNAMIC SIZE LOGIC
    # If the AI explicitly asks for 'latest', we only need 1. Otherwise, fetch 50 for context/stats.
    query_size = 1 if latest else 50

    # 5. Build Query with STRICT SORTING
    search_body = {
        "query": {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}]
            }
        },
        "sort": [{"start_time": {"order": "desc"}}], 
        "size": query_size  # <--- Use the variable here
    }

    try:
        res = es.search(index="disaster_events", body=search_body)
        results = [hit["_source"] for hit in res["hits"]["hits"]]
        return results
    except Exception as e:
        print(f"ES Error: {e}")
        return []

async def chatbot_response(user_text):
    client = openai.OpenAI(api_key=os.getenv("IG_OPENAI_API_KEY"))
    
    messages = [
    {
        "role": "system", 
        "content": (
            "You are DisasterLens AI, an expert on Malaysian disasters. "
            "IMPORTANT TERMINOLOGY:\n"
            "1. 'Kilat' on its own usually refers to Lightning or Thunderstorms.\n"
            "2. 'Banjir Kilat' refers specifically to Flash Floods.\n"
            "3. If the user asks for 'Kilat', look for reports categorized as 'Storm' or 'Lightning'. "
            "Do NOT assume they mean 'Banjir Kilat' (Flash Flood) unless they say the word 'Banjir'.\n\n"
            
            "DATA HANDLING:\n"
                "The search results are SORTED BY DATE (newest first). "
                "1. If the user asks for the 'latest' or 'most recent' event, describe the FIRST result in detail.\n"
                "2. If the user asks 'What happened in [Month]?' or 'How many events?', you MUST summarize the data.\n"
                "   - Count the events by type and location.\n"
                "   - Format: 'In [Month], there were [Count] [Type] in [Location] and [Count] [Type] in [Location].'\n"
                "   - Example: 'In January, there were 2 floods in Kuching and 1 landslide in Pahang.'\n\n"
        )
    },
    {"role": "user", "content": user_text}
    ]

    tools = [{
        "type": "function",
        "function": {
            "name": "get_historical_disasters",
            "description": "Search the database for disaster events by location, month, year, or type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "disaster_type": {"type": "string"},
                    "month": {"type": "string"},
                    "year": {"type": "string", "description": "Year of the event (e.g., '2025')"},
                    "latest": {
                        "type": "boolean", 
                        "description": "Set to true ONLY if the user explicitly asks for the 'latest', 'newest', or 'most recent' event."
                    }
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
    client = openai.OpenAI(api_key=os.getenv("IG_OPENAI_API_KEY"))
    
    messages = [
    {
        "role": "system", 
        "content": (
            "You are DisasterLens AI, an expert on Malaysian disaster data. "
            "The database contains specific Malaysian states and districts (e.g., Pahang, Kuching, Penang). "
            "If a user asks about 'Malaysia' generally, search without a location filter. "
            "ALWAYS look for the newest records by date. "
            "Don't offer user to ask impact of the event and current situation of the disaster."
        )
    },
    {"role": "user", "content": user_input}
]

    tools = [{
        "type": "function",
        "function": {
            "name": "get_historical_disasters",
            "description": "Search the database for disaster events by location, month, year, or type.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "disaster_type": {"type": "string"},
                    "month": {"type": "string"},
                    "year": {"type": "string", "description": "Year of the event (e.g., '2025')"},
                    "latest": {
                        "type": "boolean", 
                        "description": "Set to true ONLY if the user explicitly asks for the 'latest', 'newest', or 'most recent' event."
                    }
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