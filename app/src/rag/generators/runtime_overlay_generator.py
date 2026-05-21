from app.src.modules.legacy_rag.generator import generate_openrouter_text_async

async def generate_runtime_overlay(
    topic: str,
    event: str
):
    prompt = f"""
You are an educational physics tutor.

A simulation runtime detected:

Event:
{event}

Topic:
{topic}

Generate a short educational overlay for the student.

Keep it concise and educational.
"""

    response = await generate_openrouter_text_async(
        prompt,
        temperature=0.2,
        max_output_tokens=220,
        system_prompt=None,
    )

    return response or "Observe the simulation carefully."
