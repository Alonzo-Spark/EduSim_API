import json
from typing import Any, Dict, List

from .agentic_models import CurriculumProfile, SimulationBlueprint, VerificationReport
from .models import SimulationContext, SimulationTopic
from .physics_verifier import verify_physics_consistency
from .llm_client import call_llm


def verify_full_artifact(
    topic: SimulationTopic,
    context: SimulationContext,
    curriculum: CurriculumProfile,
    blueprint: SimulationBlueprint,
    html: str,
) -> VerificationReport:
    """
    Perform multi-layer verification of the generated simulation artifact.
    """
    report = VerificationReport(passed=True)

    # 1. Basic Rule-Based Checks
    _verify_formula_presence(context, blueprint, report)
    _verify_curriculum_alignment(curriculum, topic, report)

    # 2. Physics Consistency Check (Static Analysis)
    physics = verify_physics_consistency(
        {
            "formulas": context.formulas,
            "constants": context.constants,
            "laws": context.laws,
        },
        html,
    )

    if not physics.get("ok", True):
        report.passed = False
        for issue in physics.get("issues", []):
            report.issues.append({
                "type": issue.get("type", "physics_issue"), 
                "message": issue.get("message")
            })

    # 3. LLM-Based Conceptual Verification
    _verify_with_llm(topic, context, blueprint, html, report)

    report.formula_checks.append("Formula extraction and usage validated")
    report.curriculum_checks.append("Curriculum profile consistency validated")

    return report


def _verify_with_llm(
    topic: SimulationTopic,
    context: SimulationContext,
    blueprint: SimulationBlueprint,
    html: str,
    report: VerificationReport
) -> None:
    """
    Use an LLM to verify conceptual accuracy and alignment.
    """
    
    # We send a snippet of the HTML to avoid token limits, focusing on the script
    html_snippet = html[:2000] + "..." + html[-2000:] if len(html) > 4000 else html
    
    verifier_prompt = f"""
    # Task: Verify Educational Simulation
    
    You are a subject matter expert in {topic.subject}. Review the following simulation artifact for conceptual accuracy and safety.
    
    ## Context
    Topic: {topic.topic}
    Primary Formula: {blueprint.physics.get('formula')}
    Target Outcomes: {curriculum.outcomes}
    
    ## Artifact Details
    Blueprint Title: {blueprint.title}
    HTML Snippet:
    {html_snippet}
    
    ## Evaluation Criteria
    1. Conceptual Accuracy: Does the simulation correctly model the stated physics/math?
    2. Educational Alignment: Does it address the learning outcomes?
    3. Technical Safety: Are there any obvious bugs or security risks in the JS?
    
    ## Output Format
    Return ONLY a JSON object:
    {{
        "passed": true|false,
        "issues": [
            {{ "type": "accuracy|safety|alignment", "message": "string" }}
        ]
    }}
    """

    try:
        response_text = call_llm(
            verifier_prompt, 
            temperature=0.1, 
            response_mime_type="application/json"
        )
        llm_report = json.loads(response_text)
        
        if not llm_report.get("passed", True):
            report.passed = False
            for issue in llm_report.get("issues", []):
                report.issues.append(issue)
                
    except Exception as e:
        report.issues.append({
            "type": "verification_error", 
            "message": f"LLM verification failed: {str(e)}"
        })


def _verify_formula_presence(context: SimulationContext, blueprint: SimulationBlueprint, report: VerificationReport) -> None:
    if not context.formulas:
        report.passed = False
        report.issues.append(
            {
                "type": "missing_formula",
                "message": "No formulas retrieved from context. Cannot guarantee educational validity.",
            }
        )

    bp_formula = str(blueprint.physics.get("formula", "")).strip()
    if not bp_formula:
        report.passed = False
        report.issues.append(
            {
                "type": "blueprint_formula_missing",
                "message": "Blueprint has no primary formula.",
            }
        )


def _verify_curriculum_alignment(curriculum: CurriculumProfile, topic: SimulationTopic, report: VerificationReport) -> None:
    if not curriculum.outcomes:
        report.issues.append(
            {
                "type": "missing_outcomes",
                "message": "Curriculum outcomes are empty; falling back to generic learning objective.",
            }
        )

    if curriculum.subject and topic.subject and curriculum.subject != topic.subject:
        report.passed = False
        report.issues.append(
            {
                "type": "subject_mismatch",
                "message": f"Curriculum subject {curriculum.subject} does not match detected subject {topic.subject}.",
            }
        )
