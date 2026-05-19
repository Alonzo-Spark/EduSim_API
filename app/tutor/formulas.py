from app.rag.retriever import build_rag_context
from app.core.llm_client import generate_structured_response
from app.tutor.prompts import BASE_SYSTEM_PROMPT

def generate_formulas(topic: str, class_name: str, chunks: list[dict]) -> dict:
    context = build_rag_context(chunks)

    prompt = f"""
From the textbook content below about "{topic}" for {class_name}, extract all formulas, relationships, and generate graph data.

TEXTBOOK CONTENT:
{context}

Return this exact JSON structure:
{{
    "formulas": [
        {{
            "name": "Name of this formula",
            "expression": "e.g. v = u + at",
            "description": "What this formula calculates",
            "variables": [
                {{"symbol": "v", "meaning": "final velocity", "unit": "m/s"}},
                {{"symbol": "u", "meaning": "initial velocity", "unit": "m/s"}},
                {{"symbol": "a", "meaning": "acceleration", "unit": "m/s²"}},
                {{"symbol": "t", "meaning": "time", "unit": "s"}}
            ],
            "derivation": ["Step 1: ...", "Step 2: ..."],
            "source": "Textbook page reference"
        }}
    ],
    "relationships": [
        {{
            "parameter": "velocity",
            "effect": "kinetic energy",
            "type": "direct | inverse | exponential | none",
            "description": "As velocity increases, kinetic energy increases (KE = ½mv²)"
        }}
    ],
    "graphConfigs": [
        {{
            "title": "Velocity vs Time",
            "xLabel": "Time (s)",
            "yLabel": "Velocity (m/s)",
            "xKey": "t",
            "yKey": "v",
            "dataPoints": [
                {{"t": 0, "v": 0}},
                {{"t": 1, "v": 10}},
                {{"t": 2, "v": 20}},
                {{"t": 3, "v": 30}},
                {{"t": 4, "v": 40}},
                {{"t": 5, "v": 50}}
            ],
            "type": "linear | curve | parabola"
        }}
    ]
}}
Return empty arrays if topic has no formulas (e.g. for some Class 1–3 topics).
"""
    return generate_structured_response(BASE_SYSTEM_PROMPT, prompt, temperature=0.2)
