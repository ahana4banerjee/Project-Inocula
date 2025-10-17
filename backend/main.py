from fastapi import FastAPI
from datetime import datetime, timedelta
import motor.motor_asyncio
from os import getenv
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from transformers import pipeline
import google.generativeai as genai
from bson import ObjectId


# --- CONFIGURATION & SECRETS ---
load_dotenv()
MONGO_CONNECTION_STRING = getenv("MONGO_CONNECTION_STRING")
GEMINI_API_KEY = getenv("GEMINI_API_KEY")
HF_TOKEN = getenv("HF_TOKEN")
genai.configure(api_key=GEMINI_API_KEY)
explainer_model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- AI AGENT INITIALIZATION ---
print("Loading AI agents from Hugging Face Hub...")

detector_agent = pipeline(
    "text-classification", 
    model="./toxic-bert", # The online name
    return_all_scores=True,
    token=HF_TOKEN 
)

analyzer_agent = pipeline(
    "text-classification", 
    model="./emotion-english-distilroberta-base",
    return_all_scores=True,
    token=HF_TOKEN 
)

print(" AI agents loaded successfully.")

# --- DATABASE & CACHE CONNECTIONS ---
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
db = client.project_inocula
analysis_collection = db.get_collection("analyses")
reports_collection = db.get_collection("reports")
feedback_collection = db.get_collection("feedback")

# --- PYDANTIC MODELS ---
class AnalysisRequest(BaseModel):
    text: str
class AnalysisResponse(BaseModel):
    score: int
    reasons: List[str]
    status: str
    explanation: str
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

# --- AGENT LOGIC FUNCTIONS ---
def run_detector_agent(text: str):
    list_of_results = detector_agent(text)[0]
    for result in list_of_results:
        if result['label'] == 'toxic': return result['score']
    return 0.0

def run_analyzer_agent(text: str):
    emotions = analyzer_agent(text)[0]
    found_patterns = []
    for emotion in emotions:
        if emotion['label'] in ['anger', 'fear'] and emotion['score'] > 0.6:
            found_patterns.append(f"Appeals to '{emotion['label'].upper()}' (Confidence: {int(emotion['score']*100)}%).")
    return found_patterns

def run_explainer_agent(score: int, reasons: list, text_snippet: str):
    snippet = text_snippet[:500]
    prompt = f"As a misinformation analyst, provide a concise, one-sentence explanation for a user based on this data: Score ({score}/100), Reasons ({', '.join(reasons)}), Snippet ({snippet}). If score > 70, be reassuring. If 40-70, start with 'Caution:'. If < 40, start with 'High Risk:'."
    try:
        response = explainer_model.generate_content(prompt)
        return response.text.strip().replace("*", "")
    except Exception as e:
        print(f"Gemini API Error (fallback enabled): {e}")
        if score > 70: return "This content appears credible based on initial checks."
        elif score > 40: return f"Caution: This content shows signs of potential bias."
        else: return "High Risk: This content strongly matches patterns of known misinformation."

async def save_analysis(request_text: str, result: dict, status: str):
    # This now returns the inserted ID so we can link it in reports
    inserted = await analysis_collection.insert_one({"timestamp": datetime.now(), "request_text": request_text, "result": result, "status": status})
    return inserted.inserted_id

# --- API ENDPOINTS ---
@app.get("/")
def read_root(): return {"message": "Project Inocula API is running!"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    score, reasons, status = 100, [], "quick_analysis_complete"
    # Heuristics & AI Agents
    all_caps_words = [word for word in request.text.split() if word.isupper() and len(word) > 2]
    if len(all_caps_words) > 0:
        score -= 25; reasons.append(f"Contains capitalized words suggesting urgency: {', '.join(all_caps_words)}")
    if request.text.count('!') > 0:
        score -= 15; reasons.append("Contains exclamation marks suggesting urgency or sensationalism.")
    misinfo_prob = run_detector_agent(request.text)
    if misinfo_prob > 0.75:
        score -= int(misinfo_prob * 40); reasons.append(f"AI Detector: High probability ({int(misinfo_prob*100)}%) of being toxic.")
    psy_patterns = run_analyzer_agent(request.text)
    if psy_patterns:
        score -= 15 * len(psy_patterns); reasons.extend(psy_patterns)
    score = max(0, score)
    # Final Response
    explanation = run_explainer_agent(score, reasons, request.text)
    final_result = {"score": score, "reasons": reasons, "status": status, "explanation": explanation}
    await save_analysis(request.text, final_result, status)
    return final_result

@app.get("/history")
async def get_history():
    history_cursor = analysis_collection.find().sort("timestamp", -1).limit(20)
    history = await history_cursor.to_list(length=20)
    for item in history: item["_id"] = str(item["_id"])
    return history

@app.post("/report")
async def submit_report(report: ReportRequest):
    await reports_collection.insert_one({"analysis_id": ObjectId(report.analysis_id), "comment": report.comment, "timestamp": datetime.now(), "status": "submitted"})
    return {"message": "Report submitted successfully."}

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    await feedback_collection.insert_one({"analysis_id": ObjectId(feedback.analysis_id), "is_helpful": feedback.is_helpful, "timestamp": datetime.now()})
    return {"message": "Feedback received."}

# --- ADMIN ENDPOINTS ---
@app.get("/reports")
async def get_all_reports():
    # This pipeline joins reports with their original analysis for context
    pipeline = [
        {"$sort": {"timestamp": -1}},
        {"$lookup": {
            "from": "analyses",
            "localField": "analysis_id",
            "foreignField": "_id",
            "as": "analysis"
        }},
        {"$unwind": "$analysis"} # Deconstructs the analysis array to be a single object
    ]
    reports_cursor = reports_collection.aggregate(pipeline)
    reports = await reports_cursor.to_list(length=100) # Get up to 100 reports
    # Convert ObjectIds to strings for JSON compatibility
    for item in reports:
        item["_id"] = str(item["_id"])
        item["analysis_id"] = str(item["analysis_id"])
        item["analysis"]["_id"] = str(item["analysis"]["_id"])
    return reports

@app.put("/reports/{report_id}")
async def update_report_status(report_id: str, update: ReportStatusUpdate):
    await reports_collection.update_one(
        {"_id": ObjectId(report_id)},
        {"$set": {"status": update.status}}
    )
    return {"message": "Report status updated."}

@app.get("/analytics")
async def get_analytics():
    # Pipeline to count reports by their status
    status_pipeline = [{"$group": {"_id": "$status", "count": {"$sum": 1}}}]
    status_counts_cursor = reports_collection.aggregate(status_pipeline)
    status_counts_raw = await status_counts_cursor.to_list(length=10)
    status_counts = {s['_id']: s['count'] for s in status_counts_raw}

    # Pipeline to count reports per day for the last 7 days
    daily_pipeline = [
        {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=7)}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    daily_reports_cursor = reports_collection.aggregate(daily_pipeline)
    daily_reports = await daily_reports_cursor.to_list(length=7)

    return {
        "status_counts": {
            "submitted": status_counts.get("submitted", 0),
            "escalated": status_counts.get("escalated", 0),
            "resolved": status_counts.get("resolved", 0)
        },
        "daily_reports": daily_reports
    }



