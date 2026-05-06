import faiss
import numpy as np
import pickle
from pathlib import Path

# Paths
INDEX_PATH = Path("faiss_index")
INDEX_FILE = INDEX_PATH / "index.faiss"
METADATA_FILE = INDEX_PATH / "metadata.pkl"


def create_vector_store(chunks, embeddings_model, force_rebuild=False):
    """
    Create or load a FAISS vector store.

    Args:
        chunks: List of document chunks
        embeddings_model: SentenceTransformer model
        force_rebuild: If True, rebuild index

    Returns:
        (index, metadata)
    """

    # 🔁 Force rebuild
    if force_rebuild and INDEX_PATH.exists():
        import shutil
        print("🔄 Force rebuilding index...")
        shutil.rmtree(INDEX_PATH)

    # ✅ Load existing index
    if INDEX_FILE.exists() and METADATA_FILE.exists():
        try:
            print("✓ Loading existing FAISS index...")
            index = faiss.read_index(str(INDEX_FILE))

            with open(METADATA_FILE, "rb") as f:
                metadata = pickle.load(f)

            return index, metadata

        except Exception as e:
            print(f"⚠ Failed to load index: {e}")
            print("🔄 Rebuilding index...")
            import shutil
            shutil.rmtree(INDEX_PATH)

    # 🆕 Create new index
    print("✓ Creating new FAISS index...")
    INDEX_PATH.mkdir(exist_ok=True)

    # 📄 Extract text
    texts = [chunk.page_content for chunk in chunks]

    # 🔗 Create embeddings
    embeddings = embeddings_model.encode(texts, convert_to_numpy=True)

    # 🔥 Normalize for cosine similarity
    embeddings = embeddings.astype(np.float32)
    faiss.normalize_L2(embeddings)

    # 📦 Create index (cosine similarity using inner product)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # 🧾 Metadata
    metadata = [
        {
            "text": chunk.page_content,
            "source": chunk.metadata.get("source", ""),
            "page": chunk.metadata.get("page", 0),
        }
        for chunk in chunks
    ]

    # 💾 Save index
    faiss.write_index(index, str(INDEX_FILE))

    with open(METADATA_FILE, "wb") as f:
        pickle.dump(metadata, f)

    print(f"✓ Created FAISS index with {len(metadata)} chunks")

    return index, metadata