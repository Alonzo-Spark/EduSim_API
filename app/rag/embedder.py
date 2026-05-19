from sentence_transformers import SentenceTransformer
from functools import lru_cache
from app.config import settings

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Singleton — loaded once, reused across all requests."""
    print(f"Loading embedding model: {settings.embedding_model}")
    return SentenceTransformer(settings.embedding_model)

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.encode(texts, batch_size=32, show_progress_bar=False).tolist()

def embed_query(query: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(query).tolist()
