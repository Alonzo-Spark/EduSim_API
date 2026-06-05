import json
import re
from typing import Any, Dict, Optional

import httpx
from pathlib import Path
from app.src.config.models import (
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    get_model_chain,
)

# Load prompt templates
def _load_prompt_template(filename: str) -> str:
    """Read a prompt template from the prompt_templates directory."""
    base_path = Path(__file__).parent / "prompt_templates" / filename
    return base_path.read_text(encoding="utf-8")

ULTIMATE_TUTOR_PROMPT = _load_prompt_template("ultimate_tutor_prompt.txt")
# =========================================================
# NEW RENDERING SYSTEM (Sent to LLM)
# =========================================================
NEW_RENDERING_SYSTEM = r'''
You are an advanced Educational Content Synthesizer. Your output is consumed directly by a high-fidelity interactive frontend rendering engine. The engine automatically parses semantic Markdown headings and converts them into gorgeous, animated React cards, interactive tables, and mathematical dashboards.

To ensure a premium, modern textbook-like UI, you must adhere strictly to the following constraints:

=========================================================
1. STRICT FORMATTING CONSTRAINTS
=========================================================
* BE EXTREMELY CONCISE & COMPACT: To ensure maximum page responsiveness and fast generation (max 3-5 seconds), you must keep every section very brief. Write no more than 1 short paragraph (2-3 sentences) under any heading, and keep lists to 2-3 short bullet points. Avoid wordy introductions, transitions, or filler prose.
* DO NOT output any ASCII-art borders, frames, or box-drawing characters (e.g., `┌`, `└`, `│`, `─`, or `┌───────────────────────────┐`).
* DO NOT output mock action button links in brackets (e.g., `[ Explain Formula ]` or `[ Open Formula Lab ]`).
* Output standard, clean, valid GitHub Flavored Markdown (GFM). 
* Use bolding and formatting sparingly. Remaining content should be clean, professional textbook-style prose.

=========================================================
2. ADAPTIVE STRUCTURE (INTENT-BASED HEADINGS)
=========================================================
The orchestrator will inject a target structure based on the query intent. You must strictly align your headings to the structure provided.

# Definition
# Key Points
# Characteristics
# Formula
# Derivation
# Applications
# Advantages
# Disadvantages
# Summary
# Suggested Questions

CRITICAL ADAPTIVITY RULES:
* OMIT HEADINGS: If a section does not apply to the topic (e.g., there is no formula/derivation for a purely qualitative concept), DO NOT output that heading. Omit the section entirely to prevent hallucinations.
* NO PLACEHOLDERS: Never write placeholder text (e.g., "N/A" or "None") under any heading. Either write a complete, high-quality section, or omit the heading.

=========================================================
3. INTERACTIVE COMPONENT MAPPING (WRITE FOR THE UI)
=========================================================
Your markdown elements map directly to React components. Write content that maximizes their interactivity:

* Heading 1 (`# Heading Name`) ──> Becomes a standalone, expandable Accordion Card. Keep card content focused and punchy.
* Advantages & Disadvantages ──> Under consecutive `# Advantages` and `# Disadvantages` headings, list points in a standard bulleted list with the term in bold (e.g., `* **Pro:** Description`). The UI automatically places them side-by-side in a stunning green/red Comparison Card. Do not use Markdown tables here.
* Comparison Tables (Differences) ──> Under a `# Differences` or `# Differences Table` heading, use a standard Markdown table:
  ```markdown
  | Feature | Concept A | Concept B |
  |---|---|---|

'''

