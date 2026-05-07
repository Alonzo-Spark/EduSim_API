import os
from rag.loader import load_all_pdfs
from rag.splitter import split_docs
from rag.embedder import get_embeddings
from rag.vector_store import create_vector_store

def rebuild():
    print("=========================================")
    print("Rebuilding RAG Index")
    print("=========================================")
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    
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
    
    print("\n✅ Rebuild complete!")

if __name__ == "__main__":
    rebuild()
