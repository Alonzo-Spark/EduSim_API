from pydantic import BaseModel
from typing import List, Dict, Optional


# =========================================================
# Environment
# =========================================================

class Environment(BaseModel):
    gravity: float = 9.8
    friction: float = 0.0
    air_resistance: float = 0.0


# =========================================================
# Entity
# =========================================================

class Entity(BaseModel):
    id: str
    type: str

    mass: Optional[float] = None

    properties: Dict = {}


# =========================================================
# Interaction
# =========================================================

class Interaction(BaseModel):
    type: str

    target: Optional[str] = None

    parameters: Dict = {}


# =========================================================
# Visualization
# =========================================================

class Visualization(BaseModel):
    type: str


# =========================================================
# Main DSL Schema
# =========================================================

class SimulationDSL(BaseModel):
    simulation_type: str

    topic: str

    environment: Environment

    entities: List[Entity]

    interactions: List[Interaction]

    visualizations: List[Visualization]

    equations: List[str]