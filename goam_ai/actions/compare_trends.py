import numpy as np
import pandas as pd

def _slope(series: pd.Series) -> float:
    if len(series) < 2:
        return 0.0
    x = np.arange(len(series))
    y = series.values
    A = np.vstack([x, np.ones(len(x))]).T
    m, _ = np.linalg.lstsq(A, y, rcond=None)[0]
    return float(m)

def compare_trends(df: pd.DataFrame, players: list[str], metric: str, window: int = 3):
    if len(players) != 2:
        return {"error": "compare_trends requires exactly two players"}

    p1, p2 = players

    result = {"action": "compare_trends", "metric": metric}

    trends = {}
    for p in players:
        data = df[df["player"] == p].sort_values("month")
        series = data[metric].tail(window)
        trends[p] = _slope(series) if not series.empty else 0.0

    result["trends"] = trends
    result["most_improving"] = min(trends, key=trends.get)  # lower IPS slope = improving

    return result
