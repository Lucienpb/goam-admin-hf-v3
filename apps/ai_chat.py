# apps/ai_chat.py
import streamlit as st
import textwrap

from utils.llm_client import FreeLLMClient
from utils.rag_engine import retrieve_context


SYSTEM_PROMPT = """
You are GOAM Assistant, a golf analytics expert.
You ONLY answer using the context provided.
If the answer is not in the context, say you don't know.
Explain numbers in simple English.
"""


def _build_prompt(question: str, context_chunks: list[str]) -> str:
    context_block = "\n".join(context_chunks)
    return textwrap.dedent(f"""
        {SYSTEM_PROMPT}

        Context:
        {context_block}

        Question:
        {question}

        Answer:
    """)


def run():
    st.header("🤖 AI Chat — Free Version (Gemma‑2B‑IT)")

    st.markdown("Ask anything about GOAM scores, players, pairings, or trends.")

    if "goam_chat" not in st.session_state:
        st.session_state.goam_chat = []

    # Display chat history
    for role, msg in st.session_state.goam_chat:
        if role == "user":
            st.markdown(f"**You:** {msg}")
        else:
            st.markdown(f"**GOAM Assistant:** {msg}")

    st.markdown("---")

    question = st.text_input("Your question")

    if st.button("Ask") and question.strip():
        st.session_state.goam_chat.append(("user", question))

        with st.spinner("Thinking..."):
            context = retrieve_context(question)
            prompt = _build_prompt(question, context)

            client = FreeLLMClient()
            answer = client.chat(prompt)

        st.session_state.goam_chat.append(("assistant", answer))
        st.experimental_rerun()
