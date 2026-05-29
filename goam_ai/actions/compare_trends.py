import pandas as pd
import numpy as np

def _slope(series: pd.Series) -> float:
    if len(series) < 2:
        return 0.0
    x = np.arange(len(series))
    y = series.values
    # simple linear regression slope
    A = np.vstack([x, np.ones(len(x))]).T
    m, _ = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(m)

def compare_trends(df: pd.DataFrame, players: list[str], metric: str, window: int = 5) -> dict:
    if len(players) != 2:
        return {"error": "compare_trends requires exactly two players"}

    p1, p2 = players
    if metric not in df.columns:
        return {"error": f"Unknown metric: {metric}"}

    result = {"action": "compare_trends", "metric": metric, "window": window}

    trends = {}
    for p in players:
        data = df[df["player"] == p].copy()
        if "date" in data.columns:
            data = data.sort_values("date")
        series = data[metric].tail(window)
        trends[p] = _slope(series) if not series.empty else 0.0

    result["trends"] = trends
    # lower slope might mean improving if metric is "score" (downwards)
    improving = min(trends, key=trends.get)
    result["most_improving_player"] = improving

    return result
