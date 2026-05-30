import pandas as pd

def plot_trajectory(df, player: str, metric="ips", rounds=None):
    pdf = df[df["name"] == player].sort_values("date")

    if pdf.empty:
        return {"error": f"No data for {player}"}

    if rounds:
        pdf = pdf.tail(rounds)

    return {
        "player": player,
        "metric": metric,
        "dates": pdf["date"].astype(str).tolist(),
        "values": [float(v) for v in pdf[metric].tolist()],
    }
