from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.curriculum import Class, Subject, Chapter, Topic, Subtopic

async def get_all_classes(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Class).order_by(Class.display_order))
    classes = result.scalars().all()
    return [{"id": c.id, "name": c.name, "display_order": c.display_order} for c in classes]

async def get_subjects(class_id: int, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Subject).where(Subject.class_id == class_id).order_by(Subject.id)
    )
    subjects = result.scalars().all()
    return [{"id": s.id, "name": s.name, "icon": s.icon, "description": s.description} for s in subjects]

async def get_chapters(subject_id: int, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Chapter).where(Chapter.subject_id == subject_id).order_by(Chapter.order_index)
    )
    chapters = result.scalars().all()
    return [{"id": c.id, "name": c.name, "order_index": c.order_index} for c in chapters]

async def get_topics(chapter_id: int, db: AsyncSession) -> list[dict]:
    result = await db.execute(
        select(Topic).where(Topic.chapter_id == chapter_id)
    )
    topics = result.scalars().all()
    return [
        {
            "id": t.id, "name": t.name, "slug": t.slug,
            "has_simulation": t.has_simulation,
            "simulation_type": t.simulation_type
        }
        for t in topics
    ]

async def get_topic_by_slug(slug: str, db: AsyncSession) -> Topic | None:
    result = await db.execute(select(Topic).where(Topic.slug == slug))
    return result.scalar_one_or_none()

async def get_topic_full_context(topic_id: int, db: AsyncSession) -> dict:
    """Returns full hierarchy for a topic: class > subject > chapter > topic."""
    topic = await db.get(Topic, topic_id)
    if not topic:
        return {}
    chapter = await db.get(Chapter, topic.chapter_id)
    subject = await db.get(Subject, chapter.subject_id)
    class_ = await db.get(Class, subject.class_id)
    return {
        "topic_id": topic.id,
        "topic": topic.name,
        "chapter": chapter.name,
        "subject": subject.name,
        "class_name": class_.name,
        "slug": topic.slug
    }
