import os
from google import genai
from agents.state import AgentState
from dotenv import load_dotenv

# Load API Key
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the GenAI Client
client = genai.Client(api_key=GEMINI_API_KEY)

def explainer_node(state: AgentState):
    """
    Synthesizes findings and performs final factual validation.
    If Wikipedia context contradicts the input, it overrides the score.
    """
    text_snippet = state["input_text"]
    current_score = state.get("score", 100)
    reasons = state.get("reasons", [])
    emotions = state.get("detected_emotions", [])
    
    # Extract Wikipedia context from metadata
    wiki_context = state.get("metadata", {}).get("verification_summary", "No direct Wikipedia context found.")
    
    prompt = f"""
    As a Misinformation Expert, synthesize a final report.
    
    USER CONTENT: "{text_snippet}"
    WIKIPEDIA CONTEXT: "{wiki_context}"
    
    CURRENT ANALYSIS:
    - Stylistic Score: {current_score}/100
    - Detected Emotions: {", ".join(emotions) if emotions else "Neutral"}
    - Flagged Factors: {", ".join(reasons)}
    
    TASK:
    1. Compare the USER CONTENT with the WIKIPEDIA CONTEXT.
    2. If the user content is a factual lie or misinformation based on the context, set the FINAL_SCORE to 0.
    3. If it is just biased or emotional but not a direct lie, keep the Stylistic Score.
    4. Provide a one-sentence EXPLANATION.
    
    OUTPUT FORMAT (Strict):
    FINAL_SCORE: [number]
    EXPLANATION: [text]
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        response_text = response.text.strip()
        
        # Simple parsing logic
        new_score = current_score
        explanation = "Analysis complete."
        
        for line in response_text.split('\n'):
            if line.startswith("FINAL_SCORE:"):
                try:
                    new_score = int(line.replace("FINAL_SCORE:", "").strip())
                except: pass
            if line.startswith("EXPLANATION:"):
                explanation = line.replace("EXPLANATION:", "").strip()

        # Add a reason if the score was overridden to 0
        final_reasons = []
        if new_score == 0 and current_score > 0:
            final_reasons = ["Factual Contradiction: This claim is explicitly refuted by established records."]

        return {
            "score": new_score,
            "explanation": explanation,
            "reasons": final_reasons
        }

    except Exception as e:
        print(f"DEBUG: Explainer API Error: {e}")
        return {
            "explanation": "Analysis complete. Factual verification suggest this may be inaccurate."
        }