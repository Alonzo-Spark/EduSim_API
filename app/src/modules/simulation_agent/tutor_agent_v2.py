import json
from typing import Any, Dict, List

from .agentic_models import AdaptiveLearningProfile, CurriculumProfile, SimulationBlueprint, TutorPacket, PedagogicalStrategy
from .models import SimulationContext, SimulationTopic
from .llm_client import call_llm


def build_tutor_packet(
    prompt: str,
    topic: SimulationTopic,
    context: SimulationContext,
    curriculum: CurriculumProfile,
    adaptive_profile: AdaptiveLearningProfile,
    blueprint: SimulationBlueprint,
    strategy: PedagogicalStrategy = PedagogicalStrategy(),
) -> TutorPacket:
    """
    Generate a personalized tutoring packet using LLM-based Tutor Fusion,
    enhanced by pedagogical intelligence.
    """
    
    tutor_prompt = f"""
    # Task: Generate Pedagogically Tailored AI Tutor Packet
    
    You are an AI Tutor for a high-quality educational platform. 
    
    ## Educational Context
    Topic: {topic.topic}
    Subject: {topic.subject}
    Difficulty: {curriculum.difficulty}
    
    ## Pedagogical Strategy
    Explanation Style: {strategy.explanation_style}
    Instruction Mode: {strategy.instruction_mode}
    
    ## Simulation Blueprint
    Title: {blueprint.title}
    Controls: {[c['label'] for c in blueprint.controls]}
    Primary Formula: {blueprint.physics.get('formula')}
    
    ## Student Profile
    Learning Style: {adaptive_profile.cognitive.learning_style}
    Learning Speed: {adaptive_profile.cognitive.learning_speed}
    Weak Topics: {adaptive_profile.weak_topics}
    
    ## Requirements
    1. Explanation: Use '{strategy.explanation_style}' style. 
       - 'analogical': Use real-world metaphors.
       - 'technical': Focus on formulas and precision.
       - 'step-by-step': Break down the logic into manageable chunks.
    2. Adaptive Tip: Provide a tip that helps bridge gaps in '{adaptive_profile.weak_topics}'.
    3. Quiz: Tailor quiz complexity to the student's mastery.
    
    ## Output Format
    Return ONLY a JSON object that conforms to this structure:
    {{
        "explanation": "string",
        "adaptive_tip": "string",
        "revision_recommendations": ["string"],
        "quiz": [
            {{ "type": "mcq", "question": "string", "options": ["string"], "answer": 0 }},
            {{ "type": "short_answer", "question": "string", "expected": "string" }},
            {{ "type": "practical", "question": "string", "rubric": ["string"] }}
        ]
    }}
    """

    try:
        response_text = call_llm(
            tutor_prompt, 
            temperature=0.3, 
            response_mime_type="application/json"
        )
        packet_data = json.loads(response_text)
        
        return TutorPacket(**packet_data)
        
    except Exception as e:
        print(f"Tutor fusion failed: {e}. Falling back to template.")
        return _build_fallback_tutor_packet(topic, context, curriculum, adaptive_profile)


def _build_fallback_tutor_packet(
    topic: SimulationTopic,
    context: SimulationContext,
    curriculum: CurriculumProfile,
    adaptive_profile: AdaptiveLearningProfile,
) -> TutorPacket:
    formula = context.formulas[0] if context.formulas else "N/A"

    explanation = (
        f"Welcome! We're exploring {topic.topic}. "
        f"This simulation uses the formula: {formula}. "
        "Interact with the sliders to see how the variables affect the outcome."
    )

    adaptive_tip = f"Since you're working at a {curriculum.difficulty} level, focus on small changes first."
    
    recommendations = [f"Review {topic.topic} basics", f"Study {topic.subject} formulas"]

    quiz = [
        {
            "type": "mcq",
            "question": f"What is the primary concept in this simulation?",
            "options": [topic.topic, "Something else", "Nothing", "I don't know"],
            "answer": 0,
        }
    ]

    return TutorPacket(
        explanation=explanation,
        adaptive_tip=adaptive_tip,
        revision_recommendations=recommendations,
        quiz=quiz,
    )
