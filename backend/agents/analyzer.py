from transformers import pipeline
from agents.state import AgentState

print("Loading Analyzer Agent (emotion-distilroberta)...")
emotion_pipeline = pipeline(
    "text-classification", 
    model="j-hartmann/emotion-english-distilroberta-base", 
    return_all_scores=True
)

def analyzer_node(state: AgentState):
    """
    Deducts points from the score established by the detector.
    """
    text = state["input_text"]
    current_score = state.get("score", 100)
    
    results = emotion_pipeline(text)[0]
    
    found_emotions = []
    new_reasons = []
    deduction = 0
    
    # Anger and Fear are major red flags for manipulation
    for entry in results:
        if entry['label'] in ['anger', 'fear'] and entry['score'] > 0.4:
            found_emotions.append(entry['label'])
            new_reasons.append(f"Emotional trigger: {entry['label'].upper()}")
            deduction += 15
    
    return {
        "detected_emotions": found_emotions,
        "reasons": new_reasons,
        "score": max(0, current_score - deduction)
    }