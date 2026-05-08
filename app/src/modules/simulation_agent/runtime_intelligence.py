import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class RuntimeReport(BaseModel):
    simulation_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    fps_avg: float
    js_errors: List[Dict[str, Any]] = Field(default_factory=list)
    interaction_count: int
    failed_controls: List[str] = Field(default_factory=list)
    physics_stability: float = 1.0 # 0.0 to 1.0
    memory_usage_estimate: Optional[float] = None

class SimulationHealthScore(BaseModel):
    stability: int
    interactivity: int
    educational_clarity: int
    performance: int
    overall: int

class RuntimeIntelligenceAgent:
    """
    Analyzes simulation runtime reports and provides health scores,
    optimization suggestions, and repair triggers.
    """
    
    def __init__(self, memory_system=None):
        self.memory_system = memory_system

    def analyze_report(self, report: RuntimeReport) -> SimulationHealthScore:
        """Calculate health scores based on runtime metrics."""
        
        # Stability: Deduct for JS errors and low physics stability
        stability = 100 - (len(report.js_errors) * 20)
        stability = max(0, min(100, int(stability * report.physics_stability)))
        
        # Interactivity: Based on interaction count and failed controls
        interactivity = min(100, report.interaction_count * 5)
        if report.failed_controls:
            interactivity -= len(report.failed_controls) * 15
        interactivity = max(0, interactivity)
        
        # Performance: Based on average FPS
        performance = int((report.fps_avg / 60.0) * 100)
        performance = max(0, min(100, performance))
        
        # Educational Clarity (Heuristic for now, can be improved with LLM)
        educational_clarity = 90 if stability > 80 and interactivity > 50 else 70
        
        overall = (stability + interactivity + performance + educational_clarity) // 4
        
        return SimulationHealthScore(
            stability=stability,
            interactivity=interactivity,
            educational_clarity=educational_clarity,
            performance=performance,
            overall=overall
        )

    def should_trigger_repair(self, score: SimulationHealthScore) -> bool:
        """Determine if a simulation needs automatic repair."""
        return score.stability < 70 or score.performance < 40

    def generate_optimization_advice(self, report: RuntimeReport) -> List[str]:
        """Suggest performance optimizations based on report."""
        advice = []
        if report.fps_avg < 30:
            advice.append("Reduce particle count")
            advice.append("Simplify canvas drawing operations")
            advice.append("Throttle physics updates")
        if report.js_errors:
            advice.append("Check for null pointer exceptions in animation loop")
        return advice

    def optimize_blueprint(self, blueprint: Any, report: RuntimeReport) -> Any:
        """Dynamically optimize a blueprint based on performance issues."""
        if report.fps_avg < 25:
            # Simplify animations
            if "animations" in blueprint:
                blueprint["animations"]["trail"] = False
                blueprint["animations"]["fps_target"] = 30
            # Reduce objects if many
            if len(blueprint.get("objects", [])) > 5:
                blueprint["objects"] = blueprint["objects"][:3]
        
        return blueprint

# Global instance
runtime_agent = RuntimeIntelligenceAgent()

