# ai_reviewer.py
import json
import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# Configure the Gemini client
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

def build_review_prompt(diff_text: str, file_contents: dict) -> str:
    """
    Build a single user prompt for Gemini with all the context it needs.
    """
    context_sections = []
    for fname, content in file_contents.items():
        # Truncate very long files to avoid hitting API limits
        context_sections.append(f"### {fname}\n```\n{content[:5000]}\n```")
    full_context = "\n\n".join(context_sections)

    # Combine system instructions and user query into one string for Gemini
    full_prompt = f"""You are an expert code reviewer. Analyze the provided code diff and the surrounding file content.
Focus on:
- Architectural improvements (e.g., better separation of concerns, design patterns)
- Security vulnerabilities (e.g., injection, unsafe deserialization, missing auth checks)
- Performance issues (e.g., N+1 queries, unnecessary allocations)
- Maintainability (e.g., unclear naming, missing error handling)
- Potentially buggy logic

Ignore style, formatting, and trivial linting issues.

Return your suggestions as a JSON array of objects with the following fields:
- "file": the filename
- "line": the line number in the new (head) version where the issue appears (if unclear, use the first changed line)
- "category": one of "security", "architecture", "performance", "maintainability", "bug"
- "severity": "low", "medium", or "high"
- "comment": a helpful, concise suggestion

If no significant issues are found, return an empty array [].

Only return the JSON array, nothing else.

Here is the unified diff of the pull request:

{diff_text}


Here are the full current versions (base) of the changed files for context:

{full_context}

Please review and return your suggestions in JSON as instructed."""
    return full_prompt

def review_code(diff_text: str, file_contents: dict, model="gemini-2.5-flash") -> list:
    """
    Send the code diff and file contents to Google Gemini for review.
    Returns a list of suggestion dictionaries.
    """
    full_prompt = build_review_prompt(diff_text, file_contents)

    try:
        response = client.models.generate_content(
            model=model,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=8192,                # plenty of room for multiple suggestions
                response_mime_type="application/json", # ensures clean JSON output
            )
        )
        raw_text = response.text.strip()

        # With response_mime_type=application/json we rarely see markdown fences,
        # but keep the safe‑guard just in case.
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        suggestions = json.loads(raw_text)
        return suggestions if isinstance(suggestions, list) else []

    except json.JSONDecodeError:
        print("Failed to parse Gemini response as JSON. Raw output (first 500 chars):")
        print(raw_text[:500])
        return []
    except Exception as e:
        print(f"Gemini review call failed: {e}")
        # Simple retry logic for transient errors
        print("Retrying in 5 seconds...")
        time.sleep(5)
        try:
            response = client.models.generate_content(
                model=model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=8192,
                    response_mime_type="application/json",
                )
            )
            raw_text = response.text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
            raw_text = raw_text.strip()
            suggestions = json.loads(raw_text)
            return suggestions if isinstance(suggestions, list) else []
        except Exception as retry_e:
            print(f"Gemini review retry also failed: {retry_e}")
            return []