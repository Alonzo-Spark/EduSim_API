from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts, convert_to_numpy=True):
        return self.model.encode(
            texts,
            convert_to_numpy=convert_to_numpy
        )


def get_embeddings():
    return Embedder()