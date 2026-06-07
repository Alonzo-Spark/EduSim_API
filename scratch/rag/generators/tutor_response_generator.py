from app.src.modules.legacy_rag.generator import generate_openrouter_text_async

async def generate_tutor_response(
    topic: str,
    question: str
):
    prompt = f"""
You are an educational physics tutor.

Topic:
{topic}

Student Question:
{question}

Explain clearly and educationally.
"""

    response = await generate_openrouter_text_async(
        prompt,
        temperature=0.2,
        max_output_tokens=1200,
        system_prompt=None,
    )

    return response or "Tutor response is currently unavailable."
