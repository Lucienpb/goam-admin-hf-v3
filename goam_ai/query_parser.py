import streamlit as st

# ------------------------------------------------------------
# PLAYER DETECTION (full names, nicknames, logged-in user)
# ------------------------------------------------------------
def extract_players(question: str):
    q = f" {question.lower()} "
    matched = []

    if "players" not in st.session_state:
        return matched

    players_data = st.session_state["players"]

    # Logged-in user
    logged_email = st.session_state.get("email", "").lower()
    logged_player = None

    for p in players_data:
        if p.get("email", "").lower() == logged_email:
            logged_player = p.get("name")
            break

    # Pronoun-based self reference
    if logged_player:
        if any(w in q for w in [" me ", " my ", " myself ", " i "]):
            matched.append(logged_player)

    # Explicit names / nicknames
    for p in players_data:
        full = p.get("name", "")
        nicks = [
            p.get("Nick1", ""),
            p.get("Nick2", ""),
            p.get("Nick3", ""),
            p.get("Nick4", "")
        ]

        tokens = [full.lower()] + [n.lower() for n in nicks if n]

        if any(t and t in q for t in tokens):
            if full not in matched:
                matched.append(full)

    return matched


# ------------------------------------------------------------
# TEAM DETECTION
# ------------------------------------------------------------
def extract_team(question: str):
    q = question.lower()

    if "players" not in st.session_state:
        return None

    teams = set(p.get("team", "") for p in st.session_state["players"])
    teams = [t for t in teams if t]

    for t in teams:
        if t.lower() in q:
            return t

    return None


# ------------------------------------------------------------
# COURSE DETECTION
# ------------------------------------------------------------
def extract_course(question: str):
    q = question.lower()

    known_courses = [
        "akasia",
        "pgc",
        "kyalami",
        "copperleaf",
        "silver lakes",
        "centurion",
        "services",
    ]

    for c in known_courses:
        if c.lower() in q:
            return c.title()

    return None


# ------------------------------------------------------------
# MAIN PARSER
# ------------------------------------------------------------
def parse_query(question: str):
    q = question.lower()
    # --------------------------------------------------------
    # IDENTITY QUESTIONS ("Who am I", "What is my name")
    # --------------------------------------------------------
    if any(phrase in q for phrase in ["who am i", "what is my name", "who is logged in"]):
        logged_email = st.session_state.get("email", "").lower()
        players = st.session_state.get("players", [])

        for p in players:
            if p.get("email", "").lower() == logged_email:
                return {
                    "action": "identity",
                    "player": p.get("name")
                }

        return {
            "action": "identity",
            "player": None
        }

    players = extract_players(question)
    team = extract_team(question)
    course = extract_course(question)

    # --------------------------------------------------------
    # 1. Compare trends (ONLY if exactly 2 players)
    # --------------------------------------------------------
    if ("compare" in q or " vs " in q or " versus " in q) and len(players) == 2:
        return {
            "action": "compare_trends",
            "players": players,
            "team": team,
            "course": course,
        }

    # --------------------------------------------------------
    # 2. Single-player trend / trajectory
    # --------------------------------------------------------
    if any(w in q for w in ["trend", "trajectory", "improving", "progress"]):
        if len(players) == 1:
            return {
                "action": "plot_trajectory",
                "player": players[0],
                "team": team,
                "course": course,
            }

    # --------------------------------------------------------
    # 3. Team summary
    # --------------------------------------------------------
    if team:
        return {
            "action": "summarize_team",
            "team": team,
            "course": course,
        }

    # --------------------------------------------------------
    # 4. Course summary
    # --------------------------------------------------------
    if course:
        return {
            "action": "summarize_course",
            "course": course,
        }

    # --------------------------------------------------------
    # 5. Single-player summary
    # --------------------------------------------------------
    if len(players) == 1:
        return {
            "action": "summarize_player",
            "player": players[0],
            "team": team,
            "course": course,
        }

    # --------------------------------------------------------
    # 6. Fallback
    # --------------------------------------------------------
    return {
        "action": "general_question",
        "query": question,
    }

