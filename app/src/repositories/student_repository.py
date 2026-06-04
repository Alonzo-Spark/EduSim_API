from sqlalchemy.orm import Session
from app.src.models.persistence import StudentProfile
import uuid

class StudentRepository:
    @staticmethod
    def get_or_create_profile(db: Session, user_id: uuid.UUID) -> StudentProfile:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
        if not profile:
            profile = StudentProfile(
                user_id=user_id,
                skill_level="beginner",
                mastered_topics=[],
                misconceptions=[]
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def update_profile(
        db: Session,
        user_id: uuid.UUID,
        skill_level: str | None = None,
        mastered_topics: list | None = None,
        misconceptions: list | None = None
    ) -> StudentProfile:
        profile = StudentRepository.get_or_create_profile(db, user_id)
        if skill_level is not None:
            profile.skill_level = skill_level
        if mastered_topics is not None:
            profile.mastered_topics = mastered_topics
        if misconceptions is not None:
            profile.misconceptions = misconceptions
        db.commit()
        db.refresh(profile)
        return profile
