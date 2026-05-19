from app.services.curriculum_service import (
    get_all_classes,
    get_subjects,
    get_chapters,
    get_topics,
    get_topic_by_slug,
    get_topic_full_context,
)
from app.services.progress_service import (
    log_step_completion,
    update_quiz_score,
    get_or_create_progress,
)
from app.services.gamification_service import (
    calculate_level,
    award_xp,
    check_and_award_badges,
    update_streak,
    XP_EVENTS,
    BADGE_DEFINITIONS,
)
from app.services.asset_service import (
    load_asset_catalog,
    get_assets_for_topic,
)

__all__ = [
    "get_all_classes",
    "get_subjects",
    "get_chapters",
    "get_topics",
    "get_topic_by_slug",
    "get_topic_full_context",
    "log_step_completion",
    "update_quiz_score",
    "get_or_create_progress",
    "calculate_level",
    "award_xp",
    "check_and_award_badges",
    "update_streak",
    "XP_EVENTS",
    "BADGE_DEFINITIONS",
    "load_asset_catalog",
    "get_assets_for_topic",
]
