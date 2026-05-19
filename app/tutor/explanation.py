from app.rag.retriever import build_rag_context
from app.core.llm_client import generate_structured_response
from app.tutor.prompts import BASE_SYSTEM_PROMPT

def generate_explanation(
    topic: str,
    class_name: str,
    subject: str,
    chapter: str,
    chunks: list[dict]
) -> dict:
    context = build_rag_context(chunks)

    prompt = f"""
Using ONLY the textbook content below, teach the topic "{topic}" to a {class_name} {subject} student.

TEXTBOOK CONTENT:
{context}

Return this exact JSON structure:
{{
    "title": "{topic}",
    "overview": "2–3 clear paragraphs. Use simple language for lower classes, detailed for Class 9–10. Must be fully grounded in the textbook content above.",
    "keyPoints": [
        "Key concept 1 from textbook",
        "Key concept 2 from textbook",
        "Key concept 3 from textbook",
        "Key concept 4 from textbook"
    ],
    "realWorldExample": "A real-world example exactly as mentioned in the textbook",
    "definition": "Exact or paraphrased definition from textbook",
    "prerequisiteNote": "What students should already know before this topic (or null if none)",
    "difficulty": "beginner | intermediate | advanced",
    "sources": [
        {{"chapter": "chapter name", "page": 0}}
    ]
}}
"""
    return generate_structured_response(BASE_SYSTEM_PROMPT, prompt, temperature=0.3)
