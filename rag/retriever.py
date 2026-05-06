import numpy as np
import faiss

def get_retriever(index, metadata, embeddings_model, k=15):

    def retrieve(query: str):

        try:
            query_embedding = embeddings_model.encode(
                query,
                convert_to_numpy=True
            )

            query_embedding = query_embedding.astype(np.float32).reshape(1, -1)

            # cosine normalization
            faiss.normalize_L2(query_embedding)

            distances, indices = index.search(query_embedding, k)

            results = []

            for idx in indices[0]:

                if idx >= 0 and idx < len(metadata):

                    results.append(metadata[idx])

            return results

        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []

    return retrieve