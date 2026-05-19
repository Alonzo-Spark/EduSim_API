"""
normalize_textbook_corpus.py
=========================================================
EduSim Intelligent PDF Normalizer + Chapter Extractor

Features
--------
1. Extract ZIP files
2. Scan nested folders
3. Find all PDFs recursively
4. Remove duplicate PDFs
5. Detect:
    - Class
    - Subject
    - Chapter Name
6. Rename PDFs cleanly as:
       class_<n>_<subject>_<chapter>.pdf
7. Move processed PDFs into:
       data/chapters/
8. Save mappings JSON
9. Save processing report JSON

Usage
-----
python scripts/normalize_textbook_corpus.py
"""

import os
import re
import json
import shutil
import hashlib
import zipfile
import logging
from pathlib import Path
from collections import defaultdict

try:
    import pdfplumber
except:
    pdfplumber = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S"
)

log = logging.getLogger("edusim-normalizer")

ROOT_DIR = Path("data/textbooks")
OUTPUT_DIR = Path("data/chapters")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# ZIP EXTRACTION
# =========================================================

def extract_zip_files(root):

    zip_files = list(root.rglob("*.zip"))

    for zip_path in zip_files:

        try:

            extract_folder = zip_path.parent / zip_path.stem

            extract_folder.mkdir(exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_folder)

            log.info(f"Extracted: {zip_path.name}")

        except Exception as e:
            log.error(f"ZIP extraction failed: {zip_path.name} -> {e}")

# =========================================================
# PDF DISCOVERY
# =========================================================

def find_all_pdfs(root):

    return list(root.rglob("*.pdf"))

# =========================================================
# HASHING
# =========================================================

def file_hash(path):

    sha = hashlib.sha256()

    with open(path, "rb") as f:

        while True:

            chunk = f.read(8192)

            if not chunk:
                break

            sha.update(chunk)

    return sha.hexdigest()

# =========================================================
# TEXT EXTRACTION
# =========================================================

def extract_text(pdf_path, max_pages=10):

    if not pdfplumber:
        return ""

    text = ""

    try:

        with pdfplumber.open(pdf_path) as pdf:

            pages = pdf.pages[:max_pages]

            for page in pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

    except Exception as e:

        log.warning(f"Text extraction failed: {pdf_path.name}")

    return text.lower()

# =========================================================
# CLASS DETECTION
# =========================================================

def detect_class(text, filename=""):

    combined = f"{filename} {text}".lower()

    patterns = [
        r"class\s*(\d+)",
        r"grade\s*(\d+)",
        r"\b([1-9]|10|11|12)(st|nd|rd|th)?\b"
    ]

    for pattern in patterns:

        matches = re.finditer(pattern, combined)

        for match in matches:

            try:

                num = int(match.group(1))

                if 1 <= num <= 12:
                    return num

            except:
                pass

    return None

# =========================================================
# SUBJECT DETECTION
# =========================================================

def detect_subject(text, filename=""):

    combined = f"{filename} {text}".lower()

    subject_map = {

        "mathematics": [
            "mathematics",
            "math",
            "maths",
            "algebra",
            "geometry"
        ],

        "physics": [
            "physics",
            "motion",
            "force",
            "laws of motion",
            "gravitation"
        ],

        "chemistry": [
            "chemistry",
            "atoms",
            "molecules",
            "chemical"
        ],

        "biology": [
            "biology",
            "cell",
            "tissue",
            "organism",
            "life processes"
        ],

        "science": [
            "science"
        ]
    }

    scores = {}

    for subject, words in subject_map.items():

        score = 0

        for word in words:
            score += combined.count(word)

        scores[subject] = score

    best = max(scores, key=scores.get)

    if scores[best] == 0:
        return None

    return best

# =========================================================
# CHAPTER DETECTION
# =========================================================

