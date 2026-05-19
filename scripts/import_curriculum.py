"""
Seeds PostgreSQL with the full curriculum from data/curriculum.json.
Run once after alembic upgrade head:
    python scripts/import_curriculum.py
"""
import asyncio
import json
import sys
from pathlib import Path

# Add root folder to sys.path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.database import engine, AsyncSessionLocal
from app.models.curriculum import Class, Subject, Chapter, Topic, Subtopic

def make_slug(*parts: str) -> str:
    return "_".join(p.lower().replace(" ", "_").replace("'", "").replace("-", "_") for p in parts)

async def import_curriculum():
    with open("data/curriculum.json") as f:
        data = json.load(f)

    async with AsyncSessionLocal() as session:
        # Pre-clean existing curriculum to avoid unique constraint violations on re-runs
        print("Cleaning up old curriculum...")
        await session.execute(delete(Subtopic))
        await session.execute(delete(Topic))
        await session.execute(delete(Chapter))
        await session.execute(delete(Subject))
        await session.execute(delete(Class))
        await session.flush()

        for class_data in data["classes"]:
            print(f"\nImporting: {class_data['name']}")

            class_obj = Class(
                name=class_data["name"],
                display_order=class_data.get("display_order", 0)
            )
            session.add(class_obj)
            await session.flush()

            for subj_data in class_data.get("subjects", []):
                subj_obj = Subject(
                    class_id=class_obj.id,
                    name=subj_data["name"],
                    icon=subj_data.get("icon", "book"),
                    description=subj_data.get("description", "")
                )
                session.add(subj_obj)
                await session.flush()

                for ch_idx, ch_data in enumerate(subj_data.get("chapters", [])):
                    ch_obj = Chapter(
                        subject_id=subj_obj.id,
                        name=ch_data["name"],
                        order_index=ch_data.get("order_index", ch_idx + 1)
                    )
                    session.add(ch_obj)
                    await session.flush()

                    for topic_data in ch_data.get("topics", []):
                        slug = make_slug(class_data["name"], subj_data["name"], topic_data["name"])
                        topic_obj = Topic(
                            chapter_id=ch_obj.id,
                            name=topic_data["name"],
                            slug=slug,
                            has_simulation=topic_data.get("has_simulation", False),
                            simulation_type=topic_data.get("simulation_type")
                        )
                        session.add(topic_obj)
                        await session.flush()

                        for st_name in topic_data.get("subtopics", []):
                            session.add(Subtopic(topic_id=topic_obj.id, name=st_name))

                    print(f"  [OK] {ch_data['name']} ({len(ch_data.get('topics',[]))} topics)")

        await session.commit()
        print("\n[SUCCESS] Curriculum import complete.")

if __name__ == "__main__":
    asyncio.run(import_curriculum())
