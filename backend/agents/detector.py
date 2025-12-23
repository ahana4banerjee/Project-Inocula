from transformers import pipeline
from agents.state import AgentState

print("Loading Detector Agent (toxic-bert)...")
tox_pipeline = pipeline("text-classification", model="unitary/toxic-bert")

def detector_node(state: AgentState):
    """
    Starts with 100 points. Deducts based on toxicity.
    """
    text = state["input_text"]
    results = tox_pipeline(text)
    
    # toxicity-bert returns scores for 'toxic'
    toxicity_score = 0
    for result in results:
        if result['label'] == 'toxic':
            toxicity_score = int(result['score'] * 100)
    
    is_toxic = toxicity_score > 50
    reasons = []
    
    if is_toxic:
        reasons.append(f"Toxicity detected (Level: {toxicity_score}%)")
    else:
        reasons.append("Initial scan: Content does not show immediate toxic patterns.")

    # START at 100 and subtract toxicity
    # If toxicity is 0, score remains 100 (Safe)
    return {
        "score": 100 - toxicity_score,
        "reasons": reasons
    }