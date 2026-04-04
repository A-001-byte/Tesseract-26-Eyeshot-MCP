import os
import json
import requests
import audit_trail

CRITIC_PROMPT = """
You are a CAD operation critic. You review the results of executed CAD operations and identify:
1. Any suspicious or unexpected outputs
2. Steps that were skipped and why
3. Whether the overall goal was achieved
4. Any recommendations for retry or correction

Return ONLY a JSON object like:
{
  "overall_status": "success" | "partial" | "failure",
  "issues": ["issue 1", "issue 2"],
  "recommendations": ["do this", "retry that"],
  "summary": "one line summary"
}
"""

def review_results(user_prompt: str, results: list) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")

    content = f"""
Original user request: {user_prompt}

Execution results:
{json.dumps(results, indent=2)}
"""

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent",
        headers={"Content-Type": "application/json"},
        params={"key": api_key},
        json={
            "system_instruction": {"parts": [{"text": CRITIC_PROMPT}]},
            "contents": [{"parts": [{"text": content}]}]
        }
    )

    raw = response.json()
    text = raw["candidates"][0]["content"]["parts"][0]["text"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    review = json.loads(text)
    audit_trail.log("Critic", "review_results", {"user_prompt": user_prompt}, review,
                    status=review.get("overall_status", "unknown"))
    return review