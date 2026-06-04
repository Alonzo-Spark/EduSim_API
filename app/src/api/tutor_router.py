from fastapi import APIRouter, Query, Depends, Header, BackgroundTasks
from typing import Optional
from sqlalchemy.orm import Session
import uuid

from app.src.config.database import get_db
from app.src.services.persistence_service import record_activity, record_search_history, resolve_user_from_authorization
from app.src.modules.tutor.controller import analyze_tutor_controller, TutorQueryRequest
from app.src.modules.tutor import service as tutor_service
from app.src.models.persistence import ChatHistory
from app.src.modules.legacy_rag.generator import generate_openrouter_text_async
from fastapi.responses import StreamingResponse

tutor_router = APIRouter()


async def generate_learning_summary(explanation: str) -> str:
    prompt = f"""
    Please generate a concise educational learning summary from the following physics explanation.
    The summary must:
    1. Be 2-3 sentences maximum.
    2. Capture the main concept taught.
    3. Include important formulas if present.
    4. Capture key learning outcomes.
    5. Be suitable for revision later.
    6. Respond with ONLY the summary text itself, with no introductory or trailing text.

    Explanation:
    {explanation}
    """
    try:
        # Request a short response (150 tokens) to keep usage minimal
        summary = await generate_openrouter_text_async(
            prompt, 
            temperature=0.3, 
            max_output_tokens=150,
            system_prompt="You are a helpful physics summarizer. Create a 2-3 sentence educational summary of the explanation."
        )
        return summary.strip() if summary else "Summary unavailable."
    except Exception as e:
        print(f"[Summary Generator Error] Failed to generate LLM summary: {e}")
        # Graceful fallback: return a truncated explanation structure
        return explanation[:250].strip() + "..."


