# Agentic Dev Triage

A multi-agent triage pipeline that reads a PR review comment or a CI failure log, classifies it, retrieves a relevant fix from a knowledge base using semantic search (RAG), drafts a response, and posts it directly to GitHub.

Built with [LangGraph](https://github.com/langchain-ai/langgraph), [Groq](https://groq.com) (LLM inference), [Sentence-Transformers](https://www.sbert.net/) (embeddings), and the GitHub REST API.

## How it works

```
                 PR comment  ──┐
                                ├─→ classify_input → retrieve_kb → draft_output → GitHub dispatch
        CI failure log       ──┘
```

Two intake types share one pipeline. A `source_type` field in shared state (`pr_comment` or `ci_failure`) determines which category set, knowledge-base entries, and prompt each node uses — the graph structure itself never branches.

**1. `classify_input`** — sends the raw input to an LLM (Groq's `openai/gpt-oss-120b`), which returns a category (e.g. Performance, Logic, Flaky Test), an assignee, and a one-sentence summary, in a strict parseable format.

**2. `retrieve_kb`** — embeds the summary and every knowledge-base entry (filtered to the matching source type) using `all-MiniLM-L6-v2`, then finds the closest match by cosine similarity. Below a similarity threshold (0.4), it reports no match rather than returning an irrelevant fix.

**3. `draft_output`** — given the category and the retrieved fix, an LLM writes a short, direct comment ready to post.

**4. Dispatch** — `github_client.py` posts the drafted comment to the specified PR/issue via GitHub's REST API, and adds a category label for CI failures. If `GITHUB_TOKEN` isn't set, it prints what it would do instead of making a real API call (dry-run mode) — so the whole pipeline can be tested without GitHub credentials.

## Files

| File                 | Purpose                                                                         |
| -------------------- | ------------------------------------------------------------------------------- |
| `state.py`           | Shared `TypedDict` schema passed between all pipeline stages                    |
| `agents.py`          | The 3 LLM/RAG functions: `classify_input`, `retrieve_kb`, `draft_output`        |
| `knowledge_base.txt` | Issue → fix entries for RAG, tagged `Source: PR_COMMENT` / `Source: CI_FAILURE` |
| `github_client.py`   | Posts comments / adds labels via GitHub's REST API, with dry-run fallback       |
| `main.py`            | Builds the LangGraph `StateGraph`, CLI entry point                              |
| `requirements.txt`   | Python dependencies                                                             |

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_pat_here   # optional — omit to run in dry-run mode
```

- Get a Groq key at [console.groq.com/keys](https://console.groq.com/keys) (free tier).
- Get a GitHub token at [github.com/settings/tokens](https://github.com/settings/tokens) → "Generate new token (classic)" → scope: `repo`.

## Run

```bash
python main.py
```

You'll be asked to:

1. Choose intake type (`1` = PR comment, `2` = CI failure log)
2. Paste the comment/log text
3. Provide the target repo (`owner/repo` format)
4. Provide the PR or issue number to post the reply/label to

## Example

**Input:** `"This function recalculates fibonacci(n) recursively every time it's called, even for the same inputs repeatedly."`

**Output (posted as a GitHub comment):**

> This recursive Fibonacci function repeatedly recalculates values, leading to exponential time complexity and severe performance degradation on larger inputs. Please add memoization — using an array or hash map to cache and reuse previously computed results — to bring the runtime down to linear time.

## Extending

- Add more entries to `knowledge_base.txt` (keep the `Source:` / `Category:` / `Issue:` / `Fix:` block format, separated by a blank line).
- Add more categories in `agents.py`'s `classify_input`.
- Swap the CLI in `main.py` for a real webhook receiver (Flask/FastAPI) to trigger automatically on GitHub PR/CI events instead of manual input.
