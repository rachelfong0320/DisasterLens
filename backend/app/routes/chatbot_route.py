from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from pymongo.database import Database
from app.db.connection import get_db
from ..chatbot.chatbot_service import chatbot_response, chatbot_response_with_data
from ..chatbot.map_chatbot_sync import get_full_events_by_ids

router = APIRouter(tags=["Chatbot"])

class ChatInput(BaseModel):
    message: str

class MapSyncRequest(BaseModel):
    event_ids: List[str]    

@router.post(
    "/chat",
    summary="Frontend Chatbot Endpoint",
    description="This endpoint sends the user message to the chatbot and returns the reply. Does not include Elasticsearch debug data."
)
async def ask_bot(data: ChatInput):
    try:
        reply = await chatbot_response(data.message)
        return {"reply": reply}
    except Exception as e:
        # Log the real error
        print("Chatbot debug error:", e)

        # Return a safe HTTP error to client
        raise HTTPException(
            status_code=500,
            detail="Failed to generate chatbot response"
        )

@router.post(
    "/chatbot_debug",
    summary="Chatbot Endpoint with Debug Data",
    description="This endpoint returns both the AI's reply and the raw data fetched from Elasticsearch for debugging purposes."
)
async def ask_bot_debug(data: ChatInput):
    try:
        ai_reply, raw_data = await chatbot_response_with_data(data.message)

        return {
            "reply": ai_reply,
            "debug_data": raw_data
        }

    except Exception as e:
        # Log the real error
        print("Chatbot debug error:", e)

        # Return a safe HTTP error to client
        raise HTTPException(
            status_code=500,
            detail="Failed to generate chatbot response"
        )
    
@router.post("/map-sync")
async def sync_chatbot_to_map(data: MapSyncRequest, db: Database = Depends(get_db)):
    # The route only handles the HTTP request and response
    events = get_full_events_by_ids(db, data.event_ids)
    
    if not events:
        return []
        
    return events