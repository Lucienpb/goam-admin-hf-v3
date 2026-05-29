from goam_ai.actions import (
    compare_players,
    plot_trajectory,
    compare_trends,
    predict_next,
)

def dispatch(df, instruction: dict):
    action = instruction.get("action")

    if action == "compare_players":
        return compare_players(
            df=df,
            players=instruction.get("players", []),
            metric=instruction.get("metric", "ips"),
        )

    if action == "plot_trajectory":
        return plot_trajectory(
            df=df,
            player=instruction.get("player", ""),
            metric=instruction.get("metric", "ips"),
            rounds=instruction.get("rounds"),
        )

    if action == "compare_trends":
        return compare_trends(
            df=df,
            players=instruction.get("players", []),
            metric=instruction.get("metric", "ips"),
            window=instruction.get("window", 3),
        )

    if action == "predict_next":
        return predict_next(
            df=df,
            player=instruction.get("player", ""),
            metric=instruction.get("metric", "ips"),
            window=instruction.get("window", 3),
        )

    return {"error": f"Unknown action: {action}"}
