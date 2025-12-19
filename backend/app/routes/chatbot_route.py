from fastapi import APIRouter, HTTPException
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