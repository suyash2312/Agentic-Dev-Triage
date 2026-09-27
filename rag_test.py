from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
# issues = ["Recursive function recalculates the same subproblem multiple times, wasting time and resources.",
#           "Accessing a map with operator[] (m[key]) without checking if the key exists first, which silently inserts a default value for missing keys.",
#           "NumPy import breaks after installing TensorFlow, because TensorFlow requires a specific NumPy version range."]
query = "Recursion code gave time limit exceeded error"


# for i in range(len(issues)):
#     cosine_similarity = np.dot(query_embeddings, issue_embeddings[i]) / (
#         np.linalg.norm(query_embeddings) * np.linalg.norm(issue_embeddings[i]))
#     print("issue:", issues[i])
#     print("cosine_similarity:", cosine_similarity)

with open("knowledge_base.txt", "r") as f:
    content = f.read()
    print(repr(content[:300]))

blocks = content.split("\n\n")
# print(len(blocks))
# for b in blocks:
#     print(b)
#     print("---")

source_tag = "PR_COMMENT"

issues = []
fixes = []
best_score = -1
best_index = -1

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

for i in range(len(issues)):
    score = np.dot(query_embeddings, issue_embeddings[i]) / (
        np.linalg.norm(query_embeddings) * np.linalg.norm(issue_embeddings[i]))
    if score > best_score:
        best_score = score
        best_index = i

# print("best match:", issues[best_index])
# print("fix:", fixes[best_index])
# print("score:", best_score)

threshold = 0.4

if best_score > threshold:
    print("fix:", fixes[best_index])
else:
    print("no match found")

print("score:", best_score)
