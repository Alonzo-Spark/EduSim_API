from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.deps import get_db, get_current_user
from app.models.progress import UserProgress
from app.models.simulation import Simulation
from app.models.gamification import UserBadge
from app.services.gamification_service import BADGE_DEFINITIONS

router = APIRouter(prefix="/progress", tags=["Progress"])

@router.get("/summary")
async def get_progress_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    topics_count = await db.scalar(
        select(func.count()).select_from(UserProgress)
        .where(UserProgress.user_id == current_user.id, UserProgress.completion > 0)
    )
    sim_count = await db.scalar(
        select(func.count()).select_from(Simulation)
        .where(Simulation.user_id == current_user.id)
    )
    badges = await db.execute(
        select(UserBadge).where(UserBadge.user_id == current_user.id)
    )
    badge_list = [
        {**BADGE_DEFINITIONS.get(b.badge_key, {"title": b.badge_key}), "earned_at": b.earned_at.isoformat()}
        for b in badges.scalars().all()
    ]

    return {
        "topics_learned": topics_count or 0,
        "simulations_run": sim_count or 0,
        "xp": current_user.xp,
        "level": current_user.level,
        "streak": current_user.streak,
        "badges": badge_list
    }

@router.get("/recent")
async def get_recent_topics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    result = await db.execute(
        select(UserProgress)
        .where(UserProgress.user_id == current_user.id)
        .order_by(UserProgress.last_studied.desc())
        .limit(5)
    )
    return [
        {
            "topic_id": p.topic_id,
            "completion": p.completion,
            "quiz_score": p.quiz_score,
            "last_studied": p.last_studied.isoformat()
        }
        for p in result.scalars().all()
    ]

@router.get("/leaderboard")
async def get_leaderboard(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    from app.models.user import User
    result = await db.execute(
        select(User).order_by(User.xp.desc()).limit(20)
    )
    users = result.scalars().all()
    leaderboard = [
        {
            "rank": i + 1,
            "name": u.name,
            "xp": u.xp,
            "level": u.level,
            "streak": u.streak,
            "is_current_user": u.id == current_user.id
        }
        for i, u in enumerate(users)
    ]
    return leaderboard
