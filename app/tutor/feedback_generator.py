from app.core.llm_client import generate_structured_response
from app.tutor.prompts import BASE_SYSTEM_PROMPT

def generate_feedback(
    topic: str,
    class_name: str,
    quiz_score: float,
    quiz_total: int,
    simulation_count: int,
    time_spent_seconds: int,
    wrong_questions: list[dict]
) -> dict:
    wrong_summary = "\n".join([
        f"- Q: {q.get('questionText', '')} | Student answered: {q.get('studentAnswer', '')} | Correct: {q.get('correctAnswer', '')}"
        for q in wrong_questions
    ])

    prompt = f"""
A {class_name} student just completed a learning session on "{topic}".
Performance data:
- Quiz score: {quiz_score}/{quiz_total} ({round(quiz_score/quiz_total*100) if quiz_total else 0}%)
- Simulations launched: {simulation_count}
- Time spent: {round(time_spent_seconds/60)} minutes
- Questions answered incorrectly:
{wrong_summary if wrong_summary else "None — perfect score!"}

Generate adaptive feedback in this exact JSON:
{{
    "performanceSummary": "1–2 sentence encouraging summary of their session",
    "score": {quiz_score},
    "total": {quiz_total},
    "percentile": "Estimated percentile: e.g. top 30%",
    "weakConcepts": [
        {{"concept": "Concept name", "reason": "Why they struggled", "reviewTip": "How to improve"}}
    ],
    "recommendations": [
        {{"type": "review | practice | advance", "topic": "Topic name", "reason": "Why recommended"}}
    ],
    "masteryLevel": "beginner | developing | proficient | mastered",
    "encouragement": "A personal, motivating message for the student",
    "nextTopicSuggestion": "Name of next topic to study",
    "xpSummary": {{
        "quizXP": {round(quiz_score/quiz_total * 50) if quiz_total else 0},
        "simulationXP": {simulation_count * 15},
        "totalSessionXP": {round(quiz_score/quiz_total * 50) + simulation_count * 15 if quiz_total else simulation_count * 15}
    }}
}}
"""
    return generate_structured_response(BASE_SYSTEM_PROMPT, prompt, temperature=0.4)
