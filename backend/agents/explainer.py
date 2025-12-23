import os
from google import genai
from agents.state import AgentState
from dotenv import load_dotenv

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the GenAI Client
# We use the new google-genai SDK
client = genai.Client(api_key=GEMINI_API_KEY)

def explainer_node(state: AgentState):
    """
    Synthesizes all agent findings into a human-readable explanation.
    Updated to use models confirmed available via user diagnostics (Gemini 2.5/2.0).
    """
    text_snippet = state["input_text"][:300]
    score = state.get("score", 100)
    reasons = state.get("reasons", [])
    emotions = state.get("detected_emotions", [])
    
    prompt = f"""
    As a professional Misinformation Analyst, review these scan results:
    
    - Content: "{text_snippet}..."
    - Score: {score}/100
    - Factors: {", ".join(reasons)}
    - Emotions: {", ".join(emotions)}
    
    Task: Write a concise, one-sentence explanation for the user.
    Guidelines:
    - Score > 70: Be reassuring but objective.
    - 40-70: Start with 'Caution:' and explain why.
    - < 40: Start with 'High Risk:' and be direct about manipulation.
    - Do NOT use any markdown formatting or stars (*).
    """

    # Updated candidates based on your specific 'Available models' list
    # prioritizing 2.5-flash as it appeared first in your console log
    model_candidates = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-1.5-flash']
    explanation = "Analysis complete. Please refer to the specific factors detected below."

    for model_name in model_candidates:
        try:
            # The SDK will automatically handle the 'models/' prefix
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            explanation = response.text.strip()
            # Success!
            break
        except Exception as e:
            print(f"DEBUG: Attempt with {model_name} failed: {e}")
            
            if "404" in str(e):
                continue
            else:
                # If it's a 429 (Rate Limit) or 401 (Auth), we stop
                break
    
    # If all attempts failed, run diagnostics (kept for safety)
    if explanation.startswith("Analysis complete"):
        print("\n--- DIAGNOSTIC CHECK ---")
        try:
            available = [m.name for m in client.models.list()]
            print(f"Available models for your key: {available}")
        except Exception as list_err:
            print(f"Could not list models: {list_err}")

    return {
        "explanation": explanation
    }