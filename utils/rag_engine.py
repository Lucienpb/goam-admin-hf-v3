# utils/rag_engine.py
from pathlib import Path
from typing import List, Dict, Tuple

import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.json_utils import load_json

DATA_DIR = Path("data")


def _load_goam_data() -> Dict[str, pd.DataFrame]:
    scores = load_json(DATA_DIR / "goam_scores.json")
    players = load_json(DATA_DIR / "players.json")
    pairings = load_json(DATA_DIR / "pairings.json")
    courses = load_json(DATA_DIR / "course_data.json")

    # Scores
    score_rows = []
    for month, data in scores.items():
        for p in data.get("players", []):
            score_rows.append({
                "type": "score",
                "month": month,
                "course": data.get("course"),
                "name": p.get("name"),
                "strokes": p.get("strokes"),
                "nett": p.get("nett"),
                "ips": p.get("ips"),
                "team": p.get("team"),
            })
    scores_df = pd.DataFrame(score_rows)

    # Players
    players_df = pd.DataFrame(players)

    # Pairings
    pairing_rows = []
    for month, data in pairings.items():
        for fb in data.get("fourballs", []):
            pairing_rows.append({
                "type": "pairing",
                "month": month,
                "course": data.get("course"),
                "fourball": fb.get("fourball"),
                "players": ", ".join(fb.get("players", [])),
            })
    pairings_df = pd.DataFrame(pairing_rows)

    # Courses
    course_rows = []
    for course_name, info in courses.items():
        for tee_name, tee in info.get("tees", {}).items():
            course_rows.append({
                "type": "course",
                "course": course_name,
                "tee": tee_name,
                "slope": tee.get("slope"),
                "rating": tee.get("rating"),
                "par": tee.get("par"),
            })
    courses_df = pd.DataFrame(course_rows)

    return {
        "scores": scores_df,
        "players": players_df,
        "pairings": pairings_df,
        "courses": courses_df,
    }


def _build_documents(data: Dict[str, pd.DataFrame]) -> List[Dict]:
    docs = []

    for _, row in data["scores"].iterrows():
        docs.append({
            "text": (
                f"{row['name']} scored IPS {row['ips']} at {row['course']} "
                f"in {row['month']} (strokes {row['strokes']}, nett {row['nett']})."
            ),
            "meta": row.to_dict()
        })

    for _, row in data["players"].iterrows():
        docs.append({
            "text": (
                f"Player {row.get('name')} with handicap {row.get('handicap_index')} "
                f"and team {row.get('team')}."
            ),
            "meta": row.to_dict()
        })

    for _, row in data["pairings"].iterrows():
        docs.append({
            "text": (
                f"Fourball {row['fourball']} at {row['course']} in {row['month']} "
                f"with players {row['players']}."
            ),
            "meta": row.to_dict()
        })

    for _, row in data["courses"].iterrows():
        docs.append({
            "text": (
                f"Course {row['course']} tee {row['tee']} has slope {row['slope']}, "
                f"rating {row['rating']}, par {row['par']}."
            ),
            "meta": row.to_dict()
        })

    return docs


@st.cache_resource
def build_rag_index() -> Tuple[TfidfVectorizer, pd.DataFrame]:
    data = _load_goam_data()
    docs = _build_documents(data)

    df_docs = pd.DataFrame(docs)
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(df_docs["text"].tolist())

    df_docs["vector"] = list(vectors.toarray())
    return vectorizer, df_docs


def retrieve_context(query: str, top_k: int = 6) -> List[str]:
    vectorizer, df_docs = build_rag_index()

    q_vec = vectorizer.transform([query]).toarray()
    doc_matrix = pd.DataFrame(df_docs["vector"].tolist())

    sims = cosine_similarity(q_vec, doc_matrix)[0]
    df_docs["score"] = sims

    top = df_docs.sort_values("score", ascending=False).head(top_k)
    return top["text"].tolist()
