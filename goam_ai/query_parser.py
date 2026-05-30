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

def parse_query(question: str):
    q = question.lower()
    players = extract_players(q)

    # --- Compare trends (requires exactly 2 players) ---
    if ("compare" in q or "vs" in q or "versus" in q) and len(players) == 2:
        return {"action": "compare_trends", "players": players}

    if "trend" in q and len(players) == 2:
        return {"action": "compare_trends", "players": players}

    # --- Single-player trend / trajectory ---
    if "trend" in q or "trajectory" in q or "improving" in q:
        if len(players) == 1:
            return {"action": "plot_trajectory", "player": players[0]}

    # --- Default: single-player summary ---
    if len(players) == 1:
        return {"action": "summarize_player", "player": players[0]}

    # --- Fallback ---
    return {"action": "general_question", "query": question}

