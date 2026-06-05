from __future__ import annotations

from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, select

from app.src.models.persistence import (
    Subject,
    Chapter,
    Topic,
    ChatHistory,
    FormulaHistory,
    SimulationHistory,
    UserSetting,
    UserSession,
)
from app.src.models.user import User


class PersistenceRepository:
    def __init__(self, db: Session):
        self.db = db

    # Helper to get/set setting values
    def _get_setting(self, user_id: Any, key: str, default: Any = None) -> Any:
        setting = (
            self.db.query(UserSetting)
            .filter(UserSetting.user_id == user_id, UserSetting.setting_key == key)
            .first()
        )
        return setting.setting_value if setting else default

    def _set_setting(self, user_id: Any, key: str, value: Any) -> None:
        # Check session local objects (both pending and persistent)
        for obj in self.db.new:
            if isinstance(obj, UserSetting) and obj.user_id == user_id and obj.setting_key == key:
                obj.setting_value = value
                return
        for obj in self.db.identity_map.values():
            if isinstance(obj, UserSetting) and obj.user_id == user_id and obj.setting_key == key:
                obj.setting_value = value
                return

        setting = (
            self.db.query(UserSetting)
            .filter(UserSetting.user_id == user_id, UserSetting.setting_key == key)
            .first()
        )
        if setting:
            setting.setting_value = value
        else:
            setting = UserSetting(user_id=user_id, setting_key=key, setting_value=value)
            self.db.add(setting)

    # --- User State ---
    def get_user_state(self, user_id) -> Optional[dict[str, Any]]:
        return self._get_setting(user_id, "user_state")

    def upsert_user_state(self, user_id, payload: dict[str, Any]) -> dict[str, Any]:
        state = self.get_user_state(user_id) or {}
        state.update(payload)
        self._set_setting(user_id, "user_state", state)
        return state

    # --- Dashboard State ---
    def get_dashboard_state(self, user_id) -> Optional[dict[str, Any]]:
        return self._get_setting(user_id, "dashboard_state")

    # --- Curriculum Progress ---
    def list_curriculum_progress(self, user_id):
        return self._get_setting(user_id, "curriculum_progress", [])

    def list_curriculum_visits(self, user_id):
        return self._get_setting(user_id, "curriculum_visits", [])

    # --- Tutor Sessions & Messages ---
    def list_tutor_sessions(self, user_id):
        # Retrieve unique session_ids for user with type tutor
        subquery = (
            select(ChatHistory.session_id)
            .filter(ChatHistory.user_id == user_id, ChatHistory.session_type == "tutor")
            .group_by(ChatHistory.session_id)
        )
        
        # Get the first message of each session to extract metadata
        first_messages = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.session_id.in_(subquery))
            .order_by(ChatHistory.created_at.asc())
            .all()
        )
        
        # Deduplicate and build session dictionary
        sessions_map = {}
        for msg in first_messages:
            sid = str(msg.session_id)
            if sid not in sessions_map:
                meta = msg.metadata_json or {}
                sessions_map[sid] = {
                    "id": sid,
                    "user_id": str(msg.user_id),
                    "topic": msg.topic or meta.get("topic") or "General Physics",
                    "subject": meta.get("subject"),
                    "class_name": meta.get("class_name"),
                    "chapter": meta.get("chapter"),
                    "query_type": meta.get("query_type"),
                    "source_query": meta.get("source_query", msg.content),
                    "explanation": meta.get("explanation"),
                    "rag_content_json": meta.get("rag_content_json"),
                    "formulas_json": meta.get("formulas_json"),
                    "metadata_json": meta,
                    "created_at": msg.created_at.isoformat() if hasattr(msg.created_at, "isoformat") else str(msg.created_at),
                    "updated_at": msg.updated_at.isoformat() if hasattr(msg.updated_at, "isoformat") else str(msg.updated_at),
                    "is_active": meta.get("is_active", True),
                    "deleted_at": None,
                }
        return list(sessions_map.values())

    def get_tutor_messages(self, conversation_id):
        messages = (
            self.db.query(ChatHistory)
            .filter(ChatHistory.session_id == conversation_id)
            .order_by(ChatHistory.created_at.asc())
            .all()
        )
        return [
            {
                "id": str(msg.id),
                "conversation_id": str(msg.session_id),
                "user_id": str(msg.user_id),
                "role": msg.role,
                "content": msg.content,
                "message_type": (msg.metadata_json or {}).get("message_type") if msg.metadata_json else None,
                "metadata_json": msg.metadata_json,
                "created_at": msg.created_at.isoformat() if hasattr(msg.created_at, "isoformat") else str(msg.created_at),
                "updated_at": msg.updated_at.isoformat() if hasattr(msg.updated_at, "isoformat") else str(msg.updated_at),
            }
            for msg in messages
        ]

    # --- Formula Sessions & Calculations ---
    def list_formula_sessions(self, user_id):
        # We can store formula session metadata in user_settings under "formula_sessions"
        return self._get_setting(user_id, "formula_sessions", [])

    def list_formula_calculations(self, session_id):
        # Retrieve all calculations for a session from formula_history table
        calcs = (
            self.db.query(FormulaHistory)
            .filter(FormulaHistory.session_id == session_id)
            .order_by(FormulaHistory.created_at.desc())
            .all()
        )
        return [
            {
                "id": str(calc.id),
                "session_id": str(calc.session_id),
                "user_id": str(calc.user_id),
                "formula_id": calc.formula_id,
                "input_json": calc.input_json,
                "output_json": calc.output_json,
                "calculation_steps_json": calc.calculation_steps_json,
                "graph_json": calc.graph_json,
                "created_at": calc.created_at.isoformat() if hasattr(calc.created_at, "isoformat") else str(calc.created_at),
            }
            for calc in calcs
        ]

    def list_formula_actions(self, session_id):
        # Stored in user_settings under "formula_actions" key
        actions = self.db.query(UserSetting).filter(UserSetting.setting_key == f"formula_actions_{session_id}").first()
        return actions.setting_value if actions else []

    def list_formula_attempts(self, session_id):
        # Stored in user_settings under "formula_attempts" key
        attempts = self.db.query(UserSetting).filter(UserSetting.setting_key == f"formula_attempts_{session_id}").first()
        return attempts.setting_value if attempts else []

    # --- Sandbox/Simulation Sessions & Events ---
    def list_sandbox_sessions(self, user_id):
        # Query simulation_history table
        sims = (
            self.db.query(SimulationHistory)
            .filter(SimulationHistory.user_id == user_id, SimulationHistory.deleted_at.is_(None))
            .order_by(SimulationHistory.updated_at.desc())
            .all()
        )
        return [
            {
                "id": str(sim.id),
                "user_id": str(sim.user_id),
                "simulation_id": sim.simulation_id,
                "prompt": sim.prompt,
                "title": sim.title,
                "description": sim.description,
                "dsl_json": sim.dsl_json,
                "runtime_json": sim.runtime_json,
                "snapshot_json": sim.snapshot_json,
                "ui_state_json": sim.ui_state_json,
                "score": sim.score,
                "is_active": sim.is_active,
                "created_at": sim.created_at.isoformat() if hasattr(sim.created_at, "isoformat") else str(sim.created_at),
                "updated_at": sim.updated_at.isoformat() if hasattr(sim.updated_at, "isoformat") else str(sim.updated_at),
            }
            for sim in sims
        ]

    def list_sandbox_events(self, simulation_row_id):
        # Events stored in user_settings under key "sandbox_events_{simulation_row_id}"
        events = self.db.query(UserSetting).filter(UserSetting.setting_key == f"sandbox_events_{simulation_row_id}").first()
        return events.setting_value if events else []

    # --- Search History ---
    def list_search_history(self, user_id):
        return self._get_setting(user_id, "search_history", [])

    # --- Activity Logs ---
    def list_activity_logs(self, user_id):
        return self._get_setting(user_id, "activity_logs", [])

    # --- Core Settings, Profiles, Sessions ---
    def list_user_settings(self, user_id):
        return self.db.query(UserSetting).filter(UserSetting.user_id == user_id).all()

    def list_user_roles(self, user_id):
        # Since roles table is removed, query the user's role field directly
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            return [{"role": {"name": user.role, "description": f"Role {user.role}"}, "is_primary": True}]
        return []

    def list_profiles(self, user_id):
        profile = self._get_setting(user_id, "user_profile")
        return [profile] if profile else []

    def list_sessions(self, user_id):
        return self.db.query(UserSession).filter(UserSession.user_id == user_id).all()

    def list_refresh_tokens(self, user_id):
        # We can store refresh tokens in user_settings if needed, or query user_sessions
        sessions = self.db.query(UserSession).filter(UserSession.user_id == user_id).all()
        return [
            {
                "id": str(s.id),
                "user_id": str(s.user_id),
                "token_jti": s.session_key,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
                "device_info": s.device_info,
                "user_agent": s.user_agent,
                "ip_address": s.ip_address,
                "metadata_json": s.metadata_json,
                "created_at": s.created_at.isoformat() if hasattr(s.created_at, "isoformat") else str(s.created_at),
            }
            for s in sessions
        ]

    def list_roles(self):
        return [{"name": "student", "is_active": True}, {"name": "teacher", "is_active": True}]
