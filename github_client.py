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
    print(response.status_code)


if __name__ == "__main__":
    post_comment("suyash2312/Agentic-Dev-Triage", 1, "Test comment")
