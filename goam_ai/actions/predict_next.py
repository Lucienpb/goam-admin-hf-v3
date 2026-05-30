import pandas as pd

def predict_next(df, player: str, metric="ips", window=3):
    pdf = df[df["name"] == player].sort_values("date")

    if len(pdf) < window:
        return {"error": "Not enough rounds to predict"}

    recent = pdf[metric].tail(window).mean()

    return {
        "player": player,
        "metric": metric,
        "window": window,
        "predicted_next": float(recent),
    }
