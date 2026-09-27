from typing import TypedDict


class AgentState(TypedDict):
    source_type: str
    raw_input: str
    category: str
    assignee: str
    summary: str
    kb_solution: str
    draft: str
    repo: str
    target_number: str
