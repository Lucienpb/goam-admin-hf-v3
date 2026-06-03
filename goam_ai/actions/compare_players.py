def compare_players(df, players: list, metric="ips"):
    if len(players) != 2:
        return {"error": "compare_players requires exactly 2 players"}

    p1, p2 = players
    d1 = df[df["player"] == p1]
    d2 = df[df["player"] == p2]

    if d1.empty or d2.empty:
        return {"error": "One or both players have no data"}

    p1_avg = float(d1[metric].mean())
    p2_avg = float(d2[metric].mean())
    
    # Determine winner (higher is better for IPS, lower is better for strokes)
    if metric == "ips":
        p1_better = p1_avg > p2_avg
        comparison_text = f"{p1} has {p1_avg:.1f} IPS, {p2} has {p2_avg:.1f} IPS. {'HIGHER IPS IS BETTER' if p1_better else 'BUT'} {p1 if p1_better else p2} performs better."
    else:  # strokes - lower is better
        p1_better = p1_avg < p2_avg
        comparison_text = f"{p1} has {p1_avg:.1f} strokes, {p2} has {p2_avg:.1f} strokes. LOWER IS BETTER. {p1 if p1_better else p2} performs better."

    return {
        "players": players,
        "metric": metric,
        "p1_name": p1,
        "p2_name": p2,
        "p1_avg": p1_avg,
        "p2_avg": p2_avg,
        "p1_best": float(d1[metric].max()),
        "p2_best": float(d2[metric].max()),
        "p1_worst": float(d1[metric].min()),
        "p2_worst": float(d2[metric].min()),
        "winner": p1 if p1_better else p2,
        "comparison_summary": comparison_text
    }

