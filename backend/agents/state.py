from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    input_text: str
    score: int
    reasons: Annotated[List[str], operator.add]
    detected_emotions: List[str]
    explanation: str
    metadata: dict
    # New fields for Phase 2
    is_memory_hit: bool
    memory_context: str