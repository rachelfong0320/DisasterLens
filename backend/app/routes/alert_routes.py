# app/routes.py
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.database import db_connection 
from typing import List
from core.run_root_pipeline import run_master_pipeline

router = APIRouter(tags=["Alerts & Subscriptions"])

class SubscriberModel(BaseModel):
    email: EmailStr
    locations: List[str]
    

@router.post("/subscribe", response_description="Subscribe user to alerts")
async def subscribe_user(subscription: SubscriberModel):
    """
    Saves user email and preferred locations to the 'subscriber' collection 
    in the 'Subscriptions' database.
    """
    if not subscription.locations:
        raise HTTPException(status_code=400, detail="At least one location is required.")

    try:
        # Use 'update_one' with 'upsert=True'. 
        # This creates a new entry if the email doesn't exist, 
        # or updates the locations if the email is already there.
        db_connection.subscriber_collection.update_one(
            {"email": subscription.email},
            {
                "$set": {
                    "locations": subscription.locations,
                    "updatedAt": time.time()
                },
                "$setOnInsert": {
                    "createdAt": time.time()
                }
            },
            upsert=True
        )
        return {"message": "Subscription successful", "data": subscription}
        
    except Exception as e:
        print(f"Subscription Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    