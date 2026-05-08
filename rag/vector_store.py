import faiss
import numpy as np
import pickle
import shutil
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
        embeddings_model: Embedding model
        force_rebuild: If True, rebuild index

    Returns:
        (index, metadata)
    """

    # =========================
    # FORCE REBUILD
    # =========================
    if force_rebuild and INDEX_PATH.exists():

        print("Force rebuilding index...")
        try:
            shutil.rmtree(INDEX_PATH)
        except PermissionError:
            print("Warning: FAISS index is locked by another process.")
            print("Warning: Close backend/uvicorn/python processes and retry.")
            return None, None

    # =========================
    # LOAD EXISTING INDEX
    # =========================
    if INDEX_FILE.exists() and METADATA_FILE.exists():
        try:
            print("Loading existing FAISS index...")
            index = faiss.read_index(str(INDEX_FILE))
            with open(METADATA_FILE, "rb") as f:
                metadata = pickle.load(f)

            print(f"Loaded {len(metadata)} chunks")
            return index, metadata
        except Exception as e:
            print(f"Failed to load index: {e}")
            print("Rebuilding corrupted index...")
            try:
                shutil.rmtree(INDEX_PATH)
            except PermissionError:
                print("Warning: Could not delete locked FAISS index.")
                return None, None

    # =========================
    # CREATE NEW INDEX
    # =========================
    print("Creating new FAISS index...")
    INDEX_PATH.mkdir(exist_ok=True)

    # Extract text from chunks
    texts = []
    for chunk in chunks:
        if hasattr(chunk, "page_content"):
            texts.append(chunk.page_content)
        else:
            texts.append(str(chunk))

    # =========================
    # CREATE EMBEDDINGS
    # =========================
    print("Generating embeddings...")
    embeddings = embeddings_model.encode(
        texts,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype(np.float32)
    # Normalize for cosine similarity
    faiss.normalize_L2(embeddings)

    # =========================
    # CREATE FAISS INDEX
    # =========================
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    # =========================
    # CREATE METADATA
    # =========================
    metadata = []
    for chunk in chunks:
        if hasattr(chunk, "metadata"):
            metadata.append({
                "text": chunk.page_content,
                "source": chunk.metadata.get("source", ""),
                "page": chunk.metadata.get("page", 0),
            })
        else:
            metadata.append({
                "text": str(chunk),
                "source": "",
                "page": 0,
            })

    # =========================
    # SAVE INDEX
    # =========================
    print("Saving FAISS index...")
    faiss.write_index(index, str(INDEX_FILE))

    with open(METADATA_FILE, "wb") as f:
        pickle.dump(metadata, f)

    print(f"Created FAISS index with {len(metadata)} chunks")

    return index, metadata