import re

def parse_query(question: str, players_list, teams_list, courses_list, logged_in_player=None):
    """
    Final GOAM AI Query Parser
    - Detects identity questions
    - Detects player, team, course references
    - Routes to correct action
    - Avoids accidental compare_trends triggers
    """

    q = question.lower().strip()

    # ------------------------------------------------------------
    # 1. IDENTITY HANDLER
    # ------------------------------------------------------------
    if any(x in q for x in ["who am i", "my name", "who is me", "what is my name"]):
        return {
            "action": "identity",
            "player": logged_in_player
        }

    # ------------------------------------------------------------
    # 2. PLAYER DETECTION
    # ------------------------------------------------------------
    matched_players = []

    # Pronouns → logged-in player
    if logged_in_player:
        if any(x in q.split() for x in ["me", "my", "i"]):
            matched_players.append(logged_in_player)

    # Explicit player name detection
    for p in players_list:
        # full match
        if p.lower() in q:
            matched_players.append(p)
            continue
    
        # partial match (first name, last name, nickname)
        tokens = p.lower().split()
        if any(t in q for t in tokens):
            matched_players.append(p)

    matched_players = list(dict.fromkeys(matched_players))  # dedupe

    # ------------------------------------------------------------
    # 3. TEAM DETECTION
    # ------------------------------------------------------------
    matched_team = None
    for t in teams_list:
        if t.lower() in q:
            matched_team = t
            break

    # ------------------------------------------------------------
    # 4. COURSE DETECTION
    # ------------------------------------------------------------
    matched_course = None
    for c in courses_list:
        if c.lower() in q:
            matched_course = c
            break

    # ------------------------------------------------------------
    # 5. ACTION ROUTING
    # ------------------------------------------------------------

    # TEAM SUMMARY
    if matched_team and "compare" not in q:
        return {
            "action": "summarize_team",
            "team": matched_team
        }

    # COURSE SUMMARY
    if matched_course and "compare" not in q:
        return {
            "action": "summarize_course",
            "course": matched_course
        }

    # COMPARE PLAYERS
    if ("compare" in q or "vs" in q or "versus" in q) and len(matched_players) == 2:
        return {
            "action": "compare_players",
            "players": matched_players,
            "metric": "ips"
        }

    # COMPARE TRENDS
    if "trend" in q and len(matched_players) == 2:
        return {
            "action": "compare_trends",
            "players": matched_players,
            "metric": "ips",
            "window": 3
        }

    # TRAJECTORY
    if any(x in q for x in ["trajectory", "progress", "improving", "history"]) and len(matched_players) == 1:
        return {
            "action": "plot_trajectory",
            "player": matched_players[0],
            "metric": "ips"
        }

    # PREDICT NEXT
    if any(x in q for x in ["predict", "next round", "next score"]) and len(matched_players) == 1:
        return {
            "action": "predict_next",
            "player": matched_players[0],
            "metric": "ips"
        }

    # PLAYER MONTHLY SCORES (for tables/full year data)
    if any(x in q for x in ["table", "scores", "all my", "entire year", "breakdown", "each round"]) and len(matched_players) == 1:
        return {
            "action": "player_monthly_scores",
            "player": matched_players[0]
        }

    # PLAYER SUMMARY
    if len(matched_players) == 1:
        return {
            "action": "summarize_player",
            "player": matched_players[0]
        }

    # ------------------------------------------------------------
    # 6. FALLBACK
    # ------------------------------------------------------------
    return {
        "action": "unknown",
        "query": question
    }
