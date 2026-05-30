def compare_players(df, players: list, metric="ips"):
    if len(players) != 2:
        return {"error": "compare_players requires exactly 2 players"}

    p1, p2 = players
    d1 = df[df["player"] == p1]
    d2 = df[df["player"] == p2]

    if d1.empty or d2.empty:
        return {"error": "One or both players have no data"}

    return {
        "players": players,
        "metric": metric,
        "p1_avg": float(d1[metric].mean()),
        "p2_avg": float(d2[metric].mean()),
        "p1_best": float(d1[metric].max()),
        "p2_best": float(d2[metric].max()),
        "p1_worst": float(d1[metric].min()),
        "p2_worst": float(d2[metric].min()),
    }
