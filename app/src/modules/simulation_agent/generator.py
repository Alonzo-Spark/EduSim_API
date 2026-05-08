import os
import json
from pathlib import Path
import google.generativeai as genai
from typing import Optional
from datetime import datetime, timezone
from uuid import uuid4

from .models import (
    SimulationTopic,
    SimulationContext,
    SimulationInteraction,
    AgentGenerateResponse,
)
from .analyzer import (
    generate_title_from_topic,
    extract_learning_objectives,
    extract_related_concepts,
)
from .context_builder import (
    build_enhanced_context_prompt,
    extract_interaction_hints,
)
from app.src.modules.simulation_synthesis.sanitizer import sanitize_html, validate_html_safety_beautifulsoup


GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_FALLBACK_MODEL = "gemini-flash-latest"
GENERATED_SIMULATIONS_DIR = Path("generated_simulations")


def _configure_gemini(model_name: str = GEMINI_MODEL):
    """Configure and return Gemini model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing. Add it to .env to enable Gemini generation.")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)


def _call_gemini_for_simulation(enhanced_prompt: str, temperature: float = 0.2, max_tokens: int = 4000) -> str:
    """Call Gemini API to generate simulation HTML."""
    last_error = None
    
    for model_name in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL):
        try:
            model = _configure_gemini(model_name)
            response = model.generate_content(
                enhanced_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
            )
            
            generated_text = getattr(response, "text", None)
            if not generated_text:
                raise ValueError("Gemini returned an empty response.")
            
            return generated_text.strip()
        except Exception as e:
            last_error = e
            if model_name != GEMINI_FALLBACK_MODEL:
                print(f"Gemini primary model failed ({model_name}); trying fallback {GEMINI_FALLBACK_MODEL}: {e}")
    
    raise RuntimeError(f"Gemini generation failed: {str(last_error)}") from last_error


def _extract_html_from_response(raw_output: str) -> str:
    """Extract HTML document from Gemini response."""
    import re
    
    cleaned = raw_output.strip()
    
    # Try to extract from markdown code fence
    fenced = re.search(r"```(?:html)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    
    # Find start of HTML
    if "<!DOCTYPE html" in cleaned:
        idx = cleaned.find("<!DOCTYPE html")
        cleaned = cleaned[idx:]
    
    # Validate
    if not cleaned.lower().startswith("<!doctype html"):
        raise ValueError("Model output does not contain a valid HTML document.")
    
    return cleaned


def _validate_html_safety(html: str) -> None:
    """Validate generated HTML against security patterns."""
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
    
    import re
    for pattern in blocked_patterns:
        if re.search(pattern, html, flags=re.IGNORECASE):
            raise ValueError(f"Generated HTML contains blocked content: {pattern}")


def _inject_csp(html: str) -> str:
    """Inject Content-Security-Policy meta tag."""
    import re
    
    csp_meta = (
        '<meta http-equiv="Content-Security-Policy" '
        'content="default-src \'none\'; script-src \'unsafe-inline\'; style-src \'unsafe-inline\'; '
        'img-src data:; font-src data:; connect-src \'none\'; media-src \'none\'; frame-src \'none\'; '
        'object-src \'none\'; base-uri \'none\'; form-action \'none\'">'
    )
    
    # Check if already present
    if re.search(r'http-equiv\s*=\s*["\']Content-Security-Policy["\']', html, flags=re.IGNORECASE):
        return html
    
    # Insert in head
    if "<head>" in html:
        return html.replace("<head>", f"<head>\n  {csp_meta}", 1)
    
    # Insert after html tag
    if "<html" in html:
        return re.sub(r"(<html[^>]*>)", rf"\1\n<head>\n  {csp_meta}\n</head>", html, count=1)
    
    return html


def _slugify_filename(text: str, max_length: int = 50) -> str:
    """Convert text to slug for filename."""
    import re
    
    slug = re.sub(r'[^a-z0-9]+', '_', text.lower())
    slug = slug.strip('_')
    return slug[:max_length]


def _save_generated_html(html: str, topic: SimulationTopic, prompt: str) -> str:
    """Save generated HTML to file."""
    GENERATED_SIMULATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = int(datetime.now(timezone.utc).timestamp())
    slug = _slugify_filename(topic.topic)
    filename = f"{slug}_{timestamp}.html"
    
    file_path = GENERATED_SIMULATIONS_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return str(file_path)


def generate_simulation_with_agent(
    prompt: str,
    topic: SimulationTopic,
    context: SimulationContext,
) -> tuple[str, list[str], str | None]:
    """
    Generate simulation HTML using AI agent pipeline.
    
    Args:
        prompt: User prompt
        topic: Detected topic
        context: Retrieved context
        
    Returns:
        Tuple of (html, generation_stages)
    """
    stages = ["Initializing"]
    
    # Stage 1: Build enhanced prompt
    stages.append("Building enhanced prompt")
    enhanced_prompt = build_enhanced_context_prompt(prompt, topic, context, for_html_generation=True)
    
    # Stage 2: Call Gemini
    stages.append("Calling Gemini API for synthesis")
    raw_response = None
    try:
        raw_response = _call_gemini_for_simulation(enhanced_prompt)
    except Exception as e:
        # LLM call failed entirely
        stages.append(f"Gemini failed: {str(e)}")
        return "", stages, str(e)

    # Stage 3: Extract HTML
    stages.append("Extracting HTML from response")
    try:
        html = _extract_html_from_response(raw_response)
    except Exception as e:
        # Could not extract HTML — return raw_response for repair
        stages.append(f"HTML extraction failed: {str(e)}")
        return (raw_response or "", stages, str(e))

    # Stage 4: Validate security (regex-based)
    stages.append("Validating HTML safety (regex)")
    try:
        _validate_html_safety(html)
    except Exception as e:
        stages.append(f"Regex validation failed: {str(e)}")
        return (html, stages, str(e))
    
    # Stage 5: Sanitize with BeautifulSoup
    stages.append("Sanitizing HTML with BeautifulSoup")
    try:
        html = sanitize_html(html)
    except Exception as e:
        stages.append(f"Sanitization failed: {str(e)}")
        return (html, stages, str(e))
    
    # Stage 6: Additional validation
    stages.append("Running final safety checks")
    try:
        validate_html_safety_beautifulsoup(html)
    except Exception as e:
        stages.append(f"BeautifulSoup validation failed: {str(e)}")
        return (html, stages, str(e))
    
    # Stage 7: Inject CSP
    stages.append("Injecting Content-Security-Policy")
    html = _inject_csp(html)

    # Success
    return html, stages, None


def build_agent_response(
    prompt: str,
    topic: SimulationTopic,
    context: SimulationContext,
    html: str,
    html_path: Optional[str] = None,
    stages: Optional[list[str]] = None,
) -> AgentGenerateResponse:
    """
    Build the complete response object from agent generation.
    
    Args:
        prompt: Original user prompt
        topic: Detected topic
        context: Retrieved context
        html: Generated HTML
        html_path: Optional saved HTML file path
        stages: Generation stages completed
        
    Returns:
        AgentGenerateResponse
    """
    # Get primary formula
    primary_formula = context.formulas[0] if context.formulas else None
    
    # Build interactions
    interactions = []
    for hint in extract_interaction_hints(prompt, context):
        interactions.append(SimulationInteraction(**hint))
    
    # Get learning objectives and related concepts
    learning_objectives = extract_learning_objectives(prompt, topic)
    related_concepts = extract_related_concepts(topic)
    
    # Generate title
    title = generate_title_from_topic(topic)
    description = f"AI-generated interactive simulation for {topic.topic.lower()}"
    
    response = AgentGenerateResponse(
        success=True,
        id=str(uuid4()),
        title=title,
        description=description,
        topic=topic,
        html=html,
        formula=primary_formula,
        formulas=context.formulas,
        learning_objectives=learning_objectives,
        related_concepts=related_concepts,
        interactions=interactions,
        context=context,
        html_path=html_path,
        timestamp=datetime.now(timezone.utc),
        generation_stages=stages or [],
    )
    
    return response


def store_agent_response(response: AgentGenerateResponse) -> None:
    """Store agent response metadata."""
    PERSISTENCE_FILE = Path("data/agent_generations.json")
    
    # Create data directory
    PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing data
    if PERSISTENCE_FILE.exists():
        with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
            items = json.load(f)
    else:
        items = []
    
    # Convert response to dict (excluding html for storage)
    item_dict = response.model_dump()
    item_dict["html"] = ""  # Don't store full HTML in metadata
    item_dict["timestamp"] = response.timestamp.isoformat()
    
    # Add to beginning of list
    items.insert(0, item_dict)
    
    # Keep only latest 100
    items = items[:100]
    
    # Write back
    with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=True)
