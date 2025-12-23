from transformers import pipeline
from agents.state import AgentState

# Load the model once when the module is imported
# This ensures we don't reload the model every time we run a scan
print("Loading Detector Agent (toxic-bert)...")
tox_pipeline = pipeline("text-classification", model="unitary/toxic-bert")

def detector_node(state: AgentState):
    """
    Analyzes the input text for toxicity and patterns of harmful content.
    Updates the state with a risk score and initial reasons.
    """
    text = state["input_text"]
    
    # Run the model
    results = tox_pipeline(text)
    
    # Process results (usually returns a list of scores)
    # toxic-bert usually returns 'label': 'toxic' or 'non-toxic'
    is_toxic = False
    highest_score = 0
    
    for result in results:
        if result['label'] == 'toxic' and result['score'] > 0.5:
            is_toxic = True
            highest_score = int(result['score'] * 100)
    
    # Determine the initial reasons to add to the state
    reasons = []
    if is_toxic:
        reasons.append(f"High toxicity detected (Confidence: {highest_score}%)")
    else:
        reasons.append("Initial scan: Content does not show immediate toxic patterns.")

    # Return the keys we want to update in the AgentState
    return {
        "score": highest_score if is_toxic else 0,
        "reasons": reasons
    }