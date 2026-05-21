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
        Called AFTER the IPS leaderboard is built.
        Leaderboard MUST contain a 'Position' column.
        """

        if ips_leaderboard.empty:
            return

        # Build dict of current positions
        current_positions = {
            row["Name"]: row["Position"]
            for _, row in ips_leaderboard.iterrows()
        }

        # Compute position change
        self.position_change = {}
        for name, new_pos in current_positions.items():
            old_pos = self.previous_positions.get(name, new_pos)
            delta = old_pos - new_pos  # positive = moved up
            self.position_change[name] = delta

        # Store new positions for next comparison
        self.previous_positions = current_positions.copy()

    def get_position_change(self, name):
        """
        Returns +N, -N, or "–"
        """
        if name not in self.position_change:
            return "–"

        delta = self.position_change[name]

        if delta == 0:
            return "–"
        elif delta > 0:
            return f"+{delta}"
        else:
            return str(delta)
