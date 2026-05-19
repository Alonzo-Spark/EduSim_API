import json
import re
from pathlib import Path

TEXTBOOK_DIR = Path("data/textbooks")
OUTPUT_MANIFEST = Path("data/ingestion_manifest.json")

SUBJECT_KEYWORDS = {
    "physics": "Physics",
    "biology": "Biology",
    "math": "Mathematics",
    "maths": "Mathematics",
    "science": "Science",
    "evs": "EVS",
    "chemistry": "Chemistry",
}

CLASS_PATTERNS = {
    "4": "Class 4",
    "5": "Class 5",
    "6": "Class 6",
    "vi": "Class 6",
    "7": "Class 7",
    "vii": "Class 7",
    "8": "Class 8",
    "viii": "Class 8",
    "9": "Class 9",
    "ix": "Class 9",
    "10": "Class 10",
    "x": "Class 10",
}


def detect_class(filename: str):
    lower = filename.lower()

    for pattern, cls in CLASS_PATTERNS.items():
        if re.search(rf"\b{pattern}\b", lower):
            return cls

    return "Unknown"


def detect_subject(filename: str):
    lower = filename.lower()

    for keyword, subject in SUBJECT_KEYWORDS.items():
        if keyword in lower:
            return subject

    return "General"


def clean_filename(class_name, subject):
    cls_num = class_name.replace("Class ", "")
    return f"class_{cls_num}_{subject.lower()}.pdf"


def main():
    manifest = []

    if not TEXTBOOK_DIR.exists():
        print(f"[ERROR] Textbook folder not found: {TEXTBOOK_DIR}")
        return

    pdf_files = list(TEXTBOOK_DIR.glob("*.pdf"))

    if not pdf_files:
        print("[WARNING] No PDF files found.")
        return

    for pdf in pdf_files:
        original_name = pdf.name

        class_name = detect_class(original_name)
        subject = detect_subject(original_name)

        new_filename = clean_filename(class_name, subject)
        new_path = TEXTBOOK_DIR / new_filename

        counter = 1
        while new_path.exists() and new_path != pdf:
            new_filename = clean_filename(class_name, f"{subject}_{counter}")
            new_path = TEXTBOOK_DIR / new_filename
            counter += 1

        if pdf != new_path:
            pdf.rename(new_path)

        print(f"[OK] Renamed: {original_name} -> {new_filename}")

        manifest.append({
            "path": f"data/textbooks/{new_filename}",
            "class": class_name,
            "subject": subject,
            "chapters": []
        })

    with open(OUTPUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n[SUCCESS] ingestion_manifest.json generated successfully.")
    print(f"[INFO] Total textbooks processed: {len(manifest)}")


if __name__ == "__main__":
    main()