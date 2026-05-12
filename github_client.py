import os
import time
import base64
import tempfile
import jwt
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID = int(os.getenv('GITHUB_APP_ID', '0'))

def _load_private_key():
    """
    If PRIVATE_KEY_B64 is set, decode it into a temporary file and return the path.
    Otherwise, use the local private-key.pem (development).
    """
    b64_key = os.getenv('PRIVATE_KEY_B64')
    if b64_key:
        # Create a temporary file with the decoded PEM content
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        tmp.write(base64.b64decode(b64_key))
        tmp.close()
        return tmp.name   # return path to the temp file
    # Local development fallback
    with open('private-key.pem', 'r') as f:
        return f.read()

def _generate_jwt():
    key_path = _load_private_key()
    if key_path.endswith('.pem'):
        # Only need to read the file once; for temp file we already have the path
        if os.getenv('PRIVATE_KEY_B64'):
            with open(key_path, 'r') as f:
                private_key = f.read()
        else:
            # local file: read directly
            with open('private-key.pem', 'r') as f:
                private_key = f.read()
    else:
        private_key = open(key_path, 'r').read()

    now = int(time.time())
    payload = {
        'iat': now - 60,
        'exp': now + 600,
        'iss': APP_ID
    }
    token = jwt.encode(payload, private_key, algorithm='RS256')
    return token

def get_installation_token(installation_id: str) -> str:
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
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text

def get_pr_files(owner, repo, pull_number, token):
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/files'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json'
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_file_content(owner, repo, file_path, ref, token):
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={ref}'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.raw'
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.text

def post_pr_review(owner, repo, pull_number, token, comments):
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/reviews'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github+json'
    }
    github_comments = []
    for comment in comments:
        if not comment.get("file") or not comment.get("line"):
            continue
        github_comments.append({
            "path": comment.get("file"),
            "line": int(comment.get("line")),
            "side": "RIGHT",
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