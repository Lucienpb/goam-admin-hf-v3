import json
import textwrap
from goam_ai.llm_client import generate

SYSTEM_PROMPT = """
You are a query interpreter for a golf analytics app called GOAM.
You NEVER answer questions directly.
You ONLY output a single JSON object.

JSON schema:
{
  "action": "compare_players | plot_trajectory | compare_trends | predict_next",
  "players": [],
  "player": "",
  "metric": "ips | strokes | nett",
  "rounds": null,
  "time_range": "",
  "course": ""
}

Rules:
- If user says "me" or "my", map to "Lucien Barnes".
- If comparing two players, fill "players".
- If asking about improvement, use compare_trends.
- If asking about future performance, use predict_next.
- Output ONLY valid JSON.
"""

def build_parser_prompt(question: str) -> str:
    return textwrap.dedent(f"""
        {SYSTEM_PROMPT}
        User question: {question}
        JSON:
    """)

def parse_query(question: str) -> dict:
    prompt = build_parser_prompt(question)
    raw = generate(prompt, max_new_tokens=256, temperature=0.1).strip()

    # Extract JSON safely
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end+1]

    return json.loads(raw)
