import pandas as pd

def compare_players(df: pd.DataFrame, players: list[str], metric: str) -> dict:
    if len(players) != 2:
        return {"error": "compare_players requires exactly two players"}

    p1, p2 = players

    if metric not in df.columns:
        return {"error": f"Unknown metric: {metric}"}

    d1 = df[df["player"] == p1][metric]
    d2 = df[df["player"] == p2][metric]

    if d1.empty or d2.empty:
        return {"error": "No data for one or both players"}

    return {
        "action": "compare_players",
        "metric": metric,
        "player_1": p1,
        "player_2": p2,
        "player_1_avg": float(d1.mean()),
        "player_2_avg": float(d2.mean()),
        "difference": float(d1.mean() - d2.mean()),
    }
