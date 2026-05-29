import pandas as pd

def predict_next(df: pd.DataFrame, player: str, metric: str, window: int = 3):
    data = df[df["player"] == player].sort_values("month")
    series = data[metric].tail(window)

    if series.empty:
        return {"error": "Not enough data"}

    prediction = float(series.mean())

    return {
        "action": "predict_next",
        "player": player,
        "metric": metric,
        "predicted_value": prediction,
    }
