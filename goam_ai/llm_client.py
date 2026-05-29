import os
from huggingface_hub import InferenceClient

MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

def get_client() -> InferenceClient:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is missing in environment variables / Hugging Face Secrets")
    return InferenceClient(MODEL_ID, token=token)

def generate(prompt: str, max_new_tokens: int = 300, temperature: float = 0.2) -> str:
    client = get_client()
    return client.text_generation(
        prompt,
        max_new_tokens=max_new_tokens,
        temperature=temperature,
        repetition_penalty=1.1,
    )
