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
# LLM MODELS (via OpenRouter)
# =========================================================
# Using reliable non-Gemini models as primary to avoid quota confusion
#OPENROUTER_MODEL = "anthropic/claude-3-haiku" 
OPENROUTER_MODEL = "google/gemini-3-flash-preview"
#OPENROUTER_FALLBACK = "openai/gpt-4o-mini"
OPENROUTER_FALLBACK = "google/gemini-2.5-flash"


# =========================================================
# OPENROUTER GENERATION
# =========================================================
def _generate_openrouter_text(prompt: str, model_name: str, temperature: float, max_tokens: int):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY is missing from environment.")
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
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
            
            print(f"⚠ OpenRouter returned unexpected format: {data}")
            return None
            
    except Exception as e:
        print(f"⚠ OpenRouter failed ({model_name}): {e}")
        return None


# =========================================================
# GENERATE RAW TEXT
# =========================================================
def generate_llm_text(
    final_prompt: str,
    temperature: float = 0.3,
    max_output_tokens: int = 2048
):
    """
    Unified text generation using OpenRouter exclusively.
    """
    last_error = None

    # Try OpenRouter Models
    print(f"🔄 Attempting OpenRouter generation with {OPENROUTER_MODEL}...")
    for model_name in (OPENROUTER_MODEL, OPENROUTER_FALLBACK):
        result = _generate_openrouter_text(final_prompt, model_name, temperature, max_output_tokens)
        if result:
            return result

    print(f"\n❌ All OpenRouter generation paths failed.")
    return "Error: Unable to generate response from OpenRouter after multiple attempts."


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

    return generate_llm_text(
        final_prompt,
        temperature=0.2,
        max_output_tokens=1500
    )