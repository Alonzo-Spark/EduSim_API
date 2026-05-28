import json
from typing import Any, Dict, Optional

import httpx
from app.src.config.models import (
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    get_model_chain,
)

# =========================================================
# NEW RENDERING SYSTEM (Sent to LLM)
# =========================================================
NEW_RENDERING_SYSTEM = r'''
The KaTeX rendering and table styling are working, but the AI Tutor still feels like a markdown document.

I do NOT want the output to look like ChatGPT notes.

I want it to look like an interactive textbook.

=========================================================
NEW RENDERING SYSTEM
=========================================================

Instead of rendering markdown sequentially:

# Heading
Paragraph

## Formula

$$F=ma$$

Table

Convert content into structured UI blocks.

=========================================================
SECTION DETECTION
=========================================================

Detect sections automatically:

Introduction
Definition
Key Concepts
Characteristics
Formula
Applications
Advantages
Disadvantages
Important Notes
Summary
Suggested Questions

Render each section as a card.

Example:

┌───────────────────────────┐
│ Quick Definition          │
│                           │
│ Photosynthesis is ...     │
└───────────────────────────┘

=========================================================
FORMULA CARD SYSTEM
=========================================================

Whenever a display formula exists:

$$
...
$$

Render:

┌───────────────────────────┐
│ Main Formula              │
│                           │
│     Rendered Formula      │
│                           │
│ [ Explain Formula ]       │
│ [ Open Formula Lab ]      │
└───────────────────────────┘

Do not leave formulas floating in text.

Every formula must become a dedicated FormulaCard component.

=========================================================
FORMULA EXTRACTION
=========================================================

During markdown parsing:

Extract all display LaTeX blocks.

Store:

{
 formula,
 title,
 surroundingContext,
 variables
}

Use this for Formula Lab.

Do not parse again later.

=========================================================
TABLE RENDERING
=========================================================

Markdown tables must render as:

Card
  -> Responsive table
'''

