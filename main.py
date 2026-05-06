from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.src.api.simulation_router import simulation_router


app = FastAPI(
    title="EduSim Physics API",
    description="Backend APIs for EduSim physics simulations",
    version="1.0.0"
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

    return {
        "success": True,
        "message": "EduSim FastAPI Backend Running"
    }


# Simulation Routes

app.include_router(
    simulation_router,
    prefix="/api/simulations"
)