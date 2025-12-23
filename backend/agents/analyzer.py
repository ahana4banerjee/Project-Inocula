from transformers import pipeline
from agents.state import AgentState

# Load the model once when the module is imported
# Use the local path if you downloaded it, otherwise use the repo name
print("Loading Analyzer Agent (emotion-distilroberta)...")
emotion_pipeline = pipeline(
    "text-classification", 
    model="j-hartmann/emotion-english-distilroberta-base", 
    return_all_scores=True
)

def analyzer_node(state: AgentState):
    """
    Analyzes the text for emotional triggers like anger and fear.
    Deducts score based on detected manipulative patterns.
    """
    text = state["input_text"]
    current_score = state.get("score", 100)
    
    # Run the model
    results = emotion_pipeline(text)[0]
    
    found_emotions = []
    new_reasons = []
    score_deduction = 0
    
    # Check specifically for 'anger' and 'fear' (common misinfo triggers)
    for entry in results:
        if entry['label'] in ['anger', 'fear'] and entry['score'] > 0.6:
            found_emotions.append(entry['label'])
            new_reasons.append(
                f"Psychological trigger detected: {entry['label'].upper()} "
                f"(Confidence: {int(entry['score']*100)}%)"
            )
            score_deduction += 15
    
    # Return updates to the state
    return {
        "detected_emotions": found_emotions,
        "reasons": new_reasons,
        "score": max(0, current_score - score_deduction)
    }