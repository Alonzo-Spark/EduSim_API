from rag.vector_loader import vector_store
from rag.subject_router import detect_subject
from rag.generator import generate_response
import time

def query_rag(query: str) -> dict:
    retrieval_start = time.time()
    subject = detect_subject(query)
    retriever = vector_store.get_retriever(subject)
    
    print(f"RAG searching for: {query}")
    results = retriever(query) if retriever else []
    retrieval_time = time.time() - retrieval_start
    
    if not results:
        context = ""
    else:
        context = "\n\n".join([f"[Page {doc.get('page', '?')}]\n{doc.get('text', '')}" for doc in results])
    
    print("Generating response...")
    response = generate_response(context=context, question=query)
    return response
