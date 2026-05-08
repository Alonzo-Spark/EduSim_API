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
    
    print("Initializing RAG System (Lazy Load)...")
    _embeddings_model = get_embeddings()
    # Pass empty chunks because we rely on the existing index to be loaded
    index, metadata = create_vector_store([], _embeddings_model, force_rebuild=False)
    _retriever = get_retriever(index, metadata, _embeddings_model, k=8)
    print("RAG System Initialized")

def query_rag(query: str) -> str:
    _initialize_rag()
    
    print(f"RAG searching for: {query}")
    results = _retriever(query)
    
    if not results:
        context = ""
    else:
        context = "\n\n".join([f"[Page {doc.get('page', '?')}]\n{doc.get('text', '')}" for doc in results])
    
    print("Generating response...")
    response = generate_response(context=context, question=query)
    return response
