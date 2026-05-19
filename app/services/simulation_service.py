import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.rag.retriever import retrieve_chunks, build_rag_context
from app.core.llm_client import generate_structured_response
from app.tutor.prompts import BASE_SYSTEM_PROMPT
from app.models.simulation import Simulation
from app.services.asset_service import get_assets_for_topic
from app.services.gamification_service import award_xp, check_and_award_badges
import uuid

async def generate_and_save_simulation(
    user_id: uuid.UUID,
    topic: str,
    class_name: str,
    subject: str,
    chapter: str | None,
    topic_id: int | None,
    db: AsyncSession
) -> dict:
    """
    RAG-grounded educational simulation generator.
    1. Retrieves context chunks from ChromaDB textbook embeddings.
    2. Builds asset summaries.
    3. Calls the LLM to output a beautiful, structured simulation JSON configuration.
    4. Commits record to PostgreSQL and awards progression experience points (XP).
    """
    # 1. Retrieve Textbook Context via RAG
    query_str = f"{topic} experiment formulas parameters visualization diagram lab"
    chunks = retrieve_chunks(
        query=query_str,
        class_name=class_name,
        subject=subject,
        chapter=chapter or "",
        n_results=6
    )
    
    context = build_rag_context(chunks) if chunks else f"Basic curriculum context of {topic} for {class_name} {subject}."

    # 2. Extract Assets from Catalog
    assets = await get_assets_for_topic(topic, subject)
    asset_summary = json.dumps([
        {"id": a["id"], "label": a["label"], "topics": a["topics"]}
        for a in assets
    ] if assets else [], indent=2)

    # 3. Formulate Prompt for Structured LLM Generation
    prompt = f"""
    You are an expert interactive physics, mathematics, and biology simulation architect (similar to PhET Interactive Simulations and GeoGebra).
    Based on the textbook context, generate a complete interactive laboratory schema for "{topic}" ({class_name} {subject}).
    
    TEXTBOOK EMBEDDINGS GROUNDING:
    {context}
    
    AVAILABLE VISUAL OBJECT ASSETS:
    {asset_summary}
    
    Ensure you classify the simulation into one of the following active simulation_type values:
    "projectile_motion" | "newtons_laws" | "friction" | "gravitation" | "work_energy" | "electricity_circuit" | "wave" | "optics" | "graph_plotting" | "trigonometry" | "cell_structure" | "photosynthesis" | "respiration" | "custom"

    Return a valid JSON object matching the exact specification below:
    {{
        "simulation_type": "one of the type strings listed above",
        "title": "A premium engaging educational title",
        "description": "A comprehensive summary of the interactive lab",
        "parameters": [
            {{
                "name": "variable_name (e.g. velocity, mass, gravity, resistance)",
                "label": "Display Label",
                "min": 0,
                "max": 100,
                "default": 20,
                "unit": "m/s or kg or V or ohms",
                "step": 1,
                "description": "Explanation of parameter impact"
            }}
        ],
        "formulas": [
            {{
                "name": "Formula Name",
                "latex": "LaTeX expression (e.g. R = \\\\frac{{u^2 \\\\sin(2\\\\theta)}}{{g}})",
                "desc": "Explanation of variable mappings"
            }}
        ],
        "controls": [
            "play", "pause", "reset", "step", "zoom", "graph_toggle"
        ],
        "visualization": {{
            "width": 800,
            "height": 500,
            "background": "#0b0f1e",
            "gridLines": true,
            "scale": 50
        }},
        "steps": [
            {{
                "step_number": 1,
                "title": "Guided Step Title",
                "instructions": "Step-by-step instruction on slider tuning or observation",
                "target_task": "Adjust velocity to 30 m/s and launch"
            }}
        ],
        "quiz_questions": [
            {{
                "question": "A multiple choice conceptual question",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correctIndex": 1,
                "explanation": "Detailed explanation grounding this formula"
            }}
        ]
    }}
    """

    # Generate JSON structure
    config = generate_structured_response(BASE_SYSTEM_PROMPT, prompt, temperature=0.3)
    
    # Clean fallback overrides if key outputs are missing
    if "simulation_type" not in config:
        config["simulation_type"] = "projectile_motion" if "projectile" in topic.lower() else "custom"
    if "title" not in config:
        config["title"] = f"Dynamic {topic} Lab"

    # 4. Save to Database
    sim = Simulation(
        user_id=user_id,
        topic_id=topic_id,
        topic_name=topic,
        class_name=class_name,
        subject=subject,
        config=config,
        is_saved=False
    )
    
    db.add(sim)
    await db.commit()
    await db.refresh(sim)

    # 5. Reward Progress XP and badges
    await award_xp(user_id, "simulation_launched", db)
    new_badges = await check_and_award_badges(user_id, db)

    return {
        "simulation_id": str(sim.id),
        "config": config,
        "new_badges": new_badges
    }
