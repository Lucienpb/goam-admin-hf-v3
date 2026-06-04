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
from utils.aggrid_helper import show_aggrid


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
        # Only show movement against first player in each tied group
        seen_positions = set()
        pos_movement = []
        for _, row in ips_table.iterrows():
            pos = row["Position"]
            if pos not in seen_positions:
                seen_positions.add(pos)
                pos_movement.append(movement.get(row["Name"], "–"))
            else:
                pos_movement.append("")
        ips_table.insert(2, "Pos Movement", pos_movement)

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
        from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
        gb = GridOptionsBuilder.from_dataframe(display_table)
        gb.configure_default_column(resizable=True, minWidth=60)
        gb.configure_column("Pos", headerName="Pos", minWidth=55, maxWidth=70)
        gb.configure_column("Name", headerName="Name", minWidth=150)
        gb.configure_column("Pos Movement", headerName="Pos Movement", minWidth=110, maxWidth=130)
        gb.configure_column("IPS", headerName="IPS", minWidth=60, maxWidth=80)
        gb.configure_column("Best6_IPS", headerName="Best 6", minWidth=70, maxWidth=90)
        gb.configure_column("Rounds_Played", headerName="Rounds", minWidth=70, maxWidth=90)
        gb.configure_grid_options(domLayout="autoHeight")
        grid_options = gb.build()
        AgGrid(
            display_table,
            gridOptions=grid_options,
            columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
            theme="streamlit",
            height=600,
            use_container_width=True,
        )
    elif leaderboard_choice == "Strokes":
        st.subheader("⛳ Strokes Leaderboard (Best 6 Over Par)")
        show_aggrid(strokes_table)
    elif leaderboard_choice == "LIV":
        st.subheader("🏁 LIV Team Leaderboard (Top 3 IPS per Course)")
        show_aggrid(liv_table)


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
        show_aggrid(course_sheets[choice])

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
