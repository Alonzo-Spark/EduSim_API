import math
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.models.gamification import UserBadge
from app.models.progress import UserProgress
from app.models.simulation import Simulation

def calculate_level(xp: int) -> int:
    """Level = floor(1 + sqrt(xp / 100))"""
    return max(1, int(1 + math.sqrt(xp / 100)))

XP_EVENTS = {
    "explanation_viewed": 10,
    "formulas_viewed": 5,
    "quiz_completed": 20,
    "quiz_perfect_score": 30,      # bonus on top of quiz_completed
    "simulation_launched": 15,
    "simulation_saved": 10,
    "daily_login": 5,
    "streak_7_days": 50,
    "streak_30_days": 200,
}

BADGE_DEFINITIONS = {
    "first_steps": {
        "title": "First Steps",
        "description": "Opened your first topic",
        "rarity": "common",
        "icon": "👣"
    },
    "first_simulation": {
        "title": "Lab Rat",
        "description": "Launched your first simulation",
        "rarity": "common",
        "icon": "🧪"
    },
    "quiz_master": {
        "title": "Quiz Master",
        "description": "Scored 100% on 5 quizzes",
        "rarity": "rare",
        "icon": "🏆"
    },
    "seven_day_streak": {
        "title": "On Fire",
        "description": "7-day learning streak",
        "rarity": "rare",
        "icon": "🔥"
    },
    "formula_pro": {
        "title": "Formula Pro",
        "description": "Studied formulas for 10 topics",
        "rarity": "common",
        "icon": "📐"
    },
    "sim_collector": {
        "title": "Simulation Collector",
        "description": "Saved 10 simulations",
        "rarity": "rare",
        "icon": "💾"
    },
    "century": {
        "title": "Century Club",
        "description": "Earned 1000 XP",
        "rarity": "epic",
        "icon": "💯"
    },
    "explorer": {
        "title": "Explorer",
        "description": "Studied topics in 3+ subjects",
        "rarity": "rare",
        "icon": "🔭"
    },
    "speed_learner": {
        "title": "Speed Learner",
        "description": "Completed a full learning flow in under 20 minutes",
        "rarity": "epic",
        "icon": "⚡"
    },
}

async def award_xp(user_id, event: str, db: AsyncSession) -> dict:
    xp_amount = XP_EVENTS.get(event, 0)
    if xp_amount == 0:
        return {"xp_awarded": 0, "new_level": None}

    user = await db.get(User, user_id)
    if not user:
        return {"xp_awarded": 0, "new_level": None}
        
    old_level = user.level
    user.xp += xp_amount
    user.level = calculate_level(user.xp)
    await db.commit()

    new_level = user.level if user.level > old_level else None
    return {"xp_awarded": xp_amount, "new_level": new_level, "total_xp": user.xp}

async def check_and_award_badges(user_id, db: AsyncSession) -> list[dict]:
    """Check all badge conditions and award any newly earned badges."""
    user = await db.get(User, user_id)
    if not user:
        return []

    # Get existing badges
    existing = await db.execute(
        select(UserBadge.badge_key).where(UserBadge.user_id == user_id)
    )
    earned_keys = {row[0] for row in existing.fetchall()}

    # Gather stats for condition checking
    sim_count = await db.scalar(
        select(func.count()).select_from(Simulation).where(Simulation.user_id == user_id)
    )
    saved_count = await db.scalar(
        select(func.count()).select_from(Simulation)
        .where(Simulation.user_id == user_id, Simulation.is_saved == True)
    )
    perfect_quizzes = await db.scalar(
        select(func.count()).select_from(UserProgress)
        .where(UserProgress.user_id == user_id, UserProgress.quiz_score >= 100.0)
    )
    formulas_topics = await db.scalar(
        select(func.count()).select_from(UserProgress)
        .where(UserProgress.user_id == user_id, UserProgress.formulas_viewed == True)
    )

    conditions = {
        "first_steps": True,                               # always after first session
        "first_simulation": (sim_count or 0) >= 1,
        "quiz_master": (perfect_quizzes or 0) >= 5,
        "seven_day_streak": (user.streak or 0) >= 7,
        "formula_pro": (formulas_topics or 0) >= 10,
        "sim_collector": (saved_count or 0) >= 10,
        "century": (user.xp or 0) >= 1000,
        "explorer": False,                                 # check separately via subjects
    }

    new_badges = []
    for badge_key, condition in conditions.items():
        if condition and badge_key not in earned_keys:
            badge = UserBadge(user_id=user_id, badge_key=badge_key)
            db.add(badge)
            new_badges.append({
                **BADGE_DEFINITIONS[badge_key],
                "badge_key": badge_key,
                "earned_at": datetime.utcnow().isoformat()
            })

    if new_badges:
        await db.commit()

    return new_badges

async def update_streak(user_id, db: AsyncSession):
    user = await db.get(User, user_id)
    if not user:
        return 0
        
    today = date.today()
    last = user.last_active.date() if user.last_active else None

    if last is None or (today - last).days > 1:
        user.streak = 1
    elif (today - last).days == 1:
        user.streak += 1
        # Award streak XP milestones
        if user.streak == 7:
            user.xp += XP_EVENTS["streak_7_days"]
        elif user.streak == 30:
            user.xp += XP_EVENTS["streak_30_days"]

    user.last_active = datetime.utcnow()
    user.level = calculate_level(user.xp)
    await db.commit()
    return user.streak
