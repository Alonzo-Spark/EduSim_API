import sys
import app.src.modules.physics.rag.services as s

def test_query():
    s._initialize_rag()
    query = "Explain Newton's Second Law"
    results = s._retriever(query)
    
    print(f"Results for '{query}':")
    for i, res in enumerate(results):
        print(f"--- Chunk {i+1} (Page {res.get('page')}) ---")
        print(res.get('text'))
        print("\n")

if __name__ == "__main__":
    test_query()
