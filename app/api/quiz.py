from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_user
from app.tutor.quiz_generator import generate_quiz_from_chunks
from app.rag.retriever import retrieve_chunks
from app.services.curriculum_service import get_topic_full_context
from app.services.progress_service import update_quiz_score
from app.services.gamification_service import award_xp, check_and_award_badges
from app.schemas.quiz import QuizSubmitRequest

router = APIRouter(prefix="/quiz", tags=["Quiz"])

@router.get("/{topic_id}")
async def get_quiz(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    ctx = await get_topic_full_context(topic_id, db)
    if not ctx:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    chunks = retrieve_chunks(
        query=f"{ctx['topic']} questions exercises board exam problems",
        class_name=ctx["class_name"],
        subject=ctx["subject"],
        chapter=ctx["chapter"],
        n_results=8
    )
    
    # Fallback to simple context if empty
    if not chunks:
        chunks = [{
            "text": f"Study questions for {ctx['topic']}",
            "metadata": {"class": ctx["class_name"], "subject": ctx["subject"], "chapter": ctx["chapter"], "page": 1},
            "relevance_score": 1.0
        }]
        
    return generate_quiz_from_chunks(ctx["topic"], ctx["class_name"], chunks)

@router.post("/submit")
async def submit_quiz(
    payload: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    score_pct = (payload.score / payload.total) * 100 if payload.total > 0 else 0.0

    await update_quiz_score(current_user.id, payload.topic_id, score_pct, db)
    xp_result = await award_xp(current_user.id, "quiz_completed", db)

    if score_pct == 100:
        bonus = await award_xp(current_user.id, "quiz_perfect_score", db)
        xp_result["xp_awarded"] += bonus["xp_awarded"]

    new_badges = await check_and_award_badges(current_user.id, db)
    return {
        "score": payload.score,
        "total": payload.total,
        "percentage": round(score_pct, 1),
        "xp_earned": xp_result["xp_awarded"],
        "new_level": xp_result.get("new_level"),
        "new_badges": new_badges
    }
