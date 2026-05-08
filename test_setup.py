#!/usr/bin/env python3
"""
Test script to verify Gemini API connectivity.
Run this before using the full RAG system.
"""

import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

def test_api_connection():
    """Test Gemini API connectivity."""
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    if not GOOGLE_API_KEY:
        print("❌ GOOGLE_API_KEY not found in .env")
        return False
    
    if "your_actual_key_here" in GOOGLE_API_KEY.lower():
        print("❌ GOOGLE_API_KEY appears to be placeholder")
        return False
    
    print("🔧 Testing Gemini API connection...")
    
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say 'API is working!' in one sentence.")

        if response and getattr(response, "text", None):
            print("✅ API Connection Successful!")
            print(f"📝 Response: {response.text}")
            return True

        print("❌ Gemini returned an empty response")
        return False
    except json.JSONDecodeError:
        print("❌ Failed to parse API response")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_embeddings():
    """Test embeddings model loading."""
    print("\n🔧 Testing embeddings model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Test embedding
        embedding = model.encode("Test sentence")
        print(f"✅ Embeddings model loaded successfully")
        print(f"   Embedding dimension: {len(embedding)}")
        return True
    except Exception as e:
        print(f"❌ Embeddings error: {e}")
        return False

def test_faiss():
    """Test FAISS installation."""
    print("\n🔧 Testing FAISS...")
    
    try:
        import faiss
        import numpy as np
        
        # Create small test index
        dimension = 384
        index = faiss.IndexFlatL2(dimension)
        vectors = np.random.random((5, dimension)).astype(np.float32)
        index.add(vectors)
        
        print(f"✅ FAISS installed successfully")
        print(f"   Test index created with {index.ntotal} vectors")
        return True
    except Exception as e:
        print(f"❌ FAISS error: {e}")
        return False

def main():
    print("=" * 60)
    print("RAG System - Dependency & API Test")
    print("=" * 60 + "\n")
    
    results = {
        "Gemini API": test_api_connection(),
        "Embeddings Model": test_embeddings(),
        "FAISS": test_faiss(),
    }
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {name}")
    
    if all(results.values()):
        print("\n🎉 All tests passed! You're ready to use the RAG system.")
        print("Run: python rag_app.py")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
