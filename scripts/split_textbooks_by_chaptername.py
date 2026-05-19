import os
import re
import json
import fitz
from pathlib import Path

TEXTBOOK_DIR = Path("data/textbooks")
OUTPUT_DIR = Path("data/chapters")
CURRICULUM_JSON = Path("data/generated_curriculum.json")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHAPTER_REGEX = re.compile(
    r"(chapter\s+\d+|unit\s+\d+|\d+\.\s+[A-Z][^\n]+)",
    re.IGNORECASE
)

CLASS_REGEX = re.compile(r"(class|grade)\s*(\d+|ix|x|xi|xii)", re.IGNORECASE)

SUBJECT_KEYWORDS = {
    "physics": "Physics",
    "biology": "Biology",
    "chemistry": "Chemistry",
    "mathematics": "Mathematics",
    "math": "Mathematics",
    "science": "Science",
    "english": "English",
    "social": "Social"
}


def normalize_filename(name):
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def detect_class(text):
    match = CLASS_REGEX.search(text)
    if not match:
        return "Unknown_Class"

    value = match.group(2).lower()

    roman_map = {
        "ix": "9",
        "x": "10",
        "xi": "11",
        "xii": "12"
    }

    value = roman_map.get(value, value)

    return f"Class_{value}"


def detect_subject(text):
    text_lower = text.lower()

    for key, value in SUBJECT_KEYWORDS.items():
        if key in text_lower:
            return value

    return "Unknown_Subject"


def extract_text(pdf_path, max_pages=15):
    doc = fitz.open(pdf_path)

    content = ""

    pages = min(max_pages, len(doc))

    for i in range(pages):
        try:
            content += doc[i].get_text()
        except:
            pass

    doc.close()

    return content


def detect_chapters(doc):

    chapters = []

    chapter_patterns = [
        r"chapter\s+\d+[:\-\s]*([A-Z].+)",
        r"unit\s+\d+[:\-\s]*([A-Z].+)",
        r"^\d+\.\s+([A-Z].+)",
        r"^chapter\s+\d+",
    ]

    combined = re.compile(
        "|".join(chapter_patterns),
        re.IGNORECASE | re.MULTILINE
    )

    for page_num in range(len(doc)):

        try:
            text = doc[page_num].get_text()

            if not text.strip():
                continue

            matches = combined.finditer(text)

            for match in matches:

                raw = match.group(0).strip()

                if len(raw) < 3:
                    continue

                raw = raw.replace("\n", " ")

                chapters.append({
                    "page": page_num,
                    "title": raw
                })

        except Exception:
            continue

    cleaned = []

    seen = set()

    for ch in chapters:

        title = ch["title"].lower()

        title = re.sub(r"\s+", " ", title)

        if title not in seen:

            seen.add(title)

            cleaned.append(ch)

    cleaned = sorted(cleaned, key=lambda x: x["page"])

    return cleaned


def split_pdf(pdf_path):
    pdf_path = Path(pdf_path)

    print(f"\nScanning: {pdf_path.name}")

    first_text = extract_text(pdf_path)

    class_name = detect_class(first_text)
    subject_name = detect_subject(first_text)

    doc = fitz.open(pdf_path)

    chapters = detect_chapters(doc)

    if not chapters:
        print("No chapters detected")
        return None

    curriculum_entry = {
        "source_pdf": pdf_path.name,
        "class": class_name,
        "subject": subject_name,
        "chapters": []
    }

    for idx, chapter in enumerate(chapters):

        start_page = chapter["page"]

        if idx < len(chapters) - 1:
            end_page = chapters[idx + 1]["page"] - 1
        else:
            end_page = len(doc) - 1

        chapter_title = chapter["title"]

        clean_title = normalize_filename(chapter_title)

        output_filename = (
            f"{normalize_filename(class_name)}_"
            f"{normalize_filename(subject_name)}_"
            f"{clean_title}.pdf"
        )

        output_path = OUTPUT_DIR / output_filename

        new_pdf = fitz.open()

        for p in range(start_page, end_page + 1):
            new_pdf.insert_pdf(doc, from_page=p, to_page=p)

        new_pdf.save(output_path)
        new_pdf.close()

        print(f"Saved: {output_filename}")

        curriculum_entry["chapters"].append({
            "chapter_name": chapter_title,
            "start_page": start_page + 1,
            "end_page": end_page + 1,
            "file": output_filename
        })

    doc.close()

    return curriculum_entry


def main():
    curriculum = []

    pdf_files = list(TEXTBOOK_DIR.rglob("*.pdf"))

    if not pdf_files:
        print("No PDFs found")
        return

    for pdf in pdf_files:
        try:
            result = split_pdf(pdf)

            if result:
                curriculum.append(result)

        except Exception as e:
            print(f"Error processing {pdf.name}: {e}")

    with open(CURRICULUM_JSON, "w", encoding="utf-8") as f:
        json.dump(curriculum, f, indent=2, ensure_ascii=False)

    print("\nCurriculum JSON generated")
    print(f"Saved at: {CURRICULUM_JSON}")


if __name__ == "__main__":
    main()