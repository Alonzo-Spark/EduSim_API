import json
import re
from typing import List, Optional
from models.question_models import QuestionGenerationResponse, QuestionModel
from services.rag_service import RagService
from app.src.modules.legacy_rag.generator import generate_llm_text_async

class QuestionService:
    @staticmethod
    async def generate_questions(
        subject: str, 
        class_name: str, 
        chapter: str, 
        topic: str
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

Context provided from textbook:
{context_text}

Instructions:
Generate exactly 4 important educational questions about this topic, along with their answers. Include a mix of conceptual, definition, and application questions. 
If the context is empty, rely on your general knowledge to generate accurate questions for this subject.

Respond STRICTLY in this JSON format, no markdown blocks:
{{
  "questions": [
    {{
      "question": "string",
      "answer": "string"
    }}
  ]
}}
"""
        try:
            llm_text = await generate_llm_text_async(prompt, temperature=0.3, max_output_tokens=1000)
            if llm_text:
                llm_text = re.sub(r"^```json|```$", "", llm_text.strip(), flags=re.MULTILINE).strip()
                data = json.loads(llm_text)
                
                questions = []
                for q in data.get("questions", []):
                    questions.append(QuestionModel(
                        question=q.get("question", ""),
                        answer=q.get("answer", "")
                    ))
                
                # Ensure we don't return an empty array if possible
                if questions:
                    return QuestionGenerationResponse(questions=questions[:5])
        except Exception as e:
            print(f"Error generating questions via LLM: {e}")
            
        # Fallback if RAG + LLM fails entirely
        fallback = [
            QuestionModel(question=f"What is the main concept of {topic}?", answer="This is a placeholder answer due to generation failure."),
            QuestionModel(question="Provide an example of this concept.", answer="Example could not be retrieved."),
            QuestionModel(question="Why is this topic important?", answer="Importance is context dependent.")
        ]
        return QuestionGenerationResponse(questions=fallback)
