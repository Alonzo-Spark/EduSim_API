import json
import os
import pickle
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

import faiss
from sentence_transformers import SentenceTransformer

from rag.retriever import get_retriever
from rag.generator import generate_llm_text
from .templates import detect_subject
from .prompt_builder import build_dsl_prompt
from .sanitizer import sanitize_json
from .validator import validate_simulation


INDEX_FILE = Path("faiss_index/index.faiss")
METADATA_FILE = Path("faiss_index/metadata.pkl")
PERSISTENCE_FILE = Path("data/generated_simulations.json")

_retriever = None
_store_lock = Lock()


def _load_retriever():
    global _retriever
    if _retriever is not None:
        return _retriever

    if not INDEX_FILE.exists() or not METADATA_FILE.exists():
        return None

    index = faiss.read_index(str(INDEX_FILE))
    with open(METADATA_FILE, "rb") as file:
        metadata = pickle.load(file)

    embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
    _retriever = get_retriever(index, metadata, embeddings_model, k=10)
    return _retriever


def _build_context_block(chunks: list[dict[str, Any]]):
    lines = []
    for chunk in chunks:
        source = os.path.basename(chunk.get("source", "Textbook"))
        page = chunk.get("page", "?")
        text = re.sub(r"\s+", " ", chunk.get("text", "")).strip()
        lines.append(f"Source: {source} | Page: {page}\n{text}")
    return "\n\n".join(lines)


def _read_store():
    if not PERSISTENCE_FILE.exists():
        return []

    with open(PERSISTENCE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def _write_store(items: list[dict[str, Any]]):
    PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERSISTENCE_FILE, "w", encoding="utf-8") as file:
        json.dump(items, file, indent=2, ensure_ascii=True)


def _build_sources(chunks: list[dict[str, Any]]):
    sources = []
    seen = set()

    for chunk in chunks:
        raw_source = chunk.get("source", "Textbook")
        source = os.path.basename(raw_source.replace("\\", "/"))
        page = chunk.get("page", "?")
        key = f"{source}:{page}"
        if key in seen:
            continue
        seen.add(key)
        sources.append({"source": source, "page": page})

    return sources


def generate_simulation_synthesis(prompt: str, topic: str | None = None):
    print("AI request started: simulation retrieval")
    retriever = _load_retriever()
    raw_chunks = retriever(prompt)[:10] if retriever else []
    
    # Simple filtering for better context
    chunks = raw_chunks[:6]
    print(f"RAG retrieval completed: {len(chunks)} context chunks selected")

    context = _build_context_block(chunks)
    
    print("OpenRouter request started: EduSim Architecture synthesis")
    dsl_prompt = build_dsl_prompt(prompt, context)
    raw_generated = generate_llm_text(dsl_prompt, temperature=0.2, max_output_tokens=3500)
    print("OpenRouter generation completed")
    
    response_json = sanitize_json(raw_generated)
    
    validation_result = validate_simulation(response_json)
    if not validation_result["success"]:
        raise ValueError(f"EduSimResponse validation failed: {validation_result['errors']}")
    
    valid_response = validation_result["data"]
    simulation_id = str(uuid4())

    # Final item for storage (preserves structure while adding internal tracking)
    item = {
        "id": simulation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sources": _build_sources(chunks),
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
        # Return summary structure
        trimmed.append(
            {
                "id": item.get("id"),
                "title": item.get("dsl", {}).get("meta", {}).get("title"),
                "topic": item.get("metadata", {}).get("topic"),
                "timestamp": item.get("timestamp"),
            }
        )

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
        
        # Event 1: Started
        yield _format_sse_event("started", {"id": simulation_id, "stage": "Initializing..."})

        # Event 2: Retrieving context
        yield _format_sse_event("progress", {"stage": "Retrieving textbook context..."})
        retriever = _load_retriever()
        raw_chunks = retriever(prompt)[:10] if retriever else []
        chunks = raw_chunks[:6]
        
        yield _format_sse_event("progress", {"stage": f"Retrieved {len(chunks)} context chunks"})

        # Event 3: Calling LLM
        yield _format_sse_event("progress", {"stage": "Synthesizing Architecture with AI..."})
        context = _build_context_block(chunks)
        dsl_prompt = build_dsl_prompt(prompt, context)
        raw_generated = generate_llm_text(dsl_prompt, temperature=0.2, max_output_tokens=3500)
        
        # Event 4: Sanitizing and Validating
        yield _format_sse_event("progress", {"stage": "Validating EduSim Contract..."})
        response_json = sanitize_json(raw_generated)
        validation_result = validate_simulation(response_json)
        
        if not validation_result["success"]:
            raise ValueError(f"Validation failed: {validation_result['errors']}")
        
        valid_response = validation_result["data"]

        # Event 5: Saving
        yield _format_sse_event("progress", {"stage": "Saving to store..."})
        item = {
            "id": simulation_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources": _build_sources(chunks),
            **valid_response
        }

        with _store_lock:
            items = _read_store()
            items.insert(0, item)
            _write_store(items)

        # Event 6: Complete
        yield _format_sse_event("complete", item)

    except Exception as e:
        yield _format_sse_event("error", {"error": str(e), "type": type(e).__name__})