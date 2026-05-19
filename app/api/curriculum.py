from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db
from app.services.curriculum_service import (
    get_all_classes, get_subjects, get_chapters,
    get_topics, get_topic_by_slug
)

router = APIRouter(tags=["Curriculum"])

@router.get("/classes")
async def list_classes(db: AsyncSession = Depends(get_db)):
    return await get_all_classes(db)

@router.get("/subjects/{class_id}")
async def list_subjects(class_id: int, db: AsyncSession = Depends(get_db)):
    return await get_subjects(class_id, db)

@router.get("/chapters/{subject_id}")
async def list_chapters(subject_id: int, db: AsyncSession = Depends(get_db)):
    return await get_chapters(subject_id, db)

@router.get("/topics/{chapter_id}")
async def list_topics(chapter_id: int, db: AsyncSession = Depends(get_db)):
    return await get_topics(chapter_id, db)

@router.get("/topic/{slug}")
async def get_topic(slug: str, db: AsyncSession = Depends(get_db)):
    topic = await get_topic_by_slug(slug, db)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic
