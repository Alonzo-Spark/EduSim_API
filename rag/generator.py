import os
import json
from pathlib import Path

import google.generativeai as genai
import httpx
from dotenv import load_dotenv

# =========================================================
# LOAD ENV
# =========================================================
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# =========================================================
# LLM MODELS
# =========================================================
# Gemini Models
GEMINI_MODEL = "gemini-2.5flash" # More modern and likely more available
GEMINI_FALLBACK_MODEL = "gemini-flash-latest"

# OpenRouter Models (Fallback)
OPENROUTER_MODEL = "google/gemini-2.0-flash-001" # Very fast and reliable fallback
OPENROUTER_FALLBACK = "anthropic/claude-3-haiku"


# =========================================================
# CONFIGURE GEMINI
# =========================================================
def _configure_gemini(model_name: str = GEMINI_MODEL):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    
    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
    except Exception:
        return None


# =========================================================
# OPENROUTER GENERATION
# =========================================================
def _generate_openrouter_text(prompt: str, model_name: str, temperature: float, max_tokens: int):
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
                    "HTTP-Referer": "https://edusim.ai", # Optional
                    "X-Title": "EduSim", # Optional
                },
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"⚠ OpenRouter failed ({model_name}): {e}")
        return None


# =========================================================
# GENERATE RAW TEXT
# =========================================================
def generate_gemini_text(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 2048
):
    last_error = None

    # 1. Try Gemini (Native)
    for model_name in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL, "gemini-2.5flash"):
        try:
            model = _configure_gemini(model_name)
            if not model:
                continue

            response = model.generate_content(
                final_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
            )

            generated_text = getattr(response, "text", None)
            if generated_text:
                return generated_text.strip()
            
            # If no text but response exists (safety filter?)
            print(f"⚠ Gemini returned no text for {model_name}. Possible safety filter.")
        except Exception as e:
            last_error = e
            print(f"⚠ Gemini model failed ({model_name}): {e}")

    # 2. Try OpenRouter (Fallback)
    print("🔄 Switching to OpenRouter fallback...")
    for model_name in (OPENROUTER_MODEL, OPENROUTER_FALLBACK):
        result = _generate_openrouter_text(final_prompt, model_name, temperature, max_output_tokens)
        if result:
            return result

    print(f"\n❌ All LLM generation paths failed. Last error: {last_error}")
    # Return a minimal valid JSON if we are in synthesis mode, 
    # but since this function is generic, we return the error message.
    # The caller (service.py) should handle non-JSON better or we should fix it here.
    return "Error: Unable to generate response after multiple attempts."


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