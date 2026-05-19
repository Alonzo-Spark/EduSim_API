import logging
from typing import List, Dict, Any
from .vector_loader import vector_store
from .generator import generate_response

logger = logging.getLogger("EduSim.RAGService")

async def query_rag_service(query: str, subject: str = "physics") -> Dict[str, Any]:
    """
    Core RAG service logic: retrieve context and generate response.
    """
    try:
        # 1. Get retriever for the subject
        retriever = vector_store.get_retriever(subject)
        
        if not retriever:
            logger.warning(f"No retriever found for subject: {subject}. Falling back to default.")
            retriever = vector_store.get_retriever() # Default fallback
            
        if not retriever:
            # Fatal error: no vector stores available
            return {
                "answer": "I'm sorry, but I don't have access to the textbook data right now.",
                "context": [],
                "fallback_mode": True
            }

        # 2. Retrieve documents
        results = retriever(query)
        
        # 3. Filter and build context
        filtered_results = [r for r in results if r["score"] > 0.35]
        
        if not filtered_results:
            logger.info("No strong matches found in RAG. Using fallback mode.")
            context = ""
            fallback_mode = True
        else:
            context = "\n\n".join([
                f"[SUBJECT]: {r.get('subject', 'unknown')}\n"
                f"[SOURCE]: {r.get('source', 'unknown')}\n"
                f"[PAGE]: {r.get('page', 0)}\n\n"
                f"{r['text']}"
                for r in filtered_results
            ])
            fallback_mode = False

        # 4. Generate response
        answer = generate_response(
            context=context,
            question=query,
            fallback_mode=fallback_mode
        )

        return {
            "answer": answer,
            "context": filtered_results,
            "fallback_mode": fallback_mode
        }

    except Exception as e:
        logger.error(f"Error in query_rag_service: {e}", exc_info=True)
        raise e