@tutor_router.post("/analyze-stream")
async def analyze_query_stream(
    request: TutorQueryRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Analyzes a physics query and streams the response back for ultra-fast first token.
    """
    from app.src.modules.tutor.service import analyze_tutor_query_stream
    from fastapi.responses import StreamingResponse
    from app.src.config.database import SessionLocal
    
    user = resolve_user_from_authorization(authorization, db)
    student_profile = None
    if user:
        from app.src.repositories.student_repository import StudentRepository
        profile_obj = StudentRepository.get_or_create_profile(db, user.id)
        student_profile = {
            "skill_level": profile_obj.skill_level,
            "mastered_topics": profile_obj.mastered_topics,
            "misconceptions": profile_obj.misconceptions
        }
        
    history_dicts = None
    if request.history:
        history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
    return StreamingResponse(
        analyze_tutor_query_stream(
            request.query,
            history=history_dicts,
            subject=request.subject,
            chapter=request.chapter,
            topic=request.topic,
            student_profile=student_profile,
            user_id=user.id if user else None,
            db_session_factory=SessionLocal
        ),
        media_type="text/event-stream"
    )


@tutor_router.post("/analyze")
async def analyze_query(
    request: TutorQueryRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Analyzes a physics query to detect concepts, formulas, and provide AI/RAG explanations.
    """
    user = resolve_user_from_authorization(authorization, db)
    student_profile = None
    if user:
        from app.src.repositories.student_repository import StudentRepository
        profile_obj = StudentRepository.get_or_create_profile(db, user.id)
        student_profile = {
            "skill_level": profile_obj.skill_level,
            "mastered_topics": profile_obj.mastered_topics,
            "misconceptions": profile_obj.misconceptions
        }
        
    response = await analyze_tutor_controller(request, student_profile)
    print("--- DEBUG AUTH ---")
    print(f"Authorization Header: {authorization}")
    print(f"Resolved User: {user.id if user else 'NONE'}")
    print("------------------")
    data = response.get("data", {}) if isinstance(response, dict) else {}
    explanation = data.get("explanation") or data.get("ai_explanation") or ""
    
    if user:
        from app.src.repositories.persistence_repository import PersistenceRepository
        repo = PersistenceRepository(db)
        sessions = repo.list_tutor_sessions(user.id)
        
        session_id = None
        if sessions:
            session_id = uuid.UUID(sessions[0]["id"])
        else:
            session_id = uuid.uuid4()
        
        # 1. Extract the topic
        concepts = data.get("concepts") or []
        topic = concepts[0] if concepts else request.query
        if len(topic) > 100:
            topic = topic[:97] + "..."
            
        if "Error:" in explanation:
            print("[DB SAVE SKIPPED] Tutor generation failed")
            return response
            
        # 2. Generate a concise educational summary
        summary = await generate_learning_summary(explanation)
        
        # 3. Save the summary and explanation into chat_history
        try:
            user_record = ChatHistory(
                user_id=user.id,
                session_id=session_id,
                session_type="tutor",
                role="user",
                topic=topic,
                content=request.query,
                summary=summary,
                metadata_json={
                    "class_name": request.class_name,
                    "subject": request.subject,
                    "chapter": request.chapter,
                    "topic": request.topic
                }
            )
            
            assistant_record = ChatHistory(
                user_id=user.id,
                session_id=session_id,
                session_type="tutor",
                role="assistant",
                topic=topic,
                content=explanation,
                summary=None,
                metadata_json={
                    "class_name": request.class_name,
                    "subject": request.subject,
                    "chapter": request.chapter,
                    "topic": request.topic
                }
            )
            
            print("--- PERSISTENCE LOG ---")
            print(f"user_id: {user.id}")
            print(f"session_id: {session_id}")
            print(f"topic: {topic}")
            print(f"summary length: {len(summary) if summary else 0}")
            
            print("Before db.add()")
            db.add(user_record)
            db.add(assistant_record)
            print("After db.add()")
            
            record_activity(
                db,
                user=user,
                domain="tutor",
                action="analyze",
                entity_type="query",
                entity_id=request.query[:120],
                source="/api/tutor/analyze",
                metadata={"topic": topic},
            )

            print("Before db.commit()")
            db.commit()
            print("After db.commit()")
            
            print("Before db.refresh()")
            db.refresh(user_record)
            db.refresh(assistant_record)
            print("After db.refresh()")
            
            print(f"INSERTED RECORD ID: {user_record.id}")
            print("-----------------------")
            
            if isinstance(response, dict):
                response["success"] = True
                response["message"] = "Learning summary saved successfully"
                
            # Queue profile update in background
            if explanation and "Error:" not in explanation:
                from app.src.config.database import SessionLocal
                from app.src.modules.tutor.service import analyze_and_update_profile_task
                background_tasks.add_task(
                    analyze_and_update_profile_task,
                    SessionLocal,
                    user.id,
                    request.query,
                    explanation
                )
        except Exception as e:
            db.rollback()
            print(f"Exception during save: {repr(e)}")
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to save learning summary."})
    
    print("Tutor request:", request.query)
    if explanation:
        try:
            print("LLM response:", explanation[:200])
        except Exception:
            print("LLM response contains non-ascii characters")
    try:
        print("Tutor API response success:", response.get("success") if isinstance(response, dict) else True)
    except Exception:
        pass
    
    return response


@tutor_router.post("/guide")
async def get_tutor_guide(
    request: TutorQueryRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Analyzes a physics query to construct only the simulation guide/instructions (saving tokens).
    """
    from app.src.modules.tutor.service import generate_tutor_guide
    from fastapi import HTTPException
    
    try:
        response = await generate_tutor_guide(request.query)
        user = resolve_user_from_authorization(authorization, db)
        if user:
            concepts = request.topic or request.query
            if len(concepts) > 100:
                concepts = concepts[:97] + "..."
            
            record_activity(
                db,
                user=user,
                domain="tutor",
                action="guide",
                entity_type="query",
                entity_id=request.query[:120],
                source="/api/tutor/guide",
                metadata={"topic": concepts},
            )
            try:
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"Exception during save guide activity: {repr(e)}")
                
        return {
            "success": True,
            "data": response
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tutor Guide Generation Error: {str(e)}"
        )


@tutor_router.post("/explain-sim")
async def explain_sim(
    request: TutorQueryRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """
    Direct, fast, and RAG-free dynamic LLM explanation for simulation physics events.
    """
    from app.src.modules.tutor.service import explain_simulation_query
    from fastapi import HTTPException
    try:
        history_dicts = None
        if request.history:
            history_dicts = [{"role": msg.role, "content": msg.content} for msg in request.history]
        data = await explain_simulation_query(request.query, history=history_dicts)
        response = {
            "success": True,
            "data": data
        }
        user = resolve_user_from_authorization(authorization, db)
        if user:
            from app.src.repositories.persistence_repository import PersistenceRepository
            repo = PersistenceRepository(db)
            sessions = repo.list_tutor_sessions(user.id)
            
            session_id = None
            if sessions:
                session_id = uuid.UUID(sessions[0]["id"])
            else:
                session_id = uuid.uuid4()
                
            explanation = data.get("explanation") or data.get("ai_explanation") or ""
            
            # 1. Extract topic
            topic = request.query
            if len(topic) > 100:
                topic = topic[:97] + "..."
                
            if "Error:" in explanation:
                print("[DB SAVE SKIPPED] Tutor generation failed")
                return response
                
            # 2. Generate a concise educational summary
            summary = await generate_learning_summary(explanation)
            
            # 3. Save the summary and explanation into chat_history
            try:
                user_record = ChatHistory(
                    user_id=user.id,
                    session_id=session_id,
                    session_type="tutor",
                    role="user",
                    topic=topic,
                    content=request.query,
                    summary=summary,
                    metadata_json={
                        "class_name": request.class_name,
                        "subject": request.subject,
                        "chapter": request.chapter,
                        "topic": request.topic
                    }
                )
                
                assistant_record = ChatHistory(
                    user_id=user.id,
                    session_id=session_id,
                    session_type="tutor",
                    role="assistant",
                    topic=topic,
                    content=explanation,
                    summary=None,
                    metadata_json={
                        "class_name": request.class_name,
                        "subject": request.subject,
                        "chapter": request.chapter,
                        "topic": request.topic
                    }
                )
                
                print("--- PERSISTENCE LOG ---")
                print(f"user_id: {user.id}")
                print(f"session_id: {session_id}")
                print(f"topic: {topic}")
                print(f"summary length: {len(summary) if summary else 0}")
                
                print("Before db.add()")
                db.add(user_record)
                db.add(assistant_record)
                print("After db.add()")
                
                record_activity(
                    db,
                    user=user,
                    domain="tutor",
                    action="explain-sim",
                    entity_type="query",
                    entity_id=request.query[:120],
                    source="/api/tutor/explain-sim",
                )

                print("Before db.commit()")
                db.commit()
                print("After db.commit()")
                
                print("Before db.refresh()")
                db.refresh(user_record)
                db.refresh(assistant_record)
                print("After db.refresh()")
                
                print(f"INSERTED RECORD ID: {user_record.id}")
                print("-----------------------")
                
                if isinstance(response, dict):
                    response["success"] = True
                    response["message"] = "Learning summary saved successfully"
                
            except Exception as e:
                db.rollback()
                print(f"Exception during save: {repr(e)}")
                from fastapi.responses import JSONResponse
                return JSONResponse(status_code=500, content={"success": False, "message": "Failed to save learning summary."})
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Simulation Tutor Explanation Error: {str(e)}"
        )

    from app.src.modules.tutor.service import analyze_tutor_query_stream
    return StreamingResponse(
        analyze_tutor_query_stream(request.query),
        media_type="text/event-stream"
    )


@tutor_router.get("/search")
async def search_curriculum(
    q: str = Query(..., min_length=1),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Search the curriculum and return matching subjects/chapters/topics."""
    results = tutor_service.search_curriculum(q)
    user = resolve_user_from_authorization(authorization, db)
    if user:
        record_search_history(
            db,
            user=user,
            payload={
                "query": q,
                "scope": "curriculum",
                "result_count": len(results),
                "results_json": results,
            },
        )
        try:
            db.commit()
            print("[Database] User setting saved in the database: updated")
            return {"query": q, "results": results, "message": "Settings saved successfully."}
        except Exception as e:
            db.rollback()
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to save settings."})
    return {"query": q, "results": results}


@tutor_router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Return autocomplete suggestions for curriculum topics/chapters."""
    suggestions = tutor_service.autocomplete_curriculum(q)
    user = resolve_user_from_authorization(authorization, db)
    if user:
        record_search_history(
            db,
            user=user,
            payload={
                "query": q,
                "scope": "autocomplete",
                "result_count": len(suggestions),
                "results_json": suggestions,
            },
        )
        try:
            db.commit()
            print("[Database] User setting saved in the database: updated")
            return {"query": q, "results": suggestions, "suggestions": suggestions, "message": "Settings saved successfully."}
        except Exception as e:
            db.rollback()
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to save settings."})
    return {"query": q, "results": suggestions, "suggestions": suggestions}


@tutor_router.get("/topic")
async def get_topic(
    subject: str,
    class_name: str,
    chapter: str,
    topic: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Load stored curriculum content for the selected topic/chapter."""
    content = tutor_service.get_topic_content(subject, class_name, chapter, topic)
    user = resolve_user_from_authorization(authorization, db)
    if user:
        record_activity(
            db,
            user=user,
            domain="curriculum",
            action="open-topic",
            entity_type="topic",
            entity_id=f"{subject}:{class_name}:{chapter}:{topic or ''}",
            source="/api/tutor/topic",
            metadata={"subject": subject, "class_name": class_name, "chapter": chapter, "topic": topic},
        )
        try:
            db.commit()
            print("[Database] Activity logs saved in the database: updated")
            if isinstance(content, dict):
                content["message"] = "Settings saved successfully."
        except Exception as e:
            db.rollback()
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=500, content={"success": False, "message": "Failed to save settings."})
    return content
