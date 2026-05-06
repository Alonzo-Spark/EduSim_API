from sentence_transformers import SentenceTransformer

def get_embeddings():
    """Get embeddings model using sentence-transformers."""
    try:
        model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✓ Embeddings model loaded: all-MiniLM-L6-v2")
        return model
    except Exception as e:
        raise Exception(f"Error loading embeddings model: {e}")

def embed_text(embeddings_model, text: str):
    """Embed a single text string."""
    return embeddings_model.encode(text, convert_to_numpy=True)

def embed_texts(embeddings_model, texts: list):
    """Embed multiple texts."""
    return embeddings_model.encode(texts, convert_to_numpy=True)