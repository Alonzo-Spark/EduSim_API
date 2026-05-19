from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.schemas.tutor import TutorRequest, ChatRequest
from app.tutor.pipeline import run_tutor_pipeline
from app.services.progress_service import log_step_completion
from app.services.gamification_service import award_xp, check_and_award_badges

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])

@router.post("/step")
async def tutor_step(
    request: TutorRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Main endpoint for all 6 learning steps.
    Frontend calls this with step="explanation"|"formulas"|"quiz"|"simulation"|"feedback"|"chat"
    """
    result = await run_tutor_pipeline(
        step=request.step,
        topic=request.topic,
        class_name=request.class_name,
        subject=request.subject,
        chapter=request.chapter,
        subtopic=request.subtopic,
        message=request.message,
        chat_history=request.chat_history,
        quiz_performance=request.quiz_performance
    )

    # Award XP for completing each step
    xp_event_map = {
        "explanation": "explanation_viewed",
        "formulas": "formulas_viewed",
        "simulation": "simulation_launched",
    }
    if request.step in xp_event_map:
        await award_xp(current_user.id, xp_event_map[request.step], db)

    # Log progress
    if request.topic_id:
        await log_step_completion(current_user.id, request.topic_id, request.step, db)

    # Check for new badges
    new_badges = await check_and_award_badges(current_user.id, db)

    return {**result, "new_badges": new_badges}

@router.post("/chat")
async def tutor_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Persistent chat console — handles free-text doubts at any step."""
    from app.tutor.chat import handle_chat_message
    from app.rag.topic_classifier import infer_curriculum_context
    
    inferred = infer_curriculum_context(request.message)
    
    response_text, chunks = handle_chat_message(
        message=request.message,
        class_name=request.class_name,
        subject=request.subject,
        chapter=request.chapter or "",
        topic=request.topic,
        chat_history=request.chat_history or []
    )
    return {
        "response": response_text,
        "citations": chunks,
        "inferred_context": inferred
    }
