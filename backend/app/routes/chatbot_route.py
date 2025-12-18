from fastapi import APIRouter
from pydantic import BaseModel
from ..chatbot.chatbot_service import chatbot_response, chatbot_response_with_data

router = APIRouter(tags=["Chatbot"])

class ChatInput(BaseModel):
    message: str

@router.post(
    "/chat",
    summary="Frontend Chatbot Endpoint",
    description="This endpoint sends the user message to the chatbot and returns the reply. Does not include Elasticsearch debug data."
)
async def ask_bot(data: ChatInput):
    reply = await chatbot_response(data.message)
    return {"reply": reply}

@router.post("/chatbot_debug", summary="Chatbot Endpoint with Debug Data", description="This endpoint returns both the AI's reply and the raw data fetched from Elasticsearch for debugging purposes."  )
async def ask_bot_debug(data: ChatInput):
    # 1. Get the AI's natural language answer
    # We modify your chatbot_response to return both the answer AND the tool data
    ai_reply, raw_data = await chatbot_response_with_data(data.message) 
    
    return {
        "reply": ai_reply,
        "debug_data": raw_data # This lets you see exactly what the AI was looking at
    }