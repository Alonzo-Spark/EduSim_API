from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.progress import UserProgress

async def get_or_create_progress(user_id, topic_id, db: AsyncSession) -> UserProgress:
    result = await db.execute(
        select(UserProgress).where(
            UserProgress.user_id == user_id,
            UserProgress.topic_id == topic_id
        )
    )
    progress = result.scalar_one_or_none()
    if not progress:
        progress = UserProgress(
            user_id=user_id,
            topic_id=topic_id,
            completion=0.0,
            xp_earned=0,
            quiz_score=None,
            quiz_attempts=0,
            simulation_count=0,
            explanation_viewed=False,
            formulas_viewed=False,
            last_studied=datetime.utcnow()
        )
        db.add(progress)
        await db.flush()
    return progress

async def log_step_completion(user_id, topic_id, step: str, db: AsyncSession) -> UserProgress:
    progress = await get_or_create_progress(user_id, topic_id, db)
    
    if step == "explanation":
        progress.explanation_viewed = True
    elif step == "formulas":
        progress.formulas_viewed = True
    elif step == "simulation":
        progress.simulation_count += 1
        
    # Recalculate completion score (explanation: 30%, formulas: 30%, simulation: 20%, quiz: 20%)
    completion_sum = 0.0
    if progress.explanation_viewed:
        completion_sum += 0.3
    if progress.formulas_viewed:
        completion_sum += 0.3
    if progress.simulation_count > 0:
        completion_sum += 0.2
    if progress.quiz_score is not None:
        completion_sum += 0.2
        
    progress.completion = min(1.0, completion_sum)
    progress.last_studied = datetime.utcnow()
    await db.commit()
    return progress

async def update_quiz_score(user_id, topic_id, score: float, db: AsyncSession) -> UserProgress:
    progress = await get_or_create_progress(user_id, topic_id, db)
    progress.quiz_attempts += 1
    progress.quiz_score = score
    
    # Recalculate completion
    completion_sum = 0.0
    if progress.explanation_viewed:
        completion_sum += 0.3
    if progress.formulas_viewed:
        completion_sum += 0.3
    if progress.simulation_count > 0:
        completion_sum += 0.2
    if progress.quiz_score is not None:
        completion_sum += 0.2
        
    progress.completion = min(1.0, completion_sum)
    progress.last_studied = datetime.utcnow()
    await db.commit()
    return progress
