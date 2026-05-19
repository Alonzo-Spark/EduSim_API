from app.rag.retriever import retrieve_chunks, build_rag_context
from app.core.llm_client import generate_chat_response

CHAT_SYSTEM_PROMPT = """
You are EduSim's AI Tutor — a helpful, friendly, and expert educational assistant.
You answer student doubts clearly and concisely.
You always ground your answers in the textbook content provided in each message.
Never fabricate formulas or facts. If unsure, say so.
Keep responses concise (3–5 sentences). Be encouraging and age-appropriate.
"""

def handle_chat_message(
    message: str,
    class_name: str,
    subject: str,
    chapter: str,
    topic: str,
    chat_history: list[dict]
) -> tuple[str, list[dict]]:
    """
    Handle a chat message from the persistent console.
    Retrieves relevant context and responds conversationally.
    """
    # Retrieve relevant chunks for the question
    chunks = retrieve_chunks(
        query=message,
        class_name=class_name,
        subject=subject,
        chapter=chapter,
        topic=topic,
        n_results=3
    )

    rag_context = build_rag_context(chunks) if chunks else "No specific textbook content found."

    # Inject RAG context into the last user message
    augmented_messages = []
    # Make sure we convert list of dicts safely without mutating original
    for msg in chat_history:
        augmented_messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })

    augmented_messages.append({
        "role": "user",
        "content": f"""
Student question: {message}

Relevant textbook content for context:
{rag_context}

Answer the student's question using the textbook content above.
"""
    })

    response_text = generate_chat_response(CHAT_SYSTEM_PROMPT, augmented_messages, temperature=0.5)
    return response_text, chunks
