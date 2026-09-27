from sentence_transformers import SentenceTransformer
import numpy as np
from state import AgentState
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")

model = SentenceTransformer("all-MiniLM-L6-v2")


def get_text(response):
    return response.content[0]["text"]


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
    response = llm.invoke(prompt)
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

    response = llm.invoke(prompt)
    text = get_text(response)
    return {"draft": text.strip()}

# if __name__ == "__main__":
#     test_state = {
#         "source_type": "pr_comment",
#         "raw_input": "",
#         "category": "",
#         "assignee": "",
#         "summary": "Recursion code gave time limit exceeded error",
#         "kb_solution": "",
#         "draft": "",
#         "repo": "",
#         "target_number": "",
#     }
#     result = retrieve_kb(test_state)
#     print(result)


if __name__ == "__main__":
    test_state = {
        "source_type": "pr_comment",
        "raw_input": "This function recalculates fibonacci(n) recursively every time it's called, even for the same inputs repeatedly.",
        "category": "", "assignee": "", "summary": "",
        "kb_solution": "", "draft": "", "repo": "", "target_number": "",
    }
    classify_result = classify_input(test_state)
    test_state.update(classify_result)   # merge classify's output into state
    print("After classify:", test_state)

    kb_result = retrieve_kb(test_state)
    test_state.update(kb_result)
    print("After retrieve_kb:", test_state)

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
