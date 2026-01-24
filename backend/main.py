from fastapi import FastAPI, HTTPException, BackgroundTasks
from celery.result import AsyncResult
from datetime import datetime
import motor.motor_asyncio
from os import getenv
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import logging

# 1. Import the Celery app and task from your worker file
from celery_worker import celery_app, analyze_misinformation_task
from agents.chat import run_chat_followup

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(title="Project Inocula - Async API")

# Enable CORS for Extension and Dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE SETUP ---
client = motor.motor_asyncio.AsyncIOMotorClient(getenv("MONGO_CONNECTION_STRING"))
db = client.project_inocula
analysis_collection = db.get_collection("analyses")

# --- MODELS ---
class AnalysisRequest(BaseModel):
    text: str

class ChatRequest(BaseModel):
    analysis_id: str
    message: str

# --- ENDPOINTS ---

@app.post("/analyze")
async def analyze_text(request: AnalysisRequest):
    """
    Step 1: Start the Async Task.
    This sends the text to Redis and returns a task_id immediately.
    """
    try:
        # Trigger the Celery task (.delay() is what makes it async)
        task = analyze_misinformation_task.delay(request.text)
        return {"task_id": task.id, "status": "processing"}
    except Exception as e:
        logger.error(f"Failed to queue task: {e}")
        raise HTTPException(status_code=500, detail="Could not queue the AI analysis task.")

@app.get("/status/{task_id}")
async def get_task_status(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.state == 'PENDING':
        return {"status": "pending"}
    elif task_result.state == 'STARTED':
        return {"status": "processing"}
    elif task_result.state == 'SUCCESS':
        result_data = task_result.result
        
        # Ensure we don't save duplicates
        existing = await analysis_collection.find_one({"task_id": task_id})
        
        if not existing:
            doc = {
                "task_id": task_id,
                "timestamp": datetime.now(),
                "request_text": "Remote Scan Result", # You can pass text in the task result if needed
                "result": result_data,
                "status": "complete"
            }
            inserted = await analysis_collection.insert_one(doc)
            result_data["analysis_id"] = str(inserted.inserted_id)

        return {"status": "completed", "result": result_data}
    
    # Handle failures
    elif task_result.state == 'FAILURE':
        return {"status": "failed", "error": str(task_result.info)}
    
    return {"status": task_result.state}

@app.post("/chat")
async def chat_with_analysis(request: ChatRequest):
    """
    Allows follow-up questions about a specific analysis.
    """
    try:
        analysis = await analysis_collection.find_one({"_id": ObjectId(request.analysis_id)})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis session not found.")
            
        answer = await run_chat_followup(analysis, request.message)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    """
    Returns the most recent analyses.
    """
    try:
        cursor = analysis_collection.find().sort("timestamp", -1).limit(20)
        history = await cursor.to_list(length=20)
        for item in history:
            item["_id"] = str(item["_id"])
        return history
    except Exception as e:
        return []

@app.get("/")
def read_root():
    return {"status": "online", "engine": "Celery Distributed Queue"}