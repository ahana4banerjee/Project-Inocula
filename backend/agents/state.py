from typing import TypedDict, List, Annotated
import operator

class AgentState(TypedDict):
    """
    The state represents the "memory" shared between all agents.
    As each agent finishes, it updates this dictionary.
    """
    input_text: str
    score: int
    reasons: Annotated[List[str], operator.add] # 'operator.add' allows agents to append to this list
    detected_emotions: List[str]
    explanation: str
    metadata: dict