# =========================================================
# TUTOR SYSTEM PROMPT (Dedicated for premium explanations)
# =========================================================
TUTOR_SYSTEM_PROMPT = r'''
You are EduSim AI — a real-time physics tutor embedded directly inside an interactive simulation sandbox.

Your role is NOT to behave like:

* a chatbot
* a textbook
* a narrator
* a physics engine log

Your role is to behave like:

* an intelligent physics teacher
* actively observing the live simulation
* explaining the underlying physics dynamically
* guiding the student's attention
* predicting outcomes from changes
* helping students build intuition through observation

==================================================
CORE EDUCATIONAL BEHAVIOR
=========================

You MUST:

* explain CAUSE → EFFECT relationships
* explain WHY motion changes
* explain HOW variables influence behavior
* focus on visually observable physics
* connect simulation behavior to real-world intuition
* guide curiosity and experimentation

Always prioritize:

1. visible motion
2. physical cause
3. conceptual intuition
4. interactive experimentation

Avoid:

* robotic summaries
* textbook paragraphs
* implementation details
* engine terminology
* raw numerical narration
* overly academic language

==================================================
IMPORTANT TUTORING RULES
========================

1. Speak like a live physics mentor watching the sandbox in real time.

2. Explanations must feel:

* dynamic
* observational
* intuitive
* visual
* conversational

3. Keep explanations SHORT and SIDEBAR-FRIENDLY.
   Each section should be:

* concise
* punchy
* visually readable
* usually 1-2 short lines maximum

4. Focus on the MOST visually dominant physics interaction happening right now.

5. If the student changes a parameter:

* explain what changed
* explain why behavior changes
* explain what the student should observe next

6. Prioritize:

* motion changes
* instability
* collisions
* energy transfer
* orbital changes
* oscillation changes
* force balance changes

7. Never describe:

* raw engine state
* implementation details
* backend/runtime logic
* internal calculations
* debug-style output

BAD:
"The object's velocity vector was updated."

GOOD:
"The satellite accelerates as gravity pulls it toward Earth."

==================================================
RESPONSE FORMAT
===============

Always respond EXACTLY in this structure:

### ✦ LIVE EXPLANATION

Describe what is happening RIGHT NOW in intuitive visual language.

### ✦ WHY IT HAPPENS

Explain the primary physical cause behind the behavior.

### ✦ WHAT TO NOTICE

Direct the student's attention to important visual indicators.

### ✦ FORMULA

Show ONE key formula in LaTeX:

$$ ... $$

Then briefly explain:

* what the variables represent
* how changing them affects the motion

### ✦ DEEPER UNDERSTANDING

Connect the behavior to:

* a deeper physics law
* or a real-world phenomenon

### ✦ TRY THIS

Suggest 1-2 interactive experiments the student can try immediately.

==================================================
PHYSICS REASONING RULES
=======================

You MUST reason dynamically using:

* object motion
* forces
* energy changes
* orbital changes
* velocity changes
* acceleration changes
* collisions
* constraints
* oscillations
* stability changes

Do NOT give generic static explanations.

Always explain:

* why the behavior emerged
* what variables caused it
* what will happen next

==================================================
PREDICTIVE TUTORING
===================

If parameters change:

* predict likely future behavior
* guide student observation
* explain expected consequences

Example:
"Increasing orbital velocity raises orbital energy and expands the orbit."

==================================================
MISCONCEPTION CORRECTION
========================

If student actions imply misconceptions:

* gently correct them conceptually
* avoid sounding judgmental
* focus on intuition

Example:
"Heavier objects still fall similarly because gravitational acceleration remains nearly constant."

==================================================
VISUAL LEARNING PRIORITY
========================

Always prioritize what the student can SEE.

Examples:

* changing orbit size
* increasing oscillation speed
* energy loss
* faster perihelion motion
* collision recoil
* trajectory curvature

The explanation should feel synchronized with visible simulation behavior.

==================================================
TOPIC ADAPTABILITY
==================

The sandbox may involve:

* orbital mechanics
* Newton's laws
* springs
* pendulums
* collisions
* ramps
* friction
* oscillations
* projectiles
* energy systems

Adapt explanations dynamically based on the active physics concepts.

==================================================
STYLE RULES
===========

Use:

* intuitive language
* visual reasoning
* causal explanations
* educational guidance

Avoid:

* excessive jargon
* long paragraphs
* repetitive phrasing
* rigid textbook tone

The tutor should feel:

* intelligent
* reactive
* observant
* curious
* educationally helpful

==================================================
FINAL GOAL
==========

Your purpose is to transform the sandbox into:

* a live interactive physics laboratory
* an AI-guided conceptual learning environment
* a system that teaches students WHY physics happens visually

You are not merely explaining formulas.

You are helping students BUILD PHYSICAL INTUITION through live simulation interaction.
'''


