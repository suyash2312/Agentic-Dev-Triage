from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

# (source_type, query, expected) -- expected is just a label for your own reading,
# not used in the logic. "match" = should find a real KB entry, "none" = should not.
test_queries = [
    # PR_COMMENT — Security
    ("pr_comment", "API key is written directly in the source file", "match"),
    ("pr_comment", "User input goes straight into a SQL string", "match"),
    ("pr_comment", "Page renders raw user text into HTML without escaping it", "match"),
    ("pr_comment", "Login token is kept in browser localStorage", "match"),
    # PR_COMMENT — Performance
    ("pr_comment", "Recursion code gave time limit exceeded error", "match"),
    ("pr_comment", "Loop hits the database once per item instead of one batch call", "match"),
    ("pr_comment", "Whole file is loaded into memory before processing it", "match"),
    ("pr_comment", "Membership check inside a loop is slow because it's a list, not a set", "match"),
    # PR_COMMENT — Logic
    ("pr_comment", "Accessing a dictionary key without checking it exists first inserts a blank value", "match"),
    ("pr_comment", "Code assumes a field always exists in the API response", "match"),
    ("pr_comment", "A mutable list is used as a default argument and state leaks between calls", "match"),
    ("pr_comment", "All exceptions are caught with a blanket except with no type specified", "match"),
    ("pr_comment", "Comparing two floats directly with == sometimes fails unexpectedly", "match"),
    # PR_COMMENT — Style
    ("pr_comment", "This function has too many responsibilities crammed into it", "match"),
    ("pr_comment", "Unexplained literal numbers scattered through the code with no context", "match"),
    ("pr_comment", "Four levels of nested if statements make this hard to read", "match"),
    # PR_COMMENT — none
    ("pr_comment", "What's the best pizza topping", "none"),
    ("pr_comment", "How do I center a div in CSS", "none"),
    ("pr_comment", "My favorite movie is Inception", "none"),
    ("pr_comment", "What's a good name for my new puppy", "none"),
    # CI_FAILURE — Flaky Test
    ("ci_failure", "Tests fail randomly only when run together", "match"),
    ("ci_failure", "Async test checks the result before the background task finishes", "match"),
    ("ci_failure", "Test fails only near midnight or month-end, never during the day", "match"),
    ("ci_failure", "A slow network response makes the test hang with no timeout set", "match"),
    # CI_FAILURE — Dependency Issue
    ("ci_failure", "Install fails because numpy and tensorflow versions clash", "match"),
    ("ci_failure", "Lockfile doesn't match the manifest so installs fail only in CI", "match"),
    ("ci_failure", "Two indirect dependencies want conflicting versions of the same package", "match"),
    ("ci_failure", "Build fails with a missing system library not managed by pip or npm", "match"),
    # CI_FAILURE — Infra Outage
    ("ci_failure", "Build gets OOM killed with no code changes explaining it", "match"),
    ("ci_failure", "Every job across unrelated repos fails at once with auth errors", "match"),
    ("ci_failure", "Docker image pull fails immediately with a connection error", "match"),
    # CI_FAILURE — Actual Bug
    ("ci_failure", "A test result changed to a different but consistent value after the last merge", "match"),
    ("ci_failure", "Test fails in CI only because it hardcodes a local file path", "match"),
    ("ci_failure", "Failure reproduces locally after updating a dependency, changelog shows a breaking change", "match"),
    # CI_FAILURE — none
    ("ci_failure", "The weather is nice today", "none"),
    ("ci_failure", "What time is the football match tonight", "none"),
    ("ci_failure", "What should I cook for dinner", "none"),
]


def load_kb(source_type):
    source_tag = source_type.upper()
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
                    issues.append(line.replace("Issue: ", "").strip())
                if line.startswith("Fix: "):
                    fixes.append(line.replace("Fix: ", "").strip())
    return issues, fixes


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def run():
    match_scores = []
    none_scores = []

    for source_type, query, expected in test_queries:
        issues, fixes = load_kb(source_type)
        issue_embeddings = model.encode(issues)
        query_embedding = model.encode(query)

        scores = []
        for i, issue in enumerate(issues):
            score = cosine_similarity(query_embedding, issue_embeddings[i])
            scores.append((score, issue))

        scores.sort(key=lambda x: x[0], reverse=True)
        top_score = scores[0][0]

        if expected == "match":
            match_scores.append(top_score)
        else:
            none_scores.append(top_score)

        print(f"\nQuery ({source_type}, expected={expected}): \"{query}\"")
        print(f"  Top score: {top_score:.3f}  -> {scores[0][1][:70]}...")
        if len(scores) > 1:
            print(
                f"  2nd score: {scores[1][0]:.3f}  -> {scores[1][1][:70]}...")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print(
        f"  Match queries   -> min: {min(match_scores):.3f}  max: {max(match_scores):.3f}")
    print(
        f"  None queries    -> min: {min(none_scores):.3f}  max: {max(none_scores):.3f}")
    print(f"  Suggested threshold (midpoint of the gap): "
          f"{(min(match_scores) + max(none_scores)) / 2:.3f}")


if __name__ == "__main__":
    run()
