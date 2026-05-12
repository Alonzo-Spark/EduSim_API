from pydantic import BaseModel, Field, model_validator
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

class WorldConfig(BaseModel):
    width: float = 800
    height: float = 600

class BackgroundConfig(BaseModel):
    color: str = "#ffffff"

class Environment(BaseModel):
    gravity: Vector2D
    airResistance: float = 0.0
    world: Optional[WorldConfig] = Field(default_factory=WorldConfig)
    background: Optional[BackgroundConfig] = Field(default_factory=BackgroundConfig)

class Shape(BaseModel):
    type: str  # "rectangle", "circle"
    width: Optional[float] = None
    height: Optional[float] = None
    radius: Optional[float] = None

class PhysicsProps(BaseModel):
    mass: float = 1.0
    isSensor: bool = False

class MaterialProps(BaseModel):
    friction: float = 0.5
    restitution: float = 0.5

class VisualProps(BaseModel):
    color: str
    label: Optional[str] = None
    showVelocityVector: bool = False

class SimulationObject(BaseModel):
    id: str
    type: str = "dynamicBody"
    shape: Shape
    position: Vector2D
    velocity: Optional[Vector2D] = None
    acceleration: Optional[Vector2D] = None
    rotation: float = 0.0
    physics: PhysicsProps = Field(default_factory=PhysicsProps)
    material: MaterialProps = Field(default_factory=MaterialProps)
    visual: VisualProps
    initialState: Optional[Dict[str, Any]] = None

class Force(BaseModel):
    id: str
    type: str  # "applied", "drag", "friction", "force"
    target: str
    vector: Optional[Vector2D] = None
    coefficient: Optional[float] = None
    enabled: bool = True

class Constraint(BaseModel):
    id: str
    type: str  # "rope", "spring", "link"
    bodyA: str
    bodyB: str
    length: float
    stiffness: float = 0.9

class Behavior(BaseModel):
    id: str
    type: str  # "drag", "brownian"
    targets: List[str]
    coefficient: Optional[float] = None
    enabled: bool = True

class Interaction(BaseModel):
    id: Optional[str] = None
    type: str  # "slider", "toggle", "button"
    label: str
    bind: str  # e.g. "objects[0].physics.mass"
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None

    @model_validator(mode='after')
    def check_type_constraints(self) -> 'Interaction':
        if self.type == "toggle" or self.type == "button":
            if self.min is not None or self.max is not None or self.step is not None:
                raise ValueError(f"{self.type.capitalize()}s cannot have min/max/step fields")
        elif self.type == "slider":
            if self.min is None or self.max is None:
                raise ValueError("Sliders must have min and max fields")
            if self.step is None:
                self.step = 0.1
        return self

class RuntimeConfig(BaseModel):
    engine: str = "matter-js"
    fps: int = 60
    scale: int = 40

class SimulationDSL(BaseModel):
    meta: Meta
    environment: Environment
    objects: List[SimulationObject]
    forces: List[Force] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    behaviors: List[Behavior] = Field(default_factory=list)
    interactions: List[Interaction] = Field(default_factory=list)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)

    def dict(self, **kwargs):
        kwargs.update({"exclude_none": True})
        return super().dict(**kwargs)

class KnowledgeSection(BaseModel):
    relevant_formulas: List[str]
    related_concepts: List[str]
    laws: List[str]
    explanations: List[str]

class MetadataSection(BaseModel):
    topic: Optional[str] = None
    subject: str
    difficulty: str
    generated_at: Optional[str] = None
    simulation_type: str

class EduSimResponse(BaseModel):
    dsl: SimulationDSL
    knowledge: KnowledgeSection
    metadata: MetadataSection

    def dict(self, **kwargs):
        kwargs.update({"exclude_none": True})
        return super().dict(**kwargs)