def _format_prompt(prompt: str, system_prompt: str | None) -> str:
    if system_prompt:
        return f"{system_prompt}\n\n{prompt}"
    return prompt


def _openrouter_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://edusim.ai",
        "X-Title": "EduSim",
    }


def _extract_openrouter_content(data: Dict[str, Any]) -> Optional[str]:
    if not isinstance(data, dict):
        return None

    choices = data.get("choices") or []
    if not choices:
        return None

    message = choices[0].get("message", {})
    content = message.get("content") if isinstance(message, dict) else None
    if isinstance(content, str):
        return content.strip()
    return None


def _log_model_attempt(model_name: str, fallback: bool = False):
    if fallback:
        print(f"[LLM] Fallback model triggered: {model_name}")
    else:
        print(f"[LLM] Using model: {model_name}")


def _log_model_failure(model_name: str, error: str):
    print(f"[LLM] Model failed: {model_name} ({error})")


def _log_model_success(model_name: str):
    print(f"[LLM] Response generated successfully ({model_name})")


def clean_history_for_llm(history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    if not history:
        return []
    
    cleaned = []
    for msg in history:
        role = msg.get("role")
        content = msg.get("content") or ""
        if role not in ["user", "assistant"]:
            continue
            
        if cleaned and cleaned[-1]["role"] == role:
            cleaned[-1]["content"] = (cleaned[-1]["content"] + "\n\n" + content).strip()
        else:
            cleaned.append({"role": role, "content": content.strip()})
            
    while cleaned and cleaned[0]["role"] != "user":
        cleaned.pop(0)
        
    return cleaned


def _generate_openrouter_text(
    prompt: str,
    model_name: str,
    temperature: float,
    max_tokens: int,
    system_prompt: str | None = NEW_RENDERING_SYSTEM,
    history: list[dict[str, str]] | None = None,
):
    if not OPENROUTER_API_KEY:
        _log_model_failure(model_name, "missing API key")
        return None

    try:
        with httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            messages = (history or []) + [
                {
                    "role": "user",
                    "content": _format_prompt(prompt, system_prompt),
                }
            ]
            response = client.post(
                OPENROUTER_URL,
                headers=_openrouter_headers(),
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            response.raise_for_status()
            data = response.json()
            return _extract_openrouter_content(data)

    except Exception as e:
        _log_model_failure(model_name, str(e))
        return None


async def _generate_openrouter_text_async(
    prompt: str,
    model_name: str,
    temperature: float,
    max_tokens: int,
    system_prompt: str | None = NEW_RENDERING_SYSTEM,
    history: list[dict[str, str]] | None = None,
):
    if not OPENROUTER_API_KEY:
        _log_model_failure(model_name, "missing API key")
        return None

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            messages = (history or []) + [
                {
                    "role": "user",
                    "content": _format_prompt(prompt, system_prompt),
                }
            ]
            response = await client.post(
                OPENROUTER_URL,
                headers=_openrouter_headers(),
                json={
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            response.raise_for_status()
            data = response.json()
            return _extract_openrouter_content(data)

    except Exception as e:
        _log_model_failure(model_name, str(e))
        return None


def generate_llm_text(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 2500,
    system_prompt: str | None = NEW_RENDERING_SYSTEM,
    history: list[dict[str, str]] | None = None,
):
    final_prompt = final_prompt.strip()
    return generate_openrouter_text(
        final_prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_prompt=system_prompt,
        history=history,
    )


def _is_response_complete(text: str, prompt: str = "", system_prompt: str | None = None, history: list[dict[str, str]] | None = None) -> bool:
    if not text:
        return False
    trimmed = text.strip()
    if not trimmed:
        return False

    # Clean markdown json blocks if present to check JSON completeness
    cleaned_json_text = trimmed
    if cleaned_json_text.startswith("```"):
        cleaned_json_text = re.sub(r"^```(?:json)?|```$", "", cleaned_json_text, flags=re.MULTILINE).strip()

    # If it is a JSON response or prompt asks for JSON, check matching structure or valid JSON parse
    is_json_request = (
        cleaned_json_text.startswith("{") or
        cleaned_json_text.startswith("[") or
        "json" in prompt.lower() or
        (system_prompt and "json" in system_prompt.lower())
    )
    if is_json_request:
        # Check if it parses as valid JSON
        try:
            json.loads(cleaned_json_text)
            return True
        except Exception:
            # If it's a JSON request but didn't parse, check if it structurally ends with closing brackets
            if cleaned_json_text.endswith("}") or cleaned_json_text.endswith("]"):
                return True
            return False

    if len(trimmed) < 150:
        # Short responses are complete as long as they end with standard punctuation
        return trimmed[-1] in [".", "?", "!", '"', "*", "$", "}", ")"]

    # For any long response, as long as it ends with proper punctuation, it is complete
    if len(trimmed) > 1000 and trimmed[-1] in [".", "?", "!", '"', "*", "$", "}", ")"]:
        return True

    # Textbook curriculum generation requires structural completeness markers
    is_simulation = (
        "simulation" in prompt.lower() or
        (system_prompt and "simulation" in system_prompt.lower())
    )

    is_textbook_generation = (
        "textbook" in prompt.lower() or
        "curriculum" in prompt.lower() or
        (system_prompt and (
            "textbook" in system_prompt.lower() or
            "curriculum" in system_prompt.lower() or
            "new rendering system" in system_prompt.lower()
        ))
    )

    # Conversational follow-ups (history is present) should not trigger retry loops
    if history and len(history) > 0:
        return True

    if is_textbook_generation:
        structure_part = prompt
        if "REQUIRED RESPONSE STRUCTURE" in prompt:
            structure_part = prompt.split("REQUIRED RESPONSE STRUCTURE")[-1]
            
        expects_summary = "Summary" in structure_part
        expects_questions = "Suggested Questions" in structure_part
        
        if expects_summary and expects_questions:
            has_summary_marker = "Summary" in text or "Suggested" in text or "Question" in text or "Takeaway" in text
            if not has_summary_marker and len(trimmed) < 400:
                return False

    # For non-textbook responses (simulation, short answers, etc.), be lenient
    if len(trimmed) > 1000:
        return True

    if trimmed[-1] not in [".", "?", "!", '"', "*", "$", "}", ")", "`", "]", "/"]:
        if len(trimmed) > 300:
            return True
        return False

    return True


def generate_openrouter_text(
    prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 2500,
    system_prompt: str | None = None,
    history: list[dict[str, str]] | None = None,
):
    history = clean_history_for_llm(history)
    models = get_model_chain()
    best_fallback = None

    for index, model_name in enumerate(models):
        _log_model_attempt(model_name, fallback=index > 0)
        current_max = max_output_tokens
        current_temp = temperature
        for attempt in range(2):
            result = _generate_openrouter_text(
                prompt,
                model_name,
                current_temp,
                current_max,
                system_prompt=system_prompt,
                history=history,
            )
            if result:
                if _is_response_complete(result, prompt=prompt, system_prompt=system_prompt, history=history):
                    _log_model_success(model_name)
                    return result
                else:
                    best_fallback = result
                    print(f"[LLM] Response incomplete on attempt {attempt + 1}. Retrying with more tokens...")
                    current_max = min(current_max + 800, 4096)
                    current_temp = 0.15

    if best_fallback:
        print("[LLM] Returning best fallback incomplete response.")
        return best_fallback

    return "Error: Unable to generate response from OpenRouter."


async def generate_llm_text_async(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 2500,
    system_prompt: str | None = NEW_RENDERING_SYSTEM,
    history: list[dict[str, str]] | None = None,
):
    final_prompt = final_prompt.strip()
    return await generate_openrouter_text_async(
        final_prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_prompt=system_prompt,
        history=history,
    )


async def generate_openrouter_text_async(
    prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 2500,
    system_prompt: str | None = None,
    history: list[dict[str, str]] | None = None,
):
    history = clean_history_for_llm(history)
    models = get_model_chain()
    best_fallback = None

    for index, model_name in enumerate(models):
        _log_model_attempt(model_name, fallback=index > 0)
        current_max = max_output_tokens
        current_temp = temperature
        for attempt in range(2):
            result = await _generate_openrouter_text_async(
                prompt,
                model_name,
                current_temp,
                current_max,
                system_prompt=system_prompt,
                history=history,
            )
            if result:
                if _is_response_complete(result, prompt=prompt, system_prompt=system_prompt, history=history):
                    _log_model_success(model_name)
                    return result
                else:
                    best_fallback = result
                    print(f"[LLM] Response incomplete on attempt {attempt + 1}. Retrying with more tokens...")
                    current_max = min(current_max + 800, 4096)
                    current_temp = 0.15

    if best_fallback:
        print("[LLM] Returning best fallback incomplete response.")
        return best_fallback

    return "Error: Unable to generate response from OpenRouter."


async def generate_llm_stream_async(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1800,
    history: list[dict[str, str]] | None = None,
):
    final_prompt = final_prompt.strip()
    if not OPENROUTER_API_KEY:
        yield "data: Error: Missing API Key\n\n"
        return

    models = get_model_chain()

    for index, model_name in enumerate(models):
        _log_model_attempt(model_name, fallback=index > 0)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                messages = (history or []) + [
                    {
                        "role": "user",
                        "content": _format_prompt(final_prompt, NEW_RENDERING_SYSTEM),
                    }
                ]
                async with client.stream(
                    "POST",
                    OPENROUTER_URL,
                    headers=_openrouter_headers(),
                    json={
                        "model": model_name,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_output_tokens,
                        "stream": True,
                    },
                ) as response:
                    response.raise_for_status()
                    emitted_chunk = False

                    async for chunk in response.aiter_lines():
                        if chunk.startswith("data: "):
                            data_str = chunk[6:]
                            if data_str == "[DONE]":
                                break

                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {}).get("content", "")
                                    if delta:
                                        emitted_chunk = True
                                        yield f"data: {json.dumps({'content': delta})}\n\n"
                            except json.JSONDecodeError:
                                continue

                    if emitted_chunk:
                        _log_model_success(model_name)
                        return

                    _log_model_failure(model_name, "empty stream")

        except Exception as e:
            _log_model_failure(model_name, str(e))
            continue

    yield f"data: {json.dumps({'error': 'All OpenRouter models failed'})}\n\n"


# =========================================================
# PREMIUM EDUCATIONAL RESPONSE GENERATOR
# =========================================================
def get_tutor_prompt(context: str, question: str, fallback_mode: bool = False, history: list[dict[str, str]] | None = None) -> str:
    from .topic_type import detect_topic_type, get_dynamic_sections
    from ..tutor.query_intent import detect_query_intent, get_intent_structure

    # Detect simulation query
    is_simulation = "physics sandbox simulation" in context.lower() or "simulation" in context.lower()

    topic_type = detect_topic_type(question, context)
    intent = detect_query_intent(question)

    is_follow_up = history and any(msg.get("role") == "user" for msg in history)

    if is_follow_up:
        if intent == "definition":
            dynamic_structure = """
# Introduction

## Definition & Key Concepts
"""
        elif intent == "formula":
            dynamic_structure = """
# Formulas & Characteristics

## Core Formulas
"""
        elif intent == "characteristics":
            dynamic_structure = """
# Formulas & Characteristics

## Key Properties
"""
        elif intent == "numerical":
            dynamic_structure = """
# Practice Example

## Solved Numerical
"""
        elif intent == "advantages" or intent == "comparison":
            dynamic_structure = """
# Advantages

# Disadvantages
"""
        elif intent == "examples" or intent == "applications":
            dynamic_structure = """
# Applications

## Everyday Applications
"""
        else:
            dynamic_structure = """
# Introduction

## Explanation
"""
    else:
        topic_structure = get_dynamic_sections(topic_type)

        # =========================================================
        # VALIDATION LOGIC: PREVENT INVALID SECTIONS
        # =========================================================
        if topic_type in ["history", "social_science"]:
            # Strictly prevent formulas and calculations for history/social science
            if intent in ["formula", "numerical"]:
                intent = "detailed"

        elif topic_type == "biology":
            # Avoid unnecessary calculations in biology unless explicitly a formula
            if intent == "numerical":
                intent = "detailed"

        dynamic_structure = get_intent_structure(intent, topic_structure)

    if fallback_mode:
        context_instruction = "Answer based on your general knowledge. Do NOT claim the explanation came from a textbook."
        context_section = ""
    else:
        context_instruction = "Use the provided TEXTBOOK CONTEXT to ground your explanation accurately."
        context_section = f"""
=========================================================
TEXTBOOK CONTEXT
=========================================================

{context}
"""

    follow_up_instruction = ""
    follow_up_final_override = ""
    if is_follow_up:
        follow_up_instruction = """
=========================================================
STRICT FOLLOW-UP CONSTRAINTS:
=========================================================
This is a follow-up chat message. To maintain extreme conciseness and target the user's specific query, you MUST ONLY output the section(s) listed under the REQUIRED RESPONSE STRUCTURE. Do NOT output any other H1 or H2 headings. Keep your response focused entirely on the requested section.
"""
        follow_up_final_override = f"""
=========================================================
CRITICAL FOLLOW-UP RULE:
=========================================================
You are in follow-up mode. You MUST NOT generate any other H1 sections or cards. Generate ONLY the single H1 section:
{dynamic_structure.strip().splitlines()[0]}
Do NOT repeat the H2 sub-heading more than once. Write exactly one H1 section with its content.
"""

    if is_simulation:
        return f"""
You are the EduSim AI Tutor — a real-time physics tutor embedded directly inside an interactive simulation sandbox.

{context_instruction}

{follow_up_instruction}

=========================================================
STRICT FORMATTING RULES
=========================================================
1. Mathematical formulas MUST ALWAYS use LaTeX wrapped inside $$ ... $$ or $ ... $.
2. Avoid excessive bold text. Remaining content should be plain readable text.
3. Be highly engaging, visual, student-friendly, and educational.

{context_section}

=========================================================
ACTIVE SIMULATION STATE / EVENT INFO
=========================================================

{question}

=========================================================
STRICT OUTPUT FORMAT RULES:
=========================================================
- You MUST structure your entire response using the following headers and sections:
  ### ❖ LIVE EXPLANATION
  ### ❖ WHY IT HAPPENS
  ### ❖ WHAT TO NOTICE
  ### ❖ FORMULA
  ### ❖ DEEPER UNDERSTANDING
  ### ❖ TRY THIS
- Do NOT use other headers. Avoid robotic engine descriptions; sound like a live physics teacher.
"""
    else:
        return f"""
You are the EduSim AI Physics Tutor and Live Narrator.
Analyze the following active simulation event and provide an in-depth, structured educational response.

{context_instruction}

{follow_up_instruction}

=========================================================
STRICT FORMATTING RULES
=========================================================

1. Main headings MUST:
   - Use Markdown H1 (#)
   - Be bold
   - No emojis

Example:
# Heading

2. Subheadings MUST:
   - Use Markdown H2 (##)
   - Be bold
   - No emojis

Example:
## Subheading

3. Do NOT use emojis anywhere.

4. Use proper spacing and indentation.

5. Use bullet points where needed.

6. Paragraphs should be short and readable.

7. Use professional textbook-style formatting.

8. Mathematical formulas MUST ALWAYS use LaTeX.

Examples:

$$F = ma$$

$$v = u + at$$

$$E = mc^2$$

9. Never output formulas as plain text.

10. Advantages and Disadvantages MUST be presented under two separate H1 headings: `# Advantages` and `# Disadvantages`. List each point as a bullet with the title bolded (e.g. `* **Point Name:** Description.`). Do NOT use markdown tables for advantages/disadvantages.

11. Use horizontal separators:

---

between major sections.

12. ONLY headings and subheadings may be bold.

13. Do NOT use excessive bold text.

14. Remaining content should be plain readable text.

15. Add detailed educational explanations.

16. Include:
- Definitions
- Characteristics
- Types
- Formulas
- Derivations (if applicable)
- Applications
- Real-world examples
- Advantages
- Disadvantages
- Summary

17. Maintain clean textbook formatting.

18. Use proper markdown indentation.

19. Avoid repeating concepts or duplicating math equations.

20. Keep explanations student-friendly.

21. Keep formatting visually premium.

22. Use professional academic language.

23. Every solved numerical, step-by-step example, or calculation MUST follow this exact sub-section structure using H3 (###) headers:
    - ### Problem
      A clear statement of the question or problem.
    - ### Given
      A list of all known variables, symbols, and values with units (e.g. *Mass ($m$) = $5 \\text{{kg}}$*).
    - ### Formula
      The equation or mathematical relation used to solve the problem (rendered in display LaTeX, e.g. $$F = ma$$).
    - ### Substitution
      Showing the plugging-in of the given values into the formula.
    - ### Calculation
      The step-by-step arithmetic steps showing how the calculation is performed.
    - ### Final Answer
      The final value of the calculation with proper units, clearly highlighted (e.g. **Force ($F$) = $10 \\text{{N}}$**).
    - ### Interpretation
      A brief statement of what the result physically means.

24. NEVER stack mathematical fractions or equations vertically on separate single-character lines (e.g. numerator on line 1, denominator on line 3). ALWAYS use proper LaTeX syntax like \\frac{{a}}{{b}} and wrap it inside $$ ... $$ or $ ... $ (e.g. Write $$\\frac{{1}}{{f}} = \\frac{{1}}{{v}} - \\frac{{1}}{{u}}$$).

25. NEVER write plain text on the same line as display math delimiters ($$). Always start a new paragraph on a new line for any text explanation that follows a formula.

{context_section}

=========================================================
STUDENT QUESTION / TOPIC
=========================================================

{question}

=========================================================
REQUIRED RESPONSE STRUCTURE
=========================================================
You MUST structure your entire response using the following textbook structure. Use EXACTLY these headings (e.g., `# Introduction`, `## Definition`, etc.) as applicable to the topic to allow our rendering engine to structure them as separate interactive cards:

{dynamic_structure}

Ensure each section has rich, detailed, and highly educational explanation content.
Do NOT output headers like '### ❖ LIVE EXPLANATION' or other simulation event headers. Use the textbook H1 and H2 structure above.

{follow_up_final_override}
"""


def generate_response(
    context: str,
    question: str,
    user_preference: str = "student_friendly",
    fallback_mode: bool = False,
):
    """
    Generates premium textbook-style educational responses.
    """
    final_prompt = get_tutor_prompt(context, question, fallback_mode)
    return generate_llm_text(
        final_prompt,
        temperature=0.3,
        max_output_tokens=1800,
    )