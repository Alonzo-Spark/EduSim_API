from app.src.modules.legacy_rag.generator import generate_openrouter_text_async

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

    response = await generate_openrouter_text_async(
        prompt,
        temperature=0.25,
        max_output_tokens=900,
        system_prompt=None,
    )

    return response or concept_explanation
