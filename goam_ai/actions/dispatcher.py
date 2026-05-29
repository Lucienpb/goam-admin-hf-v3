import pandas as pd
from goam_ai.actions import (
    compare_players,
    plot_trajectory,
    compare_trends,
    predict_next,
)

def dispatch(df: pd.DataFrame, instruction: dict):
    action = instruction.get("action")

    if action == "compare_players":
        return compare_players(
            df=df,
            players=instruction.get("players", []),
            metric=instruction.get("metric", "IPS"),
        )

    if action == "plot_trajectory":
        return plot_trajectory(
            df=df,
            player=instruction.get("player", ""),
            metric=instruction.get("metric", "IPS"),
            rounds=instruction.get("rounds"),
        )

    if action == "compare_trends":
        return compare_trends(
            df=df,
            players=instruction.get("players", []),
            metric=instruction.get("metric", "IPS"),
            window=instruction.get("window", 5),
        )

    if action == "predict_next":
        return predict_next(
            df=df,
            player=instruction.get("player", ""),
            metric=instruction.get("metric", "IPS"),
            window=instruction.get("window", 5),
        )

    return {"error": f"Unknown action: {action}"}
