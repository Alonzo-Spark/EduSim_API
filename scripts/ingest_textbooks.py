import os
import sys
import time
import json
from pathlib import Path

# Add root folder to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.rag.ingestion import ingest_textbook

TEXTBOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "textbooks"))
CURRICULUM_JSON = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "generated_curriculum.json"))

def run():
    start_time = time.time()
    
    if not os.path.exists(CURRICULUM_JSON):
        print(f"[ERROR] Generated curriculum JSON not found at: {CURRICULUM_JSON}")
        print("Please run: python scripts/generate_curriculum_from_pdfs.py first!")
        return

    with open(CURRICULUM_JSON, "r", encoding="utf-8") as f:
        books = json.load(f)

    # Statistics counters
    books_processed = 0
    chunks_inserted = 0
    failures_count = 0
    missing_any = []

    print("==================================================")
    print("  NCERT CURRICULUM-AWARE TEXTBOOK INGESTION PIPELINE  ")
    print("==================================================")
    print(f"Loading curriculum map from: {CURRICULUM_JSON}")
    print(f"Reading physical PDFs from: {TEXTBOOKS_DIR}")

    for book in books:
        pdf_name = book.get("pdf")
        if not pdf_name:
            continue
            
        pdf_path = os.path.join(TEXTBOOKS_DIR, pdf_name)
        if not os.path.exists(pdf_path):
            missing_any.append(pdf_name)
            continue
            
        books_processed += 1
        
        try:
            print(f"\n[START] Ingesting textbook: {pdf_name} ({book['class']} - {book['subject']})")
            # Ingest full textbook to automatically index all chapters & topics in one high-performance pass
            n = ingest_textbook(
                pdf_path=pdf_path,
                class_name=book["class"],
                subject=book["subject"],
                chapter="Full Textbook",
                start_page=None,
                end_page=None
            )
            chunks_inserted += n
        except Exception as e:
            print(f"[ERROR] Failed to ingest {pdf_name}: {e}")
            failures_count += 1

    total_time = round(time.time() - start_time, 2)

    # Ingestion final report
    print("\n==================================================")
    print("          INGESTION PIPELINE FINAL SUMMARY        ")
    print("==================================================")
    print(f"  - Books Processed:    {books_processed}")
    print(f"  - Chunks Inserted:    {chunks_inserted}")
    print(f"  - Ingestion Failures: {failures_count}")
    print(f"  - Total Elapsed Time: {total_time}s")
    
    if missing_any:
        print(f"\n[WARNING] The following {len(missing_any)} files were listed in curriculum but missing from disk:")
        for missing in missing_any:
            print(f"    - {missing}")
            
    print("==================================================")

if __name__ == "__main__":
    run()
