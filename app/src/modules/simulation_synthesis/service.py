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
from rag.generator import generate_gemini_text
from .templates import detect_subject
from .prompt_builder import build_dsl_prompt
from .sanitizer import sanitize_json
from .validator import validate_simulation


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash"

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


def _extract_items(pattern: str, text: str, max_items: int = 8):
    items = []
    for match in re.findall(pattern, text, flags=re.IGNORECASE):
        candidate = match.strip()
        if candidate and candidate not in items:
            items.append(candidate)
        if len(items) >= max_items:
            break
    return items


def _extract_context_features(chunks: list[dict[str, Any]]):
    text_blob = "\n".join(chunk.get("text", "") for chunk in chunks)

    formulas = _extract_items(
        r"([A-Za-z][A-Za-z0-9_ ]{0,30}\s*=\s*[-+*/(). A-Za-z0-9^]+)",
        text_blob,
        max_items=10,
    )
    constants = _extract_items(
        r"((?:g|c|h|G|R)\s*=\s*[-+]?\d+(?:\.\d+)?\s*[A-Za-z/0-9^]*)",
        text_blob,
        max_items=6,
    )
    laws = _extract_items(r"([^\n.]{5,120}(?:law|principle)[^\n.]*)", text_blob, max_items=8)
    definitions = _extract_items(
        r"([^\n.]{8,140}(?:is defined as|refers to|means)[^\n.]*)",
        text_blob,
        max_items=8,
    )

    return {
        "formulas": formulas,
        "constants": constants,
        "laws": laws,
        "definitions": definitions,
    }


def _build_context_block(chunks: list[dict[str, Any]]):
    lines = []
    for chunk in chunks:
        source = os.path.basename(chunk.get("source", "Textbook"))
        page = chunk.get("page", "?")
        text = re.sub(r"\s+", " ", chunk.get("text", "")).strip()
        lines.append(f"Source: {source} | Page: {page}\n{text}")
    return "\n\n".join(lines)


# HTML generation functions removed in favor of JSON DSL


def _read_store():
    if not PERSISTENCE_FILE.exists():
        return []

    with open(PERSISTENCE_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def _write_store(items: list[dict[str, Any]]):
    PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERSISTENCE_FILE, "w", encoding="utf-8") as file:
        json.dump(items, file, indent=2, ensure_ascii=True)


def _guess_topic(prompt: str):
    """
    Improved topic/subject detection using template-based classification.
    Returns a descriptive topic title based on detected subject and keywords.
    """
    lowered = prompt.lower()
    
    # Specific topic patterns for better granularity
    specific_topics = {
        "projectile motion": ["projectile", "launch", "trajectory", "angle", "range"],
        "pendulum": ["pendulum", "swing", "oscillate"],
        "circular motion": ["circular", "centripetal", "angular velocity", "orbit"],
        "momentum": ["momentum", "collision", "elastic", "inelastic"],
        "waves": ["wave", "frequency", "wavelength", "amplitude", "oscillation"],
        "refraction": ["refraction", "lens", "prism", "light"],
        "molecular structure": ["molecule", "atom", "bond", "electron"],
        "chemical reaction": ["reaction", "oxidation", "reduction", "catalyst"],
        "orbital mechanics": ["orbit", "gravity", "planet", "kepler"],
        "cell biology": ["cell", "mitochondria", "chloroplast", "organelle"],
        "photosynthesis": ["photosynthesis", "chlorophyll", "glucose"],
        "functions": ["function", "graph", "equation", "polynomial"],
    }
    
    for topic, keywords in specific_topics.items():
        if any(kw in lowered for kw in keywords):
            return topic.title()
    
    # Fall back to subject-based title
    subject = detect_subject(prompt)
    subject_titles = {
        "physics": "Physics Simulation",
        "chemistry": "Chemistry Visualization",
        "astronomy": "Astronomy Simulation",
        "biology": "Biology Visualization",
        "mathematics": "Mathematics Visualization",
    }
    return subject_titles.get(subject, "AI Generated Simulation")


