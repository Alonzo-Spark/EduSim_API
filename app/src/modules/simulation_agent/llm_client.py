import os
import google.generativeai as genai
from typing import Optional

GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_FALLBACK_MODEL = "gemini-1.5-flash-8b"

def configure_llm(model_name: str = GEMINI_MODEL):
    """Configure and return Gemini model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is missing. Add it to .env to enable Gemini generation.")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

def call_llm(prompt: str, temperature: float = 0.2, max_tokens: int = 4000, response_mime_type: Optional[str] = None) -> str:
    """Call Gemini API with fallback support."""
    last_error = None
    
    generation_config = {
        "temperature": temperature,
        "max_output_tokens": max_tokens,
    }
    
    if response_mime_type:
        generation_config["response_mime_type"] = response_mime_type

    for model_name in (GEMINI_MODEL, GEMINI_FALLBACK_MODEL):
        try:
            model = configure_llm(model_name)
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
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

