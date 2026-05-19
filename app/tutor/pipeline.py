from app.rag.retriever import retrieve_chunks
from app.tutor.explanation import generate_explanation
from app.tutor.formulas import generate_formulas
from app.tutor.quiz_generator import generate_quiz_from_chunks
from app.tutor.simulation_generator import generate_simulation_config
from app.tutor.feedback_generator import generate_feedback
from app.tutor.chat import handle_chat_message
from app.services.asset_service import get_assets_for_topic
from fastapi import HTTPException

async def run_tutor_pipeline(
    step: str,
    topic: str,
    class_name: str,
    subject: str,
    chapter: str = None,
    subtopic: str = None,
    message: str = None,
    chat_history: list[dict] = None,
    quiz_performance: dict = None
) -> dict:
    """
    Master pipeline: given a step and curriculum context,
    retrieves textbook chunks and runs the appropriate generator.
    Returns structured data + source references.
    """
    # Build query string tuned to each step
    query_map = {
        "explanation": f"explain {topic} definition concept overview",
        "formulas": f"{topic} formulas equations derivations variables",
        "quiz": f"{topic} questions exercises problems examples",
        "simulation": f"{topic} experiment observation parameters variables",
        "feedback": f"{topic} summary key concepts",
        "chat": message or topic,
    }

    query = query_map.get(step, topic)
    n_results = 8 if step in ("quiz", "simulation") else 6

    chunks = retrieve_chunks(
        query=query,
        class_name=class_name,
        subject=subject,
        chapter=chapter,
        topic=topic,
        n_results=n_results
    )

    if not chunks and step != "feedback":
        # Log warning instead of strictly crashing if no textbooks are ingested yet during setup
        print(f"WARNING: No textbook chunks found for {class_name} > {subject} > {topic}")
        # Build mock chunks defensively so the pipeline remains testable
        chunks = [{
            "text": f"Study of {topic} in {subject} for {class_name}.",
            "metadata": {"class": class_name, "subject": subject, "chapter": chapter or "General", "page": 1},
            "relevance_score": 1.0
        }]

    sources = [
        {
            "chapter": c["metadata"].get("chapter", ""),
            "page": c["metadata"].get("page", ""),
            "relevance": c["relevance_score"]
        }
        for c in chunks[:3]
    ]

    # Route to appropriate generator
    if step == "explanation":
        data = generate_explanation(topic, class_name, subject, chapter or "", chunks)

    elif step == "formulas":
        data = generate_formulas(topic, class_name, chunks)

    elif step == "quiz":
        data = generate_quiz_from_chunks(topic, class_name, chunks)

    elif step == "simulation":
        assets = await get_assets_for_topic(topic, subject)
        data = generate_simulation_config(topic, class_name, subject, chunks, assets)

    elif step == "feedback":
        if not quiz_performance:
            raise HTTPException(status_code=400, detail="quiz_performance required for feedback step")
        data = generate_feedback(
            topic=topic,
            class_name=class_name,
            quiz_score=quiz_performance.get("score", 0),
            quiz_total=quiz_performance.get("total", 5),
            simulation_count=quiz_performance.get("simulation_count", 0),
            time_spent_seconds=quiz_performance.get("time_spent", 0),
            wrong_questions=quiz_performance.get("wrong_questions", [])
        )

    elif step == "chat":
        response_text, chat_chunks = handle_chat_message(
            message=message,
            class_name=class_name,
            subject=subject,
            chapter=chapter or "",
            topic=topic,
            chat_history=chat_history or []
        )
        chat_sources = [
            {
                "chapter": c["metadata"].get("chapter", ""),
                "page": c["metadata"].get("page", ""),
                "relevance": c["relevance_score"]
            }
            for c in chat_chunks[:3]
        ]
        return {
            "step": "chat",
            "data": {
                "answer": response_text,
                "response": response_text,
                "citations": chat_chunks,
                "retrieved_chunks": chat_chunks,
            },
            "sources": chat_sources,
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown step: {step}")

    return {"step": step, "data": data, "sources": sources}
