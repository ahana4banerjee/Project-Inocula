from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from datetime import datetime
import motor.motor_asyncio
from os import getenv
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId
import logging

# Import Agents
from agents.graph import run_inocula_agent
from agents.chat import run_chat_followup # New Chat Agent

load_dotenv()
app = FastAPI(title="Project Inocula API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

# --- DB SETUP ---
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
async def analyze_text(request: AnalysisRequest, background_tasks: BackgroundTasks):
    # (Existing analysis logic stays the same)
    final_state = await run_in_threadpool(run_inocula_agent, request.text)
    
    result = {
        "score": final_state.get("score", 0),
        "reasons": final_state.get("reasons", []),
        "explanation": final_state.get("explanation", ""),
        "detected_emotions": final_state.get("detected_emotions", [])
    }
    
    # Save to DB and get the ID back so user can chat with it
    doc = {
        "timestamp": datetime.now(),
        "request_text": request.text,
        "result": result,
        "status": "complete"
    }
    inserted = await analysis_collection.insert_one(doc)
    
    # Return result with the new analysis_id
    return {**result, "analysis_id": str(inserted.inserted_id)}

@app.post("/chat")
async def chat_with_analysis(request: ChatRequest):
    """
    NEW: Allows users to ask follow-up questions about a specific analysis.
    This fulfills the 'State Management / Thread Persistence' task in Phase 1.
    """
    try:
        # 1. Retrieve the previous analysis from MongoDB
        analysis = await analysis_collection.find_one({"_id": ObjectId(request.analysis_id)})
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis session not found.")
            
        # 2. Use the Chat Agent to generate a contextual response
        answer = await run_chat_followup(analysis, request.message)
        
        return {"answer": answer}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    cursor = analysis_collection.find().sort("timestamp", -1).limit(20)
    history = await cursor.to_list(length=20)
    for item in history:
        item["_id"] = str(item["_id"])
    return history