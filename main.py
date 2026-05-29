import sys
import os
# Configure Python Path to allow loading absolute namespaces (rag, tutor, sandbox)
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))
sys.path.append(os.path.join(root_dir, "app", "src"))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.src.modules.legacy_rag import load_all_pdfs
from app.src.api.simulation_router import simulation_router
from app.src.api.rag_router import rag_router
from app.src.api.tutor_router import tutor_router
from app.src.api.generate_router import generate_router
from app.src.modules.sandbox.controller import sandbox_router
from app.src.api.scene_router import scene_router
from app.src.api.auth import auth_router

from api.formula import router as generic_formula_router
from api.rag import router as generic_rag_router
from api.questions import router as generic_questions_router
from app.src.config.database import ping_database

# Configure global logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EduSim")
logger.info("EduSim Backend Starting Up...")
print("Formula Registry Loaded")
print("Vector Store Loaded")
print("Chapter Index Loaded")
print("Formula APIs Ready")
print("Question APIs Ready")
print("RAG Ready")
print("Server Ready")

from contextlib import asynccontextmanager
from app.src.modules.legacy_rag import vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload FAISS globally
    vector_store.load_all()
    
    # Automatically create tables for SQLite/PostgreSQL
    try:
        from app.src.config.database import Base, engine
        from app.src.models.user import User  # Registers User model with Base metadata
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database tables: {e}")
        
    yield

app = FastAPI(
    title="EduSim Physics API",
    description="Backend APIs for EduSim simulations",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change later in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Route
@app.get("/")
async def root():
    logger.info("Health check endpoint pinged.")
    return {
        "success": True,
        "message": "EduSim FastAPI Backend Running"
    }


@app.get("/api/db/health")
async def database_health():
    return ping_database()

# Simulation Routes

app.include_router(
    auth_router,
    prefix="/api/auth"
)

app.include_router(
    generate_router,
    prefix="/api"
)

app.include_router(
    sandbox_router,
    prefix="/api"
)

app.include_router(
    scene_router,
    prefix="/api"
)

app.include_router(
    simulation_router,
    prefix="/api/simulations"
)

app.include_router(
    rag_router,
    prefix="/api/rag"
)

app.include_router(
    tutor_router,
    prefix="/api/tutor"
)

# New Educational Intelligence Engine RAG router
from app.src.rag.controller import router as edusim_rag_router
app.include_router(edusim_rag_router)

# --- Generic APIs for Formula Lab and Q&A ---
app.include_router(generic_formula_router, prefix="/api/formula")
app.include_router(generic_rag_router, prefix="/api/rag")
app.include_router(generic_questions_router, prefix="/api/questions")
