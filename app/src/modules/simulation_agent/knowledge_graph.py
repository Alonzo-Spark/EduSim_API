import json
from typing import List, Dict, Any
from .llm_client import call_llm

class ConceptGraph:
    """
    Manages a knowledge graph of educational concepts, formulas, and prerequisites.
    """
    
    def __init__(self):
        # In a real system, this might be a graph database or a persistent JSON
        self.graph = {}

    def get_contextual_graph(self, topic: str, subject: str) -> Dict[str, Any]:
        """
        Infers concept relationships for a specific topic using LLM.
        """
        
        graph_prompt = f"""
        # Task: Build Concept Relationship Graph
        For the given topic, identify prerequisites, related concepts, and core formulas.
        
        Topic: {topic}
        Subject: {subject}
        
        ## Output Format
        Return ONLY a JSON object:
        {{
            "topic": "string",
            "prerequisites": ["string"],
            "related_concepts": ["string"],
            "core_formulas": ["string"],
            "cognitive_dependencies": ["string"]
        }}
        """
        
        try:
            response_text = call_llm(
                graph_prompt, 
                temperature=0.1, 
                response_mime_type="application/json"
            )
            return json.loads(response_text)
        except Exception:
            return {
                "topic": topic,
                "prerequisites": [],
                "related_concepts": [],
                "core_formulas": []
            }

# Global instance
concept_graph = ConceptGraph()
