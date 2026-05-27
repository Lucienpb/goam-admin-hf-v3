#---------------------------------
# GOAM Rounds Data Structure
#   - Stores all rounds (loaded from JSON) in memory
#   - Tracks position history for position change calculations
#---------------------------------

import pandas as pd

class GOAMRounds:
    """
    Stores all rounds (loaded from JSON) in memory.
    Tracks position history for position change calculations.
    """

    def __init__(self):
        self.rounds = []  # list of DataFrames
        self.previous_positions = {}  # {player_name: last_position}
        self.position_change = {}     # {player_name: delta}

    def add_round(self, df, course_name=None):
        df = df.copy()
        if course_name:
            df["Course"] = course_name
        self.rounds.append(df)

    def get_all_rounds(self):
        if not self.rounds:
            return pd.DataFrame(columns=["Name", "Strokes", "IPS", "Course", "Team"])

        combined = pd.concat(self.rounds, ignore_index=True)

        if "Team" not in combined.columns:
            combined["Team"] = None

        return combined

def update_position_history(self, ips_leaderboard):
    """
    Computes position change relative to the last displayed leaderboard.
    First load → all players show "–".
    Subsequent loads → compare previous vs current positions.
    """

    if ips_leaderboard.empty:
        return

    # Build dict of current positions
    current_positions = {
        row["Name"]: int(row["Position"])
        for _, row in ips_leaderboard.iterrows()
    }

    # FIRST LOAD → no previous positions stored
    if not self.previous_positions:
        self.position_change = {name: None for name in current_positions}
        self.previous_positions = current_positions.copy()
        return

    # Compute deltas
    movement = {}
    for name, new_pos in current_positions.items():
        old_pos = self.previous_positions.get(name)

        if old_pos is None:
            # New player → no previous position
            movement[name] = None
        else:
            movement[name] = old_pos - new_pos  # positive = moved up

    # Store for next comparison
    self.previous_positions = current_positions.copy()
    self.position_change = movement

    def get_position_change(self, name):
        """
        Returns +N, -N, or "–"
        """
        delta = self.position_change.get(name, None)

        if delta is None:
            return "–"
        if delta == 0:
            return "–"
        if delta > 0:
            return f"⬆️{delta}"
        return f"⬇️{abs(delta)}"
