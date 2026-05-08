import re
import os
from typing import Any, Optional
from pathlib import Path
from .models import SimulationContext, SimulationTopic
from rag.retriever import get_retriever
import faiss
from sentence_transformers import SentenceTransformer
import pickle


def _load_retriever():
    """Load and initialize the RAG retriever."""
    INDEX_FILE = Path("faiss_index/index.faiss")
    METADATA_FILE = Path("faiss_index/metadata.pkl")
    
    if not INDEX_FILE.exists() or not METADATA_FILE.exists():
        return None

    index = faiss.read_index(str(INDEX_FILE))
    with open(METADATA_FILE, "rb") as file:
        metadata = pickle.load(file)

    embeddings_model = SentenceTransformer("all-MiniLM-L6-v2")
    return get_retriever(index, metadata, embeddings_model, k=12)


def _extract_patterns(pattern: str, text: str, max_items: int = 10) -> list[str]:
    """Extract matching patterns from text."""
    items = []
    for match in re.findall(pattern, text, flags=re.IGNORECASE):
        candidate = match.strip()
        if candidate and candidate not in items:
            items.append(candidate)
        if len(items) >= max_items:
            break
    return items


def retrieve_context(prompt: str, topic: SimulationTopic) -> SimulationContext:
    """
    Retrieve enhanced context from textbooks using RAG.
    
    Args:
        prompt: User prompt
        topic: Detected topic information
        
    Returns:
        SimulationContext with formulas, constants, laws, and definitions
    """
    # Load retriever
    retriever = _load_retriever()
    if not retriever:
        return SimulationContext(
            topic=topic.topic,
            formulas=[],
            constants=[],
            laws=[],
            definitions=[],
            sources=[]
        )
    
    # Retrieve chunks
    chunks = retriever(prompt)[:10] if retriever else []
    
    # Build text blob from chunks
    text_blob = "\n".join(chunk.get("text", "") for chunk in chunks)
    
    # Extract formulas: Match patterns like "F = ma", "v = at", "E = mc²"
    formulas = _extract_patterns(
        r"([A-Za-z][A-Za-z0-9_]?\s*=\s*[^.\n;]{5,80})",
        text_blob,
        max_items=12,
    )
    
    # Extract constants: g, c, h, G, R, etc.
    constants = _extract_patterns(
        r"((?:g|G|c|h|R|k|π|e|m_e|m_p|k_B)\s*[=≈]\s*[-+]?\d+(?:\.\d+)?(?:\s*[×]?\s*10^[-+]?\d+)?\s*[A-Za-z/0-9²³⁻]*)",
        text_blob,
        max_items=8,
    )
    
    # Extract laws/principles: Match lines containing "law" or "principle"
    laws = _extract_patterns(
        r"([^\n.]{10,150}(?:law|principle|theorem|rule)[^\n.]*)",
        text_blob,
        max_items=8,
    )
    
    # Extract definitions: Match "is defined as", "refers to", "means"
    definitions = _extract_patterns(
        r"([^\n.]{15,160}(?:is defined as|refers to|means|is the|denoted by)[^\n.]*)",
        text_blob,
        max_items=8,
    )
    
    # Extract worked examples (sentences containing "example", "for instance", "such as")
    worked_examples = _extract_patterns(
        r"([^\n.]{20,200}(?:example|for instance|such as|illustration)[^\n.]*)",
        text_blob,
        max_items=5,
    )
    
    # Build sources list
    sources = _build_sources(chunks)
    
    return SimulationContext(
        topic=topic.topic,
        formulas=formulas,
        constants=constants,
        laws=laws,
        definitions=definitions,
        worked_examples=worked_examples,
        sources=sources,
    )


