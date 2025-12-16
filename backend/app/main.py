# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import disaster_data, pipeline_ops

app = FastAPI(title="DisasterLens API")

# Allow your frontend (e.g., localhost:3000) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(disaster_data.router, prefix="/api/v1") 
app.include_router(pipeline_ops.router, prefix="/api/v1")   

@app.get("/")
def read_root():
    return {"status": "Backend is running"}