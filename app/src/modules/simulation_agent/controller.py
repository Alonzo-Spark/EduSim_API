import json
from datetime import datetime
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator

from .models import AgentGenerateRequest, AgentGenerateResponse
from .analyzer import analyze_prompt
from .context_builder import retrieve_context, build_enhanced_context_prompt, extract_interaction_hints
from .generator import (
    generate_simulation_with_agent,
    build_agent_response,
    store_agent_response,
    _save_generated_html,
)
from . import repair as repair_module
from .physics_verifier import verify_physics_consistency
from .blueprint_store import store_blueprint, append_repair_history, update_quality_score
from .quality import score_simulation, optimize_html
from app.src.modules.simulation_synthesis.sanitizer import sanitize_html, validate_html_safety_beautifulsoup


def _format_sse_event(event_type: str, data: str | dict) -> str:
    """Format a Server-Sent Events message."""
    if isinstance(data, dict):
        data = json.dumps(data)
    return f"event: {event_type}\ndata: {data}\n\n"


async def agent_generate_controller(request: AgentGenerateRequest) -> AgentGenerateResponse:
    """
    Handle non-streaming generation request.
    
    Args:
        request: AgentGenerateRequest with prompt and optional overrides
        
    Returns:
        AgentGenerateResponse with complete simulation
        
    Raises:
        HTTPException on validation or generation errors
    """
    try:
        # Stage 1: Analyze prompt
        topic = analyze_prompt(request.prompt)
        
        # Apply complexity override if provided
        if request.complexity:
            topic.complexity = request.complexity
        
        # Apply topic override if provided
        if request.topic:
            topic.topic = request.topic
        
        # Stage 2: Retrieve context
        context = retrieve_context(request.prompt, topic)
        
        # Stage 3: Generate HTML (may return raw output and an error message)
        html, stages, gen_error = generate_simulation_with_agent(request.prompt, topic, context)

        repaired = False
        repair_info = None

        if gen_error is not None:
            # Attempt automatic repair using heuristics
            expected_controls = [c for c in extract_interaction_hints(request.prompt, context)]
            raw_input_for_repair = html or gen_error
            repaired_html = repair_module.repair_generated_html(raw_input_for_repair, request.prompt, expected_controls)

            # Validate repaired HTML
            try:
                sanitize_html(repaired_html)
                validate_html_safety_beautifulsoup(repaired_html)
                repaired = True
                repair_info = {"reason": gen_error, "details": "Automatic heuristic repair applied"}
                html = repaired_html
                stages.append("Repaired via Repair Agent")
            except Exception as e:
                # Repair failed — persist attempted repair for debugging and return error
                save_path = _save_generated_html(repaired_html if repaired_html else raw_input_for_repair, topic, request.prompt)
                raise HTTPException(status_code=500, detail=f"Generation failed and repair unsuccessful: {str(e)}; saved_attempt: {save_path}")

        # Optional physics verification
        verification = verify_physics_consistency({
            "formulas": context.formulas,
            "constants": context.constants,
            "laws": context.laws,
        }, html)
        if not verification.get("ok", True):
            # Attempt minor repair heuristics if possible
            stages.append("Physics verification flagged issues")

        # Optimize HTML
        try:
            optimized = optimize_html(html)
            html = optimized
            stages.append("Optimized HTML")
        except Exception:
            # Ignore optimization failures
            pass

        # Stage 4: Save HTML
        html_path = _save_generated_html(html, topic, request.prompt)

        # Stage 5: Build response
        response = build_agent_response(
            request.prompt,
            topic,
            context,
            html,
            html_path=html_path,
            stages=stages,
        )

        # Quality scoring
        quality = score_simulation(html, {"formulas": context.formulas, "constants": context.constants, "laws": context.laws}, response.interactions)

        # Stage 6: Store metadata + blueprint
        store_agent_response(response)
        bp = {
            "id": response.id,
            "prompt": request.prompt,
            "topic": topic.topic,
            "formulas": context.formulas,
            "structure": {"interactions": [i.model_dump() for i in response.interactions]},
            "html_path": html_path,
            "created_at": response.timestamp.isoformat(),
            "versions": [{"version": "original_repaired" if repaired else "original", "path": html_path}],
            "repair_history": [repair_info] if repair_info else [],
            "quality_score": quality.get("score"),
        }
        store_blueprint(bp)
        update_quality_score(response.id, quality.get("score"))

        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation agent generation failed: {str(e)}"
        )


