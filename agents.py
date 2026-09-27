from sentence_transformers import SentenceTransformer
import numpy as np
from state import AgentState
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from groq import APIError, RateLimitError, APIConnectionError

load_dotenv()
llm = ChatGroq(model="openai/gpt-oss-120b")

model = SentenceTransformer("all-MiniLM-L6-v2")


def get_text(response):
    return response.content


def classify_input(state: AgentState):
    if state["source_type"] == "pr_comment":
        categories = "Security, Performance, Logic, Style"
    else:
        categories = "Dependency Issue, Flaky Test"
    prompt = f"""
    Classify this input:{state["raw_input"]}
    Categories:{categories}
    Respond in exactly this format:
    CATEGORY: [one of the categories]
    ASSIGNEE: [who/what team]
    SUMMARY: [one sentence]
    """
    try:
        response = llm.invoke(prompt)
    except RateLimitError:
        print("Groq rate limit hit — wait a bit and try again.")
        return {"category": "Unknown", "assignee": "Unassigned", "summary": "Could not classify — rate limited."}
    except APIConnectionError:
        print("Could not reach Groq — check your internet connection.")
        return {"category": "Unknown", "assignee": "Unassigned", "summary": "Could not classify — connection error."}
    except APIError as e:
        print(f"Groq API error: {e}")
        return {"category": "Unknown", "assignee": "Unassigned", "summary": "Could not classify — API error."}
    text = get_text(response)
    lines = text.split("\n")
    category = ""
    assignee = ""
    summary = ""

    for line in lines:
        if line.strip().startswith("CATEGORY:"):
            category = line.replace("CATEGORY:", "").strip()
        if line.strip().startswith("ASSIGNEE:"):
            assignee = line.replace("ASSIGNEE:", "").strip()
        if line.strip().startswith("SUMMARY:"):
            summary = line.replace("SUMMARY:", "").strip()

    return {"category": category, "assignee": assignee, "summary": summary}


def retrieve_kb(state: AgentState):
    source_tag = state["source_type"].upper()
    query = state["summary"]

    with open("knowledge_base.txt", "r") as f:
        content = f.read()
    blocks = content.split("\n\n")
    issues = []
    fixes = []
    for block in blocks:
        if f"Source: {source_tag}" in block:
            lines = block.split("\n")
            for line in lines:
                if line.startswith("Issue: "):
                    clean = line.replace("Issue: ", "")
                    issues.append(clean)
                if line.startswith("Fix: "):
                    clean = line.replace("Fix: ", "")
                    fixes.append(clean)
    issue_embeddings = model.encode(issues)
    query_embeddings = model.encode(query)

    best_score = -1
    best_index = -1
    for i in range(len(issues)):
        score = np.dot(query_embeddings, issue_embeddings[i]) / (
            np.linalg.norm(query_embeddings) * np.linalg.norm(issue_embeddings[i]))
        if score > best_score:
            best_score = score
            best_index = i
    threshold = 0.4

    if best_score > threshold:
        return {"kb_solution": fixes[best_index]}
    else:
        return {"kb_solution": "No close match found in knowledge base."}


def draft_output(state: AgentState):
    prompt = f"""
    Write a short code review reply.
    Category: {state["category"]}
    Problem: {state["summary"]}
    Suggested fix: {state["kb_solution"]}

    Keep it under 3 sentences, direct and constructive.
    """

    try:
        response = llm.invoke(prompt)
    except RateLimitError:
        print("Groq rate limit hit — wait a bit and try again.")
        return {"draft": "Could not generate draft — rate limited. Please try again shortly."}
    except APIConnectionError:
        print("Could not reach Groq — check your internet connection.")
        return {"draft": "Could not generate draft — connection error."}
    except APIError as e:
        print(f"Groq API error: {e}")
        return {"draft": f"Could not generate draft — API error."}
    text = get_text(response)
    return {"draft": text.strip()}


if __name__ == "__main__":
    test_state = {
        "source_type": "pr_comment",
        "raw_input": "This function recalculates fibonacci(n) recursively every time it's called, even for the same inputs repeatedly.",
        "category": "", "assignee": "", "summary": "",
        "kb_solution": "", "draft": "", "repo": "", "target_number": "",
    }
    test_state.update(classify_input(test_state))
    test_state.update(retrieve_kb(test_state))
    test_state.update(draft_output(test_state))
    print(test_state["draft"])
