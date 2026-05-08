from rag.embedder import get_embeddings
from rag.vector_store import create_vector_store
from rag.retriever import get_retriever
from rag.generator import generate_response

# Global singletons to avoid reloading model on every request
_embeddings_model = None
_retriever = None

def _initialize_rag():
    global _embeddings_model, _retriever
    if _retriever is not None:
        return
    
    print("[RAG] Initializing RAG System (Lazy Load)...")
    _embeddings_model = get_embeddings()
    # Pass empty chunks because we rely on the existing index to be loaded
    index, metadata = create_vector_store([], _embeddings_model, force_rebuild=False)
    _retriever = get_retriever(index, metadata, _embeddings_model, k=8)
    print("[RAG] System Initialized")

import time

def query_rag(query: str) -> dict:
    _initialize_rag()
    
    start_time = time.time()
    
    print(f"[RAG] searching for: {query}")
    retrieval_start = time.time()
    results = _retriever(query)
    retrieval_time = time.time() - retrieval_start
    
    if not results:
        context = ""
    else:
        context = "\n\n".join([f"[Page {doc.get('page', '?')}]\n{doc.get('text', '')}" for doc in results])
    
    print("[RAG] Generating response...")
    generation_start = time.time()
    answer = generate_response(context=context, question=query)
    generation_time = time.time() - generation_start
    
    total_time = time.time() - start_time
    
    return {
        "answer": answer,
        "chunks": results[:5], # Return top 5 as requested
        "metrics": {
            "retrieval_time": round(retrieval_time, 3),
            "generation_time": round(generation_time, 3),
            "total_time": round(total_time, 3)
        }
    }
