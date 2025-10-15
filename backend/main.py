from fastapi import FastAPI
from datetime import datetime
import motor.motor_asyncio
from os import getenv
import redis
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv # <-- ADD THIS for security
from fastapi.middleware.cors import CORSMiddleware # Add this import


# --- SECURITY IMPROVEMENT ---
# Load variables from a .env file into the environment
load_dotenv() 
# Now get the connection string safely from the environment
MONGO_CONNECTION_STRING = getenv("MONGO_CONNECTION_STRING")

# --- DATABASE & CACHE CONNECTIONS ---
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_CONNECTION_STRING)
db = client.project_inocula
analysis_collection = db.get_collection("analyses")

redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# --- Pydantic Models (Data Shapes) ---
class AnalysisRequest(BaseModel):
    text: str

class AnalysisResponse(BaseModel):
    score: int
    reasons: List[str]
    status: str

# --- HEURISTICS (Rules Engine) ---
SENSATIONAL_KEYWORDS = ["shocking", "secret", "revealed", "miracle", "doctors hate"]
UNTRUSTED_DOMAINS = ["yourforwarded.news", "healthynews4u.info", "secretenergy.blogspot.com"]

# --- FastAPI App ---
app = FastAPI()

origins = [
    "*" # Allow all origins for the hackathon
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Project Ino`cula API is running!"}

async def save_analysis(request_text: str, result: dict, status: str):
    log_entry = {
        "timestamp": datetime.now(),
        "request_text": request_text,
        "result": result,
        "status": status  # <-- FIXED BUG #1: Use the status passed into the function
    }
    await analysis_collection.insert_one(log_entry)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    score = 100
    reasons = []
    status = "quick_analysis_complete"  # <-- FIXED BUG #2: Initialize status with a default value
    text_lower = request.text.lower()

    # --- Rules Engine Logic ---
    # Rule 1: Sensational Keywords
    for keyword in SENSATIONAL_KEYWORDS:
        if keyword in text_lower:
            score -= 20
            reasons.append(f"Contains sensational keyword: '{keyword}'")

    # Rule 2: Untrusted Domains
    for domain in UNTRUSTED_DOMAINS:
        if domain in text_lower:
            score -= 50
            reasons.append(f"Mentions an untrusted source: '{domain}'")
    
    # Rule 3: Excessive Punctuation
    if request.text.count('!') > 2:
        score -= 15
        reasons.append("Contains excessive exclamation marks.")

    # Rule 4: Excessive Capitalization
    all_caps_words = [word for word in request.text.split() if word.isupper() and len(word) > 2]
    if len(all_caps_words) > 1:
        score -= 15
        reasons.append(f"Contains excessive capitalization: {', '.join(all_caps_words)}")

    if score < 0:
        score = 0

    # --- Task Queue Placeholder ---
    if 40 <= score <= 70:
        status = "detailed_pending"  # Update status if needed
        redis_client.lpush("deep_analysis_queue", request.text)
        reasons.append("Score is uncertain. Queued for deeper AI analysis.")

    # --- Create final result dictionary ---
    final_result = {
        "score": score, 
        "reasons": reasons, 
        "status": status # <-- FIXED BUG #3: Add status to the dictionary
    }

    # --- Save to Database ---
    await save_analysis(request.text, final_result, status)

    return final_result