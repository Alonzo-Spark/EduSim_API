from app.api.auth import router as auth_router
from app.api.curriculum import router as curriculum_router
from app.api.tutor import router as tutor_router
from app.api.simulations import router as simulations_router
from app.api.quiz import router as quiz_router
from app.api.progress import router as progress_router

__all__ = [
    "auth_router",
    "curriculum_router",
    "tutor_router",
    "simulations_router",
    "quiz_router",
    "progress_router",
]
