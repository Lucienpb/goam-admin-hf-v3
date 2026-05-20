#######################################
# Data Manager Page (Admin Only)
#######################################
# Allows admins to upload Excel files to update:
# - Course information (course_data.json)
# - Player information (players.json)
# - Pairings information (pairings.json)
# - GOAM Scores (goam_scores.json) with derived fields
# Also allows downloading all JSON data files
#######################################

import streamlit as st
import pandas as pd
import os
from utils.json_utils import load_json, save_json

# -------------------------------------------------------------------
# SAFE HELPERS
# -------------------------------------------------------------------
def safe_str(value):
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    return str(value).strip()


def safe_float(value, default=0.0):
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        s = str(value).strip()
        if s == "":
            return default
        return float(s)
    except Exception:
        return default


def safe_int(value, default=0):
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        s = str(value).strip()
        if s == "":
            return default
        return int(float(s))
    except Exception:
        return default


# -------------------------------------------------------------------
# COURSES SECTION
# -------------------------------------------------------------------
def convert_course_excel_to_json(df: pd.DataFrame):
    required_cols = ["Course Name", "Tee Name", "Slope Rating", "Course Rating", "Par"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in Course_Information.xlsx: {missing}")

    courses = {}

    for _, row in df.iterrows():
        course = safe_str(row.get("Course Name"))
        tee = safe_str(row.get("Tee Name"))

        if not course or not tee:
            continue

        slope = safe_float(row.get("Slope Rating"))
        rating = safe_float(row.get("Course Rating"))
        par = safe_int(row.get("Par"))

        if course not in courses:
            courses[course] = {"tees": {}}

        courses[course]["tees"][tee] = {
            "slope": slope,
            "rating": rating,
            "par": par,
        }

    return courses


def full_load_course_data(df: pd.DataFrame):
    data = convert_course_excel_to_json(df)
    save_json("data/course_data.json", data)


def delta_load_course_data(df: pd.DataFrame):
    existing = load_json("data/course_data.json") or {}
    incoming = convert_course_excel_to_json(df)

    for course, data in incoming.items():
        if course not in existing:
            existing[course] = data
        else:
            existing[course].setdefault("tees", {})
            existing[course]["tees"].update(data["tees"])

    save_json("data/course_data.json", existing)


# -------------------------------------------------------------------
# PLAYERS SECTION
# -------------------------------------------------------------------
def convert_players_excel_to_json(df):
    required_cols = ["Name", "membership_number", "Handicap Index Cap"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in Players.xlsx: {missing}")

    nickname_cols = ["Nick1", "Nick2", "Nick3", "Nick4"]
    for col in nickname_cols:
        if col not in df.columns:
            df[col] = None

    players = []

    for _, row in df.iterrows():
        name = safe_str(row.get("Name"))
        membership = safe_str(row.get("membership_number"))
        handicap_index = safe_float(row.get("Handicap Index Cap"))
        team = safe_str(row.get("Team")) if "Team" in df.columns else None

        if not name or not membership:
            continue

        players.append({
            "name": name,
            "membership": membership,
            "handicap_index": handicap_index,
            "team": team,
            "Nick1": safe_str(row.get("Nick1")),
            "Nick2": safe_str(row.get("Nick2")),
            "Nick3": safe_str(row.get("Nick3")),
            "Nick4": safe_str(row.get("Nick4")),
        })

    return players


def full_load_players(df: pd.DataFrame):
    data = convert_players_excel_to_json(df)
    save_json("data/players.json", data)


def delta_load_players(df: pd.DataFrame):
    existing = load_json("data/players.json") or []
    incoming = convert_players_excel_to_json(df)

    existing_map = {p["membership"]: p for p in existing}

    for p in incoming:
        existing_map[p["membership"]] = p

    merged = list(existing_map.values())
    save_json("data/players.json", merged)


# -------------------------------------------------------------------
# PAIRINGS SECTION
# -------------------------------------------------------------------
def extract_month_and_course(df: pd.DataFrame):
    header_text = safe_str(df.iloc[0, 0])

    if ":" in header_text:
        month_part, _ = header_text.split(":", 1)
        month_key = month_part.strip()
    else:
        month_key = "Unknown"

    if "-" in header_text:
        course = header_text.split("-")[-1].strip()
    else:
        course = "Unknown Course"

    return month_key, course


def convert_pairings_excel_to_json(df: pd.DataFrame):
    month_key, course = extract_month_and_course(df)

    df = df.copy()
    df.columns = ["Fourball", "Player 1", "Player 2", "Player 3", "Player 4"]

    fourballs = []

    for _, row in df.iterrows():
        fb_raw = safe_str(row.get("Fourball"))
        if not fb_raw.isdigit():
            continue

        fb_no = int(fb_raw)
        players = []
        for col in ["Player 1", "Player 2", "Player 3", "Player 4"]:
            name = safe_str(row.get(col))
            if name:
                players.append(name)

        if not players:
            continue

        fourballs.append({
            "fourball": fb_no,
            "players": players,
        })

    return month_key, {
        "course": course,
        "fourballs": fourballs,
    }


def full_load_pairings(df: pd.DataFrame):
    month_key, data = convert_pairings_excel_to_json(df)
    save_json("data/pairings.json", {month_key: data})


def delta_load_pairings(df: pd.DataFrame):
    existing = load_json("data/pairings.json") or {}
    month_key, data = convert_pairings_excel_to_json(df)

    existing[month_key] = data
    save_json("data/pairings.json", existing)


# -------------------------------------------------------------------
# GOAM SCORES SECTION
# -------------------------------------------------------------------
SHEET_MONTH_MAP = {
    "Akasia": "Feb'26",
    "PGC": "Mar'26",
    "Kyalami": "Apr'26",
    "CopperLeaf": "May'26",
    "Services": "Jun'26",
    "July": "Jul'26",
    "August": "Aug'26",
    "September": "Sep'26",
    "October": "Oct'26",
}


def compute_derived_fields(players):
    if not players:
        return {
            "best_gross": None,
            "best_nett": None,
            "ox_nau": None,
            "placements": [],
            "liv_totals": {},
            "pool_winner": None,
            "fines_total": 0,
        }

    best_gross_player = min(players, key=lambda p: p.get("strokes", 9999))
    best_gross = best_gross_player.get("name")

    for p in players:
        hcp = p.get("handicap")
        strokes = p.get("strokes")
        if hcp not in [None, "", 0] and strokes not in [None, ""]:
            try:
                p["nett"] = int(strokes) - int(hcp)
            except Exception:
                p["nett"] = None
        else:
            p["nett"] = None

    nett_players = [p for p in players if p.get("nett") is not None]
    best_nett = min(nett_players, key=lambda p: p["nett"])["name"] if nett_players else None

    ox_nau_player = min(players, key=lambda p: p.get("ips", 9999))
    ox_nau = ox_nau_player.get("name")

    placements_sorted = sorted(players, key=lambda p: p.get("ips", 0), reverse=True)
    placements = [
        {"position": i + 1, "name": p.get("name"), "ips": p.get("ips")}
        for i, p in enumerate(placements_sorted)
    ]

    team_map = {}
    for p in players:
        team = p.get("team", "")
        ips = p.get("ips", 0) or 0
        team_map.setdefault(team, []).append(ips)

    liv_totals = {
        team: sum(sorted(ips_list, reverse=True)[:3])
        for team, ips_list in team_map.items()
        if team
    }

    pool_players = [p for p in players if p.get("pool_payouts")]
    pool_winner = max(pool_players, key=lambda p: p.get("pool_payouts", 0)).get("name") if pool_players else None

    fines_total = sum([p.get("fines", 0) or 0 for p in players])

    return {
        "best_gross": best_gross,
        "best_nett": best_nett,
        "ox_nau": ox_nau,
        "placements": placements,
        "liv_totals": liv_totals,
        "pool_winner": pool_winner,
        "fines_total": fines_total,
    }


def convert_goam_scores_workbook_to_json(xls: dict):
    result = {}

    for sheet_name, df in xls.items():
        if sheet_name not in SHEET_MONTH_MAP:
            continue

        month_key = SHEET_MONTH_MAP[sheet_name]
        course_name = sheet_name

        df = df.copy()
        df.columns = [safe_str(c) for c in df.columns]

        players = []
        for _, row in df.iterrows():
            name = safe_str(row.get("Name"))
            if not name:
                continue

            strokes = safe_int(row.get("Strokes"))
            ips = safe_int(row.get("IPS"))
            team = safe_str(row.get("LIV"))

            player = {
                "name": name,
                "strokes": strokes,
                "ips": ips,
                "team": team,
            }

            for col in ["Handicap", "NP1", "NP2", "LD1", "LD2", "BG", "BN",
                        "Pool Bet", "Pool Payouts", "Fines"]:
                if col in df.columns:
                    key = col.lower().replace(" ", "_")
                    player[key] = safe_int(row.get(col))

            players.append(player)

        derived = compute_derived_fields(players)

        result[month_key] = {
            "course": course_name,
            "players": players,
            **derived,
        }

    return result


def full_load_goam_scores(xls: dict):
    data = convert_goam_scores_workbook_to_json(xls)
    save_json("data/goam_scores.json", data)


def delta_load_goam_scores(xls: dict):
    existing = load_json("data/goam_scores.json") or {}
    incoming = convert_goam_scores_workbook_to_json(xls)

    for month, data in incoming.items():
        existing[month] = data

    save_json("data/goam_scores.json", existing)


# -------------------------------------------------------------------
# MAIN PAGE
# -------------------------------------------------------------------
def show_data_manager_page():
    st.title("📂 Data Manager (Admin Only)")

    # ---------------- COURSES ----------------
    st.subheader("📘 Course Information")
    uploaded = st.file_uploader("Upload Course_Information.xlsx", type=["xlsx"])
    mode = st.radio("Load Mode", ["FULL", "DELTA"])

    if st.button("Process Course Data"):
        if not uploaded:
            st.error("Please upload Course_Information.xlsx.")
        else:
            try:
                df = pd.read_excel(uploaded)
                if mode == "FULL":
                    full_load_course_data(df)
                    st.success("Course data fully replaced.")
                else:
                    delta_load_course_data(df)
                    st.success("Course data merged (delta load).")
            except Exception as e:
                st.error(f"Error processing course data: {e}")

    st.markdown("---")

    # ---------------- PLAYERS ----------------
    st.subheader("👥 Players")
    uploaded_players = st.file_uploader("Upload Players.xlsx", type=["xlsx"], key="players_upload")
    mode_players = st.radio("Load Mode (Players)", ["FULL", "DELTA"], key="players_mode")

    if st.button("Process Player Data"):
        if not uploaded_players:
            st.error("Please upload Players.xlsx.")
        else:
            try:
                df = pd.read_excel(uploaded_players)
                if mode_players == "FULL":
                    full_load_players(df)
                    st.success("Players fully replaced.")
                else:
                    delta_load_players(df)
                    st.success("Players merged (delta load).")
            except Exception as e:
                st.error(f"Error processing player data: {e}")

    st.markdown("---")

    # ---------------- PAIRINGS ----------------
    st.subheader("⛳ Pairings (GOAM 4-Ball)")
    uploaded_pairings = st.file_uploader("Upload Pairings.xlsx", type=["xlsx"], key="pairings_upload")
    mode_pairings = st.radio("Load Mode (Pairings)", ["FULL", "DELTA"], key="pairings_mode")

    if st.button("Process Pairing Data"):
        if not uploaded_pairings:
            st.error("Please upload Pairings.xlsx.")
        else:
            try:
                df = pd.read_excel(uploaded_pairings, header=0)
                if mode_pairings == "FULL":
                    full_load_pairings(df)
                    st.success("Pairings fully replaced.")
                else:
                    delta_load_pairings(df)
                    st.success("Pairings merged (delta load).")
            except Exception as e:
                st.error(f"Error processing pairing data: {e}")

    st.markdown("---")

    # ---------------- GOAM SCORES ----------------
    st.subheader("📘 GOAM Scores 2026 (with derived fields)")
    uploaded_scores = st.file_uploader(
        "Upload GOAM_Scores_2026_upload.xlsx",
        type=["xlsx"],
        key="goam_scores_upload",
    )
    mode_scores = st.radio("Load Mode (GOAM Scores)", ["FULL", "DELTA"], key="goam_scores_mode")

    if st.button("Process GOAM Scores 2026"):
        if not uploaded_scores:
            st.error("Please upload the GOAM_Scores_2026_upload.xlsx workbook.")
        else:
            try:
                xls = pd.read_excel(uploaded_scores, sheet_name=None)
                if mode_scores == "FULL":
                    full_load_goam_scores(xls)
                    st.success("GOAM scores fully replaced for 2026.")
                else:
                    delta_load_goam_scores(xls)
                    st.success("GOAM scores merged (delta load).")
            except Exception as e:
                st.error(f"Error processing GOAM scores: {e}")

    st.markdown("---")

    # ---------------- DOWNLOAD SECTION ----------------
    st.subheader("⬇️ Download Data Files (CSV Format)")

    data_files = {
        "Course Data": "data/course_data.json",
        "Players": "data/players.json",
        "Pairings": "data/pairings.json",
        "GOAM Scores": "data/goam_scores.json",
    }

    for label, path in data_files.items():
        if os.path.exists(path):
            try:
                # Load JSON
                data = load_json(path)

                # Convert to DataFrame depending on structure
                if isinstance(data, dict):
                    # Pairings, Courses, GOAM Scores
                    df = pd.json_normalize(data, sep="_")
                elif isinstance(data, list):
                    # Players
                    df = pd.DataFrame(data)
                else:
                    st.warning(f"Unsupported format in {label}")
                    continue

                # Convert to CSV bytes
                csv_bytes = df.to_csv(index=False).encode("utf-8")

                st.download_button(
                    label=f"Download {label} (CSV)",
                    data=csv_bytes,
                    file_name=f"{label.replace(' ', '_').lower()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

            except Exception as e:
                st.error(f"Error converting {label} to CSV: {e}")

        else:
            st.warning(f"{label} file not found: {path}")