async def agent_generate_stream_controller(
    request: AgentGenerateRequest,
) -> StreamingResponse:
    """
    Handle streaming generation request with progress updates.
    
    Args:
        request: AgentGenerateRequest with prompt and optional overrides
        
    Returns:
        StreamingResponse with SSE events
    """
    async def generate_stream() -> AsyncGenerator[str, None]:
        try:
            # Event 1: Started
            simulation_id = "gen_" + str(id(request))  # Simple ID
            yield _format_sse_event("started", {
                "id": simulation_id,
                "message": "Starting simulation generation agent..."
            })
            
            # Stage 1: Analyze prompt
            yield _format_sse_event("progress", {
                "stage": "Analyzing prompt...",
                "progress": 10,
                "message": "Detecting topic, subject, and complexity"
            })
            topic = analyze_prompt(request.prompt)
            if request.complexity:
                topic.complexity = request.complexity
            if request.topic:
                topic.topic = request.topic
            
            yield _format_sse_event("progress", {
                "stage": f"Detected: {topic.topic}",
                "progress": 15,
                "message": f"Subject: {topic.subject} | Complexity: {topic.complexity}"
            })
            
            # Stage 2: Retrieve context
            yield _format_sse_event("progress", {
                "stage": "Retrieving textbook context...",
                "progress": 25,
                "message": "Querying RAG system for relevant formulas and concepts"
            })
            context = retrieve_context(request.prompt, topic)
            
            yield _format_sse_event("progress", {
                "stage": f"Retrieved context",
                "progress": 35,
                "message": f"Found {len(context.formulas)} formulas, {len(context.constants)} constants, {len(context.laws)} laws"
            })
            
            # Stage 3: Build enhanced prompt
            yield _format_sse_event("progress", {
                "stage": "Building enhanced prompt...",
                "progress": 40,
                "message": "Preparing context-aware instructions for AI generation"
            })
            enhanced_prompt = build_enhanced_context_prompt(
                request.prompt,
                topic,
                context,
                for_html_generation=True
            )
            
            # Stage 4: Generate HTML
            yield _format_sse_event("progress", {
                "stage": "Generating simulation with Gemini AI...",
                "progress": 50,
                "message": "Creating HTML/CSS/JavaScript simulation"
            })
            html, stages, gen_error = generate_simulation_with_agent(request.prompt, topic, context)

            if gen_error:
                yield _format_sse_event("progress", {
                    "stage": "Generation produced validation errors, attempting repair...",
                    "progress": 65,
                    "message": str(gen_error)
                })

                # Attempt repair
                expected_controls = [c for c in extract_interaction_hints(request.prompt, context)]
                raw_input_for_repair = html or gen_error
                repaired_html = repair_module.repair_generated_html(raw_input_for_repair, request.prompt, expected_controls)

                try:
                    sanitize_html(repaired_html)
                    validate_html_safety_beautifulsoup(repaired_html)
                    html = repaired_html
                    stages.append("Repaired via Repair Agent")
                    yield _format_sse_event("progress", {"stage": "Repair succeeded", "progress": 72})
                except Exception as e:
                    save_path = _save_generated_html(repaired_html if repaired_html else raw_input_for_repair, topic, request.prompt)
                    yield _format_sse_event("error", {"error": f"Repair failed: {str(e)}", "saved_attempt": save_path})
                    return

            yield _format_sse_event("progress", {
                "stage": "HTML generated",
                "progress": 70,
                "message": f"Completed {len(stages)} validation stages"
            })
            
            # Stage 5: Save HTML
            yield _format_sse_event("progress", {
                "stage": "Saving generated simulation...",
                "progress": 80,
                "message": "Persisting HTML to file system"
            })
            html_path = _save_generated_html(html, topic, request.prompt)
            
            # Stage 6: Build response
            yield _format_sse_event("progress", {
                "stage": "Building response metadata...",
                "progress": 90,
                "message": "Extracting learning objectives and related concepts"
            })
            response = build_agent_response(
                request.prompt,
                topic,
                context,
                html,
                html_path=html_path,
                stages=stages,
            )
            
            # Stage 7: Store metadata
            yield _format_sse_event("progress", {
                "stage": "Storing metadata...",
                "progress": 95,
                "message": "Recording generation metadata"
            })
            store_agent_response(response)
            
            # Final event: Complete
            yield _format_sse_event("complete", response.model_dump(mode="json"))
            yield _format_sse_event("done", {"status": "complete"})
            
        except Exception as e:
            error_msg = str(e)
            yield _format_sse_event("error", {
                "error": error_msg,
                "type": type(e).__name__
            })
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


async def report_runtime_error_controller(simulation_id: str | None, payload: dict):
    """Receive runtime error reports forwarded from the frontend (from iframe via postMessage).

    Stores the report in `data/runtime_error_reports.json` and appends to blueprint repair history if simulation_id provided.
    """
    from pathlib import Path
    import json

    P = Path("data/runtime_error_reports.json")
    P.parent.mkdir(parents=True, exist_ok=True)
    reports = []
    if P.exists():
        try:
            with open(P, "r", encoding="utf-8") as f:
                reports = json.load(f)
        except Exception:
            reports = []

    entry = {
        "simulation_id": simulation_id,
        "payload": payload,
        "received_at": datetime.utcnow().isoformat(),
    }
    reports.insert(0, entry)
    with open(P, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=True)

    # Optionally append to blueprint repair history
    if simulation_id:
        append_repair_history(simulation_id, {"type": "runtime_error", "payload": payload, "at": datetime.utcnow().isoformat()})

    return {"success": True}
