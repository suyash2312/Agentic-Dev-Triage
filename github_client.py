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

    try:
        response = requests.post(url, headers=headers, json={
                                 "body": body}, timeout=10)
    except requests.exceptions.ConnectionError:
        print("Failed to reach GitHub — check your internet connection.")
        return
    except requests.exceptions.Timeout:
        print("Request to GitHub timed out. Try again.")
        return
    except requests.exceptions.RequestException as e:
        print(f"Unexpected network error while posting comment: {e}")
        return

    if response.status_code == 201:
        print(f"Comment posted on {repo}#{number}")
    elif response.status_code == 401:
        print("Failed to post comment: invalid or expired GitHub token.")
    elif response.status_code == 404:
        print(
            f"Failed to post comment: repo '{repo}' or issue #{number} not found (check access/spelling).")
    else:
        print(
            f"Failed to post comment (status {response.status_code}): {response.text}")


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

    try:
        response = requests.post(url, headers=headers, json={
                                 "labels": [label]}, timeout=10)
    except requests.exceptions.ConnectionError:
        print("Failed to reach GitHub — check your internet connection.")
        return
    except requests.exceptions.Timeout:
        print("Request to GitHub timed out. Try again.")
        return
    except requests.exceptions.RequestException as e:
        print(f"Unexpected network error while adding label: {e}")
        return

    if response.status_code == 200:
        print(f"Label '{label}' added to {repo}#{number}")
    elif response.status_code == 401:
        print("Failed to add label: invalid or expired GitHub token.")
    elif response.status_code == 404:
        print(
            f"Failed to add label: repo '{repo}' or issue #{number} not found (check access/spelling).")
    else:
        print(
            f"Failed to add label (status {response.status_code}): {response.text}")


if __name__ == "__main__":
    post_comment("suyash2312/Agentic-Dev-Triage", 1, "Test comment")
    add_label("suyash2312/Agentic-Dev-Triage", 1, "performance")
