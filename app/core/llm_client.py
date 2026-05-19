import json
import re
from app.config import settings

def get_llm_client():
    """Returns the appropriate LLM client based on config."""
    if settings.llm_provider == "groq":
        from groq import Groq
        return Groq(api_key=settings.groq_api_key)
    else:
        from openai import OpenAI
        kwargs = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return OpenAI(**kwargs)

def generate_structured_response(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3
) -> dict:
    """
    Call LLM and parse JSON response.
    Handles both Groq and OpenAI APIs.
    Strips markdown fences before parsing.
    """
    client = get_llm_client()

    # OpenRouter can sometimes complain about response_format depending on model support, 
    # but modern OpenAI/Groq/OpenRouter all support JSON mode.
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=4096,
        response_format={"type": "json_object"}
    )

    raw = response.choices[0].message.content

    # Strip markdown fences defensively
    raw = re.sub(r'^```json\s*', '', raw.strip())
    raw = re.sub(r'```$', '', raw.strip())

    return json.loads(raw)

def generate_chat_response(
    system_prompt: str,
    messages: list[dict],
    temperature: float = 0.5
) -> str:
    """For the persistent chat console — returns plain text."""
    client = get_llm_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=temperature,
        max_tokens=1024
    )
    return response.choices[0].message.content
