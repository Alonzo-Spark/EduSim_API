import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# =========================================================
# GEMINI MODELS
# =========================================================
GEMINI_MODEL = "gemini-1.5-flash"

GEMINI_FALLBACK_MODEL = "gemini-flash-latest"


# =========================================================
# CONFIGURE GEMINI
# =========================================================
def _configure_gemini(model_name: str = GEMINI_MODEL):

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "❌ GOOGLE_API_KEY missing in .env"
        )

    genai.configure(api_key=api_key)

    return genai.GenerativeModel(model_name)


# =========================================================
# GENERATE RAW TEXT
# =========================================================
def generate_gemini_text(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 2048
):

    last_error = None

    for model_name in (
        GEMINI_MODEL,
        GEMINI_FALLBACK_MODEL
    ):

        try:

            model = _configure_gemini(model_name)

            response = model.generate_content(

                final_prompt,

                generation_config={

                    "temperature": temperature,

                    "max_output_tokens": max_output_tokens,

                },
            )

            generated_text = getattr(
                response,
                "text",
                None
            )

            if not generated_text:
                raise ValueError(
                    "Gemini returned empty response"
                )

            return generated_text.strip()

        except Exception as e:

            last_error = e

            print(
                f"⚠ Gemini model failed ({model_name}): {e}"
            )

    print(f"\n❌ Gemini generation failed: {last_error}")

    return "Unable to generate response."


# =========================================================
# MAIN EDUCATIONAL RESPONSE
# =========================================================
def generate_response(
    context: str,
    question: str,
    user_preference: str = "standard"
):

    final_prompt = f"""
You are EduSim, an advanced AI Educational Tutor and Intelligent Learning Assistant.

Your responsibilities:
- explain educational concepts clearly
- use the provided textbook context as the primary source
- stay accurate and educational
- simplify difficult topics
- generate structured and beginner-friendly answers
- adapt explanations for students
- improve conceptual understanding

RULES:
1. Prioritize textbook/RAG context first.
2. Do not generate unrelated information.
3. If the textbook context is insufficient, clearly mention:
   "The textbook does not fully cover this topic, but here is a general explanation."
4. Keep explanations educational and easy to understand.
5. Avoid hallucinating facts not supported by the context.
6. Explain formulas and variables clearly.
7. Use examples when useful.
8. Keep formatting clean and readable.

WHEN RELEVANT:
- include formulas
- include definitions
- include examples
- include real-world applications
- include step-by-step explanations

USER PREFERENCE:
{user_preference}

TEXTBOOK CONTEXT:
{context}

QUESTION:
{question}

Return response in this format:

## Topic Name

## Core Concept

## Important Formulas / Definitions

## Key Points

## Example / Working

## Real-World Applications
"""

    return generate_gemini_text(
        final_prompt,
        temperature=0.2,
        max_output_tokens=1500
    )