def _build_sources(chunks: list[dict[str, Any]]):
    sources = []
    seen = set()

    for chunk in chunks:
        # Handle both Windows and Linux paths correctly
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
    # Detect subject from prompt (used for template selection)
    subject = detect_subject(prompt)
    
    print("Gemini request started: simulation retrieval")
    retriever = _load_retriever()
    chunks = retriever(prompt)[:8] if retriever else []
    print(f"Gemini retrieval completed: {len(chunks)} chunks")

    context = _build_context_block(chunks)
    extracted = _extract_context_features(chunks)
    
    print("Gemini request started: DSL synthesis")
    dsl_prompt = build_dsl_prompt(prompt, context, extracted)
    raw_generated = generate_gemini_text(dsl_prompt, temperature=0.2, max_output_tokens=3500)
    print("Gemini generation completed: DSL synthesis")
    
    # Sanitize and parse JSON
    dsl_json = sanitize_json(raw_generated)
    
    # Validate DSL
    validation_result = validate_simulation(dsl_json)
    if not validation_result["success"]:
        raise ValueError(f"DSL validation failed: {validation_result['errors']}")
    
    valid_dsl = validation_result["data"]

    title = topic or _guess_topic(prompt)
    formula = extracted.get("formulas", [""])[0] if extracted.get("formulas") else ""
    description = f"AI-synthesized interactive simulation for: {prompt.strip()}"
    sources = _build_sources(chunks)

    topic_info = {
        "topic": title,
        "subject": subject,
        "complexity": "medium"
    }

    context_info = {
        "topic": title,
        "formulas": extracted.get("formulas", []),
        "constants": extracted.get("constants", []),
        "laws": extracted.get("laws", []),
        "definitions": extracted.get("definitions", []),
        "sources": sources
    }

    item = {
        "id": str(uuid4()),
        "title": title,
        "description": description,
        "topic": topic_info,
        "dsl": valid_dsl,
        "formula": formula,
        "formulas": extracted.get("formulas", []),
        "learning_objectives": [],
        "related_concepts": [],
        "interactions": [],
        "context": context_info,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "generation_stages": ["Started", "Retrieved", "Synthesized", "Complete"]
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
        trimmed.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "description": item.get("description"),
                "formula": item.get("formula"),
                "sources": item.get("sources", []),
                "topic": item.get("topic"),
                "prompt": item.get("prompt"),
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
    """
    Format a Server-Sent Events (SSE) message.
    Format: event: <type>\ndata: <json>\n\n
    """
    if isinstance(data, dict):
        import json
        data = json.dumps(data)
    return f"event: {event_type}\ndata: {data}\n\n"


def generate_simulation_synthesis_stream(prompt: str, topic: str | None = None):
    """
    Streaming version of simulation synthesis.
    Yields SSE events showing progress at each stage.
    
    Events emitted:
    - started: Initial event with simulation ID
    - progress: Stage updates (retrieving, extracting, synthesizing, validating, rendering)
    - complete: Final event with complete simulation object
    - error: Error event (if something fails)
    """
    import json as json_module
    
    try:
        simulation_id = str(uuid4())
        
        # Event 1: Started
        yield _format_sse_event("started", {"id": simulation_id, "stage": "Initializing..."})

        # Detect subject
        subject = detect_subject(prompt)
        yield _format_sse_event("progress", {"stage": "Detecting subject: " + subject})

        # Event 2: Retrieving context
        yield _format_sse_event("progress", {"stage": "Retrieving textbook context..."})
        print("Gemini request started: simulation retrieval")
        retriever = _load_retriever()
        chunks = retriever(prompt)[:8] if retriever else []
        print(f"Gemini retrieval completed: {len(chunks)} chunks")
        yield _format_sse_event("progress", {"stage": f"Retrieved {len(chunks)} context chunks"})

        # Event 3: Extracting features
        yield _format_sse_event("progress", {"stage": "Extracting formulas and concepts..."})
        context = _build_context_block(chunks)
        extracted = _extract_context_features(chunks)
        yield _format_sse_event("progress", {
            "stage": f"Extracted {len(extracted.get('formulas', []))} formulas, {len(extracted.get('constants', []))} constants"
        })

        # Event 4: Calling LLM for DSL synthesis
        yield _format_sse_event("progress", {"stage": "Synthesizing Physics DSL with AI..."})
        dsl_prompt = build_dsl_prompt(prompt, context, extracted)
        raw_generated = generate_gemini_text(dsl_prompt, temperature=0.2, max_output_tokens=3500)
        
        # Event 5: Sanitizing JSON
        yield _format_sse_event("progress", {"stage": "Sanitizing and parsing JSON..."})
        dsl_json = sanitize_json(raw_generated)

        # Event 6: Validating DSL Schema
        yield _format_sse_event("progress", {"stage": "Validating DSL schema..."})
        validation_result = validate_simulation(dsl_json)
        if not validation_result["success"]:
            raise ValueError(f"DSL validation failed: {validation_result['errors']}")
        
        valid_dsl = validation_result["data"]

        # Event 10: Saving
        yield _format_sse_event("progress", {"stage": "Saving simulation to store..."})
        title = topic or _guess_topic(prompt)
        formula = extracted.get("formulas", [""])[0] if extracted.get("formulas") else ""
        description = f"AI-synthesized interactive simulation for: {prompt.strip()}"
        sources = _build_sources(chunks)

        topic_info = {
            "topic": title,
            "subject": subject,
            "complexity": "medium"
        }

        context_info = {
            "topic": title,
            "formulas": extracted.get("formulas", []),
            "constants": extracted.get("constants", []),
            "laws": extracted.get("laws", []),
            "definitions": extracted.get("definitions", []),
            "sources": sources
        }

        item = {
            "id": simulation_id,
            "title": title,
            "description": description,
            "topic": topic_info,
            "dsl": valid_dsl,
            "formula": formula,
            "formulas": extracted.get("formulas", []),
            "learning_objectives": [],
            "related_concepts": [],
            "interactions": [],
            "context": context_info,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "generation_stages": ["Started", "Retrieved", "Synthesized", "Complete"]
        }

        with _store_lock:
            items = _read_store()
            items.insert(0, item)
            _write_store(items)

        # Event 11: Complete
        yield _format_sse_event("complete", item)

    except Exception as e:
        error_msg = str(e)
        yield _format_sse_event("error", {"error": error_msg, "type": type(e).__name__})