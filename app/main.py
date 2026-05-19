from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine
from app.models import user, curriculum, progress, simulation, gamification
from app.database import Base
from app.api import auth, curriculum as curriculum_api, tutor, simulations, quiz, progress as progress_api

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables automatically if they don't exist yet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title="EduSim API",
    description="AI-powered educational platform with RAG-based textbook learning",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration with exact dev origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Registration with unified /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(curriculum_api.router, prefix="/api")
app.include_router(tutor.router, prefix="/api")
app.include_router(simulations.router, prefix="/api")
app.include_router(quiz.router, prefix="/api")
app.include_router(progress_api.router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "ok", "service": "EduSim API", "version": "1.0.0"}
