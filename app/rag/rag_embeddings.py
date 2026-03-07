import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
EMBED_MODEL = os.getenv("OPEN_AI_EMBED_MODEL", "text-embedding-3-small")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Returns a list of embedding vectors (list[float]) for each input text.
    """
    resp = client.embeddings.create(
        model=EMBED_MODEL,
        input=texts,
    )
    # Keep order aligned to input
    return [item.embedding for item in resp.data]
