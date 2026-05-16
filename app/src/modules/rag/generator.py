import os
import json
from pathlib import Path

import httpx
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# =========================================================
# LLM MODELS
# =========================================================
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "google/gemini-3-flash-preview"
)

OPENROUTER_FALLBACK = os.getenv(
    "OPENROUTER_FALLBACK",
    "google/gemini-2.5-flash"
)

# =========================================================
# SYNC GENERATION
# =========================================================
def _generate_openrouter_text(
    prompt: str,
    model_name: str,
    temperature: float,
    max_tokens: int
):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return None

    try:
        with httpx.Client(timeout=60.0) as client:

            response = client.post(
                "https://openrouter.ai/api/v1/chat/completions",

                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://edusim.ai",
                    "X-Title": "EduSim",
                },

                json={
                    "model": model_name,

                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            response.raise_for_status()

            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:

                return (
                    data["choices"][0]
                    ["message"]["content"]
                    .strip()
                )

            return None

    except Exception as e:

        print(f"⚠ OpenRouter sync failed ({model_name}): {e}")

        return None


# =========================================================
# MAIN GENERATION FUNCTION
# =========================================================
def generate_llm_text(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1800
):

    for model_name in (
        OPENROUTER_MODEL,
        OPENROUTER_FALLBACK
    ):

        result = _generate_openrouter_text(
            final_prompt,
            model_name,
            temperature,
            max_output_tokens
        )

        if result:
            return result

    return "Error: Unable to generate response from OpenRouter."


# =========================================================
# ASYNC GENERATION
# =========================================================
async def _generate_openrouter_text_async(
    prompt: str,
    model_name: str,
    temperature: float,
    max_tokens: int
):
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:

            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",

                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://edusim.ai",
                    "X-Title": "EduSim",
                },

                json={
                    "model": model_name,

                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],

                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            response.raise_for_status()

            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:

                return (
                    data["choices"][0]
                    ["message"]["content"]
                    .strip()
                )

            return None

    except Exception as e:

        print(f"⚠ OpenRouter async failed ({model_name}): {e}")

        return None


# =========================================================
# ASYNC PUBLIC GENERATION
# =========================================================
async def generate_llm_text_async(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1800
):

    for model_name in (
        OPENROUTER_MODEL,
        OPENROUTER_FALLBACK
    ):

        result = await _generate_openrouter_text_async(
            final_prompt,
            model_name,
            temperature,
            max_output_tokens
        )

        if result:
            return result

    return "Error: Unable to generate response from OpenRouter."


# =========================================================
# STREAMING GENERATION
# =========================================================
async def generate_llm_stream_async(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 1800
):

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        yield "data: Error: Missing API Key\n\n"
        return

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:

            async with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",

                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://edusim.ai",
                    "X-Title": "EduSim",
                },

                json={
                    "model": OPENROUTER_MODEL,

                    "messages": [
                        {
                            "role": "user",
                            "content": final_prompt
                        }
                    ],

                    "temperature": temperature,
                    "max_tokens": max_output_tokens,
                    "stream": True
                },

            ) as response:

                response.raise_for_status()

                async for chunk in response.aiter_lines():

                    if chunk.startswith("data: "):

                        data_str = chunk[6:]

                        if data_str == "[DONE]":
                            break

                        try:

                            data = json.loads(data_str)

                            if (
                                "choices" in data
                                and len(data["choices"]) > 0
                            ):

                                delta = (
                                    data["choices"][0]
                                    .get("delta", {})
                                    .get("content", "")
                                )

                                if delta:

                                    yield (
                                        f"data: "
                                        f"{json.dumps({'content': delta})}\n\n"
                                    )

                        except json.JSONDecodeError:
                            continue

    except Exception as e:

        print(f"⚠ OpenRouter streaming failed: {e}")

        yield (
            f"data: "
            f"{json.dumps({'error': str(e)})}\n\n"
        )


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