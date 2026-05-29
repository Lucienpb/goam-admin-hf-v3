import streamlit as st
import textwrap
import os
from huggingface_hub import InferenceClient

from utils.rag_engine import retrieve_context

SYSTEM_PROMPT = """
You are GOAM Assistant, a golf analytics expert.
You ONLY answer using the context provided.
If the answer is not in the context, say you don't know.
Explain numbers in simple English.
"""

# Hugging Face API client
client = InferenceClient(
    "meta-llama/Llama-3.1-8B-Instruct",
    token=os.environ.get("HF_TOKEN")
)

def ask_llm(prompt: str) -> str:
    """Send prompt to Hugging Face Inference API."""
    response = client.text_generation(
        prompt,
        max_new_tokens=300,
        temperature=0.2,
        repetition_penalty=1.1
    )
    return response

def build_prompt(question: str, context_chunks: list[str]) -> str:
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
    st.header("🤖 AI Chat — GOAM Assistant (Hugging Face API)")

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
            prompt = build_prompt(question, context)

            answer = ask_llm(prompt)

        st.session_state.goam_chat.append(("assistant", answer))
        st.experimental_rerun()