def detect_chapter(text):

    lines = text.splitlines()

    clean_lines = []

    for line in lines:

        line = line.strip()

        if len(line) < 4:
            continue

        if len(line) > 80:
            continue

        if re.search(r"\d+\.\d+", line):
            continue

        clean_lines.append(line)

    chapter_patterns = [

        r"chapter\s+\d+\s*[:\-]?\s*(.+)",

        r"unit\s+\d+\s*[:\-]?\s*(.+)",

        r"^\d+\s+([A-Z][A-Za-z\s]+)$",

        r"^[A-Z][A-Z\s]{5,}$"
    ]

    for line in clean_lines[:120]:

        for pattern in chapter_patterns:

            match = re.search(
                pattern,
                line,
                re.IGNORECASE
            )

            if match:

                if match.groups():
                    chapter = match.group(1)
                else:
                    chapter = line

                chapter = chapter.lower()

                chapter = re.sub(
                    r"[^a-z0-9\s]",
                    "",
                    chapter
                )

                chapter = re.sub(
                    r"\s+",
                    "_",
                    chapter
                )

                chapter = chapter.strip("_")

                bad_words = [
                    "exercise",
                    "figure",
                    "table",
                    "example",
                    "summary",
                    "question",
                    "activity"
                ]

                if any(
                    b in chapter
                    for b in bad_words
                ):
                    continue

                if len(chapter) < 3:
                    continue

                return chapter

    return None

# =========================================================
# SAFE FILE NAME
# =========================================================

def safe_filename(name):

    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

    name = re.sub(r"_+", "_", name)

    return name.lower().strip("_")

# =========================================================
# MAIN PIPELINE
# =========================================================

def process_pdfs():

    extract_zip_files(ROOT_DIR)

    pdfs = find_all_pdfs(ROOT_DIR)

    log.info("=" * 60)
    log.info("EduSim PDF Normalizer")
    log.info("=" * 60)

    seen_hashes = set()

    mappings = {}

    counters = defaultdict(int)

    for pdf in pdfs:

        try:

            hash_value = file_hash(pdf)

            if hash_value in seen_hashes:

                log.info(f"Duplicate skipped: {pdf.name}")
                continue

            seen_hashes.add(hash_value)

            text = extract_text(pdf)

            class_num = detect_class(
                text,
                pdf.name
            )

            subject = detect_subject(
                text,
                pdf.name
            )

            chapter = detect_chapter(text)

            if not class_num:
                class_num = "unknown"

            if not subject:
                subject = "unknown"

            if not chapter:
                chapter = "chapter"

            new_name = f"class_{class_num}_{subject}_{chapter}.pdf"

            new_name = safe_filename(new_name)

            counters[new_name] += 1

            if counters[new_name] > 1:

                new_name = (
                    f"{new_name.replace('.pdf', '')}_"
                    f"{counters[new_name]}.pdf"
                )

            destination = OUTPUT_DIR / new_name

            shutil.copy2(pdf, destination)

            mappings[str(pdf)] = str(destination)

            log.info(f"{pdf.name} -> {new_name}")

        except Exception as e:

            log.error(f"Failed processing {pdf.name}: {e}")

    # =====================================================
    # SAVE JSON REPORTS
    # =====================================================

    mappings_path = Path("data/filename_mappings.json")

    with open(mappings_path, "w", encoding="utf-8") as f:

        json.dump(
            mappings,
            f,
            indent=2,
            ensure_ascii=False
        )

    report = {

        "total_processed": len(mappings),

        "duplicates_removed":
            len(pdfs) - len(mappings),

        "final_output_folder":
            str(OUTPUT_DIR)
    }

    report_path = Path("data/corpus_report.json")

    with open(report_path, "w", encoding="utf-8") as f:

        json.dump(
            report,
            f,
            indent=2
        )

    log.info("=" * 60)
    log.info("PROCESS COMPLETE")
    log.info(f"Processed PDFs: {len(mappings)}")
    log.info(f"Output Folder : {OUTPUT_DIR}")
    log.info("=" * 60)

# =========================================================
# ENTRY
# =========================================================

if __name__ == "__main__":

    process_pdfs()