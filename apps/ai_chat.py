import streamlit as st
import pandas as pd
import textwrap

from utils.rag_engine import retrieve_context
from goam_ai.query_parser import parse_query
from goam_ai.dispatcher import dispatch
from goam_ai.llm_client import call_llm


SYSTEM_PROMPT = """
You are GOAM Assistant, a friendly golf analytics expert.
You answer using:
1) The user's real GOAM data (action_result)
2) The retrieved context (RAG)
3) Simple, clear English

Rules:
- Never invent numbers.
- Always explain IPS, strokes, nett in simple terms.
- If action_result contains an error, explain it politely.
"""


def build_answer_prompt(question: str, context_chunks: list[str], action_result: dict | None) -> str:
    context_block = "\n".join(context_chunks)

    action_block = ""
    if action_result:
        action_block = f"\nAction result:\n{action_result}\n"

    return textwrap.dedent(f"""
        {SYSTEM_PROMPT}

        Context:
        {context_block}

        {action_block}

        Question:
        {question}

        Answer:
    """)


def run():
    st.header("🤖 GOAM AI Chat (Hugging Face API)")

    # Chat history
    if "goam_chat" not in st.session_state:
        st.session_state.goam_chat = []

    # Load scores DataFrame (must be set in session_state by your main app)
    df: pd.DataFrame = st.session_state.get("scores_df")
    st.dataframe(st.session_state["scores_df"])
    if df is None:
        st.error("GOAM scores DataFrame not loaded. Make sure you set st.session_state['scores_df'].")
        return

    # Display chat history
    for role, msg in st.session_state.goam_chat:
        if role == "user":
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**GOAM Assistant:** {msg}")

    st.markdown("---")

    question = st.text_input("Ask anything about your GOAM stats…")

    if st.button("Ask") and question.strip():
        st.session_state.goam_chat.append(("user", question))

        with st.spinner("Thinking…"):
            # 1) Convert question → structured action
            instruction = parse_query(question)

            # 2) Run the action on your real GOAM data
            action_result = dispatch(df, instruction)

            # 3) Retrieve RAG context
            context = retrieve_context(question)

            # 4) Build final LLM prompt
            prompt = build_answer_prompt(question, context, action_result)

            # 5) Generate natural language answer
            answer = call_llm(prompt, max_new_tokens=400, temperature=0.3)

        # Save assistant response
        st.session_state.goam_chat.append(("assistant", answer))
        st.rerun()

    # Optional: show trajectory chart if last action returned data
    if st.session_state.goam_chat:
        last_action = st.session_state.goam_chat[-1][1]
