# Agentic Dev Triage

A multi-agent pipeline that automatically triages incoming developer-workflow events — PR review comments and CI failure logs — and responds on GitHub with a classified, context-aware reply, backed by a local knowledge base.

Given a messy PR comment like _"this function recalculates fib(n) every time, seems slow"_, the pipeline:

1. Classifies it (Performance / Security / Logic / Style)
2. Assigns it to the right team
3. Retrieves a relevant, previously-documented fix using semantic search
4. Drafts a clear, actionable reply
5. Posts it back to GitHub automatically

Built as a learning project to understand agentic pipelines, retrieval-augmented generation (RAG), and LLM-orchestration frameworks end to end — every function was written, tested standalone, and debugged individually before being wired into the full graph.

---

## Table of contents

- [Architecture](#architecture)
- [Why this design](#why-this-design)
- [Files](#files)
- [Setup](#setup)
- [Usage](#usage)
- [Example run](#example-run)
- [How RAG retrieval works](#how-rag-retrieval-works)
- [Design decisions and trade-offs](#design-decisions-and-trade-offs)
- [Challenges hit while building this](#challenges-hit-while-building-this)
- [Extending this project](#extending-this-project)
- [Tech stack](#tech-stack)

---

## Architecture

```
                  PR comment  ──┐
                                ├─→ classify_input → retrieve_kb → draft_output → GitHub dispatch
              CI failure log  ──┘
```

The pipeline is a single, linear [LangGraph](https://github.com/langchain-ai/langgraph) `StateGraph` with three nodes and one shared state object flowing through all of them:

| Stage | Node                        | Input (from state)                           | Output (added to state)           |
| ----- | --------------------------- | -------------------------------------------- | --------------------------------- |
| 1     | `classify_input`            | `source_type`, `raw_input`                   | `category`, `assignee`, `summary` |
| 2     | `retrieve_kb`               | `source_type`, `summary`                     | `kb_solution`                     |
| 3     | `draft_output`              | `category`, `summary`, `kb_solution`         | `draft`                           |
| 4     | dispatch (not a graph node) | `repo`, `target_number`, `draft`, `category` | — (posts to GitHub)               |

Two intake types (`pr_comment`, `ci_failure`) share this exact same graph — no branching logic exists in the graph itself. Instead, a single `source_type` field determines which category list, which knowledge-base entries, and which prompt wording each node uses internally. This keeps the graph structure trivial while still supporting two genuinely different kinds of input.

## Why this design

The original inspiration for this project routed only one kind of input (bug reports) to email. This version deliberately extends that in two ways that make it closer to a real engineering tool:

- **Two intake sources instead of one** — PR review comments and CI failure logs are both extremely common triage targets in real engineering orgs, and structuring the pipeline around a `source_type` flag (rather than duplicating the whole pipeline) demonstrates handling genuine input diversity without doubling the codebase.
- **GitHub API dispatch instead of email** — posting directly to the PR/issue that triggered the pipeline is a more realistic delivery mechanism for this kind of tool than an email, and it's the kind of API integration (auth headers, REST endpoints, JSON payloads) that comes up constantly in real backend work.

## Files

| File                 | Purpose                                                                                                  |
| -------------------- | -------------------------------------------------------------------------------------------------------- |
| `state.py`           | Shared `TypedDict` (`AgentState`) — the schema for everything that flows between pipeline stages         |
| `agents.py`          | The three LLM/RAG functions: `classify_input`, `retrieve_kb`, `draft_output`, plus the Groq client setup |
| `knowledge_base.txt` | Plain-text issue → fix pairs, tagged `Source: PR_COMMENT` / `Source: CI_FAILURE`, used for RAG           |
| `github_client.py`   | `post_comment` and `add_label` — GitHub REST API calls with a dry-run fallback when no token is set      |
| `main.py`            | Builds the LangGraph `StateGraph`, wires the 3 nodes with edges, and runs the CLI                        |
| `requirements.txt`   | Python dependencies                                                                                      |
| `threshold_test.py` | Standalone script that measures retrieval scores across many test queries to empirically derive the similarity threshold |

## Setup

```bash
git clone https://github.com/suyash2312/Agentic-Dev-Triage.git
cd Agentic-Dev-Triage
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
GITHUB_TOKEN=your_github_pat_here   # optional — omit to run in dry-run mode
```

- **Groq key**: sign up at [console.groq.com](https://console.groq.com), then generate a key at [console.groq.com/keys](https://console.groq.com/keys) (free tier is sufficient).
- **GitHub token**: [github.com/settings/tokens](https://github.com/settings/tokens) → "Generate new token (classic)" → check the `repo` scope → generate. Needed only to actually post comments/labels; without it, the pipeline runs fully except the final dispatch step prints what it _would_ post instead.

Never commit `.env` — it's already excluded via `.gitignore`.

## Usage

```bash
python main.py
```

You'll be prompted for:

1. **Intake type** — `1` for a PR review comment, `2` for a CI failure log
2. **The text** — paste the actual comment or log excerpt
3. **Repo** — in `owner/repo` format (e.g. `suyash2312/Agentic-Dev-Triage`)
4. **PR or issue number** — which GitHub thread to post the result to

## Example run

**Input** (PR comment):

> This function recalculates fibonacci(n) recursively every time it's called, even for the same inputs repeatedly.

**Pipeline output:**

- Category: `Performance`
- Assignee: `Backend Engineering Team`
- Summary: _"The recursive Fibonacci function lacks memoization or caching, causing redundant calculations that degrade runtime performance."_
- Retrieved fix (cosine similarity ≈ 0.61 against the knowledge base): _"Store previously computed results (memoization) — e.g. a hash map or array cache — and reuse them instead of recomputing."_

**Drafted GitHub comment (posted automatically):**

> This recursive Fibonacci function repeatedly recalculates values, leading to exponential time complexity and severe performance degradation on larger inputs. Please add memoization — using an array or hash map to cache and reuse previously computed results — to bring the runtime down to linear time.

## How RAG retrieval works

`retrieve_kb` doesn't use exact keyword matching — it uses **semantic similarity**, so a query worded completely differently from the knowledge-base entry can still match correctly:

1. Read `knowledge_base.txt`, split into entries (separated by blank lines), and keep only the ones tagged for the current `source_type`.
2. Parse each entry's `Issue:` and `Fix:` lines into two parallel lists.
3. Embed every `Issue:` string and the query (the LLM-generated `summary`) into vectors using `sentence-transformers`' `all-MiniLM-L6-v2` model.
4. Compute cosine similarity between the query vector and every issue vector.
5. Return the `Fix:` text for the highest-scoring entry — but only if the score clears a **0.4 similarity threshold**; below that, it reports "no close match" rather than returning an irrelevant fix.

This was verified directly during development: the query _"Recursion code gave time limit exceeded error"_ — which shares no words with the KB entry _"Recursive function recalculates the same subproblem multiple times"_ — still scored 0.61 similarity and matched correctly, while unrelated entries scored near zero.

## Design decisions and trade-offs

- **Strict prompt-format parsing over structured output APIs.** `classify_input` asks the LLM to respond in an exact `CATEGORY: / ASSIGNEE: / SUMMARY:` template and parses it with `.startswith()` checks rather than using a provider-specific JSON/structured-output mode. This is simpler and provider-agnostic, at the cost of being slightly more fragile to LLM formatting drift.
- **Local, file-based knowledge base instead of a vector database.** For a knowledge base this size, a plain `.txt` file re-embedded on every call is simpler to read, edit, and debug than standing up a vector store — the trade-off is it re-computes all embeddings every single call rather than caching them, which wouldn't scale to a large KB.
- **Dry-run-by-default dispatch.** `github_client.py` checks for `GITHUB_TOKEN` before making any real API call, so the entire pipeline — including a full LangGraph run — can be tested and demoed without needing live GitHub credentials at all.
- **One shared LLM client, swappable provider.** `agents.py` centralizes the LLM client into a single `llm` object and a single `get_text()` helper, so switching providers (this project moved from Gemini to Groq mid-build, see below) only requires changing 2-3 lines, not every function.
- **Similarity threshold tuned empirically, not guessed.** `retrieve_kb`'s match threshold (0.285) was derived by running `threshold_test.py` — a script that tests 35 queries spanning every category against the knowledge base and reports the score distribution. It found a clean gap between genuine matches (lowest: 0.347) and unrelated queries (highest: 0.224), with the threshold set at the midpoint. Re-running this script as the knowledge base grows is recommended, since the margin between "correct match" and "close-but-wrong match" narrows as more topically similar entries are added.

## Challenges hit while building this

Documented here because debugging real infrastructure issues was as much a part of building this as the core logic:

- **Provider migration mid-build**: started with Gemini, hit its 20-requests/day free-tier quota during testing, and migrated to Groq — which required discovering that Gemini returns `response.content` as a list of dicts while Groq returns a plain string, and adjusting the shared `get_text()` helper accordingly.
- **Model deprecation**: both `gemini-2.0-flash` and `llama-3.3-70b-versatile` returned 404s mid-project as the providers changed their available model lists — resolved by querying each provider's live model list directly (`GET /v1/models`) rather than trusting a hardcoded model name.
- **Git merge with unrelated histories**: the local project folder and its GitHub remote had diverged (separate commit histories for the same files), resolved with `git merge --allow-unrelated-histories` and manual conflict resolution favoring the actively-developed local versions.
- **Editor buffer vs. disk state**: several early bugs (an "empty" knowledge base file, a "stale" `main.py` still asking for old variables) turned out to be unsaved editor buffers — a reminder that `Ctrl+S` matters before every test run.

## Extending this project

- Add more entries to `knowledge_base.txt` — same `Source:` / `Category:` / `Issue:` / `Fix:` block format, separated by a blank line.
- Add more classification categories in `agents.py`'s `classify_input`.
- Replace the CLI in `main.py` with a real webhook receiver (Flask/FastAPI) so the pipeline triggers automatically on GitHub's `pull_request_review_comment` and `workflow_run` (failed) events, instead of manual input.
- Cache knowledge-base embeddings instead of recomputing them on every `retrieve_kb` call, if the KB grows large.
- Swap the strict-format prompt parsing for a provider's native structured-output/JSON mode for more robust classification.

## Tech stack

- **[LangGraph](https://github.com/langchain-ai/langgraph)** — orchestration graph connecting the three pipeline stages
- **[Groq](https://groq.com)** (`openai/gpt-oss-120b`) — LLM inference for classification and drafting
- **[Sentence-Transformers](https://www.sbert.net/)** (`all-MiniLM-L6-v2`) — text embeddings for semantic search
- **NumPy** — cosine similarity computation
- **GitHub REST API** — comment and label dispatch
- **python-dotenv** — environment variable / secrets management

## Author

Suyash Jagtap
B.Tech Electrical Engineering, IIT Bombay
