import sys
import os
# Configure Python Path to allow loading absolute namespaces (rag, tutor, sandbox)
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "app", "src", "modules"))
sys.path.append(os.path.join(root_dir, "app", "src"))

# Dynamically extend app.src.modules.__path__ to resolve archived modules safely
import app.src.modules
archive_modules_dir = os.path.join(root_dir, "archive", "app", "src", "modules")
if os.path.exists(archive_modules_dir):
    app.src.modules.__path__.append(archive_modules_dir)

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.src.modules.legacy_rag import load_all_pdfs
from app.src.api.tutor_router import tutor_router
from app.src.modules.sandbox.controller import sandbox_router

from api.formula import router as generic_formula_router
from api.rag import router as generic_rag_router
from api.questions import router as generic_questions_router

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

# Simulation and Tutoring Routes

app.include_router(
    sandbox_router,
    prefix="/api"
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