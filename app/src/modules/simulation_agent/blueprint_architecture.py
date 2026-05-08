import json
from uuid import uuid4
from typing import Any

from .agentic_models import CurriculumProfile, SimulationBlueprint, PedagogicalStrategy
from .models import SimulationContext, SimulationTopic
from .llm_client import call_llm


def build_simulation_blueprint(
    prompt: str,
    topic: SimulationTopic,
    context: SimulationContext,
    curriculum: CurriculumProfile,
    controls: list[dict],
    strategy: PedagogicalStrategy = PedagogicalStrategy(),
) -> SimulationBlueprint:
    """
    Synthesize a structured simulation blueprint using an LLM, 
    tailored by pedagogical strategy.
    """
    
    # Construct the synthesis prompt
    synthesis_prompt = f"""
    # Task: Synthesize Tailored Simulation Blueprint JSON
    
    You are an expert educational simulation architect. 
    
    ## User Request
    {prompt}
    
    ## Pedagogical Strategy
    Mode: {strategy.instruction_mode}
    Complexity: {strategy.visualization_complexity}
    Speed: {strategy.animation_speed_scale}x
    Labels: {strategy.label_density}
    
    ## Educational Context
    Topic: {topic.topic}
    Subject: {topic.subject}
    Difficulty: {curriculum.difficulty}
    Formulas: {context.formulas}
    
    ## Guidelines
    1. Instruction Mode: 
       - 'guided': Provide clear starting state and limited variables.
       - 'discovery': More freedom, open-ended parameters.
       - 'challenge': Add constraints or goal-oriented tasks.
    2. Visualization: Scale complexity based on '{strategy.visualization_complexity}'.
    3. Animations: Adjust 'fps_target' or 'trail' based on pedagogical needs.
    
    ## Output Format
    Return ONLY a JSON object that conforms to the SimulationBlueprint schema:
    {{
        "id": "string",
        "title": "string",
        "topic": "string",
        "subject": "string",
        "difficulty": "string",
        "objects": [{{ "id": "string", "type": "string", "label": "string", "position": {{ "x": float, "y": float }}, "velocity": {{ "x": float, "y": float }}, "style": {{ "color": "string", "radius": float }} }}],
        "physics": {{ "engine": "canvas-2d", "formula": "string", "gravity": float, "time_step": float, "constants": [ "string" ], "laws": [ "string" ] }},
        "controls": [{{ "name": "string", "label": "string", "type": "slider|button", "min": float, "max": float, "default": float, "unit": "string" }}],
        "visuals": {{ "renderer": "canvas", "grid": true, "theme": {{ "background": "string", "primary": "string" }}, "annotations": {{ "show_formula": true, "show_vectors": true }} }},
        "animations": {{ "enabled": true, "fps_target": 60, "trail": true }},
        "educational_overlays": {{ "learning_outcomes": [ "string" ], "formula_card": "string" }},
        "runtime_monitoring": {{ "collect_js_errors": true, "fps_threshold": 28 }},
        "metadata": {{ "user_prompt": "string" }}
    }}
    """

    try:
        response_text = call_llm(
            synthesis_prompt, 
            temperature=0.1, 
            response_mime_type="application/json"
        )
        blueprint_data = json.loads(response_text)
        
        # Ensure ID and other critical fields are present/correct
        blueprint_data["id"] = f"bp_{uuid4()}"
        blueprint_data["metadata"] = {
            "user_prompt": prompt,
            "curriculum": curriculum.model_dump(),
            "sources": context.sources,
            "strategy": strategy.model_dump(),
        }

        
        return SimulationBlueprint(**blueprint_data)
        
    except Exception as e:
        print(f"Blueprint synthesis failed: {e}. Falling back to template.")
        return _build_fallback_blueprint(prompt, topic, context, curriculum, controls)


def _build_fallback_blueprint(
    prompt: str,
    topic: SimulationTopic,
    context: SimulationContext,
    curriculum: CurriculumProfile,
    controls: list[dict],
) -> SimulationBlueprint:
    primary_formula = context.formulas[0] if context.formulas else "No formula retrieved"

    return SimulationBlueprint(
        id=f"bp_{uuid4()}",
        title=f"{topic.topic.title()} Interactive Studio",
        topic=topic.topic,
        subject=topic.subject,
        difficulty=curriculum.difficulty,
        objects=[
            {
                "id": "main-entity",
                "type": "particle",
                "label": topic.topic.title(),
                "position": {"x": 140, "y": 360},
                "velocity": {"x": 45, "y": -60},
                "style": {"color": "#31d0aa", "radius": 10},
            }
        ],
        physics={
            "engine": "canvas-2d",
            "gravity": 9.8,
            "time_step": 0.016,
            "formula": primary_formula,
            "constants": context.constants[:5],
            "laws": context.laws[:5],
        },
        controls=controls,
        visuals={
            "renderer": "canvas",
            "grid": True,
            "theme": {
                "background": "#071722",
                "primary": "#31d0aa",
                "secondary": "#ffcc66",
                "warning": "#ff6f61",
            },
            "annotations": {
                "show_formula": True,
                "show_vectors": True,
                "show_axes": True,
            },
        },
        animations={
            "enabled": True,
            "fps_target": 60,
            "trail": True,
            "easing": "linear",
        },
        educational_overlays={
            "learning_outcomes": curriculum.outcomes,
            "prerequisites": curriculum.prerequisites,
            "formula_card": primary_formula,
            "concept_cards": context.definitions[:4],
        },
        runtime_monitoring={
            "collect_js_errors": True,
            "fps_threshold": 28,
            "max_frame_time_ms": 42,
            "repair_on_failure": True,
        },
        metadata={
            "user_prompt": prompt,
            "curriculum": curriculum.model_dump(),
            "sources": context.sources,
        },
    )
