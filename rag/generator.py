import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_FALLBACK_MODEL = "gemini-flash-latest"

def _configure_gemini(model_name: str = GEMINI_MODEL):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing. Add it to .env to enable Gemini generation.")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

def generate_gemini_text(final_prompt: str, temperature: float = 0.3, max_output_tokens: int = 2048):
    """Generate raw text from Gemini using a single final prompt."""
    last_error = None

    for model_name in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL):
        try:
            model = _configure_gemini(model_name)
            response = model.generate_content(
                final_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
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

    print(f"Gemini generation completely failed: {str(last_error)}")
    # Safe fallback instead of crashing
    return "{}" # Return empty JSON block by default as most downstream systems expect JSON



def generate_response(context: str, question: str):
    final_prompt = (
        "You are a helpful educational tutor. Use the textbook context to answer clearly and accurately.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{question}\n\n"
        "Give a concise educational answer grounded in the context."
    )
    return generate_gemini_text(final_prompt, temperature=0.2, max_output_tokens=1024)


def generate_structured_response(system_prompt: str, user_query: str):
    final_prompt = (
        f"System Instructions:\n{system_prompt}\n\n"
        f"User Input:\n{user_query}\n\n"
        "Return only the requested output format."
    )
    return generate_gemini_text(final_prompt, temperature=0.2, max_output_tokens=2048)