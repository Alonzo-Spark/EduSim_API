from datetime import datetime, timezone
from typing import Any, Generator
from uuid import uuid4

from app.src.modules.simulation_synthesis.sanitizer import sanitize_html, validate_html_safety_beautifulsoup

import logging

from .agentic_models import (
    AdaptiveLearningProfile,
    AgenticGenerateRequest,
    AgenticGenerateResponse,
    CurriculumProfile,
    SimulationBlueprint,
)
from .analyzer import analyze_prompt
from .blueprint_architecture import build_simulation_blueprint
from .context_builder import extract_interaction_hints, retrieve_context
from .curriculum_agent import map_curriculum
from .memory_system import retrieve_similar_memories, store_generation_memory, update_learning_profile
from .planner_agent import build_master_plan, mark_task
from .quality import optimize_html, score_simulation
from .regeneration_agent import apply_regeneration_instruction
from .renderer_engine import render_blueprint_to_html
from .repair import repair_generated_html
from .tutor_agent_v2 import build_tutor_packet
from .verification_agent_v2 import verify_full_artifact
from .generator import _save_generated_html
from .blueprint_store import append_repair_history, store_blueprint
from .pedagogical_agent import pedagogical_agent
from .knowledge_graph import concept_graph

logger = logging.getLogger("EduSim.Orchestrator")

def run_agentic_generation(request: AgenticGenerateRequest) -> AgenticGenerateResponse:
    """
    Main orchestration entry point for autonomous simulation generation.
    """
    logger.info(f"Starting agentic generation for prompt: {request.prompt[:50]}...")
    stages: list[str] = []


    # 1. Planning & Analysis
    planner = build_master_plan(request.prompt)
    mark_task(planner, "planning", "completed")
    stages.append("Planner initialized")

    topic = analyze_prompt(request.prompt)
    if request.subject:
        topic.subject = request.subject.lower()
    if request.difficulty:
        topic.complexity = request.difficulty

    # 2. Cognitive Analysis & Strategy
    adaptive_raw = update_learning_profile(
        request.user_id,
        {
            "topic": topic.topic,
            "type": "generation_start",
        },
    )
    adaptive_profile = AdaptiveLearningProfile(**adaptive_raw)
    
    # Pedagogical reasoning
    strategy = pedagogical_agent.determine_strategy(adaptive_profile, topic)
    stages.append(f"Pedagogical strategy determined: {strategy.instruction_mode}")

    # 3. Curriculum & Graph Context
    curriculum = map_curriculum(
        topic,
        class_level=request.class_level,
        board=request.board,
        chapter=request.chapter,
        difficulty=request.difficulty,
        subject_override=request.subject,
    )
    
    # Enhance curriculum with graph intelligence
    graph_context = concept_graph.get_contextual_graph(topic.topic, topic.subject)
    curriculum.prerequisites = list(set(curriculum.prerequisites + graph_context.get("prerequisites", [])))
    
    mark_task(planner, "curriculum_mapping", "completed", {"chapter": curriculum.chapter})
    stages.append("Curriculum and knowledge graph mapping complete")

    context = retrieve_context(request.prompt, topic)
    mark_task(planner, "rag_retrieval", "completed", {"sources": len(context.sources)})
    mark_task(planner, "formula_extraction", "completed", {"formulas": len(context.formulas)})
    stages.append("RAG retrieval and formula extraction complete")

    # 4. Memory hits
    memory_hits = retrieve_similar_memories(request.prompt, limit=5)

    # 5. Simulation Synthesis (Blueprint with Strategy)
    controls = extract_interaction_hints(request.prompt, context)
    blueprint = build_simulation_blueprint(
        request.prompt, 
        topic, 
        context, 
        curriculum, 
        controls,
        strategy=strategy # Pass strategy
    )
    mark_task(planner, "blueprint_synthesis", "completed", {"controls": len(controls)})
    stages.append("Simulation blueprint synthesized with pedagogical tailoring")

    # 6. Tutor Fusion (Aware of the Blueprint and Strategy)
    tutor_packet = build_tutor_packet(
        prompt=request.prompt,
        topic=topic,
        context=context,
        curriculum=curriculum,
        adaptive_profile=adaptive_profile,
        blueprint=blueprint,
        strategy=strategy # Pass strategy
    )

    mark_task(planner, "adaptive_tutoring", "completed")
    stages.append("Tutor fusion packet generated")

    # 6. Rendering & Verification
    html = render_blueprint_to_html(blueprint)
    mark_task(planner, "html_synthesis", "completed", {"html_size": len(html)})

    repair_history: list[dict[str, Any]] = []

    try:
        html = sanitize_html(html)
        validate_html_safety_beautifulsoup(html)
    except Exception as e:
        repaired = repair_generated_html(html, request.prompt, controls)
        html = sanitize_html(repaired)
        validate_html_safety_beautifulsoup(html)
        repair_history.append({"stage": "sanitization", "reason": str(e), "action": "repair_generated_html"})

    verification = verify_full_artifact(topic, context, curriculum, blueprint, html)
    if not verification.passed:
        repaired = repair_generated_html(html, request.prompt, controls)
        html = sanitize_html(repaired)
        validate_html_safety_beautifulsoup(html)
        repair_history.append({"stage": "verification", "issues": verification.issues, "action": "repair_generated_html"})

    mark_task(planner, "verification", "completed", {"passed": verification.passed})
    stages.append("Verification and repair cycle complete")

    # 7. Optimization & Quality
    html = optimize_html(html)
    quality = score_simulation(
        html,
        {
            "formulas": context.formulas,
            "constants": context.constants,
            "laws": context.laws,
        },
        blueprint.controls,
    )

    # 8. Persistence
    sim_id = str(uuid4())
    html_path = _save_generated_html(html, topic, request.prompt)

    bp_store_payload = {
        "id": sim_id,
        "prompt": request.prompt,
        "topic": topic.topic,
        "formulas": context.formulas,
        "structure": blueprint.model_dump(),
        "html_path": html_path,
        "versions": [{"version": "v1", "path": html_path}],
        "repair_history": repair_history,
        "quality_score": quality.get("score"),
    }
    store_blueprint(bp_store_payload)

    for repair in repair_history:
        append_repair_history(sim_id, repair)

    # 10. Marketplace & Recommendations
    recommendations = pedagogical_agent.suggest_next_steps(adaptive_profile, topic.topic)
    
    marketplace = {
        "is_public": True,
        "author": request.user_id or "Anonymous Agent",
        "tags": [topic.subject, curriculum.chapter or topic.topic],
        "recommendations": recommendations,
    }

    store_generation_memory(
        {
            "id": sim_id,
            "prompt": request.prompt,
            "subject": topic.subject,
            "topic": topic.topic,
            "difficulty": curriculum.difficulty,
            "blueprint": blueprint.model_dump(),
            "quality_score": quality.get("score"),
            "repair_history": repair_history,
        }
    )

    return AgenticGenerateResponse(
        success=True,
        id=sim_id,
        created_at=datetime.now(timezone.utc),
        planner_plan=planner,
        topic=topic,
        curriculum=curriculum,
        context=context,
        blueprint=blueprint,
        html=html,
        html_path=html_path,
        tutor=tutor_packet,
        verification=verification,
        adaptive_profile=adaptive_profile,
        pedagogical_strategy=strategy,
        generation_stages=stages,
        memory_hits=memory_hits,
        marketplace=_build_marketplace_info(),
    )


