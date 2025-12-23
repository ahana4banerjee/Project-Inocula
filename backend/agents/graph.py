from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.detector import detector_node
from agents.analyzer import analyzer_node
from agents.fallacy import fallacy_node
from agents.explainer import explainer_node
from agents.verifier import verifier_node # New
from agents.memory import search_memory

def memory_node(state: AgentState):
    text = state["input_text"]
    match = search_memory(text)
    if match:
        return {
            "is_memory_hit": True,
            "memory_context": match["label"],
            "score": 0,
            "reasons": ["Historical Match: This claim matches a previously debunked narrative."]
        }
    return {"is_memory_hit": False}

def route_after_memory(state: AgentState):
    if state.get("is_memory_hit"):
        return "explainer"
    return "verifier" # Start with fact verification after memory

workflow = StateGraph(AgentState)

workflow.add_node("memory", memory_node)
workflow.add_node("verifier", verifier_node) # Fact Check Tool
workflow.add_node("detector", detector_node)
workflow.add_node("analyzer", analyzer_node)
workflow.add_node("fallacy", fallacy_node)
workflow.add_node("explainer", explainer_node)

workflow.set_entry_point("memory")

workflow.add_conditional_edges(
    "memory",
    route_after_memory,
    {"explainer": "explainer", "verifier": "verifier"}
)

# New logical flow: Memory -> Verifier -> Detector -> Analyzer -> Fallacy -> Explainer
workflow.add_edge("verifier", "detector")
workflow.add_edge("detector", "analyzer")
workflow.add_edge("analyzer", "fallacy")
workflow.add_edge("fallacy", "explainer")
workflow.add_edge("explainer", END)

app_graph = workflow.compile()

def run_inocula_agent(text: str):
    initial_state = {
        "input_text": text, "reasons": [], "detected_emotions": [], "score": 100,
        "explanation": "", "metadata": {}, "is_memory_hit": False, "memory_context": ""
    }
    return app_graph.invoke(initial_state)