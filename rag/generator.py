import os
import json
from pathlib import Path
import httpx
from dotenv import load_dotenv
from utils.usage_tracker import log_usage

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# =========================================================
# LLM MODELS
# =========================================================
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-3-flash-preview")
OPENROUTER_FALLBACK = os.getenv("OPENROUTER_FALLBACK", "google/gemini-2.5-flash")

# =========================================================
# SYNC GENERATION
# =========================================================
def _generate_openrouter_text(prompt: str, model_name: str, temperature: float, max_tokens: int):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    try:
        with httpx.Client(timeout=30.0) as client:
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
                # Log Usage
                usage = data.get("usage", {})
                if usage:
                    log_usage(
                        model=data.get("model", model_name),
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0)
                    )
                return data["choices"][0]["message"]["content"].strip()
            return None
    except Exception as e:
        print(f"⚠ OpenRouter sync failed ({model_name}): {e}")
        return None

def generate_llm_text(final_prompt: str, temperature: float = 0.3, max_output_tokens: int = 700):
    for model_name in (OPENROUTER_MODEL, OPENROUTER_FALLBACK):
        result = _generate_openrouter_text(final_prompt, model_name, temperature, max_output_tokens)
        if result:
            return result
    return "Error: Unable to generate response from OpenRouter."

# =========================================================
# ASYNC GENERATION
# =========================================================
async def _generate_openrouter_text_async(prompt: str, model_name: str, temperature: float, max_tokens: int):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            response.raise_for_status()
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                # Log Usage
                usage = data.get("usage", {})
                if usage:
                    log_usage(
                        model=data.get("model", model_name),
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        total_tokens=usage.get("total_tokens", 0)
                    )
                return data["choices"][0]["message"]["content"].strip()
            return None
    except Exception as e:
        print(f"⚠ OpenRouter async failed ({model_name}): {e}")
        return None

async def generate_llm_text_async(final_prompt: str, temperature: float = 0.3, max_output_tokens: int = 700):
    for model_name in (OPENROUTER_MODEL, OPENROUTER_FALLBACK):
        result = await _generate_openrouter_text_async(final_prompt, model_name, temperature, max_output_tokens)
        if result:
            return result
    return "Error: Unable to generate response from OpenRouter."

# =========================================================
# ASYNC STREAMING GENERATION
# =========================================================
async def generate_llm_stream_async(final_prompt: str, temperature: float = 0.3, max_output_tokens: int = 700):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        yield "data: Error: Missing API Key\n\n"
        return

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
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
                    "messages": [{"role": "user", "content": final_prompt}],
                    "temperature": temperature,
                    "max_tokens": max_output_tokens,
                    "stream": True,
                    "stream_options": {"include_usage": true}
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
                            
                            # Handle usage chunk (usually the last one)
                            if "usage" in data and data["usage"]:
                                usage = data["usage"]
                                log_usage(
                                    model=data.get("model", OPENROUTER_MODEL),
                                    prompt_tokens=usage.get("prompt_tokens", 0),
                                    completion_tokens=usage.get("completion_tokens", 0),
                                    total_tokens=usage.get("total_tokens", 0)
                                )
                                yield f"data: {json.dumps({'usage': usage})}\n\n"

                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {}).get("content", "")
                                if delta:
                                    yield f"data: {json.dumps({'content': delta})}\n\n"
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        print(f"⚠ OpenRouter streaming failed: {e}")
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

# =========================================================
# LEGACY COMPATIBILITY
# =========================================================
def generate_response(context: str, question: str, user_preference: str = "standard"):
    final_prompt = f"""You are EduSim Tutor.
TEXTBOOK CONTEXT:
{context}

QUESTION:
{question}

Provide a concise educational explanation using the context."""
    return generate_llm_text(final_prompt, temperature=0.3, max_output_tokens=700)