import faiss
import numpy as np
import pickle
import shutil
from pathlib import Path

# =========================================================
# VECTOR STORE PATHS
# =========================================================
INDEX_PATH = Path("faiss_index")

INDEX_FILE = INDEX_PATH / "index.faiss"

METADATA_FILE = INDEX_PATH / "metadata.pkl"


# =========================================================
# CREATE / LOAD VECTOR STORE
# =========================================================
def create_vector_store(
    chunks,
    embeddings_model,
    force_rebuild=False
):
    """
    Create or load a FAISS vector store.

    Args:
        chunks: List of document chunks
        embeddings_model: SentenceTransformer model
        force_rebuild: If True, rebuild vector store

    Returns:
        (index, metadata)
    """

    # =====================================================
    # FORCE REBUILD
    # =====================================================
    if force_rebuild and INDEX_PATH.exists():

        import shutil

        print("\n🔄 Force rebuilding FAISS index...")

        shutil.rmtree(INDEX_PATH)

    # =====================================================
    # LOAD EXISTING INDEX
    # =====================================================
    if INDEX_FILE.exists() and METADATA_FILE.exists():

        try:

            print("\n✓ Loading existing FAISS index...")

            index = faiss.read_index(str(INDEX_FILE))
            with open(METADATA_FILE, "rb") as f:

                metadata = pickle.load(f)

            print(f"✓ Loaded {len(metadata)} chunks")

            return index, metadata
        except Exception as e:

            print(f"\n⚠ Failed to load existing index: {e}")

            print("🔄 Rebuilding vector store...")

            import shutil

            shutil.rmtree(INDEX_PATH)

    # =====================================================
    # CREATE NEW INDEX
    # =====================================================
    print("\n✓ Creating new FAISS index...")

    INDEX_PATH.mkdir(exist_ok=True)

    # =====================================================
    # EXTRACT TEXTS
    # =====================================================
    texts = [
        chunk.page_content
        for chunk in chunks
    ]

    print(f"✓ Total chunks for embeddings: {len(texts)}")

    # =====================================================
    # CREATE EMBEDDINGS
    # =====================================================
    embeddings = embeddings_model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    # =====================================================
    # CONVERT TO FLOAT32
    # =====================================================
    embeddings = embeddings.astype(np.float32)

    # =====================================================
    # NORMALIZE FOR COSINE SIMILARITY
    # =====================================================
    faiss.normalize_L2(embeddings)

    # =====================================================
    # CREATE FAISS INDEX
    # =====================================================
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    print("✓ FAISS index created")

    # =====================================================
    # CREATE METADATA
    # =====================================================
    metadata = []

    for chunk in chunks:

        source = chunk.metadata.get("source", "")

        path_obj = Path(source)

        # =================================================
        # SUBJECT
        # =================================================
        # Example:
        # data/physics/mechanics.pdf
        # subject = physics
        # chapter = mechanics
        # =================================================
        subject = path_obj.parent.name.lower()

        # Fallback if PDFs are directly inside /data
        if subject == "data":
            subject = path_obj.stem.lower()

        chapter = path_obj.stem.lower()

        metadata.append({

            "text": chunk.page_content,

            "source": source,

            "subject": subject,

            "chapter": chapter,

            "page": chunk.metadata.get("page", 0),

        })

    # =====================================================
    # DEBUG SAMPLE
    # =====================================================
    if metadata:

        print("\n===== SAMPLE METADATA =====")

        print(f"Subject : {metadata[0]['subject']}")
        print(f"Chapter : {metadata[0]['chapter']}")
        print(f"Source  : {metadata[0]['source']}")
        print(f"Page    : {metadata[0]['page']}")

        print("-" * 50)

    # =====================================================
    # SAVE INDEX
    # =====================================================
    faiss.write_index(index, str(INDEX_FILE))

    with open(METADATA_FILE, "wb") as f:

        pickle.dump(metadata, f)

    # =====================================================
    # FINAL LOGS
    # =====================================================
    print(f"\n✓ Saved FAISS index")

    print(f"✓ Total indexed chunks: {len(metadata)}")

    return index, metadata