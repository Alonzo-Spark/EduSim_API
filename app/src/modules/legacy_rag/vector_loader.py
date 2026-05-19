import os
import faiss
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple

from .embedder import get_embeddings
from .retriever import get_retriever

VECTORSTORE_DIR = Path("vectorstore")

class VectorStoreManager:
    """
    Singleton manager for loading FAISS indices per subject globally on startup.
    Never load FAISS inside API endpoints!
    """
    _instance = None
    _is_loaded = False
    
    _indices: Dict[str, Any] = {}
    _metadata: Dict[str, list] = {}
    _retrievers: Dict[str, Any] = {}
    _embeddings_model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreManager, cls).__new__(cls)
        return cls._instance

    def load_all(self):
        """Load all subject indices from the vectorstore directory."""
        if self._is_loaded:
            return
            
        print("\n=========================================")
        print("Preloading FAISS Vector Databases")
        print("=========================================")
        
        self._embeddings_model = get_embeddings()
        
        if not VECTORSTORE_DIR.exists():
            print(f"⚠️ Vectorstore directory {VECTORSTORE_DIR} not found. Please run create_embeddings.py")
            return
            
        # Load each subject
        loaded_subjects = []
        for subject_dir in VECTORSTORE_DIR.iterdir():
            if subject_dir.is_dir():
                subject = subject_dir.name
                index_path = subject_dir / "index.faiss"
                meta_path = subject_dir / "index.pkl"
                
                if index_path.exists() and meta_path.exists():
                    try:
                        print(f"Loading '{subject}' index...")
                        index = faiss.read_index(str(index_path))
                        with open(meta_path, "rb") as f:
                            metadata = pickle.load(f)
                            
                        self._indices[subject] = index
                        self._metadata[subject] = metadata
                        
                        # Create retriever closure (k=3 for fast retrieval)
                        self._retrievers[subject] = get_retriever(
                            index, metadata, self._embeddings_model, k=3
                        )
                        loaded_subjects.append(subject)
                    except Exception as e:
                        print(f"❌ Failed to load index for {subject}: {e}")
                        
        self._is_loaded = True
        print(f"✅ Successfully preloaded subjects: {', '.join(loaded_subjects) if loaded_subjects else 'None'}")

    def get_retriever(self, subject: str = None):
        """
        Get the preloaded retriever for a specific subject. 
        If subject is None or not found, defaults to 'physics' or the first available.
        """
        if not self._is_loaded:
            self.load_all()
            
        if not self._retrievers:
            return None
            
        if subject and subject in self._retrievers:
            return self._retrievers[subject]
            
        # Fallbacks
        if "physics" in self._retrievers:
            return self._retrievers["physics"]
            
        # Return first available
        first_subject = list(self._retrievers.keys())[0]
        return self._retrievers[first_subject]

# Global singleton instance
vector_store = VectorStoreManager()
