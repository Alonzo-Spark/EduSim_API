import httpx

from app.src.config.openrouter_config import (
    OPENROUTER_API_KEY,
    OPENROUTER_URL,
    MODEL_NAME
)

async def generate_ai_explanation(
    topic: str,
    concept_explanation: str
):
    prompt = f"""
You are an educational physics tutor.

Explain the following concept clearly and simply.

Topic:
{topic}

Concept:
{concept_explanation}

Keep the explanation concise and educational.
"""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
        data = response.json()
        return (
            data["choices"][0]
            ["message"]["content"]
            .strip()
        )
    except Exception:
        return concept_explanation
