import os
import time
import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = int(os.getenv('GITHUB_APP_ID', '0'))
PRIVATE_KEY_PATH = 'private-key.pem'

def _load_private_key():
    with open(PRIVATE_KEY_PATH, 'r') as f:
        return f.read()

def _generate_jwt():
    private_key = _load_private_key()
    now = int(time.time())
    payload = {
        'iat': now - 60,          # issued a minute ago (safety)
        'exp': now + 600,         # expires in 10 minutes
        'iss': APP_ID
    }
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token

def get_installation_token(installation_id: str) -> str:
    """Exchange app JWT for an installation access token."""
    jwt_token = _generate_jwt()
    url = f'https://api.github.com/app/installations/{installation_id}/access_tokens'
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github+json'
    }
    resp = requests.post(url, headers=headers)
    resp.raise_for_status()
    return resp.json()['token']

def get_pr_diff(owner, repo, pull_number, token):
    """Fetch the unified diff of a pull request."""
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text

def get_pr_files(owner, repo, pull_number, token):
    """Return list of changed files with their status and patch."""
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json'
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_file_content(owner, repo, file_path, ref, token):
    """Fetch full file content at a given git ref (branch/tag/commit)."""
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={ref}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.raw'
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        return None  # file doesn't exist (e.g., deleted)
    resp.raise_for_status()
    return resp.text

def post_pr_review(owner, repo, pull_number, token, comments):
    """Post a code review to a pull request with line-specific comments."""
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json'
    }
    
    github_comments = []
    for comment in comments:
        # A bit of safety check if the AI returned a dict with 'file', 'line', 'comment'
        if not comment.get("file") or not comment.get("line"):
            continue
            
        github_comments.append({
            "path": comment.get("file"),
            "line": int(comment.get("line")),
            "side": "RIGHT", # Represents the head/new commit
            "body": f"**[{str(comment.get('category', 'review')).capitalize()}]** (Severity: {comment.get('severity', 'low')})\n{comment.get('comment')}"
        })
    
    if not github_comments:
        return None
        
    payload = {
        "event": "COMMENT",
        "comments": github_comments,
        "body": "Hi there! I'm your AI code reviewer. I've left some suggestions on your recent changes below."
    }
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        print("Failed to post PR review:", resp.text)
    resp.raise_for_status()
    return resp.json()