# =========================================================
# TUTOR SYSTEM PROMPT (Dedicated for premium explanations)
# =========================================================
TUTOR_SYSTEM_PROMPT = r'''You are EduSim AI — an advanced real-time educational simulation narrator and physics explanation engine.
Your role is to behave like an intelligent physics teacher watching the simulation live inside the sandbox.

STRICT PEDAGOGICAL RULES:
1. Speak directly like a live physics teacher guiding a student. Avoid generic, robotic textbook summaries or engine logs.
2. Focus on CAUSE → EFFECT: always explain WHY interactions happen and HOW variables dynamically change over time.
3. Keep explanations highly observational, intuitive, visual, and conceptual.
4. Structure your response in EXACTLY the following format:

### ✦ LIVE EXPLANATION
[Describe what is happening right now under this specific physics concept. Include live observations, physical causes, and active quantities changing over time like velocity, acceleration, kinetic/potential energy, momentum, or forces.]

### ✦ WHY IT HAPPENS
[Explain the primary physical cause behind this behavior in a clear cause-and-effect relationship, such as how forces are balanced or unbalanced.]

### ✦ WHAT TO NOTICE
[Visually guide the student's attention to specific visual indicators in the sandbox, e.g., the spacing between shapes, the stretching of constraints, or circular arc trajectories.]

### ✦ FORMULA
[Present exactly one main formula relevant to this event using LaTeX on a separate line ($$ ... $$) and explain the variables conceptually, showing how changing them affects the motion.]

### ✦ DEEPER UNDERSTANDING
[Connect this sandbox behavior to a deeper physics law (Newton's laws, Hooke's law, energy conservation) and link it directly to a tangible, real-world connection to improve retention.]

### ✦ TRY THIS
[Provide clear observation tasks and suggest 1-2 interactive experiments in the sandbox, such as altering mass, gravity, or stiffness, to discover physics relations.]
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
    choices = data.get("choices", []) if isinstance(data, dict) else []
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


def _generate_openrouter_text(
    prompt: str,
    model_name: str,
    temperature: float,
    max_tokens: int,
    system_prompt: str | None = NEW_RENDERING_SYSTEM,
):
    if not OPENROUTER_API_KEY:
        _log_model_failure(model_name, "missing API key")
        return None

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                OPENROUTER_URL,
                headers=_openrouter_headers(),
                json={
                    "model": model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": _format_prompt(prompt, system_prompt),
                        }
                    ],
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
):
    if not OPENROUTER_API_KEY:
        _log_model_failure(model_name, "missing API key")
        return None

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                headers=_openrouter_headers(),
                json={
                    "model": model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": _format_prompt(prompt, system_prompt),
                        }
                    ],
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
    max_output_tokens: int = 1800,
    system_prompt: str | None = NEW_RENDERING_SYSTEM,
):
    return generate_openrouter_text(
        final_prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_prompt=system_prompt,
    )


def generate_openrouter_text(
    prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1800,
    system_prompt: str | None = None,
):
    models = get_model_chain()

    for index, model_name in enumerate(models):
        _log_model_attempt(model_name, fallback=index > 0)
        result = _generate_openrouter_text(
            prompt,
            model_name,
            temperature,
            max_output_tokens,
            system_prompt=system_prompt,
        )
        if result:
            _log_model_success(model_name)
            return result

    return "Error: Unable to generate response from OpenRouter."


async def generate_llm_text_async(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1800,
    system_prompt: str | None = NEW_RENDERING_SYSTEM,
):
    return await generate_openrouter_text_async(
        final_prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_prompt=system_prompt,
    )



async def generate_openrouter_text_async(
    prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1800,
    system_prompt: str | None = None,
):
    models = get_model_chain()

    for index, model_name in enumerate(models):
        _log_model_attempt(model_name, fallback=index > 0)
        result = await _generate_openrouter_text_async(
            prompt,
            model_name,
            temperature,
            max_output_tokens,
            system_prompt=system_prompt,
        )
        if result:
            _log_model_success(model_name)
            return result

    return "Error: Unable to generate response from OpenRouter."


async def generate_llm_stream_async(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1800,
):
    if not OPENROUTER_API_KEY:
        yield "data: Error: Missing API Key\n\n"
        return

    models = get_model_chain()

    for index, model_name in enumerate(models):
        _log_model_attempt(model_name, fallback=index > 0)
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    OPENROUTER_URL,
                    headers=_openrouter_headers(),
                    json={
                        "model": model_name,
                        "messages": [
                            {
                                "role": "user",
                                "content": _format_prompt(final_prompt, NEW_RENDERING_SYSTEM),
                            }
                        ],
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
def get_tutor_prompt(context: str, question: str, fallback_mode: bool = False) -> str:
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

    return f"""
You are the EduSim AI Physics Tutor and Live Narrator.
Analyze the following active simulation event and provide an in-depth, structured educational response.

{context_instruction}

{context_section}

=========================================================
ACTIVE SIMULATION STATE / EVENT INFO
=========================================================

{question}

=========================================================
STRICT OUTPUT FORMAT RULES:
=========================================================
- You MUST structure your entire response using the following headers and sections:
  ### ✦ LIVE EXPLANATION
  ### ✦ WHY IT HAPPENS
  ### ✦ WHAT TO NOTICE
  ### ✦ FORMULA
  ### ✦ DEEPER UNDERSTANDING
  ### ✦ TRY THIS
- Be highly engaging, visual, student-friendly, and educational.
- Do NOT use other headers. Avoid robotic engine descriptions; sound like a live physics teacher.
"""


def generate_response(
    context: str,
    question: str,
    user_preference: str = "student_friendly",
    fallback_mode: bool = False
):
    """
    Generates premium textbook-style educational responses.
    """
    final_prompt = get_tutor_prompt(context, question, fallback_mode)
    return generate_llm_text(
        final_prompt,
        temperature=0.3,
        max_output_tokens=1800
    )