import json
from pathlib import Path
from sqlalchemy.orm import Session
from app.src.models.persistence import Subject, Chapter, Topic


def populate_curriculum(db: Session) -> None:
    # Check if subjects is empty
    if db.query(Subject).first() is not None:
        return

    curriculum_path = Path(__file__).resolve().parents[1] / "data" / "curriculum.json"
    if not curriculum_path.exists():
        print(f"[Curriculum Loader] File not found at {curriculum_path}")
        return

    with open(curriculum_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("[Curriculum Loader] Populating database from curriculum.json...")
    for class_item in data.get("classes", []):
        class_name = class_item.get("name")
        for sub_item in class_item.get("subjects", []):
            code = sub_item.get("id")
            # Reuse subject if code already registered (since subjects can span multiple classes)
            subject = db.query(Subject).filter(Subject.code == code).first()
            if not subject:
                subject = Subject(
                    code=code,
                    name=sub_item.get("name"),
                    description=sub_item.get("description"),
                    icon=sub_item.get("icon")
                )
                db.add(subject)
                db.flush()

            chapters = sub_item.get("chapters", [])
            if isinstance(chapters, list):
                for chap_item in chapters:
                    chapter = Chapter(
                        subject_id=subject.id,
                        name=chap_item.get("name"),
                        class_name=class_name,
                        description=chap_item.get("description")
                    )
                    db.add(chapter)
                    db.flush()

                    for top_item in chap_item.get("topics", []):
                        topic = Topic(
                            chapter_id=chapter.id,
                            name=top_item.get("name"),
                            description=top_item.get("description")
                        )
                        db.add(topic)
            elif isinstance(chapters, (int, float)):
                # Just mock some numbered chapters
                for i in range(1, int(chapters) + 1):
                    chapter = Chapter(
                        subject_id=subject.id,
                        name=f"Chapter {i}",
                        class_name=class_name
                    )
                    db.add(chapter)
                    db.flush()

                    topic = Topic(
                        chapter_id=chapter.id,
                        name="Introduction"
                    )
                    db.add(topic)
    db.commit()
    print("[Curriculum Loader] Database curriculum population complete.")
