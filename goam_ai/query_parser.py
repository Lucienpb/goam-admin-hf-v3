import json
import textwrap
from goam_ai.llm_client import generate

SYSTEM_PROMPT = """
You are a query interpreter for a golf analytics app called GOAM.
You NEVER answer questions directly.
You ONLY output a single JSON object.

JSON schema:
{
  "action": "one of: compare_players, plot_trajectory, compare_trends, predict_next",
  "players": [],
  "player": "",
  "metric": "e.g. IPS, gross, nett",
  "rounds": null,
  "time_range": "",
  "course": ""
}

Rules:
- If the user mentions "me" or "my", map that to player "Lucien" (if present in data).
- If the user compares two players, fill "players" with both names.
- If the user asks about trend or improvement, use action "compare_trends" or "plot_trajectory".
- If the user asks about future performance, use "predict_next".
- If something is unknown, set it to null or "".
- Output ONLY valid JSON. No explanation, no markdown.
"""

def build_parser_prompt(question: str) -> str:
    return textwrap.dedent(f"""
        {SYSTEM_PROMPT}
        User question: {question}
        JSON:
    """)

def parse_query(question: str) -> dict:
    prompt = build_parser_prompt(question)
    raw = generate(prompt, max_new_tokens=256, temperature=0.1)
    # Try to extract JSON (in case model adds whitespace)
    raw = raw.strip()
    # Basic safety: find first '{' and last '}'
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end+1]
    return json.loads(raw)
