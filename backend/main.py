from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from datetime import datetime, timedelta
import motor.motor_asyncio
from os import getenv
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import logging

# Import the Intelligence Graph runner
from agents.graph import run_inocula_agent

# --- CONFIGURATION & LOGGING ---
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MONGO_CONNECTION_STRING = getenv("MONGO_CONNECTION_STRING")

# --- DATABASE CONNECTIONS ---
# Initialize client with a timeout to prevent Swagger from hanging on DNS issues
try:
    client = motor.motor_asyncio.AsyncIOMotorClient(
        MONGO_CONNECTION_STRING, 
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )
    db = client.project_inocula
    analysis_collection = db.get_collection("analyses")
    reports_collection = db.get_collection("reports")
    feedback_collection = db.get_collection("feedback")
except Exception as e:
    logger.error(f"Critical Database Connection Error: {e}")

# --- PYDANTIC MODELS ---
class AnalysisRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    score: int
    reasons: List[str]
    status: str
    explanation: str
    detected_emotions: List[str]

class ReportRequest(BaseModel):
    analysis_id: str
    comment: Optional[str] = None

class FeedbackRequest(BaseModel):
    analysis_id: str
    is_helpful: bool

class ReportStatusUpdate(BaseModel):
    status: str

# --- FASTAPI APP ---
app = FastAPI(title="Project Inocula API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- HELPER FUNCTIONS ---
async def save_analysis_to_db(request_text: str, result: dict, status: str):
    try:
        doc = {
            "timestamp": datetime.now(),
            "request_text": request_text,
            "result": result,
            "status": status
        }
        await analysis_collection.insert_one(doc)
    except Exception as e:
        logger.error(f"Failed to save analysis: {e}")

# --- API ENDPOINTS ---
@app.get("/")
def read_root(): 
    return {"status": "online", "engine": "Agentic Graph v2 (Async Optimized)"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest, background_tasks: BackgroundTasks):
    try:
        # CRITICAL FIX: Since run_inocula_agent runs heavy synchronous ML models,
        # we MUST run it in a threadpool so it doesn't block the FastAPI event loop.
        # This keeps the Swagger UI and other endpoints responsive.
        final_state = await run_in_threadpool(run_inocula_agent, request.text)
        
        final_result = {
            "score": final_state.get("score", 0),
            "reasons": final_state.get("reasons", []),
            "status": "agentic_analysis_complete",
            "explanation": final_state.get("explanation", ""),
            "detected_emotions": final_state.get("detected_emotions", [])
        }
        
        # Save to DB in the background to speed up response time
        background_tasks.add_task(save_analysis_to_db, request.text, final_result, "complete")
        
        return final_result

    except Exception as e:
        logger.error(f"Analysis Pipeline Failure: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    try:
        # Limit to 20 for performance
        cursor = analysis_collection.find().sort("timestamp", -1).limit(20)
        history = await cursor.to_list(length=20)
        for item in history:
            item["_id"] = str(item["_id"])
        return history
    except Exception as e:
        logger.error(f"History Fetch Error: {e}")
        return []

@app.post("/report")
async def submit_report(report: ReportRequest):
    try:
        await reports_collection.insert_one({
            "analysis_id": ObjectId(report.analysis_id), 
            "comment": report.comment, 
            "timestamp": datetime.now(), 
            "status": "submitted"
        })
        return {"message": "Report submitted."}
    except Exception as e:
        logger.error(f"Report Submission Error: {e}")
        raise HTTPException(status_code=500, detail="Database submission failed")

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    try:
        await feedback_collection.insert_one({
            "analysis_id": ObjectId(feedback.analysis_id), 
            "is_helpful": feedback.is_helpful, 
            "timestamp": datetime.now()
        })
        return {"message": "Feedback received."}
    except Exception as e:
        logger.error(f"Feedback Submission Error: {e}")
        raise HTTPException(status_code=500, detail="Database submission failed")

@app.get("/reports")
async def get_all_reports():
    try:
        # Join reports with analyses for the admin view
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$lookup": {
                "from": "analyses",
                "localField": "analysis_id",
                "foreignField": "_id",
                "as": "analysis_details"
            }},
            {"$unwind": "$analysis_details"}
        ]
        cursor = reports_collection.aggregate(pipeline)
        results = await cursor.to_list(length=100)
        for item in results:
            item["_id"] = str(item["_id"])
            item["analysis_id"] = str(item["analysis_id"])
            item["analysis_details"]["_id"] = str(item["analysis_details"]["_id"])
        return results
    except Exception as e:
        logger.error(f"Admin Reports Fetch Error: {e}")
        return []

@app.get("/analytics")
async def get_analytics():
    try:
        # Basic counts for the dashboard
        count_cursor = reports_collection.aggregate([
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ])
        counts = await count_cursor.to_list(length=10)
        
        # Format the data for Chart.js
        formatted_counts = {"submitted": 0, "escalated": 0, "resolved": 0}
        for item in counts:
            if item["_id"] in formatted_counts:
                formatted_counts[item["_id"]] = item["count"]

        return {
            "status_counts": formatted_counts,
            "daily_reports": [] # Can be populated with date-grouping later
        }
    except Exception as e:
        logger.error(f"Analytics Fetch Error: {e}")
        return {"status_counts": {"submitted": 0, "escalated": 0, "resolved": 0}, "daily_reports": []}