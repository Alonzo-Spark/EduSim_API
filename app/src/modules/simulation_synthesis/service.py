import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from rag.retriever import get_retriever
from rag.generator import generate_llm_text
from .prompt_builder import build_dsl_prompt as _build_dsl_prompt
from .sanitizer import sanitize_json
from .validator import validate_simulation
from rag.vector_loader import vector_store
from rag.subject_router import detect_subject

PERSISTENCE_FILE = Path("data/generated_simulations.json")
_store_lock = Lock()

# --- Granular Service Functions ---

def retrieve_context(prompt: str, topic: str | None = None) -> str:
    """Retrieve RAG context for a given prompt."""
    subject = detect_subject(topic if topic else prompt)
    retriever = vector_store.get_retriever(subject)
    raw_chunks = retriever(prompt)[:6] if retriever else []
    
    lines = []
    for chunk in raw_chunks:
        source = os.path.basename(chunk.get("source", "Textbook"))
        page = chunk.get("page", "?")
        text = re.sub(r"\s+", " ", chunk.get("text", "")).strip()
        lines.append(f"Source: {source} | Page: {page}\n{text}")
    return "\n\n".join(lines)

def build_dsl_prompt(prompt: str, context: str) -> str:
    """Build the final system prompt for the LLM."""
    return _build_dsl_prompt(prompt, context)

def generate_dsl(dsl_prompt: str) -> str:
    """Call the LLM to generate raw DSL text."""
    return generate_llm_text(dsl_prompt, temperature=0.2, max_output_tokens=3500)

def validate_dsl(data: dict) -> dict:
    """Validate the DSL against the v2.0 schema."""
    result = validate_simulation(data)
    if not result["success"]:
        raise ValueError(f"DSL Validation failed: {result['errors']}")
    return result["data"]

def sanitize_dsl(raw_text: str) -> dict:
    """Sanitize and parse raw LLM output into JSON."""
    return sanitize_json(raw_text)

# --- Legacy & Composite Functions ---

def _read_store():
    if not PERSISTENCE_FILE.exists():
        return []
    with open(PERSISTENCE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)

def _write_store(items: list[dict[str, Any]]):
    PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERSISTENCE_FILE, "w", encoding="utf-8") as file:
        json.dump(items, file, indent=2, ensure_ascii=True)

def generate_simulation_synthesis(prompt: str, topic: str | None = None):
    """Full generation flow with persistence."""
    # 1. Retrieve
    context = retrieve_context(prompt, topic)
    
    # 2. Build Prompt
    dsl_prompt = build_dsl_prompt(prompt, context)
    
    # 3. Generate
    raw_generated = generate_dsl(dsl_prompt)
    
    # 4. Sanitize
    response_json = sanitize_dsl(raw_generated)
    
    # 5. Validate
    valid_response = validate_dsl(response_json)
    
    simulation_id = str(uuid4())
    item = {
        "id": simulation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **valid_response
    }

    with _store_lock:
        items = _read_store()
        items.insert(0, item)
        _write_store(items)

    return item

def list_simulation_synthesis(limit: int = 30):
    safe_limit = min(max(limit, 1), 100)
    with _store_lock:
        items = _read_store()

    trimmed = []
    for item in items[:safe_limit]:
        trimmed.append({
            "id": item.get("id"),
            "title": item.get("dsl", {}).get("meta", {}).get("title"),
            "topic": item.get("metadata", {}).get("topic"),
            "timestamp": item.get("timestamp"),
        })
    return trimmed

def get_simulation_synthesis(simulation_id: str):
    with _store_lock:
        items = _read_store()
    for item in items:
        if item.get("id") == simulation_id:
            return item
    return None

def _format_sse_event(event_type: str, data: str | dict) -> str:
    if isinstance(data, dict):
        data = json.dumps(data)
    return f"event: {event_type}\ndata: {data}\n\n"

def generate_simulation_synthesis_stream(prompt: str, topic: str | None = None):
    try:
        simulation_id = str(uuid4())
        yield _format_sse_event("started", {"id": simulation_id, "stage": "Initializing..."})
        
        # 1. Retrieve
        yield _format_sse_event("progress", {"stage": "Retrieving textbook context..."})
        context = retrieve_context(prompt, topic)
        yield _format_sse_event("progress", {"stage": "Context retrieved."})

        # 2. Build Prompt
        yield _format_sse_event("progress", {"stage": "Synthesizing Architecture..."})
        dsl_prompt = build_dsl_prompt(prompt, context)

        # 3. Generate
        raw_generated = generate_dsl(dsl_prompt)

        # 4. Sanitize & 5. Validate
        yield _format_sse_event("progress", {"stage": "Validating EduSim Contract..."})
        response_json = sanitize_dsl(raw_generated)
        valid_response = validate_dsl(response_json)

        # 6. Save
        yield _format_sse_event("progress", {"stage": "Saving to store..."})
        item = {
            "id": simulation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **valid_response
        }

        with _store_lock:
            items = _read_store()
            items.insert(0, item)
            _write_store(items)

        yield _format_sse_event("complete", item)

    except Exception as e:
        yield _format_sse_event("error", {"error": str(e), "type": type(e).__name__})