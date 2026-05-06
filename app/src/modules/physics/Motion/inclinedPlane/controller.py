# controller.py

from fastapi import HTTPException
from pydantic import BaseModel
from .services import run_inclined_plane_simulation

class SimulationRequest(BaseModel):
    angle: float
    mass: float
    friction: float
    gravity: float = 9.8

async def inclined_plane_controller(request: SimulationRequest):
    try:
        if request.angle is None or request.mass is None or request.friction is None:
            raise HTTPException(status_code=400, detail="angle, mass, and friction are required")

        result = run_inclined_plane_simulation(
            angle=request.angle,
            mass=request.mass,
            friction=request.friction,
            gravity=request.gravity
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="Simulation failed")