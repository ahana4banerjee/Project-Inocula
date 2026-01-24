import os
from celery import Celery
from dotenv import load_dotenv
import ssl

# Import the logic from your graph
from agents.graph import run_inocula_agent

load_dotenv()

# Upstash Redis URL from your .env
REDIS_URL = os.getenv("REDIS_URL")

# Initialize Celery
celery_app = Celery(
    "inocula_workers",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# Celery Configuration for Production with SSL support
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    
    # REQUIRED for Upstash / rediss:// connections
    broker_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE
    },
    redis_backend_use_ssl={
        'ssl_cert_reqs': ssl.CERT_NONE
    }
)

@celery_app.task(name="analyze_misinformation_task")
def analyze_misinformation_task(text):
    """
    The heavy lifting happens here, away from the FastAPI main thread.
    """
    print(f"🚀 Executing background scan for: {text[:50]}...")
    try:
        # Run the LangGraph pipeline
        result = run_inocula_agent(text)
        
        return {
            "score": result.get("score", 0),
            "reasons": result.get("reasons", []),
            "explanation": result.get("explanation", ""),
            "detected_emotions": result.get("detected_emotions", []),
            "status": "complete"
        }
    except Exception as e:
        print(f"❌ Worker Task Error: {e}")
        return {"status": "failed", "error": str(e)}