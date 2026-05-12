from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class Vector2D(BaseModel):
    x: float
    y: float

class Meta(BaseModel):
    id: str
    title: str
    topic: str
    difficulty: str
    version: str = "1.0"

class Environment(BaseModel):
    gravity: Vector2D
    airResistance: float = 0.0
    groundFriction: float = 0.0

class Shape(BaseModel):
    type: str  # "rectangle", "circle"
    width: Optional[float] = None
    height: Optional[float] = None
    radius: Optional[float] = None

class PhysicsProps(BaseModel):
    mass: float
    movable: bool = True
    isSensor: bool = False

class MaterialProps(BaseModel):
    friction: float
    restitution: float

class VisualProps(BaseModel):
    color: str
    label: Optional[str] = None

class SimulationObject(BaseModel):
    id: str
    type: str = "dynamicBody"
    shape: Shape
    position: Vector2D
    velocity: Optional[Vector2D] = None
    acceleration: Optional[Vector2D] = None
    rotation: float = 0.0
    physics: PhysicsProps
    material: MaterialProps
    visual: VisualProps
    initialState: Optional[Dict[str, Any]] = None

class Force(BaseModel):
    id: str
    type: str  # "applied", "drag", "friction"
    target: str
    vector: Optional[Vector2D] = None
    coefficient: Optional[float] = None
    enabled: bool = True

class Interaction(BaseModel):
    type: str  # "slider", "toggle", "button"
    label: str
    bind: str  # e.g. "objects[0].physics.mass"
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = 0.1

class SimulationDSL(BaseModel):
    meta: Meta
    environment: Environment
    objects: List[SimulationObject]
    forces: List[Force]
    interactions: List[Interaction]

    def dict(self, **kwargs):
        kwargs.update({"exclude_none": True})
        return super().dict(**kwargs)

class KnowledgeSection(BaseModel):
    relevant_formulas: List[str]
    related_concepts: List[str]
    laws: List[str]
    explanations: List[str]

class MetadataSection(BaseModel):
    topic: str
    subject: str
    difficulty: str
    generated_at: str
    simulation_type: str

class EduSimResponse(BaseModel):
    dsl: SimulationDSL
    knowledge: KnowledgeSection
    metadata: MetadataSection

    def dict(self, **kwargs):
        kwargs.update({"exclude_none": True})
        return super().dict(**kwargs)