import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rag.loader import load_all_pdfs
from app.src.api.simulation_router import simulation_router
from app.src.api.rag_router import rag_router
from app.src.api.tutor_router import tutor_router

# Configure global logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("EduSim")
logger.info("EduSim Backend Starting Up...")

from contextlib import asynccontextmanager
from rag.vector_loader import vector_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload FAISS globally
    vector_store.load_all()
    yield

app = FastAPI(
    title="EduSim Physics API",
    description="Backend APIs for EduSim  simulations",
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



# Simulation Routes

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