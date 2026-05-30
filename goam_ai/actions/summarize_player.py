def summarize_player(df, player: str):
    pdf = df[df["name"] == player]

    if pdf.empty:
        return {"error": f"No data found for player {player}"}

    latest = pdf.sort_values("date").iloc[-1]

    return {
        "player": player,
        "rounds": len(pdf),
        "latest_ips": float(latest["ips"]),
        "latest_strokes": int(latest["strokes"]),
        "latest_nett": float(latest["nett"]),
        "best_ips": float(pdf["ips"].max()),
        "worst_ips": float(pdf["ips"].min()),
        "avg_ips": float(pdf["ips"].mean()),
    }
