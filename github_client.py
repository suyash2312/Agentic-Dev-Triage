import os
import requests
from dotenv import load_dotenv

load_dotenv()


def post_comment(repo, number, body):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print(f"[DryRun] No token — would post to {repo}#{number}:\n{body}")
        return

    url = f"https://api.github.com/repos/{repo}/issues/{number}/comments"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    response = requests.post(url, headers=headers, json={"body": body})
    if response.status_code == 201:
        print(f"Comment posted on {repo}#{number}")
    else:
        print(f"Failed to post comment (status {response.status_code})")


def add_label(repo, number, label):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print(
            f"[DryRun] No token — would add label '{label}' to {repo}#{number}")
        return

    url = f"https://api.github.com/repos/{repo}/issues/{number}/labels"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }
    response = requests.post(url, headers=headers, json={"labels": [label]})
    if response.status_code == 200:
        print(f"Label '{label}' added to {repo}#{number}")
    else:
        print(f"Failed to add label (status {response.status_code})")


if __name__ == "__main__":
    post_comment("suyash2312/Agentic-Dev-Triage", 1, "Test comment")
    add_label("suyash2312/Agentic-Dev-Triage", 1, "performance")
