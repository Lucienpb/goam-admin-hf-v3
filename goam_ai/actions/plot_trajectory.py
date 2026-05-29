import pandas as pd

def plot_trajectory(df: pd.DataFrame, player: str, metric: str, rounds: int | None = None):
    if metric not in df.columns:
        raise ValueError(f"Unknown metric: {metric}")

    data = df[df["player"] == player].copy()
    if data.empty:
        raise ValueError(f"No data for player: {player}")

    data = data.sort_values("month")  # months are strings like "Feb'26"
    if rounds:
        data = data.tail(rounds)

    return data[["month", metric]]
