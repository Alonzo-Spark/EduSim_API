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
TUTOR_SYSTEM_PROMPT = r'''
You are the premium EduSim AI Physics Tutor.
Your task is to provide direct, extremely short, and beautifully formatted physics explanations for sandbox simulations.

STRICT INSTRUCTIONS:
1. Be ULTRA-CONCISE: The entire response must be very short (strictly ONE single paragraph of at most 3-4 sentences total, under 70 words).
2. Direct Answer: Answer the user's specific query and explain the physics of the sandbox simulation directly and immediately in 2-3 sentences.
3. Formula: Include at most ONE key mathematical formula on its own line using standard LaTeX ($$).
4. Absolutely no long textbook notes, no multiple headings, no step-by-step derivations, and no comparisons. Keep it compact, clean, and punchy.
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
        context_instruction = "Use the provided TEXTBOOK CONTEXT to answer the question accurately and provide concise physical insights."
        context_section = f"""
=========================================================
TEXTBOOK CONTEXT
=========================================================

{context}
"""

    return f"""
You are the EduSim AI Physics Tutor.
Provide a direct, concise, and beautifully formatted physics explanation for the active sandbox simulation.

{context_instruction}

{context_section}

=========================================================
QUESTION / SIMULATION INTENT
=========================================================

{question}

=========================================================
STRICT RULES:
=========================================================
- Directly answer the question or explain the core physical concept of the simulation.
- Keep the entire response very brief (around 2-3 short, clear, and highly focused paragraphs maximum).
- Avoid long derivations, historical context, advantages/disadvantages, or verbose textbook structures.
- Use simple, student-friendly, and highly engaging language.
- Formatting: Use simple Markdown with double dollar signs ($$) on separate lines for display math formulas, or single dollar signs ($) for inline variables.
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