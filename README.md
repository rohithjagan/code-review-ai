# 🤖 AI Code Review Assistant

An intelligent, context-aware code review bot that integrates with GitHub pull requests.  
It understands your code, flags security issues, suggests architectural improvements, and provides actionable feedback — all powered by a large language model.

> **Live demo:** [https://code-review-ai.onrender.com](https://code-review-ai.onrender.com) (dashboard)

![Dashboard screen](static/dashboard-preview.png) <!-- add a screenshot later -->

## ✨ Features

- **Real‑time PR reviews** – triggered automatically via GitHub webhooks  
- **AI‑powered insights** – security, performance, architecture, maintainability, bugs  
- **Inline comments** – suggestions appear directly on the affected lines  
- **Quality dashboard** – charts & tables showing trends, severity, and recent reviews  
- **Multi‑language support** (Python out‑of‑the‑box, extendable)  
- **Zero‑cost stack** – runs on free tiers of Render, ngrok, and Google Gemini  

## 🛠 How It Works

1. You install the GitHub App on your repositories.
2. A pull request is opened or updated → GitHub sends a webhook to our server.
3. The server fetches the code diff and full file content.
4. An LLM (Google Gemini 2.5 Flash) generates a structured review.
5. Inline comments are posted on the PR via the GitHub API.
6. All review data is stored and displayed on a live dashboard.

## 📦 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask (Python), Gunicorn |
| AI Model | Google Gemini (free tier) |
| Database | SQLite |
| Deployment | Render |
| Frontend | Tailwind CSS, Chart.js |
| API | GitHub REST API v3 |

## 🚀 Quick Start (Local)

```bash
# Clone the repo
git clone https://github.com/your-username/code-review-ai.git
cd code-review-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Fill in your GitHub App credentials and Gemini API key

# Place your GitHub App private key as 'private-key.pem'

# Start the server
python app.py

Then expose your local server with ngrok:

```bash
ngrok http 5000
```

Configure the webhook URL in your GitHub App settings to:

```text
https://<ngrok-url>/webhook
```

---

# 🏗 Deployment to Render

1. Fork/clone this repository and push it to GitHub.

2. Create a new Web Service on [Render](https://render.com?utm_source=chatgpt.com).

3. Add the required environment variables  
   (refer to `.env.example`).

4. Add your `.pem` file as a **Secret File** with the path:

```text
/etc/secrets/private-key.pem
```

5. Set the following environment variable:

```env
PRIVATE_KEY_PATH=/etc/secrets/private-key.pem
```

6. Deploy the service.  
   Render will automatically detect `requirements.txt` and use Gunicorn.

> Full deployment guide available in `DEPLOYMENT.md` *(coming soon)*.

---

# 📊 Dashboard

Visit:

```text
/dashboard
```

to see aggregated metrics such as:

- Issues categorized by type and severity
- Trend analysis over time
- Recent review activity table

---

# 🤝 Contributing

We welcome contributions from the community!

Please read `CONTRIBUTING.md` for:
- Contribution guidelines
- Development setup
- Pull request workflow
- Code of conduct

---

# 📜 License

This project is licensed under the **MIT License**.  
See the `LICENSE` file for more details.

---

# 🔒 Security

Found a vulnerability?

Please report it responsibly through `SECURITY.md`.

---

Built with ❤️ by Rohith Jagan