def _build_marketplace_info() -> dict[str, Any]:
    return {
        "shareable": True,
        "export_html": True,
        "download_zip": False,
        "version": 2,
        "collaborative_editing": "beta",
    }


def run_regeneration(
    base_response: AgenticGenerateResponse,
    instruction: str,
) -> AgenticGenerateResponse:
    """
    Apply regeneration instructions to an existing response.
    """
    updated_blueprint: SimulationBlueprint = apply_regeneration_instruction(base_response.blueprint, instruction)
    html = render_blueprint_to_html(updated_blueprint)
    
    # Sanitize & verify the updated artifact
    html = sanitize_html(html)
    validate_html_safety_beautifulsoup(html)

    regen_stages = list(base_response.generation_stages)
    regen_stages.append(f"Regeneration applied: {instruction}")

    new_id = str(uuid4())
    
    # Return updated response
    return AgenticGenerateResponse(
        success=True,
        id=new_id,
        created_at=datetime.now(timezone.utc),
        planner_plan=base_response.planner_plan,
        topic=base_response.topic,
        curriculum=base_response.curriculum,
        context=base_response.context,
        blueprint=updated_blueprint,
        html=html,
        html_path=_save_generated_html(html, base_response.topic, instruction),
        tutor=base_response.tutor,
        verification=base_response.verification, # Ideally re-verify
        adaptive_profile=base_response.adaptive_profile,
        generation_stages=regen_stages,
        memory_hits=base_response.memory_hits,
        marketplace=base_response.marketplace,
    )
