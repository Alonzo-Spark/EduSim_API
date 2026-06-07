from typing import List, Dict, Any
from app.src.modules.legacy_rag.vector_loader import vector_store

class RagService:
    @staticmethod
    def search_chunks(subject: str, chapter: str, query: str) -> List[Dict[str, Any]]:
        # Map string subjects properly, fallback to physics if missing or unsupported
        subject = subject.lower() if subject else "physics"
        retriever = vector_store.get_retriever(subject)
        
        if not retriever:
            print(f"No retriever found for subject {subject}, trying physics")
            retriever = vector_store.get_retriever("physics")
            
        if not retriever:
            return []
            
        results = retriever(query)
        
        # Filter by chapter loosely if provided
        if chapter:
            chapter = chapter.lower()
            filtered = []
            for r in results:
                # fuzzy match inside chapter metadata
                meta_chap = r.get("chapter", "").lower()
                if chapter in meta_chap or meta_chap in chapter:
                    filtered.append(r)
            if filtered:
                return filtered
                
        return results
