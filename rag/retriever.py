import numpy as np
import faiss


def get_retriever(index, metadata, embeddings_model, k=5):

    def retrieve(query: str):

        try:

            # =====================================================
            # CREATE QUERY EMBEDDING
            # =====================================================
            query_embedding = embeddings_model.encode(
                query,
                convert_to_numpy=True,
                normalize_embeddings=True
            )

            query_embedding = (
                query_embedding
                .astype(np.float32)
                .reshape(1, -1)
            )

            # =====================================================
            # COSINE NORMALIZATION
            # =====================================================
            faiss.normalize_L2(query_embedding)

            # =====================================================
            # SEARCH FAISS INDEX
            # =====================================================
            distances, indices = index.search(query_embedding, k)

            results = []

            # =====================================================
            # PROCESS RESULTS
            # =====================================================
            for i, idx in enumerate(indices[0]):

                # Valid index check
                if idx >= 0 and idx < len(metadata):

                    score = float(distances[0][i])

                    # Skip weak matches
                    if score < 0.28:
                        continue

                    # Copy metadata
                    res = metadata[idx].copy()

                    # Add similarity score
                    res["score"] = score

                    # =================================================
                    # DEBUG OUTPUT
                    # =================================================
                    print("\n===== RETRIEVED =====")
                    print(f"Source  : {res.get('source')}")
                    print(f"Subject : {res.get('subject', 'unknown')}")
                    print(f"Page    : {res.get('page')}")
                    print(f"Score   : {score:.4f}")
                    print("-" * 40)

                    results.append(res)

            # =====================================================
            # NO RESULTS
            # =====================================================
            if not results:
                print("\n⚠️ No strong matches found.")

            return results

        except Exception as e:

            print(f"\n❌ Error retrieving documents: {e}")

            return []

    return retrieve