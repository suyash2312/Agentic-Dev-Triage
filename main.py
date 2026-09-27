from state import AgentState
from langgraph.graph import StateGraph, END
from agents import classify_input, retrieve_kb, draft_output
from github_client import post_comment, add_label

builder = StateGraph(AgentState)

builder.add_node("classify", classify_input)
builder.add_node("retrieve", retrieve_kb)
builder.add_node("draft", draft_output)

builder.add_edge("classify", "retrieve")
builder.add_edge("retrieve", "draft")
builder.add_edge("draft", END)
builder.set_entry_point("classify")
graph = builder.compile()


def main():
    print("1. PR review comment")
    print("2. CI failure log")
    choice = input("Select intake type (1/2): ").strip()
    if choice == "1":
        source_type = "pr_comment"
    else:
        source_type = "ci_failure"
    raw_text = input("Paste the comment / log excerpt:\n> ")
    repo = input("Repo (owner/repo): ").strip()
    target_number = input("PR number or issue number: ").strip()

    initial_state = {
        "source_type": source_type,
        "raw_input": raw_text,
        "category": "", "assignee": "", "summary": "",
        "kb_solution": "", "draft": "",
        "repo": repo,
        "target_number": target_number,
    }

    result = graph.invoke(initial_state)
    print(result["draft"])
    post_comment(result["repo"], result["target_number"], result["draft"])
    if source_type == "ci_failure":
        add_label(result["repo"], result["target_number"],
                  result["category"].lower().replace(" ", "-"))


if __name__ == "__main__":
    main()