def _build_sources(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract unique sources from retrieved chunks."""
    sources = []
    seen = set()
    
    for chunk in chunks:
        source = os.path.basename(chunk.get("source", "Textbook"))
        page = chunk.get("page", "?")
        key = f"{source}:{page}"
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "source": source,
            "page": page,
            "text_snippet": chunk.get("text", "")[:200]
        })
    
    return sources


def build_enhanced_context_prompt(
    prompt: str,
    topic: SimulationTopic,
    context: SimulationContext,
    for_html_generation: bool = True
) -> str:
    """
    Build an enhanced prompt for Gemini that includes context and specific instructions.
    
    Args:
        prompt: User's natural language prompt
        topic: Detected topic information
        context: Retrieved textbook context
        for_html_generation: If True, format for HTML generation
        
    Returns:
        Formatted prompt for Gemini
    """
    lines = []
    
    # Title and subject
    lines.append(f"# Task: Generate Interactive {topic.subject.title()} Simulation")
    lines.append(f"**Topic**: {topic.topic}")
    lines.append(f"**Grade Level**: {topic.grade_level or 'Not specified'}")
    lines.append(f"**Complexity**: {topic.complexity}")
    lines.append("")
    
    # User's intent
    lines.append(f"## User Request")
    lines.append(f"{prompt}")
    lines.append("")
    
    # Textbook context
    if context.formulas or context.laws or context.definitions:
        lines.append("## Textbook Context")
        lines.append("")
        
        if context.formulas:
            lines.append(f"**Key Formulas**:")
            for formula in context.formulas[:5]:
                lines.append(f"  - {formula}")
            lines.append("")
        
        if context.constants:
            lines.append(f"**Physical Constants**:")
            for const in context.constants[:5]:
                lines.append(f"  - {const}")
            lines.append("")
        
        if context.laws:
            lines.append(f"**Laws & Principles**:")
            for law in context.laws[:4]:
                lines.append(f"  - {law}")
            lines.append("")
        
        if context.definitions:
            lines.append(f"**Key Definitions**:")
            for defn in context.definitions[:4]:
                lines.append(f"  - {defn}")
            lines.append("")
    
    # For HTML generation, add specific requirements
    if for_html_generation:
        lines.append("## Generation Requirements")
        lines.append("")
        lines.append("Generate a **complete, self-contained HTML file** with:")
        lines.append("")
        lines.append("### Visual Requirements")
        lines.append("  - Responsive dark futuristic UI (dark background with neon accents)")
        lines.append("  - Canvas-based animations at 60 FPS")
        lines.append("  - Smooth transitions and visual feedback")
        lines.append("  - Educational annotations showing formulas")
        lines.append("  - Real-time value displays")
        lines.append("")
        lines.append("### Interactive Requirements")
        lines.append("  - Multiple sliders/inputs for parameter control")
        lines.append("  - Play/Pause/Reset buttons")
        lines.append("  - Live calculation displays")
        lines.append("  - Visual indicators of forces, vectors, or energy states")
        lines.append("")
        lines.append("### Technical Requirements")
        lines.append("  - No external libraries (no CDN imports)")
        lines.append("  - All CSS inline in <style> tag")
        lines.append("  - All JavaScript inline in <script> tag")
        lines.append("  - Must run in modern browsers (Chrome, Firefox, Safari, Edge)")
        lines.append("  - No network requests (no fetch, XMLHttpRequest, or WebSocket)")
        lines.append("  - No localStorage, sessionStorage, or cookies")
        lines.append("")
        lines.append("### Output Format")
        lines.append("Return **ONLY** the HTML starting with `<!DOCTYPE html>`")
        lines.append("No markdown, no code fences, no explanations.")
    
    return "\n".join(lines)


def extract_interaction_hints(prompt: str, context: SimulationContext) -> list[dict[str, Any]]:
    """
    Extract hints about what interactive controls might be useful.
    
    Args:
        prompt: User prompt
        context: Retrieved context
        
    Returns:
        List of suggested interactions
    """
    interactions = []
    prompt_lower = prompt.lower()
    
    # Physics-specific interactions
    if any(word in prompt_lower for word in ["projectile", "launch", "throw"]):
        interactions.extend([
            {"name": "angle", "label": "Launch Angle", "unit": "°", "min": 0, "max": 90},
            {"name": "velocity", "label": "Initial Velocity", "unit": "m/s", "min": 0, "max": 100},
        ])
    
    if any(word in prompt_lower for word in ["gravity", "gravitational", "fall"]):
        interactions.append(
            {"name": "gravity", "label": "Gravity", "unit": "m/s²", "min": 0, "max": 20}
        )
    
    if any(word in prompt_lower for word in ["pendulum", "swing", "oscillate"]):
        interactions.extend([
            {"name": "length", "label": "Pendulum Length", "unit": "m", "min": 0.1, "max": 5},
            {"name": "angle", "label": "Initial Angle", "unit": "°", "min": -60, "max": 60},
        ])
    
    if any(word in prompt_lower for word in ["mass", "weight"]):
        interactions.append(
            {"name": "mass", "label": "Mass", "unit": "kg", "min": 0.1, "max": 100}
        )
    
    if any(word in prompt_lower for word in ["speed", "velocity", "momentum"]):
        interactions.append(
            {"name": "velocity", "label": "Velocity", "unit": "m/s", "min": 0, "max": 50}
        )
    
    if any(word in prompt_lower for word in ["spring", "elastic", "oscillation"]):
        interactions.extend([
            {"name": "k", "label": "Spring Constant", "unit": "N/m", "min": 1, "max": 100},
            {"name": "amplitude", "label": "Amplitude", "unit": "m", "min": 0.1, "max": 5},
        ])
    
    if any(word in prompt_lower for word in ["frequency", "wave"]):
        interactions.extend([
            {"name": "frequency", "label": "Frequency", "unit": "Hz", "min": 0.1, "max": 10},
            {"name": "amplitude", "label": "Amplitude", "unit": "m", "min": 0.1, "max": 5},
        ])
    
    # Add reset/play buttons if not present
    if not any(interaction["name"] == "play" for interaction in interactions):
        interactions.append({"name": "play", "label": "Play/Pause", "type": "button"})
    
    return interactions
