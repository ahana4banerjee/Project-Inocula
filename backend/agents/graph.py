from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.detector import detector_node
from agents.analyzer import analyzer_node
from agents.explainer import explainer_node

# 1. Initialize the StateGraph with our custom AgentState
workflow = StateGraph(AgentState)

# 2. Add our nodes (the agents we built)
workflow.add_node("detector", detector_node)
workflow.add_node("analyzer", analyzer_node)
workflow.add_node("explainer", explainer_node)

# 3. Define the edges (the flow of information)
# Our flow: Start -> Detector -> Analyzer -> Explainer -> End
workflow.set_entry_point("detector")
workflow.add_edge("detector", "analyzer")
workflow.add_edge("analyzer", "explainer")
workflow.add_edge("explainer", END)

# 4. Compile the graph into a runnable application
app_graph = workflow.compile()

print("✅ Intelligence Graph compiled successfully.")

def run_inocula_agent(text: str):
    """
    The main entry point to run the entire agentic pipeline.
    """
    # Initial state
    initial_state = {
        "input_text": text,
        "reasons": [],
        "detected_emotions": [],
        "score": 100,
        "explanation": "",
        "metadata": {}
    }
    
    # Run the graph
    # thread_id can be used later for multi-turn conversations
    final_state = app_graph.invoke(initial_state)
    
    return final_state