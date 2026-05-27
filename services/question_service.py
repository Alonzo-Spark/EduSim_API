import json
import re
from typing import List, Optional
from services.rag_service import RagService
from app.src.modules.legacy_rag.generator import generate_llm_text_async
from app.src.models.question_models import QuestionGenerationResponse, QuestionModel

class QuestionService:
    @staticmethod
    async def generate_questions(
        subject: str, 
        class_name: str, 
        chapter: str, 
        topic: str,
        formula: str = "",
        difficulty: str = "Medium",
        question_type: str = "mixed"
    ) -> QuestionGenerationResponse:
        
        # 1. Try to fetch chunks via RAG
        query = f"{topic} in {chapter}"
        chunks = RagService.search_chunks(subject, chapter, query)
        
        context_text = "\n".join([c.get("text", "") for c in chunks])
        
        prompt = f"""You are an educational AI generating high-quality practice questions.
Subject: {subject}
Class: {class_name}
Chapter: {chapter}
Topic: {topic}
Formula: {formula}
Difficulty: {difficulty}
Question Type: {question_type}

Context provided from textbook:
{context_text}

Instructions:
Generate EXACTLY 4 high-quality practice questions based on the provided inputs. Follow these strict priority rules for generating questions:
1. First Priority: Extract or adapt actual questions found in the textbook context above.
2. Second Priority: Generate questions based specifically on calculating or applying the Formula: {formula}. Use numerical values for variables and ask to calculate the unknown.
3. Third Priority: If no formula or context exists, generate conceptual questions about the Topic: {topic}.

Ensure questions are meaningful. Do NOT generate generic placeholders like "What is the main concept?".
Include a mix of MCQ, numerical, conceptual, and application-based questions.
Difficulty should match: {difficulty}. Provide step-by-step solutions in the explanation.

Respond STRICTLY in this JSON format, no markdown blocks:
{{
  "questions": [
    {{
      "question": "string",
      "answer": "string",
      "type": "string (MCQ, numerical, conceptual)",
      "options": ["list", "of", "4 options if MCQ"],
      "explanation": "string with stepwise solution",
      "formula_used": "string",
      "related_concept": "string",
      "difficulty": "{difficulty}"
    }}
  ]
}}
"""
        try:
            llm_text = await generate_llm_text_async(prompt, temperature=0.3, max_output_tokens=3000)
            if llm_text:
                llm_text = re.sub(r"^```json|```$", "", llm_text.strip(), flags=re.MULTILINE).strip()
                # Repair single backslashes in LaTeX commands that violate JSON escaping rules
                llm_text = re.sub(r'\\(?!n|"|u[0-9a-fA-F]{4})', r'\\\\', llm_text)
                data = json.loads(llm_text)
                
                questions = []
                for q in data.get("questions", []):
                    questions.append(QuestionModel(
                        question=q.get("question", ""),
                        answer=q.get("answer", ""),
                        type=q.get("type", "conceptual"),
                        options=q.get("options", None),
                        explanation=q.get("explanation", ""),
                        formula_used=q.get("formula_used", ""),
                        related_concept=q.get("related_concept", ""),
                        difficulty=q.get("difficulty", difficulty)
                    ))
                
                # Ensure we don't return an empty array if possible
                if questions:
                    return QuestionGenerationResponse(questions=questions[:5])
        except Exception as e:
            print(f"Error generating questions via LLM: {e}")
            
        # Return empty list if generation fails. No generic fallbacks allowed.
        return QuestionGenerationResponse(questions=[])
