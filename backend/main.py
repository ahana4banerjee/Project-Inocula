from fastapi import FastAPI, HTTPException
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
# Note: Motor doesn't connect until the first operation. 
# Errors usually appear during the first 'await'.
try:
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
    db = client.project_inocula
    analysis_collection = db.get_collection("analyses")
    reports_collection = db.get_collection("reports")
    feedback_collection = db.get_collection("feedback")
except Exception as e:
    logger.error(f"Failed to initialize MongoDB client: {e}")

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
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

async def save_analysis(request_text: str, result: dict, status: str):
    doc = {
        "timestamp": datetime.now(),
        "request_text": request_text,
        "result": result,
        "status": status
    }
    # This is often where DNS/Connection errors first manifest
    inserted = await analysis_collection.insert_one(doc)
    return inserted.inserted_id

# --- API ENDPOINTS ---
@app.get("/")
def read_root(): 
    return {"message": "Project Inocula Agentic API is running!"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    try:
        # 1. Trigger the Agentic Intelligence Graph
        # This runs Detector -> Analyzer -> Explainer automatically
        # Since this is a CPU/Network intensive sync call, we use it directly for now
        final_state = run_inocula_agent(request.text)
        
        # 2. Extract the results from the final state
        score = final_state.get("score", 0)
        reasons = final_state.get("reasons", [])
        explanation = final_state.get("explanation", "")
        emotions = final_state.get("detected_emotions", [])
        
        # 3. Prepare the result object
        final_result = {
            "score": score,
            "reasons": reasons,
            "status": "agentic_analysis_complete",
            "explanation": explanation,
            "detected_emotions": emotions
        }
        
        # 4. Save to MongoDB (Wrapped in try/except for specific DB failures)
        try:
            await save_analysis(request.text, final_result, "complete")
        except Exception as db_err:
            logger.error(f"Database Error: {db_err}")
            # We still return the analysis even if DB saving fails so the user gets their result
            final_result["status"] = "analysis_complete_db_error"

        return final_result

    except Exception as e:
        logger.error(f"Analysis Pipeline Error: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during analysis: {str(e)}")

@app.get("/history")
async def get_history():
    try:
        history_cursor = analysis_collection.find().sort("timestamp", -1).limit(20)
        history = await history_cursor.to_list(length=20)
        for item in history: item["_id"] = str(item["_id"])
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
        return {"message": "Report submitted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to submit report.")

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
        raise HTTPException(status_code=500, detail="Failed to submit feedback.")

# --- ADMIN ENDPOINTS (Analytics & Moderation) ---
@app.get("/reports")
async def get_all_reports():
    try:
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$lookup": {
                "from": "analyses",
                "localField": "analysis_id",
                "foreignField": "_id",
                "as": "analysis"
            }},
            {"$unwind": "$analysis"}
        ]
        reports_cursor = reports_collection.aggregate(pipeline)
        reports = await reports_cursor.to_list(length=100)
        for item in reports:
            item["_id"] = str(item["_id"])
            item["analysis_id"] = str(item["analysis_id"])
            item["analysis"]["_id"] = str(item["analysis"]["_id"])
        return reports
    except Exception as e:
        logger.error(f"Reports Fetch Error: {e}")
        return []

@app.put("/reports/{report_id}")
async def update_report_status(report_id: str, update: ReportStatusUpdate):
    try:
        await reports_collection.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"status": update.status}}
        )
        return {"message": "Report status updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update report status.")

@app.get("/analytics")
async def get_analytics():
    try:
        status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
        status_counts_raw = await (await reports_collection.aggregate(status_pipeline)).to_list(length=10)
        status_counts = {s['_id']: s['count'] for s in status_counts_raw}

        daily_pipeline = [
            {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=7)}}},
            {"$group": {
                "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id": 1}}
        ]
        daily_reports = await (await reports_collection.aggregate(daily_pipeline)).to_list(length=7)

        return {
            "status_counts": {
                "submitted": status_counts.get("submitted", 0),
                "escalated": status_counts.get("escalated", 0),
                "resolved": status_counts.get("resolved", 0)
            },
            "daily_reports": daily_reports
        }
    except Exception as e:
        logger.error(f"Analytics Error: {e}")
        return {"status_counts": {"submitted": 0, "escalated": 0, "resolved": 0}, "daily_reports": []}
