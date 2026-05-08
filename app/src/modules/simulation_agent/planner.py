from typing import Dict, Any

# Planner scaffold: orchestrates sub-agents


def plan_generation(prompt: str, topic: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Return a plan dict describing steps and responsibilities for sub-agents."""
    plan = {
        "prompt": prompt,
        "topic": topic,
        "steps": [
            {"name": "formula_agent", "description": "Extract and verify formulas and units"},
            {"name": "visualization_agent", "description": "Plan visuals, canvas layout, annotations"},
            {"name": "interaction_agent", "description": "Plan controls and interactions"},
            {"name": "html_synthesizer", "description": "Generate HTML/CSS/JS from blueprint"},
            {"name": "repair_agent", "description": "Repair and validate output"},
            {"name": "quality_agent", "description": "Score and accept/reject"},
        ],
        "context_summary": {
            "formulas": context.get("formulas", []),
            "constants": context.get("constants", []),
            "laws": context.get("laws", [])
        }
    }
    return plan


def execute_plan(plan: Dict[str, Any]):
    """Currently a lightweight executor that returns the plan; actual sub-agents are implemented elsewhere."""
    # In future: call formula_agent -> visualization_agent -> interaction_agent -> html_synthesizer
    return {"status": "planned", "plan": plan}
