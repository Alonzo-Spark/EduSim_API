import os
from .loader import load_all_pdfs
from .splitter import split_docs
from .embedder import get_embeddings
from .vector_store import create_vector_store

def rebuild():
    print("=========================================")
    print("Rebuilding RAG Index")
    print("=========================================")
    
    # Path relative to project root
    data_dir = "data"
    
    print(f"\n1. Loading all PDFs from {data_dir}...")
    docs = load_all_pdfs(data_dir)
    print(f"Total documents loaded: {len(docs)}")
    
    if not docs:
        print("No documents found. Exiting.")
        return
        
    print("\n2. Splitting documents into chunks...")
    chunks = split_docs(docs)
    print(f"Total chunks created: {len(chunks)}")
    
    print("\n3. Loading embedding model...")
    embeddings_model = get_embeddings()
    
    print("\n4. Rebuilding vector store (Force Rebuild)...")
    index, metadata = create_vector_store(chunks, embeddings_model, force_rebuild=True)
    
    print("\n[REBUILD] Rebuild complete!")

if __name__ == "__main__":
    rebuild()
