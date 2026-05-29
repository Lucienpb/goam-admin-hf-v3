import pandas as pd

def plot_trajectory(df: pd.DataFrame, player: str, metric: str, rounds: int | None = None) -> pd.DataFrame:
    if metric not in df.columns:
        raise ValueError(f"Unknown metric: {metric}")

    data = df[df["player"] == player].copy()
    if data.empty:
        raise ValueError(f"No data for player: {player}")

    data = data.sort_values("date") if "date" in data.columns else data
    if rounds:
        data = data.tail(rounds)

    # Ensure an index suitable for plotting
    data = data.reset_index(drop=True)
    return data[["date", metric]] if "date" in data.columns else data[[metric]]
