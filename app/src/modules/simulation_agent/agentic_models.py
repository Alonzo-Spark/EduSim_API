from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .models import SimulationContext, SimulationTopic


class AgentTask(BaseModel):
    name: str
    agent: str
    status: str = "pending"
    details: Dict[str, Any] = Field(default_factory=dict)


class PlannerPlan(BaseModel):
    plan_id: str
    user_prompt: str
    quality_target: str = "high"
    tasks: List[AgentTask] = Field(default_factory=list)


class CurriculumProfile(BaseModel):
    class_level: Optional[str] = None
    board: Optional[str] = None
    subject: Optional[str] = None
    chapter: Optional[str] = None
    difficulty: str = "medium"
    outcomes: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    progression_path: List[str] = Field(default_factory=list)


class CognitiveProfile(BaseModel):
    learning_style: str = "visual" # visual, analytical, practical
    learning_speed: float = 1.0 # 0.5 (slow) to 2.0 (fast)
    engagement_score: int = 50
    confusion_patterns: List[str] = Field(default_factory=list)
    retry_frequency: float = 0.0
    exploration_bias: float = 0.5 # 0.0 (guided) to 1.0 (free)

class MasteryState(BaseModel):
    conceptual: int = 0 # 0-100
    practical: int = 0 # 0-100
    formula_confidence: int = 0 # 0-100
    overall: int = 0

class PedagogicalStrategy(BaseModel):
    instruction_mode: str = "guided" # guided, discovery, challenge
    visualization_complexity: str = "medium" # simple, medium, complex
    animation_speed_scale: float = 1.0
    label_density: str = "medium" # low, medium, high
    explanation_style: str = "analogical" # technical, analogical, step-by-step

class AdaptiveLearningProfile(BaseModel):
    user_id: Optional[str] = None
    weak_topics: List[str] = Field(default_factory=list)
    strong_topics: List[str] = Field(default_factory=list)
    completed_simulations: List[str] = Field(default_factory=list)
    interaction_patterns: Dict[str, Any] = Field(default_factory=dict)
    cognitive: CognitiveProfile = Field(default_factory=CognitiveProfile)
    mastery: Dict[str, MasteryState] = Field(default_factory=dict) # topic -> MasteryState



class TutorPacket(BaseModel):
    explanation: str
    adaptive_tip: str
    revision_recommendations: List[str] = Field(default_factory=list)
    quiz: List[Dict[str, Any]] = Field(default_factory=list)


class SimulationBlueprint(BaseModel):
    id: str
    title: str
    topic: str
    subject: str
    difficulty: str
    objects: List[Dict[str, Any]] = Field(default_factory=list)
    physics: Dict[str, Any] = Field(default_factory=dict)
    controls: List[Dict[str, Any]] = Field(default_factory=list)
    visuals: Dict[str, Any] = Field(default_factory=dict)
    animations: Dict[str, Any] = Field(default_factory=dict)
    educational_overlays: Dict[str, Any] = Field(default_factory=dict)
    runtime_monitoring: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VerificationReport(BaseModel):
    passed: bool = True
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    formula_checks: List[str] = Field(default_factory=list)
    curriculum_checks: List[str] = Field(default_factory=list)


class AgenticGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    class_level: Optional[str] = None
    board: Optional[str] = None
    chapter: Optional[str] = None
    difficulty: Optional[str] = None
    subject: Optional[str] = None


class AgenticRegenerateRequest(BaseModel):
    simulation_id: str
    instruction: str = Field(..., min_length=3)
    user_id: Optional[str] = None


class AgenticGenerateResponse(BaseModel):
    success: bool = True
    id: str
    created_at: datetime
    planner_plan: PlannerPlan
    topic: SimulationTopic
    curriculum: CurriculumProfile
    context: SimulationContext
    blueprint: SimulationBlueprint
    html: str
    html_path: Optional[str] = None
    tutor: TutorPacket
    verification: VerificationReport
    adaptive_profile: AdaptiveLearningProfile
    pedagogical_strategy: PedagogicalStrategy
    generation_stages: List[str] = Field(default_factory=list)
    memory_hits: List[Dict[str, Any]] = Field(default_factory=list)
    marketplace: Dict[str, Any] = Field(default_factory=dict)

