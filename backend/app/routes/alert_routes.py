# app/routes.py
import time
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
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
    
@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(email: str = Query(...)):
    result = db_connection.subscriber_collection.delete_one(
        {"email": email}
    )

    if result.deleted_count == 0:
        return """
        <html>
  <body style="font-family: 'Segoe UI', Tahoma, sans-serif; text-align: center; padding: 50px; background-color: #f7f7f7; color: #333;">
    <div style="max-width: 500px; margin: auto; background: #ffffff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
      <h1 style="color: #1c50a7; font-size: 32px; margin-bottom: 20px;">Email Not Found</h1>
      <p style="font-size: 16px; margin-bottom: 30px;">
        This email is already unsubscribed from DisasterLens alerts.  
        You won’t receive further notifications.
      </p>
      <a href="/" style="display: inline-block; background-color: #1c50a7; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 5px; font-weight: bold;">Return to Dashboard</a>
    </div>
  </body>
</html>
        """

    return """
    <html>
  <body style="font-family: 'Segoe UI', Tahoma, sans-serif; text-align: center; padding: 50px; background-color: #f7f7f7; color: #333;">
    <div style="max-width: 500px; margin: auto; background: #ffffff; padding: 40px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
      <h1 style="color: #1c50a7; font-size: 32px; margin-bottom: 20px;">Unsubscribed Successfully</h1>
      <p style="font-size: 16px; margin-bottom: 30px;">
        You will no longer receive disaster alerts from DisasterLens.
      </p>
      <a href="http://localhost:3000" style="display: inline-block; background-color: #1c50a7; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 5px; font-weight: bold;">
        Return to DisasterLens
      </a>
    </div>
  </body>
</html>
"""