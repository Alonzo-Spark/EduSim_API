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
from .templates import detect_subject, get_system_prompt, get_user_content_enhancement, SubjectType
from .sanitizer import sanitize_html, validate_html_safety_beautifulsoup


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


def _call_gemini_for_html(user_prompt: str, context: str, extracted: dict[str, list[str]], subject: SubjectType = "physics"):
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is missing. Add it to .env to enable synthesis.")

    print("Gemini request started: simulation synthesis")
    system_prompt = get_system_prompt(subject)
    subject_enhancement = get_user_content_enhancement(subject, extracted)
    final_prompt = (
        f"{system_prompt}\n\n"
        f"User intent: {user_prompt}\n\n"
        f"{subject_enhancement}\n\n"
        f"Retrieved textbook context:\n{context}\n\n"
        f"Extracted formulas: {extracted.get('formulas', [])}\n"
        f"Extracted constants: {extracted.get('constants', [])}\n"
        f"Extracted laws: {extracted.get('laws', [])}\n"
        f"Extracted definitions: {extracted.get('definitions', [])}\n\n"
        "Return only a complete HTML document starting with <!DOCTYPE html>."
    )

    generated = generate_gemini_text(final_prompt, temperature=0.2, max_output_tokens=3500)
    print("Gemini generation completed: simulation synthesis")
    return generated


def _extract_html_document(raw_output: str):
    cleaned = raw_output.strip()

    fenced = re.search(r"```(?:html)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()

    if "<!DOCTYPE html" in cleaned:
        idx = cleaned.find("<!DOCTYPE html")
        cleaned = cleaned[idx:]

    if not cleaned.lower().startswith("<!doctype html"):
        raise ValueError("Model output is not a complete HTML document.")

    return cleaned


def _inject_csp(html: str):
    csp_meta = (
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
        "img-src data:; font-src data:; connect-src 'none'; media-src 'none'; frame-src 'none'; "
        "object-src 'none'; base-uri 'none'; form-action 'none'\">"
    )

    if re.search(r"http-equiv\s*=\s*['\"]Content-Security-Policy['\"]", html, flags=re.IGNORECASE):
        return html

    if "<head>" in html:
        return html.replace("<head>", f"<head>\n  {csp_meta}", 1)

    if "<html" in html:
        return re.sub(r"(<html[^>]*>)", rf"\1\n<head>\n  {csp_meta}\n</head>", html, count=1)

    return html


def _validate_generated_html(html: str):
    blocked_patterns = [
        r"<script[^>]+src\s*=",
        r"https?://",
        r"\bfetch\s*\(",
        r"XMLHttpRequest",
        r"WebSocket",
        r"navigator\.sendBeacon",
        r"window\.open",
        r"document\.cookie",
        r"localStorage",
        r"sessionStorage",
        r"\btop\.",
        r"\bparent\.",
        r"<iframe",
        r"<object",
        r"<embed",
        r"<form",
        r"<link[^>]+href",
        r"\beval\s*\(",
        r"new\s+Function\s*\(",
    ]

    for pattern in blocked_patterns:
        if re.search(pattern, html, flags=re.IGNORECASE):
            raise ValueError(f"Generated HTML contains blocked content pattern: {pattern}")


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
        source = os.path.basename(chunk.get("source", "Textbook"))
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
    
    # Call Gemini with subject-specific template
    generated = _call_gemini_for_html(prompt, context, extracted, subject=subject)
    html = _extract_html_document(generated)
    
    # Regex-based validation (first layer)
    _validate_generated_html(html)
    
    # BeautifulSoup-based sanitization (second layer - defense-in-depth)
    html = sanitize_html(html)
    
    # Additional BeautifulSoup validation (third layer)
    validate_html_safety_beautifulsoup(html)
    
    # CSP injection (fourth layer)
    html = _inject_csp(html)

    title = topic or _guess_topic(prompt)
    formula = extracted.get("formulas", [""])[0] if extracted.get("formulas") else ""
    description = f"AI-synthesized interactive simulation for: {prompt.strip()}"
    sources = _build_sources(chunks)

    item = {
        "id": str(uuid4()),
        "title": title,
        "description": description,
        "formula": formula,
        "sources": sources,
        "topic": title,
        "prompt": prompt,
        "subject": subject,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "html": html,
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

        # Event 4: Calling LLM for synthesis
        yield _format_sse_event("progress", {"stage": "Synthesizing simulation with AI..."})
        generated = _call_gemini_for_html(prompt, context, extracted, subject=subject)
        
        # Event 5: Extracting HTML
        yield _format_sse_event("progress", {"stage": "Extracting HTML document..."})
        html = _extract_html_document(generated)

        # Event 6: Validating
        yield _format_sse_event("progress", {"stage": "Validating HTML safety (regex)..."})
        _validate_generated_html(html)
        
        # Event 7: Sanitizing
        yield _format_sse_event("progress", {"stage": "Sanitizing HTML with BeautifulSoup..."})
        html = sanitize_html(html)
        
        # Event 8: Additional validation
        yield _format_sse_event("progress", {"stage": "Running final safety checks..."})
        validate_html_safety_beautifulsoup(html)
        
        # Event 9: CSP injection
        yield _format_sse_event("progress", {"stage": "Injecting Content-Security-Policy..."})
        html = _inject_csp(html)

        # Event 10: Saving
        yield _format_sse_event("progress", {"stage": "Saving simulation to store..."})
        title = topic or _guess_topic(prompt)
        formula = extracted.get("formulas", [""])[0] if extracted.get("formulas") else ""
        description = f"AI-synthesized interactive simulation for: {prompt.strip()}"
        sources = _build_sources(chunks)

        item = {
            "id": simulation_id,
            "title": title,
            "description": description,
            "formula": formula,
            "sources": sources,
            "topic": title,
            "prompt": prompt,
            "subject": subject,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "html": html,
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