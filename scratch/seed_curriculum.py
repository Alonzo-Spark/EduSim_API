import json
import subprocess
from sqlalchemy.dialects.postgresql import insert
from app.src.config.database import SessionLocal
from app.src.models.persistence import CurriculumClass, Subject, Chapter, Topic

def run():
    print("Extracting curriculum from TS...")
    result = subprocess.run(
        ["npx", "tsx", "curriculum/extract_curriculum.ts"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        shell=True  # Ensure npx runs on Windows
    )
    if result.returncode != 0:
        print("Error extracting curriculum:")
        print(result.stderr)
        return
    
    try:
        classes_data = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        start = result.stdout.find('[')
        if start != -1:
            classes_data = json.loads(result.stdout[start:])
        else:
            print("JSON parse error:", e)
            print("Output was:", result.stdout)
            return

    from pathlib import Path
    try:
        curriculum_json_path = Path(__file__).resolve().parent / "app" / "src" / "data" / "curriculum.json"
        print(f"Syncing curriculum to JSON: {curriculum_json_path}")
        with open(curriculum_json_path, "w", encoding="utf-8") as f:
            json.dump({"classes": classes_data}, f, indent=2, ensure_ascii=False)
        print("Curriculum JSON file synced successfully!")
    except Exception as ex:
        print("Failed to sync curriculum JSON file:", ex)

    db = SessionLocal()
    try:
        class_order = 1
        for cls_data in classes_data:
            cls_stmt = insert(CurriculumClass).values(
                id=cls_data['id'],
                name=cls_data['name'],
                description=cls_data['description'],
                display_order=class_order
            )
            cls_stmt = cls_stmt.on_conflict_do_update(
                index_elements=['id'],
                set_={
                    'name': cls_stmt.excluded.name,
                    'description': cls_stmt.excluded.description,
                    'display_order': cls_stmt.excluded.display_order
                }
            )
            db.execute(cls_stmt)
            class_order += 1
            
            subject_order = 1
            for sub_data in cls_data.get('subjects', []):
                sub_stmt = insert(Subject).values(
                    class_id=cls_data['id'],
                    code=sub_data['id'],
                    name=sub_data['name'],
                    description=sub_data.get('description', ''),
                    icon=sub_data.get('icon', ''),
                    display_order=subject_order
                ).returning(Subject.id)
                sub_stmt = sub_stmt.on_conflict_do_update(
                    index_elements=['class_id', 'code'],
                    set_={
                        'name': sub_stmt.excluded.name,
                        'description': sub_stmt.excluded.description,
                        'icon': sub_stmt.excluded.icon,
                        'display_order': sub_stmt.excluded.display_order
                    }
                )
                sub_id_res = db.execute(sub_stmt).scalar_one_or_none()
                if not sub_id_res:
                    # If ON CONFLICT DO UPDATE didn't return id automatically due to SQLAlchemy quirks,
                    # we can query it.
                    sub_id_res = db.query(Subject.id).filter_by(class_id=cls_data['id'], code=sub_data['id']).scalar()
                subject_order += 1
                
                chapters = sub_data.get('chapters', [])
                if isinstance(chapters, int):
                    continue
                
                chapter_order = 1
                for chap_data in chapters:
                    chap_stmt = insert(Chapter).values(
                        subject_id=sub_id_res,
                        name=chap_data['name'],
                        description="",
                        display_order=chapter_order
                    ).returning(Chapter.id)
                    chap_stmt = chap_stmt.on_conflict_do_update(
                        index_elements=['subject_id', 'name'],
                        set_={
                            'description': chap_stmt.excluded.description,
                            'display_order': chap_stmt.excluded.display_order
                        }
                    )
                    chap_id_res = db.execute(chap_stmt).scalar_one_or_none()
                    if not chap_id_res:
                        chap_id_res = db.query(Chapter.id).filter_by(subject_id=sub_id_res, name=chap_data['name']).scalar()
                    chapter_order += 1
                    
                    topic_order = 1
                    for top_data in chap_data.get('topics', []):
                        top_stmt = insert(Topic).values(
                            chapter_id=chap_id_res,
                            name=top_data['name'],
                            description="",
                            has_simulation=top_data.get('hasSimulation', False),
                            simulation_route=top_data.get('simulationRoute', None),
                            display_order=topic_order
                        )
                        top_stmt = top_stmt.on_conflict_do_update(
                            index_elements=['chapter_id', 'name'],
                            set_={
                                'description': top_stmt.excluded.description,
                                'has_simulation': top_stmt.excluded.has_simulation,
                                'simulation_route': top_stmt.excluded.simulation_route,
                                'display_order': top_stmt.excluded.display_order
                            }
                        )
                        db.execute(top_stmt)
                        topic_order += 1
        
        db.commit()
        print("Curriculum seeded successfully!")
    except Exception as e:
        db.rollback()
        print("Error seeding:", e)
    finally:
        db.close()

if __name__ == "__main__":
    run()
