from app.rag.retriever import build_rag_context
from app.core.llm_client import generate_structured_response
from app.tutor.prompts import BASE_SYSTEM_PROMPT
import json

def generate_simulation_config(
    topic: str,
    class_name: str,
    subject: str,
    chunks: list[dict],
    asset_catalog: list[dict]
) -> dict:
    context = build_rag_context(chunks)

    # Provide the LLM a summary of available assets
    asset_summary = json.dumps([
        {"id": a["id"], "label": a["label"], "topics": a["topics"]}
        for a in asset_catalog
    ], indent=2)

    prompt = f"""
Based on the textbook content about "{topic}" for {class_name} {subject},
generate a simulation configuration for the EduSim platform.

TEXTBOOK CONTENT:
{context}

AVAILABLE ASSETS (use IDs from this list only):
{asset_summary}

Return this exact JSON:
{{
    "topic": "{topic}",
    "simulationType": "projectile | pendulum | circuit | motion | wave | optics | chemical | custom",
    "description": "What this simulation demonstrates",
    "parameters": {{
        "paramName": {{
            "label": "Display Label",
            "min": 0,
            "max": 100,
            "default": 20,
            "unit": "m/s",
            "step": 1,
            "description": "What this parameter controls"
        }}
    }},
    "assets": [
        {{"id": "asset_id_from_catalog", "label": "Label", "draggable": true, "initialX": 100, "initialY": 200}}
    ],
    "graphTypes": ["trajectory", "velocity_time", "displacement_time"],
    "formulaOverlay": ["v = u + at", "s = ut + ½at²"],
    "controls": ["play", "pause", "reset", "step"],
    "canvasConfig": {{
        "width": 800,
        "height": 500,
        "background": "#0a0f1e",
        "gridLines": true
    }},
    "physicsConfig": {{
        "gravity": 9.8,
        "timeStep": 0.016,
        "scale": 50
    }},
    "learningObjectives": [
        "Observe how changing angle affects trajectory",
        "See the relationship between initial velocity and range"
    ]
}}
"""
    return generate_structured_response(BASE_SYSTEM_PROMPT, prompt, temperature=0.3)
