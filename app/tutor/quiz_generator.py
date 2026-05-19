from app.rag.retriever import build_rag_context, retrieve_chunks
from app.core.llm_client import generate_structured_response
from app.tutor.prompts import BASE_SYSTEM_PROMPT

def generate_quiz_from_chunks(
    topic: str,
    class_name: str,
    chunks: list[dict],
    num_questions: int = 5
) -> dict:
    context = build_rag_context(chunks)

    prompt = f"""
Generate a {num_questions}-question quiz on "{topic}" for {class_name} students.
Use ONLY the textbook content below. No hallucinated questions.

TEXTBOOK CONTENT:
{context}

Return this exact JSON structure:
{{
    "questions": [
        {{
            "id": "q1",
            "type": "mcq",
            "questionText": "Question based on textbook content",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correctAnswer": "Option A",
            "explanation": "Explanation citing textbook: why this is correct",
            "formulaHint": "relevant formula if applicable (or null)",
            "difficulty": "easy | medium | hard",
            "source": "Chapter name, page number",
            "xpReward": 10
        }},
        {{
            "id": "q2",
            "type": "numerical",
            "questionText": "A numerical problem from textbook examples",
            "correctAnswer": "42",
            "unit": "m/s",
            "explanation": "Step-by-step solution using textbook formula",
            "formulaHint": "v = u + at",
            "difficulty": "medium",
            "source": "Chapter name, page number",
            "xpReward": 20
        }},
        {{
            "id": "q3",
            "type": "conceptual",
            "questionText": "A conceptual question about this topic",
            "correctAnswer": "The correct conceptual answer",
            "explanation": "Textbook-based explanation",
            "difficulty": "easy",
            "source": "Chapter name, page number",
            "xpReward": 10
        }}
    ],
    "totalXP": 60,
    "topic": "{topic}",
    "classLevel": "{class_name}"
}}
Mix question types: 2 MCQ, 1–2 numerical (for Class 6+), rest conceptual.
For Class 1–5: use only MCQ and simple conceptual.
"""
    return generate_structured_response(BASE_SYSTEM_PROMPT, prompt, temperature=0.5)

def generate_quiz(
    topic: str,
    class_name: str,
    difficulty_mix: str = "mixed"
) -> dict:
    """Fallback / helper to generate quiz by retrieving chunks internally if pipeline is bypassed."""
    # Split subject/class context or fallback to standard retrieval
    chunks = retrieve_chunks(
        query=f"{topic} quiz questions exercises numericals",
        class_name=class_name,
        subject="Science",  # generic fallback subject
        n_results=6
    )
    return generate_quiz_from_chunks(topic, class_name, chunks)
