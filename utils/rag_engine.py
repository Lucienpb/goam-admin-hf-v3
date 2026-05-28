# utils/rag_engine.py
from pathlib import Path
from typing import List, Dict
import streamlit as st
from utils.json_utils import load_json

DATA_DIR = Path("data")


def _load_goam_data() -> List[str]:
    """
    Load all GOAM JSON files and convert them into simple text chunks.
    No external libraries required.
    """

    chunks = []

    # Scores
    scores = load_json(DATA_DIR / "goam_scores.json")
    for month, data in scores.items():
        course = data.get("course")
        for p in data.get("players", []):
            chunks.append(
                f"{p.get('name')} scored IPS {p.get('ips')} at {course} in {month}. "
                f"Strokes {p.get('strokes')}, Nett {p.get('nett')}, Team {p.get('team')}."
            )

    # Players
    players = load_json(DATA_DIR / "players.json")
    for p in players:
        chunks.append(
            f"Player {p.get('name')} has handicap {p.get('handicap_index')} "
            f"and team {p.get('team')}."
        )

    # Pairings
    pairings = load_json(DATA_DIR / "pairings.json")
    for month, data in pairings.items():
        course = data.get("course")
        for fb in data.get("fourballs", []):
            chunks.append(
                f"Fourball {fb.get('fourball')} at {course} in {month} "
                f"with players {', '.join(fb.get('players', []))}."
            )

    # Courses
    courses = load_json(DATA_DIR / "course_data.json")
    for course_name, info in courses.items():
        for tee_name, tee in info.get("tees", {}).items():
            chunks.append(
                f"Course {course_name} tee {tee_name} has slope {tee.get('slope')}, "
                f"rating {tee.get('rating')}, par {tee.get('par')}."
            )

    return chunks


@st.cache_resource
def load_chunks() -> List[str]:
    """Cache all GOAM text chunks."""
    return _load_goam_data()


def retrieve_context(query: str, top_k: int = 6) -> List[str]:
    """
    Simple keyword-based retrieval.
    No scikit-learn, no numpy, works in Docker.
    """

    chunks = load_chunks()
    query_words = query.lower().split()

    scored = []
    for text in chunks:
        score = sum(1 for w in query_words if w in text.lower())
        if score > 0:
            scored.append((score, text))

    # Sort by score descending
    scored.sort(reverse=True, key=lambda x: x[0])

    return [t for _, t in scored[:top_k]]
