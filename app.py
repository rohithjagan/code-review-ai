import os
import hmac
import hashlib
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from github_client import (
    get_installation_token,
    get_pr_diff,
    get_pr_files,
    get_file_content,
    post_pr_review
)
from ai_reviewer import review_code
from db import init_db, save_review, get_aggregated_stats, get_all_reviews

load_dotenv()

# Initialize the database (creates table if not exists)
init_db()

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '').encode()


def verify_signature(payload_body, signature_header):
    """Check the request is genuinely from GitHub using our shared secret."""
    if not signature_header:
        return False
    sha_name, signature = signature_header.split('=', 1)
    if sha_name != 'sha256':
        return False
    mac = hmac.new(WEBHOOK_SECRET, msg=payload_body, digestmod=hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        return process_webhook()
    return "Code Review AI Webhook Server is running!"


@app.route("/webhook", methods=["POST"])
def process_webhook():
    # ---- signature verification ----
    signature = request.headers.get("X-Hub-Signature-256")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 403

    event = request.headers.get("X-GitHub-Event", "ping")
    if event == "ping":
        return jsonify({"message": "Pong!"}), 200

    if event != "pull_request":
        return jsonify({"message": "Skipping non-pull_request event"}), 200

    data = request.json
    action = data.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return jsonify({"message": f"Skipping PR action: {action}"}), 200

    # Run the actual review in a background thread to respond quickly
    threading.Thread(target=handle_pr, args=(data,), daemon=True).start()
    return jsonify({"message": "PR review started"}), 202


@app.route("/api/stats")
def api_stats():
    """Return aggregated review statistics as JSON."""
    stats = get_aggregated_stats()
    return jsonify(stats)


@app.route("/api/reviews")
def api_reviews():
    """Return the 20 most recent reviews for the dashboard table."""
    all_reviews = get_all_reviews()
    recent = all_reviews[-20:]   # last 20 entries
    return jsonify(recent)


@app.route("/dashboard")
def dashboard():
    """Serve the dashboard HTML page."""
    return app.send_static_file('dashboard.html')


# Optional diagnostic route – use it once, then remove
@app.route("/test-dashboard")
def test_dashboard():
    static_path = os.path.join(app.root_path, 'static', 'dashboard.html')
    if os.path.exists(static_path):
        return jsonify({"status": "file found", "path": static_path})
    else:
        return jsonify({"status": "file NOT found", "path": static_path}), 404


def handle_pr(data):
    try:
        installation_id = data["installation"]["id"]
        pull_request = data["pull_request"]
        owner = data["repository"]["owner"]["login"]
        repo = data["repository"]["name"]
        pull_number = pull_request["number"]
        base_sha = pull_request["base"]["sha"]
        pr_title = pull_request.get("title", "")
        pr_author = pull_request.get("user", {}).get("login", "unknown")
        action = data.get("action", "unknown")

        # 1. Authenticate
        token = get_installation_token(str(installation_id))

        # 2. Fetch the diff
        diff_text = get_pr_diff(owner, repo, pull_number, token)

        # 3. List changed files
        files = get_pr_files(owner, repo, pull_number, token)

        # 4. Get full content of each changed file (base version)
        file_contents = {}
        for file in files:
            if file.get("status") in ["modified", "added"]:
                filename = file["filename"]
                content = get_file_content(owner, repo, filename, base_sha, token)
                if content:
                    file_contents[filename] = content

        # 5. Send to AI
        suggestions = review_code(diff_text, file_contents)

        # 6. Save review data to database for the dashboard
        save_review(
            repo_full_name=f"{owner}/{repo}",
            pr_number=pull_number,
            pr_title=pr_title,
            author=pr_author,
            action=action,
            suggestions=suggestions
        )

        # 7. Post the suggestions as a GitHub review
        if suggestions:
            post_pr_review(owner, repo, pull_number, token, suggestions)
            print(f"✅ Posted {len(suggestions)} comments for PR #{pull_number}.")
        else:
            print(f"🤖 No significant issues found for PR #{pull_number}.")

    except Exception as e:
        print(f"❌ Error handling PR: {e}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)