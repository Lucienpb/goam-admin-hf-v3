from goam_ai.actions import (
    compare_players,
    plot_trajectory,
    compare_trends,
    predict_next,
    summarize_player,
    summarize_team,
    summarize_course,
)

def dispatch(df, instruction: dict):
    action = instruction.get("action")

    # --------------------------------------------------------
    # IDENTITY HANDLER ("Who am I")
    # --------------------------------------------------------
    if action == "identity":
        player = instruction.get("player")
        if player:
            return {"text": f"You are {player}."}
        else:
            return {"text": "I couldn't match your login to a GOAM player."}

    # --------------------------------------------------------
    # PLAYER SUMMARY
    # --------------------------------------------------------
    if action == "summarize_player":
        return summarize_player(
            df=df,
            player=instruction.get("player", "")
        )

    # --------------------------------------------------------
    # TEAM SUMMARY
    # --------------------------------------------------------
    if action == "summarize_team":
        return summarize_team(
            df=df,
            team=instruction.get("team", "")
        )

    # --------------------------------------------------------
    # COURSE SUMMARY
    # --------------------------------------------------------
    if action == "summarize_course":
        return summarize_course(
            df=df,
            course=instruction.get("course", "")
        )

    # --------------------------------------------------------
    # COMPARE PLAYERS
    # --------------------------------------------------------
    if action == "compare_players":
        return compare_players(
            df=df,
            players=instruction.get("players", []),
            metric=instruction.get("metric", "ips"),
        )

    # --------------------------------------------------------
    # TRAJECTORY
    # --------------------------------------------------------
    if action == "plot_trajectory":
        return plot_trajectory(
            df=df,
            player=instruction.get("player", ""),
            metric=instruction.get("metric", "ips"),
            rounds=instruction.get("rounds"),
        )

    # --------------------------------------------------------
    # COMPARE TRENDS
    # --------------------------------------------------------
    if action == "compare_trends":
        return compare_trends(
            df=df,
            players=instruction.get("players", []),
            metric=instruction.get("metric", "ips"),
            window=instruction.get("window", 3),
        )

    # --------------------------------------------------------
    # PREDICT NEXT ROUND
    # --------------------------------------------------------
    if action == "predict_next":
        return predict_next(
            df=df,
            player=instruction.get("player", ""),
            metric=instruction.get("metric", "ips"),
            window=instruction.get("window", 3),
        )

    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------
    return {"error": f"Unknown action: {action}"}
