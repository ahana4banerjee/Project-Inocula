import os
import ssl
import logging
from celery import Celery
from dotenv import load_dotenv

# Set up logging to see what's happening in the terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# 1. Initialize Celery with SSL for Upstash
REDIS_URL = os.getenv("REDIS_URL")

celery_app = Celery(
    "inocula_workers",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600, # Increased to 10 mins for heavy model loads
    broker_use_ssl={'ssl_cert_reqs': ssl.CERT_NONE},
    redis_backend_use_ssl={'ssl_cert_reqs': ssl.CERT_NONE}
)

# 2. Lazy Import to prevent worker from crashing during startup
# We import the agent runner INSIDE the task
@celery_app.task(name="analyze_misinformation_task", bind=True)
def analyze_misinformation_task(self, text):
    """
    Executes the agentic graph in the background.
    """
    logger.info(f"Task {self.request.id} started. Loading agents...")
    
    try:
        # We import here so the worker starts instantly and then loads models
        from agents.graph import run_inocula_agent
        
        logger.info(f"Agents loaded. Running graph analysis on text: {text[:50]}...")
        
        # Run the actual LangGraph logic
        result = run_inocula_agent(text)
        
        logger.info(f"Task {self.request.id} successfully completed.")
        
        return {
            "score": result.get("score", 0),
            "reasons": result.get("reasons", []),
            "explanation": result.get("explanation", ""),
            "detected_emotions": result.get("detected_emotions", []),
            "status": "complete"
        }
        
    except Exception as e:
        logger.error(f"Task Failed! Error: {str(e)}")
        return {"status": "failed", "error": str(e)}