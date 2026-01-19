import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app 

# Initialize TestClient to simulate Frontend requests
client = TestClient(app)

# ==========================================
# TEST CASE: IT-09-001
# ==========================================

def test_it_09_001_end_to_end_user_preference_persistence():
    """
    Test Case ID: IT-09-001
    Scenario: End-to-End User Preference Persistence
    Coverage: UI Component (Simulated) <-> API Route <-> Database (Upsert Logic)
    
    This verifies that when the Frontend sends a valid payload to /subscribe, 
    the Backend correctly updates the database.
    """
    
    # 1. Simulate the Frontend Payload
    # As defined in the test steps: locations "Penang", "Kedah" and a valid email.
    frontend_payload = {
        "email": "frontend_user@example.com",
        "locations": ["Penang", "Kedah"]
    }

    # 2. Mock the Database Connection
    # We need to ensure the update_one method is called successfully.
    mock_collection = MagicMock()
    mock_collection.update_one.return_value = MagicMock(upserted_id="12345")

    with patch("app.routes.alert_routes.db_connection") as mock_db_conn:
        mock_db_conn.subscriber_collection = mock_collection

        # 3. Execute Request (Simulates clicking "Submit" on the UI)
        # Note: Assuming the router is mounted at /api/v1 based on previous tests
        response = client.post("/api/v1/subscribe", json=frontend_payload)

        # 4. Verify Backend Response (Expected: 200 OK)
        assert response.status_code == 200, "Backend should accept valid frontend payloads"
        
        data = response.json()
        assert data["message"] == "Subscription successful"
        assert data["data"]["email"] == "frontend_user@example.com"
        # Verify the location array is preserved exactly as sent
        assert data["data"]["locations"] == ["Penang", "Kedah"]

        # 5. Verify Database Interaction (The "Upsert Logic")
        mock_collection.update_one.assert_called_once()
        
        # Inspect arguments to ensure strict matching of frontend data
        call_args = mock_collection.update_one.call_args
        filter_query = call_args[0][0]
        update_doc = call_args[0][1]
        
        assert filter_query["email"] == "frontend_user@example.com"
        assert update_doc["$set"]["locations"] == ["Penang", "Kedah"]

# ==========================================
# TEST CASE: IT-09-004
# ==========================================

def test_it_09_004_api_failure_handling():
    """
    Test Case ID: IT-09-004
    Scenario: Handling API Failures during Subscription
    Coverage: Error Propagation (Backend -> Frontend Error Boundaries)
    
    This verifies that if the Backend Database fails (e.g., Network Error),
    the API returns a proper 500 error code that the Frontend can catch.
    """
    
    # 1. Simulate the Frontend Payload
    frontend_payload = {
        "email": "error_test@example.com",
        "locations": ["Johor"]
    }

    # 2. Mock a Database Failure (Simulate 'Manual Stop' or 'Network Interception')
    mock_collection = MagicMock()
    # Force update_one to raise a generic Exception
    mock_collection.update_one.side_effect = Exception("Database Connection Lost")

    with patch("app.routes.alert_routes.db_connection") as mock_db_conn:
        mock_db_conn.subscriber_collection = mock_collection

        # 3. Execute Request
        response = client.post("/api/v1/subscribe", json=frontend_payload)

        # 4. Verify Error Response
        # The frontend expects a failure status code to trigger the "DisasterToast"
        assert response.status_code == 500
        
        # Verify the error detail matches what the frontend might log
        assert response.json() == {"detail": "Internal Server Error"}
        
        # Ensure the backend actually tried to call the DB before failing
        mock_collection.update_one.assert_called_once()

# ==========================================
# NOTE ON IT-09-002 & IT-09-003
# ==========================================
# IT-09-002 (Data Export) and IT-09-003 (Locale Switching) are primarily 
# Client-Side/Middleware logic. They are best tested with Cypress/Playwright.
# However, if IT-09-002 relies on a specific API endpoint to fetch data before 
# export, a test similar to IT-09-001 should be added here for that endpoint.