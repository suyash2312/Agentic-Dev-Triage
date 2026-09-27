from sentence_transformers import SentenceTransformer
import numpy as np
from state import AgentState

model = SentenceTransformer("all-MiniLM-L6-v2")

def retrieve_kb(state:AgentState):
    source_tag=state["source_type"]
    query=state["summary"]

    with open("knowledge_base.txt", "r") as f:
        content = f.read()
    blocks=content.split("\n\n")
