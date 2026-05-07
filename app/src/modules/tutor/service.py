import re
import json
from typing import List, Dict, Any
from rag.generator import call_openrouter_api, generate_response
from rag.retriever import get_retriever
import pickle
import faiss
from sentence_transformers import SentenceTransformer
import os

# RAG Setup
_retriever = None
_embeddings_model = None

def get_rag_components():
    global _retriever, _embeddings_model
    if _retriever is None:
        try:
            # Load FAISS index and metadata
            index = faiss.read_index("faiss_index/index.faiss")
            with open("faiss_index/metadata.pkl", "rb") as f:
                metadata = pickle.load(f)
            
            _embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
            _retriever = get_retriever(index, metadata, _embeddings_model)
        except Exception as e:
            print(f"⚠️ RAG Initialization Warning: {e}")
            return None, None
    return _retriever, _embeddings_model

def analyze_with_llm(query: str, context: str) -> Dict[str, Any]:
    """
    Uses LLM to extract physics concepts, formulas, query type, and explanation from the context.
    """
    system_prompt = (
        "You are an intelligent physics textbook tutor. Analyze the user's query and the provided Context.\n\n"
        "1. Determine the 'queryType': 'concept', 'formula', or 'mixed'.\n"
        "2. Extract 'concepts': list of related physics topics from the context.\n"
        "3. Extract 'formulas': find relevant formulas in the context. IF the query is a concept but has fundamental formulas (like F=ma for force) not present in context, you MUST include them from your knowledge. Provide formula, name, topic, meaning.\n"
        "4. Generate an 'explanation' answering the query based on the context.\n\n"
        "Return ONLY a valid JSON object:\n"
        "{\n"
        "  \"queryType\": \"string\",\n"
        "  \"concepts\": [\"string\"],\n"
        "  \"formulas\": [\n"
        "    {\"formula\": \"string\", \"name\": \"string\", \"topic\": \"string\", \"meaning\": \"string\"}\n"
        "  ],\n"
        "  \"explanation\": \"string\"\n"
        "}\n"
    )
    
    user_prompt = f"Context:\n{context}\n\nQuery:\n{query}"
    
    try:
        response_text = call_openrouter_api(system_prompt, user_prompt)
        # Extract JSON from response (handling potential markdown blocks)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Error extracting structured data: {e}")
    
    return {
        "queryType": "concept", 
        "concepts": [], 
        "formulas": [], 
        "explanation": "Failed to analyze query with LLM."
    }

def analyze_tutor_query(query: str) -> Dict[str, Any]:
    # 1. RAG Retrieval First
    retriever, _ = get_rag_components()
    rag_content = []
    context = ""
    
    if retriever:
        docs = retriever(query)
        # Format RAG content for frontend
        for doc in docs[:5]: # Top 5
            source = os.path.basename(doc.get("source", "Textbook"))
            content = doc.get("text", "").strip()
            
            # Clean up text
            content = re.sub(r'\s+', ' ', content)
            if len(content) > 400:
                content = content[:400] + "..."

            rag_content.append({
                "title": source,
                "content": content
            })
            
            context += f"{content}\n\n"
    else:
        context = "Tutor is currently operating without textbook context. (RAG not initialized)"

    # 2. Use LLM for intelligent extraction based on context
    structured = analyze_with_llm(query, context)
    # 3. Get detailed Markdown RAG explanation
    rag_explanation = generate_response(context, query)
    
    return {
        "queryType": structured.get("queryType", "concept"),
        "concepts": structured.get("concepts", []),
        "formulas": structured.get("formulas", []),
        "explanation": rag_explanation,
        "ragContent": rag_content[:3] # Send top 3 to frontend
    }
