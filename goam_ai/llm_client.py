import os
from huggingface_hub import InferenceClient

MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

def get_client() -> InferenceClient:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN missing in Hugging Face Secrets")
    return InferenceClient(MODEL_ID, token=token)

def call_llm(prompt: str, max_new_tokens: int = 300, temperature: float = 0.2) -> str:
    """
    Sends a chat-style prompt to the Llama‑3.1‑8B‑Instruct model
    using the Novita backend (chat_completion only).
    """

    client = get_client()

    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_new_tokens,
        temperature=temperature,
    )

    return response.choices[0].message["content"]
