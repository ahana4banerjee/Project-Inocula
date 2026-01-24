import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

async def run_chat_followup(previous_analysis: dict, user_question: str):
    """
    Takes a previous analysis result and answers a follow-up question
    using Gemini, providing continuity to the 'Agentic' experience.
    """
    
    # Extract context from the previous analysis document
    original_text = previous_analysis.get("request_text", "")
    ai_explanation = previous_analysis.get("result", {}).get("explanation", "")
    score = previous_analysis.get("result", {}).get("score", 0)
    reasons = previous_analysis.get("result", {}).get("reasons", [])

    prompt = f"""
    You are the Inocula Assistant. A user just received a misinformation analysis 
    and has a follow-up question.
    
    CONTEXT OF PREVIOUS ANALYSIS:
    - Analyzed Text: "{original_text}"
    - AI Score: {score}/100
    - AI Explanation: {ai_explanation}
    - Key Factors: {", ".join(reasons)}
    
    USER FOLLOW-UP QUESTION: "{user_question}"
    
    TASK: Answer the user's question based on the context above. 
    Be helpful, objective, and keep the answer to 2-3 sentences.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"DEBUG: Chat Agent Error: {e}")
        return "I'm sorry, I'm having trouble retrieving the context for that follow-up. Please try again."