from uuid import uuid4

from .agentic_models import AgentTask, PlannerPlan


def build_master_plan(user_prompt: str) -> PlannerPlan:
    tasks = [
        AgentTask(name="planning", agent="planner_agent"),
        AgentTask(name="curriculum_mapping", agent="curriculum_agent"),
        AgentTask(name="rag_retrieval", agent="rag_retrieval_agent"),
        AgentTask(name="formula_extraction", agent="formula_extraction_agent"),
        AgentTask(name="adaptive_tutoring", agent="tutor_agent"),
        AgentTask(name="blueprint_synthesis", agent="simulation_blueprint_agent"),
        AgentTask(name="visualization_planning", agent="visualization_agent"),
        AgentTask(name="interaction_planning", agent="interaction_agent"),
        AgentTask(name="html_synthesis", agent="html_synthesis_agent"),
        AgentTask(name="verification", agent="verification_agent"),
        AgentTask(name="repair", agent="repair_agent"),
        AgentTask(name="runtime_monitoring", agent="runtime_monitoring_agent"),
        AgentTask(name="adaptive_feedback", agent="adaptive_feedback_agent"),
    ]

    return PlannerPlan(
        plan_id=f"plan_{uuid4()}",
        user_prompt=user_prompt,
        quality_target="high",
        tasks=tasks,
    )


def mark_task(plan: PlannerPlan, task_name: str, status: str, details: dict | None = None) -> None:
    for task in plan.tasks:
        if task.name == task_name:
            task.status = status
            if details:
                task.details.update(details)
            return
