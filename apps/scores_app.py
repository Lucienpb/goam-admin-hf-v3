#---------------------------------
# GOAM Scores & Rounds App (SPLIT VERSION)
#   - Leaderboards page
#   - Scorecards page
#---------------------------------

import os
import streamlit as st
import pandas as pd

from backend.goam_loader import GOAMLoader
from backend.goam_rounds import GOAMRounds
from backend.goam_calculator import GOAMCalculator
from utils.json_utils import load_json, save_json


# ---------------------------------------------------------
# INTERNAL STATE
# ---------------------------------------------------------
def _get_rounds_state():
    if "goam_rounds" not in st.session_state:
        st.session_state.goam_rounds = GOAMRounds()
    return st.session_state.goam_rounds


def _format_pos_change(delta):
    if delta is None:
        return "–"
    try:
        d = int(delta)
    except (TypeError, ValueError):
        return "–"

    if d > 0:
        return f"⬆️ {d}"
    if d < 0:
        return f"⬇️ {abs(d)}"
    return "➡️"


def _to_int_or_none(value):
    try:
        if value is None:
            return None
        s = str(value).strip()
        if s == "":
            return None
        return int(float(s))
    except Exception:
        return None


# ---------------------------------------------------------
# LOAD + PREPARE DATA (shared by both pages)
# ---------------------------------------------------------
def _load_scores():
    rounds = _get_rounds_state()

    try:
        goam_scores = GOAMLoader.load_json_scores("data/goam_scores.json")
        season_rounds = GOAMCalculator.build_from_json(goam_scores)
        # --- ADD ROUND NUMBERS ---
        season_rounds = season_rounds.sort_values(["Course"]).reset_index(drop=True)
        season_rounds["Round"] = season_rounds.groupby(["Course"]).ngroup() + 1


        if not season_rounds.empty:
            # Reset stored rounds
            rounds.rounds = []
            
            for rnd in sorted(season_rounds["Round"].unique()):
                df_round = season_rounds[season_rounds["Round"] == rnd]
                leaderboard = GOAMCalculator.build_ips_leaderboard(df_round)
                rounds.update_position_history(leaderboard)
                rounds.rounds.append(df_round)
        else:
            return None, None, "No GOAM scores found. Load data via Data Manager."

    except Exception as e:
        return None, None, f"Error loading GOAM scores: {e}"

    all_rounds_df = rounds.get_all_rounds()
    if all_rounds_df.empty:
        return None, None, "No rounds available."

    return rounds, all_rounds_df, None


# ---------------------------------------------------------
# PAGE 1 — LEADERBOARDS
# ---------------------------------------------------------
def show_leaderboards():
    st.header("📘 GOAM Scores & Rounds — Leaderboards")

    rounds, all_rounds_df, error = _load_scores()
 
    if error:
        st.error(error)
        return

    # Course selection
    st.subheader("🎯 Select courses to include in leaderboards")

    all_courses = GOAMCalculator.list_courses(all_rounds_df)
    active_courses = GOAMCalculator.get_active_courses(all_rounds_df)

    selected_courses = st.multiselect(
        "Only include these courses:",
        all_courses,
        default=active_courses
    )

    filtered_df = all_rounds_df[all_rounds_df["Course"].isin(selected_courses)]

    # Leaderboard calculations
    ips_table = GOAMCalculator.build_ips_leaderboard(filtered_df)
    strokes_table = GOAMCalculator.build_strokes_leaderboard(filtered_df)
    liv_table = GOAMCalculator.build_liv_leaderboard(filtered_df)

    if ips_table.empty:
        st.info("No IPS data available for selected courses.")
        return

    ips_table.rename(columns={c: c.strip() for c in ips_table.columns}, inplace=True)

    if "Position" not in ips_table.columns:
        if "IPS" in ips_table.columns:
            ips_table["Position"] = (
                ips_table["IPS"]
                .rank(ascending=False, method="min")
                .astype(int)
            )
        else:
            st.error("IPS column missing from IPS leaderboard.")
            return

    # 🔥 HERE: calculate position change inside GOAMRounds
    rounds.update_position_history(ips_table)

    ips_table = ips_table.copy()

    # Position Movement column
    movement = GOAMCalculator.calculate_position_movement(filtered_df)
    if movement and "Name" in ips_table.columns:
        ips_table.insert(2, "Pos. Mov.", ips_table["Name"].map(movement).fillna("–"))

    # Drop internal Position column before display
    display_table = ips_table.drop(columns=["Position"])

    # Leaderboard selector
    st.subheader("🏆 Leaderboards")

    leaderboard_choice = st.selectbox(
        "Select leaderboard:",
        ["IPS", "Strokes", "LIV"],
        index=0
    )

    if leaderboard_choice == "IPS":
        st.subheader("🏆 IPS Leaderboard (Best 6 + Course Breakdown)")
        st.dataframe(display_table, hide_index=True, use_container_width=True)
    elif leaderboard_choice == "Strokes":
        st.subheader("⛳ Strokes Leaderboard (Best 6 Over Par)")
        st.dataframe(strokes_table, hide_index=True, use_container_width=True)
    elif leaderboard_choice == "LIV":
        st.subheader("🏁 LIV Team Leaderboard (Top 3 IPS per Course)")
        st.dataframe(liv_table, hide_index=True, use_container_width=True)


