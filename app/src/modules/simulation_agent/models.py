from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SimulationTopic(BaseModel):
    """Detected topic information from user prompt."""
    topic: str = Field(..., description="Main topic (e.g., 'projectile motion')")
    subject: str = Field(..., description="Subject domain (physics, chemistry, astronomy, biology, mathematics)")
    subtopic: Optional[str] = Field(None, description="Optional subtopic for granularity")
    complexity: str = Field(default="medium", description="Complexity level: beginner, medium, advanced")
    grade_level: Optional[str] = Field(None, description="Estimated grade level: 9, 10, 11, 12, college")


class SimulationInteraction(BaseModel):
    """Interactive controls required in simulation."""
    name: str = Field(..., description="Control name (e.g., 'initial_velocity')")
    label: str = Field(..., description="Display label (e.g., 'Initial Velocity')")
    type: str = Field(default="slider", description="Control type: slider, button, input, toggle")
    min: Optional[float] = Field(None, description="Minimum value for sliders")
    max: Optional[float] = Field(None, description="Maximum value for sliders")
    default: Optional[float] = Field(None, description="Default value")
    unit: Optional[str] = Field(None, description="Unit label (e.g., 'm/s')")


class SimulationContext(BaseModel):
    """Context retrieved from textbooks via RAG."""
    topic: str
    formulas: List[str] = Field(default_factory=list, description="Extracted formulas")
    constants: List[str] = Field(default_factory=list, description="Physical/chemical constants")
    laws: List[str] = Field(default_factory=list, description="Relevant laws or principles")
    definitions: List[str] = Field(default_factory=list, description="Key term definitions")
    worked_examples: List[str] = Field(default_factory=list, description="Examples from textbook")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source citations")


class AgentGenerateRequest(BaseModel):
    """Request for autonomous agent simulation generation."""
    prompt: str = Field(..., min_length=5, description="Natural language prompt for simulation")
    topic: Optional[str] = Field(None, description="Optional topic override")
    complexity: Optional[str] = Field(None, description="Optional complexity level override")
    include_answers: bool = Field(default=True, description="Include answer key/formulas")
    streaming: bool = Field(default=True, description="Enable streaming response")


class AgentGenerateResponse(BaseModel):
    """Response from autonomous agent simulation generation."""
    success: bool = Field(True, description="Whether generation succeeded")
    id: str = Field(..., description="Simulation ID")
    
    # Metadata
    title: str = Field(..., description="Simulation title")
    description: str = Field(..., description="Educational description")
    topic: SimulationTopic = Field(..., description="Detected topic information")
    
    # Content
    html: str = Field(..., description="Generated HTML simulation")
    formula: Optional[str] = Field(None, description="Primary formula demonstrated")
    formulas: List[str] = Field(default_factory=list, description="All formulas used")
    
    # Educational
    learning_objectives: List[str] = Field(default_factory=list, description="What student will learn")
    related_concepts: List[str] = Field(default_factory=list, description="Related topics to explore")
    
    # Interactivity
    interactions: List[SimulationInteraction] = Field(default_factory=list, description="Available controls")
    
    # Context
    context: SimulationContext = Field(..., description="Retrieved textbook context")
    
    # File info
    html_path: Optional[str] = Field(None, description="Path where HTML was saved")
    timestamp: datetime = Field(..., description="When simulation was generated")
    
    # Pipeline info
    generation_stages: List[str] = Field(default_factory=list, description="Stages completed")


class AgentStreamingProgress(BaseModel):
    """Progress event during streaming generation."""
    stage: str = Field(..., description="Current stage name")
    progress: int = Field(default=0, description="Progress percentage 0-100")
    message: Optional[str] = Field(None, description="Optional detailed message")
