from transformers import pipeline
from agents.state import AgentState

print("Loading Fallacy Agent (deberta-v3-nli)...")
classifier = pipeline(
    "zero-shot-classification", 
    model="sileod/deberta-v3-base-tasksource-nli"
)

# Refined labels for better detection
FALLACY_LABELS = [
    "Slippery Slope (Doomsday prediction)", 
    "Personal Attack (Ad Hominem)", 
    "Extreme Exaggeration", 
    "Logical Reasoning",
    "Fear Mongering"
]

def fallacy_node(state: AgentState):
    """
    More sensitive fallacy detection using Zero-Shot logic.
    """
    if state.get("is_memory_hit"):
        return {}

    text = state["input_text"]
    current_score = state.get("score", 100)
    
    # We ask the model to rank the labels
    result = classifier(text, candidate_labels=FALLACY_LABELS)
    
    top_label = result['labels'][0]
    top_score = result['scores'][0]
    
    new_reasons = []
    deduction = 0
    
    # We lowered the threshold to 0.3 to catch more subtle fallacies
    if top_label != "Logical Reasoning" and top_score > 0.3:
        new_reasons.append(f"Logical Flaw: {top_label}")
        deduction = 25
        
    return {
        "score": max(0, current_score - deduction),
        "reasons": new_reasons
    }