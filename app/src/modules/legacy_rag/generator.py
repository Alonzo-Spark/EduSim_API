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
):
    return generate_openrouter_text(
        final_prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_prompt=NEW_RENDERING_SYSTEM,
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
):
    return await generate_openrouter_text_async(
        final_prompt,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
        system_prompt=NEW_RENDERING_SYSTEM,
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
    from .topic_type import detect_topic_type, get_dynamic_sections
    from ..tutor.query_intent import detect_query_intent, get_intent_structure
    
    topic_type = detect_topic_type(question, context)
    topic_structure = get_dynamic_sections(topic_type)
    
    intent = detect_query_intent(question)
    
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
        context_instruction = "Generate a comprehensive educational explanation based on your general knowledge. Do NOT claim the explanation came from a textbook."
        context_section = ""
    else:
        context_instruction = "Use the provided TEXTBOOK CONTEXT to answer the QUESTION accurately."
        context_section = f"""
=========================================================
TEXTBOOK CONTEXT
=========================================================

{context}
"""

    return f"""
You are the EduSim AI Tutor.

Your task is to create professional textbook-style educational notes
for students from Class 6 to Class 12.

{context_instruction}

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

10. Advantages and disadvantages MUST use markdown tables.

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
- Important notes
- Common mistakes
- Summary

17. Maintain clean textbook formatting.

18. Use proper markdown indentation.

19. Avoid repeating concepts.

20. Keep explanations student-friendly.

21. Keep formatting visually premium.

22. Use professional academic language.

{context_section}

=========================================================
QUESTION
=========================================================

{question}

=========================================================
FOLLOW THIS STRUCTURE EXACTLY
=========================================================
{dynamic_structure}

=========================================================
IMPORTANT
=========================================================

- Keep formatting beautiful.
- Use markdown properly.
- Generate premium educational notes.
- Keep explanations detailed but readable.
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