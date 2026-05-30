def summarize_course(df, course: str):
    cdf = df[df["course"].str.lower() == course.lower()]

    if cdf.empty:
        return {"error": f"No rounds found at {course}"}

    return {
        "course": course,
        "rounds": len(cdf),
        "avg_ips": float(cdf["ips"].mean()),
        "best_ips": float(cdf["ips"].max()),
        "worst_ips": float(cdf["ips"].min()),
        "players": sorted(cdf["name"].unique().tolist()),
    }