# ---------------------------------------------------------
# PAGE 2 — SCORECARDS
# ---------------------------------------------------------
def show_scorecards():
    st.header("📂 GOAM Scorecards")

    rounds, all_rounds_df, error = _load_scores()
    if error:
        st.error(error)
        return

    # Build course sheets
    course_sheets = GOAMCalculator.split_by_course(all_rounds_df)

    st.subheader("📄 View Score Cards")

    options = ["None"] + list(course_sheets.keys())
    choice = st.selectbox("Select Course", options)

    if choice in course_sheets:
        st.dataframe(course_sheets[choice], hide_index=True, use_container_width=True)

    st.subheader("🧾 Scorecard from 4-Ball Generator")
    generated_scorecard = load_json("data/generated_scorecard.json")

    if isinstance(generated_scorecard, dict):
        generated_rows = generated_scorecard.get("scorecard", [])
        generated_month_key = str(generated_scorecard.get("month_key", "")).strip()
        generated_course_name = str(generated_scorecard.get("course", "")).strip()
    else:
        generated_rows = []
        generated_month_key = ""
        generated_course_name = ""

    if generated_rows:
        generated_df = pd.DataFrame(generated_rows)

        month_key = st.text_input(
            "Month key for this generated scorecard",
            value=generated_month_key,
            key="generated_scorecard_month_key",
            help="Example: Jul'26",
        )
        course_name = st.text_input(
            "Course name for this generated scorecard",
            value=generated_course_name,
            key="generated_scorecard_course_name",
        )

        edited_generated_df = st.data_editor(
            generated_df,
            hide_index=True,
            use_container_width=True,
            num_rows="fixed",
            disabled=["Fourball"],
            key="generated_scorecard_editor",
        )

        generated_df = edited_generated_df

        if st.button("Save generated scorecard edits"):
            cleaned_rows = edited_generated_df.fillna("").to_dict(orient="records")
            save_json(
                "data/generated_scorecard.json",
                {
                    "month_key": month_key,
                    "course": course_name,
                    "scorecard": cleaned_rows,
                },
            )
            st.success("Generated scorecard updated.")

        if st.button("Publish generated scorecard to GOAM scores"):
            month_key_clean = month_key.strip()
            course_name_clean = course_name.strip()

            if not month_key_clean:
                st.error("Month key is required before publishing.")
            elif not course_name_clean:
                st.error("Course name is required before publishing.")
            else:
                records = edited_generated_df.fillna("").to_dict(orient="records")
                invalid_rows = []
                players = []

                optional_map = {
                    "Handicap": "handicap",
                    "NP1": "np1",
                    "NP2": "np2",
                    "LD1": "ld1",
                    "LD2": "ld2",
                    "BG": "bg",
                    "BN": "bn",
                    "Pool Bet": "pool_bet",
                    "Pool Payouts": "pool_payouts",
                    "Fines": "fines",
                }

                for idx, row in enumerate(records, 1):
                    name = str(row.get("Name", "")).strip()
                    if not name:
                        continue

                    strokes = _to_int_or_none(row.get("Strokes"))
                    ips = _to_int_or_none(row.get("IPS"))

                    if strokes is None or ips is None:
                        invalid_rows.append(idx)
                        continue

                    player = {
                        "name": name,
                        "strokes": strokes,
                        "ips": ips,
                        "team": str(row.get("LIV", "")).strip(),
                    }

                    for source_col, target_key in optional_map.items():
                        value = _to_int_or_none(row.get(source_col))
                        if value is not None:
                            player[target_key] = value

                    players.append(player)

                if invalid_rows:
                    st.error(
                        "Strokes and IPS must be numeric for all players before publish. "
                        f"Invalid rows: {invalid_rows}"
                    )
                elif not players:
                    st.error("No valid player rows found to publish.")
                else:
                    goam_scores = load_json("data/goam_scores.json")
                    if not isinstance(goam_scores, dict):
                        goam_scores = {}

                    goam_scores[month_key_clean] = {
                        "course": course_name_clean,
                        "players": players,
                    }

                    save_json("data/goam_scores.json", goam_scores)
                    save_json(
                        "data/generated_scorecard.json",
                        {
                            "month_key": month_key_clean,
                            "course": course_name_clean,
                            "scorecard": records,
                        },
                    )
                    st.success(
                        f"Published generated scorecard to data/goam_scores.json under {month_key_clean}."
                    )
                    st.rerun()
    else:
        st.info("No generated scorecard found yet. Create one in 4-Ball Generation first.")

    # Export workbook
    st.subheader("💾 Export updated GOAM workbook")

    ips_table = GOAMCalculator.build_ips_leaderboard(all_rounds_df)
    strokes_table = GOAMCalculator.build_strokes_leaderboard(all_rounds_df)
    liv_table = GOAMCalculator.build_liv_leaderboard(all_rounds_df)

    output_file = GOAMCalculator.generate_output_filename()
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", output_file)

    with pd.ExcelWriter(output_path) as writer:
        ips_table.to_excel(writer, sheet_name="IPS", index=False)
        strokes_table.to_excel(writer, sheet_name="Strokes", index=False)
        liv_table.to_excel(writer, sheet_name="LIV", index=False)

        if generated_rows:
            generated_df.to_excel(writer, sheet_name="GeneratedScorecard", index=False)

        for course, df in course_sheets.items():
            df.to_excel(writer, sheet_name=course, index=False)

    with open(output_path, "rb") as f:
        st.download_button(
            label=f"Download {output_file}",
            data=f.read(),
            file_name=output_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


# ---------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------
def run_scores_app(mode="leaderboards"):
    if mode == "leaderboards":
        show_leaderboards()

    elif mode == "scorecards":
        show_scorecards()

    else:
        st.error("Invalid mode for run_scores_app()")
