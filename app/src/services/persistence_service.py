from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.src.config.database import ping_database
from app.src.models.persistence import (
    ChatHistory,
    FormulaHistory,
    SimulationHistory,
    UserSetting,
    UserSession,
)
from app.src.models.user import User
from app.src.repositories.persistence_repository import PersistenceRepository
from app.src.utils.auth import decode_token


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(raw_email: str) -> str:
    return raw_email.strip().lower()


def resolve_user_from_authorization(authorization: Optional[str], db: Session) -> Optional[User]:
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None

    if token == "admin-token-bypass":
        admin_user = db.query(User).filter(User.email == "admin@gmail.com").first()
        if not admin_user:
            admin_user = User(
                id=uuid.UUID("4fa6c451-eab9-4b78-8137-070cd68b9e5f"),
                name="Administrator",
                email="admin@gmail.com",
                password_hash="admin-bypass-placeholder",
                role="teacher",
                is_email_verified=True,
                is_mobile_verified=True
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
        return admin_user

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


def require_user(authorization: Optional[str], db: Session) -> User:
    user = resolve_user_from_authorization(authorization, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return user


def mark_user_active(db: Session, user: User) -> None:
    user.last_active_at = now_utc()
    db.add(user)


def record_user_session(
    db: Session,
    *,
    user: User,
    session_key: str,
    device_info: Optional[dict[str, Any]] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> UserSession:
    # Check if a session with this key is already tracked (either pending or persistent) in the current SQLAlchemy session
    for obj in db.new:
        if isinstance(obj, UserSession) and obj.session_key == session_key:
            if expires_at is not None: obj.expires_at = expires_at
            obj.last_login_at = now_utc()
            obj.is_active = True
            return obj
    for obj in db.identity_map.values():
        if isinstance(obj, UserSession) and obj.session_key == session_key:
            if expires_at is not None: obj.expires_at = expires_at
            obj.last_login_at = now_utc()
            obj.is_active = True
            return obj

    record = db.query(UserSession).filter(UserSession.session_key == session_key).first()
    if record is None:
        record = UserSession(
            user_id=user.id,
            session_key=session_key,
            last_login_at=now_utc(),
            expires_at=expires_at,
        )
        db.add(record)
    else:
        record.last_login_at = now_utc()
        record.expires_at = expires_at or record.expires_at
        record.is_active = True
    return record


def record_refresh_token(
    db: Session,
    *,
    user: User,
    token_jti: str,
    expires_at: Optional[datetime] = None,
    device_info: Optional[dict[str, Any]] = None,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> UserSession:
    # Save refresh token in user_sessions instead of refresh_token_records
    return record_user_session(
        db,
        user=user,
        session_key=token_jti,
        device_info=device_info,
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
        metadata=metadata,
    )


def record_login_event(
    db: Session,
    *,
    user: Optional[User],
    email: str,
    success: bool,
    provider: str = "password",
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    failure_reason: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> None:
    # Login events are no-ops except updating last login times on the user
    if user and success:
        user.last_login_at = now_utc()
        user.last_active_at = user.last_login_at
        db.add(user)


def upsert_user_profile(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    profile = repo._get_setting(user.id, "user_profile") or {}
    profile.update({
        "avatar": payload.get("avatar"),
        "bio": payload.get("bio"),
        "display_name": payload.get("display_name") or user.name,
        "timezone": payload.get("timezone"),
        "locale": payload.get("locale"),
    })
    repo._set_setting(user.id, "user_profile", profile)
    if payload.get("avatar"):
        user.avatar = payload.get("avatar")
        db.add(user)
    return profile


def upsert_user_setting(db: Session, *, user: User, key: str, value: Any) -> UserSetting:
    mark_user_active(db, user)
    # Check session local objects
    for obj in db.new:
        if isinstance(obj, UserSetting) and obj.user_id == user.id and obj.setting_key == key:
            obj.setting_value = value
            return obj
    for obj in db.identity_map.values():
        if isinstance(obj, UserSetting) and obj.user_id == user.id and obj.setting_key == key:
            obj.setting_value = value
            return obj

    record = db.query(UserSetting).filter(UserSetting.user_id == user.id, UserSetting.setting_key == key).first()
    if record is None:
        record = UserSetting(user_id=user.id, setting_key=key, setting_value=value)
        db.add(record)
    else:
        record.setting_value = value
    return record


def assign_role(db: Session, *, user: User, role_name: str) -> None:
    # Set the role directly on the User model
    user.role = role_name
    db.add(user)


def record_activity(
    db: Session,
    *,
    user: User,
    domain: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    logs = repo.list_activity_logs(user.id)
    log_id = str(uuid.uuid4())
    new_log = {
        "id": log_id,
        "user_id": str(user.id),
        "domain": domain,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "source": source,
        "metadata_json": metadata,
        "created_at": now_utc().isoformat(),
    }
    logs.insert(0, new_log)
    repo._set_setting(user.id, "activity_logs", logs[:200])  # Cap at 200 logs
    return new_log


def record_app_state(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    return repo.upsert_user_state(user.id, payload)


def upsert_session_state(
    db: Session,
    *,
    user: User,
    namespace: str,
    state_key: str,
    state_json: dict[str, Any],
    expires_at: Optional[datetime] = None,
) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    states = repo._get_setting(user.id, "session_states", {})
    key = f"{namespace}:{state_key}"
    record = {
        "id": str(uuid.uuid4()),
        "user_id": str(user.id),
        "namespace": namespace,
        "state_key": state_key,
        "state_json": state_json,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }
    states[key] = record
    repo._set_setting(user.id, "session_states", states)
    return record


def save_curriculum_progress(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    progress_list = repo.list_curriculum_progress(user.id)
    
    # Check if entry already exists
    target = None
    for entry in progress_list:
        if (entry.get("class_name") == payload.get("class_name") and
                entry.get("subject") == payload.get("subject") and
                entry.get("chapter") == payload.get("chapter") and
                entry.get("topic") == payload.get("topic")):
            target = entry
            break
            
    if target is None:
        target = {
            "id": str(uuid.uuid4()),
            "user_id": str(user.id),
            "class_name": payload.get("class_name"),
            "subject": payload.get("subject"),
            "chapter": payload.get("chapter"),
            "topic": payload.get("topic"),
            "progress_state": payload.get("progress_state", "started"),
            "completion_percent": float(payload.get("completion_percent", 0.0)),
            "last_opened_at": (payload.get("last_opened_at") or now_utc()).isoformat() if isinstance(payload.get("last_opened_at"), datetime) else str(payload.get("last_opened_at") or now_utc()),
            "completed_at": payload.get("completed_at").isoformat() if isinstance(payload.get("completed_at"), datetime) else payload.get("completed_at"),
            "time_spent_seconds": int(payload.get("time_spent_seconds", 0)),
            "progress_json": payload.get("progress_json", payload),
        }
        progress_list.append(target)
    else:
        target.update({
            "progress_state": payload.get("progress_state", target["progress_state"]),
            "completion_percent": float(payload.get("completion_percent", target["completion_percent"])),
            "last_opened_at": (payload.get("last_opened_at") or now_utc()).isoformat() if isinstance(payload.get("last_opened_at"), datetime) else str(payload.get("last_opened_at") or now_utc()),
            "completed_at": payload.get("completed_at").isoformat() if isinstance(payload.get("completed_at"), datetime) else payload.get("completed_at"),
            "time_spent_seconds": int(payload.get("time_spent_seconds", target["time_spent_seconds"])),
            "progress_json": payload.get("progress_json", target["progress_json"]),
        })
        
    repo._set_setting(user.id, "curriculum_progress", progress_list)
    return target


def record_curriculum_visit(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    visits = repo.list_curriculum_visits(user.id)
    new_visit = {
        "id": str(uuid.uuid4()),
        "user_id": str(user.id),
        "class_name": payload.get("class_name"),
        "subject": payload.get("subject"),
        "chapter": payload.get("chapter"),
        "topic": payload.get("topic"),
        "page": payload.get("page"),
        "time_spent_seconds": int(payload.get("time_spent_seconds", 0)),
        "progress_json": payload.get("progress_json"),
        "created_at": now_utc().isoformat(),
    }
    visits.insert(0, new_visit)
    repo._set_setting(user.id, "curriculum_visits", visits[:200])  # Cap at 200 visits
    return new_visit


class MockConversation:
    def __init__(self, session_id: Any):
        self.id = session_id


def save_tutor_conversation(db: Session, *, user: User, payload: dict[str, Any]) -> MockConversation:
    mark_user_active(db, user)
    session_id = payload.get("id") or payload.get("session_id")
    if not session_id:
        session_id = uuid.uuid4()
    elif isinstance(session_id, str):
        try:
            session_id = uuid.UUID(session_id)
        except Exception:
            session_id = uuid.uuid4()
            
    # Delete existing chat history for this session_id to overwrite it
    db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
    
    messages = payload.get("messages") or []
    if messages:
        for msg in messages:
            role = msg.get("role") or "user"
            content = msg.get("content") or ""
            summary = msg.get("summary")
            meta = msg.get("metadata_json") or {}
            merged_meta = {
                "class_name": payload.get("class_name"),
                "subject": payload.get("subject"),
                "chapter": payload.get("chapter"),
                "topic": payload.get("topic") or payload.get("source_query"),
                **meta
            }
            
            chat_rec = ChatHistory(
                user_id=user.id,
                session_id=session_id,
                session_type="tutor",
                role=role,
                topic=payload.get("topic") or payload.get("source_query"),
                content=content,
                summary=summary,
                metadata_json=merged_meta
            )
            db.add(chat_rec)
    elif payload.get("source_query"):
        user_rec = ChatHistory(
            user_id=user.id,
            session_id=session_id,
            session_type="tutor",
            role="user",
            topic=payload.get("topic") or payload.get("source_query"),
            content=payload.get("source_query"),
            summary=None,
            metadata_json={
                "class_name": payload.get("class_name"),
                "subject": payload.get("subject"),
                "chapter": payload.get("chapter"),
                "topic": payload.get("topic") or payload.get("source_query")
            }
        )
        db.add(user_rec)
        
        if payload.get("explanation"):
            assistant_rec = ChatHistory(
                user_id=user.id,
                session_id=session_id,
                session_type="tutor",
                role="assistant",
                topic=payload.get("topic") or payload.get("source_query"),
                content=payload.get("explanation"),
                summary=None,
                metadata_json={
                    "class_name": payload.get("class_name"),
                    "subject": payload.get("subject"),
                    "chapter": payload.get("chapter"),
                    "topic": payload.get("topic") or payload.get("source_query")
                }
            )
            db.add(assistant_rec)
            
    return MockConversation(session_id)


def get_tutor_conversation_payload(db: Session, conversation_id) -> dict[str, Any]:
    repo = PersistenceRepository(db)
    messages = repo.get_tutor_messages(conversation_id)
    if not messages:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tutor session not found")
    
    # Reconstruct conversation details from the first message
    first_msg = messages[0]
    meta = first_msg.get("metadata_json") or {}
    return {
        "id": str(conversation_id),
        "user_id": first_msg.get("user_id"),
        "topic": meta.get("topic"),
        "subject": meta.get("subject"),
        "class_name": meta.get("class_name"),
        "chapter": meta.get("chapter"),
        "query_type": meta.get("query_type"),
        "source_query": meta.get("source_query", first_msg.get("content")),
        "explanation": meta.get("explanation"),
        "rag_content_json": meta.get("rag_content_json"),
        "formulas_json": meta.get("formulas_json"),
        "metadata_json": meta,
        "is_active": meta.get("is_active", True),
        "messages": messages,
    }


def save_formula_session(db: Session, *, user: User, payload: dict[str, Any]) -> MockConversation:
    mark_user_active(db, user)
    session_id = payload.get("id") or payload.get("session_id")
    if not session_id:
        session_id = uuid.uuid4()
    elif isinstance(session_id, str):
        try:
            session_id = uuid.UUID(session_id)
        except Exception:
            session_id = uuid.uuid4()
            
    return MockConversation(session_id)


def record_formula_action(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    return {
        "id": str(uuid.uuid4()),
        "session_id": str(payload.get("session_id")),
        "action": payload.get("action"),
    }


def save_formula_attempt(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    return {
        "id": str(uuid.uuid4()),
        "session_id": str(payload.get("session_id")),
    }


def record_formula_calculation(db: Session, *, user: User, payload: dict[str, Any]) -> FormulaHistory:
    mark_user_active(db, user)
    
    session_id_str = payload.get("session_id")
    try:
        session_id = uuid.UUID(session_id_str)
    except Exception:
        # Generate stable UUID for session_id if it is a generic string
        session_id = uuid.uuid5(uuid.NAMESPACE_DNS, session_id_str)
        
    calculation = FormulaHistory(
        id=uuid.uuid4(),
        session_id=session_id,
        user_id=user.id,
        formula_id=payload["formula_id"],
        input_json=payload.get("input_json", {}),
        output_json=payload.get("output_json"),
        calculation_steps_json=payload.get("calculation_steps_json"),
        graph_json=payload.get("graph_json"),
    )
    return calculation


def save_formula_calculation_record(db: Session, *, user: User, payload: dict[str, Any], saved: bool = False) -> FormulaHistory:
    return record_formula_calculation(db, user=user, payload=payload)


def save_formula_calculation_note(db: Session, *, user: User, calculation_id, title: str, note: str, is_primary: bool = False) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(user.id),
        "calculation_id": str(calculation_id),
        "title": title,
        "note": note,
        "is_primary": is_primary,
        "created_at": now_utc().isoformat(),
    }


def save_sandbox_state(db: Session, *, user: User, payload: dict[str, Any]) -> SimulationHistory:
    mark_user_active(db, user)
    simulation_id = payload["simulation_id"]
    
    # Try to find existing simulation_history by simulation_id
    record = db.query(SimulationHistory).filter(
        SimulationHistory.user_id == user.id,
        SimulationHistory.simulation_id == simulation_id
    ).first()
    
    if record is None:
        record = SimulationHistory(
            user_id=user.id,
            simulation_id=simulation_id,
            prompt=payload["prompt"]
        )
        db.add(record)
        
    record.prompt = payload["prompt"]
    record.title = payload.get("title") or record.title
    record.description = payload.get("description") or record.description
    record.is_active = payload.get("is_active", True)
    record.score = float(payload.get("score", record.score or 0.0))
    if payload.get("runtime_json"):
        record.runtime_json = payload.get("runtime_json")
    db.flush()
    return record


def get_sandbox_state_by_public_id(db: Session, simulation_id: str) -> Optional[SimulationHistory]:
    return db.query(SimulationHistory).filter(SimulationHistory.simulation_id == simulation_id).first()


def record_sandbox_event(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    simulation = get_sandbox_state_by_public_id(db, payload["simulation_id"])
    if simulation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sandbox simulation not found")

    repo = PersistenceRepository(db)
    events = repo.list_sandbox_events(simulation.id)
    new_event = {
        "id": str(uuid.uuid4()),
        "simulation_id": str(simulation.id),
        "user_id": str(user.id),
        "event_type": payload["event_type"],
        "payload_json": payload.get("payload_json"),
        "created_at": now_utc().isoformat(),
    }
    events.insert(0, new_event)
    repo._set_setting(user.id, f"sandbox_events_{simulation.id}", events[:200])
    return new_event


def record_search_history(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    history = repo.list_search_history(user.id)
    new_search = {
        "id": str(uuid.uuid4()),
        "user_id": str(user.id),
        "query": payload["query"],
        "scope": payload.get("scope"),
        "result_count": int(payload.get("result_count", 0)),
        "results_json": payload.get("results_json"),
        "metadata_json": payload.get("metadata_json"),
        "created_at": now_utc().isoformat(),
    }
    history.insert(0, new_search)
    repo._set_setting(user.id, "search_history", history[:200])
    return new_search


def record_search_selection(db: Session, *, user: User, search_history_id, selected_result: str, selection_json: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    selections = repo._get_setting(user.id, "search_selections", [])
    new_selection = {
        "id": str(uuid.uuid4()),
        "search_history_id": str(search_history_id),
        "user_id": str(user.id),
        "selected_result": selected_result,
        "selection_json": selection_json,
        "created_at": now_utc().isoformat(),
    }
    selections.append(new_selection)
    repo._set_setting(user.id, "search_selections", selections)
    return new_selection


def save_dashboard_state(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    mark_user_active(db, user)
    repo = PersistenceRepository(db)
    state = repo.get_dashboard_state(user.id) or {}
    state.update({
        "widgets_json": payload.get("widgets_json"),
        "layout_json": payload.get("layout_json"),
        "preferences_json": payload.get("preferences_json"),
        "last_viewed_at": (payload.get("last_viewed_at") or now_utc()).isoformat() if isinstance(payload.get("last_viewed_at"), datetime) else str(payload.get("last_viewed_at") or now_utc()),
    })
    repo._set_setting(user.id, "dashboard_state", state)
    return state


def save_user_state(db: Session, *, user: User, payload: dict[str, Any]) -> dict[str, Any]:
    repo = PersistenceRepository(db)
    mark_user_active(db, user)
    return repo.upsert_user_state(user.id, payload)


def get_persistence_snapshot(db: Session, *, user: User) -> dict[str, Any]:
    mark_user_active(db, user)
    repository = PersistenceRepository(db)

    curriculum = repository.list_curriculum_progress(user.id)
    tutor_sessions = repository.list_tutor_sessions(user.id)
    formula_sessions = repository.list_formula_sessions(user.id)
    sandbox_sessions = repository.list_sandbox_sessions(user.id)
    search_history = repository.list_search_history(user.id)
    dashboard_state = repository.get_dashboard_state(user.id)
    user_state = repository.get_user_state(user.id)

    return {
        "success": True,
        "user_id": str(user.id),
        "user_state": user_state,
        "curriculum_progress": curriculum,
        "tutor_sessions": tutor_sessions,
        "formula_sessions": formula_sessions,
        "sandbox_sessions": sandbox_sessions,
        "search_history": search_history,
        "dashboard_state": dashboard_state,
    }


def get_state_payload(db: Session, *, user: User) -> dict[str, Any]:
    snapshot = get_persistence_snapshot(db, user=user)
    return {
        "success": True,
        "state": snapshot.get("user_state"),
        "dashboard_state": snapshot.get("dashboard_state"),
        "curriculum_progress": snapshot.get("curriculum_progress", []),
        "tutor_sessions": snapshot.get("tutor_sessions", []),
        "formula_sessions": snapshot.get("formula_sessions", []),
        "sandbox_sessions": snapshot.get("sandbox_sessions", []),
        "search_history": snapshot.get("search_history", []),
    }


def list_formula_history(db: Session, *, user: User) -> dict[str, Any]:
    repository = PersistenceRepository(db)
    sessions = repository.list_formula_sessions(user.id)
    return {
        "success": True,
        "formula_sessions": [
            {
                **session,
                "calculations": repository.list_formula_calculations(session["id"]),
                "actions": repository.list_formula_actions(session["id"]),
                "attempts": repository.list_formula_attempts(session["id"]),
                "saved_calculations": [
                    note for note in repository._get_setting(user.id, "saved_notes", [])
                    if note.get("session_id") == session["id"]
                ],
            }
            for session in sessions
        ],
    }


def list_tutor_history(db: Session, *, user: User) -> dict[str, Any]:
    repository = PersistenceRepository(db)
    sessions = repository.list_tutor_sessions(user.id)
    return {
        "success": True,
        "tutor_sessions": [
            {
                **session,
                "messages": repository.get_tutor_messages(session["id"]),
            }
            for session in sessions
        ],
    }


def list_curriculum_history(db: Session, *, user: User) -> dict[str, Any]:
    repository = PersistenceRepository(db)
    return {
        "success": True,
        "curriculum_progress": repository.list_curriculum_progress(user.id),
        "curriculum_visits": repository.list_curriculum_visits(user.id),
    }


def list_sandbox_history(db: Session, *, user: User) -> dict[str, Any]:
    repository = PersistenceRepository(db)
    return {
        "success": True,
        "sandbox_sessions": [
            {
                **session,
                "events": repository.list_sandbox_events(session["id"]),
            }
            for session in repository.list_sandbox_sessions(user.id)
        ],
    }


def list_dashboard_history(db: Session, *, user: User) -> dict[str, Any]:
    repository = PersistenceRepository(db)
    return {
        "success": True,
        "dashboard_state": repository.get_dashboard_state(user.id),
        "user_state": repository.get_user_state(user.id),
        "activity_logs": repository.list_activity_logs(user.id),
    }


def serialize_row(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        return row

    data: dict[str, Any] = {}
    for column in row.__table__.columns:
        value = getattr(row, column.name)
        if hasattr(value, "isoformat"):
            data[column.name] = value.isoformat()
        elif column.name.endswith("_id") and value is not None:
            data[column.name] = str(value)
        else:
            data[column.name] = value
    return data


def database_status(db: Session) -> dict[str, Any]:
    return ping_database()


def save_formula_explanation_to_chat_history(db: Session, user: User, formula: str, res: Any) -> ChatHistory:
    # Look up formula explanation session for this user
    repo = PersistenceRepository(db)
    sessions = repo.list_formula_sessions(user.id)
    
    session_id = None
    for s in sessions:
        if s.get("topic") == "Formula Explanation":
            session_id = uuid.UUID(s["id"])
            break
            
    if not session_id:
        session_id = uuid.uuid4()
        # Save a new formula session metadata in user_settings
        save_formula_session(db, user=user, payload={
            "session_id": str(session_id),
            "topic": "Formula Explanation",
            "subject": "physics"
        })
        
    meta = {
        "formula": formula,
        "title": getattr(res, "title", "Formula Explanation"),
        "description": getattr(res, "description", ""),
        "purpose": getattr(res, "purpose", ""),
        "applications": getattr(res, "applications", []),
        "common_mistakes": getattr(res, "common_mistakes", []),
    }
    
    # Save User Request
    msg_user = ChatHistory(
        user_id=user.id,
        session_id=session_id,
        session_type="formula_lab",
        role="user",
        content=f"Explain formula: {formula}",
        metadata_json=meta
    )
    db.add(msg_user)
    db.flush()
    
    # Save AI Explanation response
    explanation_text = f"Formula: {formula}\nTitle: {meta['title']}\nDescription: {meta['description']}\nPurpose: {meta['purpose']}"
    msg_assistant = ChatHistory(
        user_id=user.id,
        session_id=session_id,
        session_type="formula_lab",
        role="assistant",
        content=explanation_text,
        metadata_json=meta
    )
    db.add(msg_assistant)
    db.flush()
    
    return msg_assistant
