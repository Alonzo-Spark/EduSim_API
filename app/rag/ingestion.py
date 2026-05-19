import fitz                          # PyMuPDF
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    pdfplumber = None
    HAS_PDFPLUMBER = False

import chromadb
import re
import time
import hashlib
from pathlib import Path
from app.config import settings
from app.rag.chunker import SemanticEducationalChunker
from app.rag.embedder import embed_texts

def get_chroma_collection():
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    return client.get_or_create_collection(
        name="edusim_textbooks",
        metadata={"hnsw:space": "cosine"}
    )

def extract_pages_pymupdf(pdf_path: str, start_page: int = None, end_page: int = None) -> list[dict]:
    """Primary extraction using PyMuPDF — fast, handles most textbooks."""
    doc = fitz.open(pdf_path)
    pages = []
    start = (start_page - 1) if start_page else 0
    end = end_page if end_page else len(doc)

    for page_num in range(start, min(end, len(doc))):
        page = doc[page_num]
        text = page.get_text("text")
        # Ensure we strip and check minimal length
        pages.append({
            "page": page_num + 1,
            "text": text.strip() if text else ""
        })
    return pages

def extract_pages_pdfplumber(pdf_path: str, start_page: int = None, end_page: int = None) -> list[dict]:
    """Fallback extraction using pdfplumber — better for tables and complex layouts."""
    if not HAS_PDFPLUMBER:
        print("  [WARNING] pdfplumber is not installed, fallback extraction skipped.")
        return []
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        start = (start_page - 1) if start_page else 0
        end = end_page if end_page else len(pdf.pages)
        for page_num in range(start, min(end, len(pdf.pages))):
            page = pdf.pages[page_num]
            text = page.extract_text()
            pages.append({
                "page": page_num + 1,
                "text": text.strip() if text else ""
            })
    return pages

def detect_headings(text: str, current_ch: str, current_tp: str, current_sec: str) -> tuple[str, str, str]:
    """
    Scan page lines to dynamically detect and track:
    - Chapter Titles
    - Topic Headings
    - Numbered Sections
    """
    if not text:
        return current_ch, current_tp, current_sec
        
    lines = text.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # Chapter pattern: e.g. "CHAPTER 8: MOTION" or "Chapter 8 - Motion"
        ch_match = re.search(r'(?i)^\s*(CHAPTER\s+\d+|CHAPTER\s+[IXVLDM]+)\b[:\-]?\s*(.*)', stripped)
        if ch_match:
            potential_title = ch_match.group(2).strip()
            current_ch = f"{ch_match.group(1)}" + (f": {potential_title}" if potential_title else "")
            continue
            
        # Numbered Subsection pattern: e.g. "8.1.1 Motion along a straight line"
        sec_match = re.search(r'^\s*(\d+\.\d+\.\d+)\s+([A-Z][a-zA-Z0-9\s,\-:]{2,80})', stripped)
        if sec_match:
            current_sec = f"{sec_match.group(1)} {sec_match.group(2).strip()}"
            continue
            
        # Topic Heading pattern: e.g. "8.1 Describing Motion"
        tp_match = re.search(r'^\s*(\d+\.\d+)\s+([A-Z][a-zA-Z0-9\s,\-:]{2,80})', stripped)
        if tp_match:
            current_tp = f"{tp_match.group(1)} {tp_match.group(2).strip()}"
            current_sec = ""  # Reset subsection on new major topic
            continue
            
    return current_ch, current_tp, current_sec

def ingest_textbook(
    pdf_path: str,
    class_name: str,
    subject: str,
    chapter: str,
    topic: str = "",
    start_page: int = None,
    end_page: int = None,
    batch_size: int = 64
) -> int:
    """
    Production-grade educational RAG ingestion pipeline:
    - Custom semantic paragraph boundary chunking (preserves headings, formulas, steps, lists)
    - Sequential real-time Chapter & Topic heading tracking
    - Deterministic MD5 hashing to prevent duplicates
    - Page-level OCR scanned validation
    - Memory-safe batched embedding updates
    
    Returns the integer count of chunks successfully stored/inserted.
    """
    start_time = time.time()
    collection = get_chroma_collection()

    print(f"\n[INFO] Starting ingestion: {class_name} > {subject} > {chapter}")
    print(f"  Source file: {pdf_path} (Pages {start_page or 1} to {end_page or 'EOF'})")

    if not Path(pdf_path).exists():
        print(f"  [ERROR] File not found: {pdf_path}")
        return 0

    # Extract pages using primary PyMuPDF extractor
    try:
        pages = extract_pages_pymupdf(pdf_path, start_page, end_page)
    except Exception as e:
        print(f"  [WARNING] PyMuPDF failed on {pdf_path}: {e}. Trying pdfplumber...")
        try:
            pages = extract_pages_pdfplumber(pdf_path, start_page, end_page)
        except Exception as inner_e:
            print(f"  [ERROR] Extraction fallbacks failed for {pdf_path}: {inner_e}")
            return 0

    if not pages:
        print(f"  [ERROR] Zero pages extracted from {pdf_path}")
        return 0

    # Initialize tracking variables
    current_ch = chapter
    current_tp = topic
    current_sec = ""
    
    scanned_pages_count = 0
    total_pages = len(pages)
    
    # Instantiate semantic chunker
    chunker = SemanticEducationalChunker(chunk_size=800, overlap=100)
    
    all_candidate_chunks = []

    for idx, page in enumerate(pages):
        page_num = page["page"]
        raw_text = page["text"]

        # OCR / Scanned Page detection
        if len(raw_text) < 15:
            print(f"  [WARNING] Page {page_num} of {pdf_path} appears scanned or empty (skipped gracefully)")
            scanned_pages_count += 1
            continue

        # Live chapter and heading detection
        current_ch, current_tp, current_sec = detect_headings(raw_text, current_ch, current_tp, current_sec)

        # Build enrichment metadata
        metadata = {
            "class": class_name,
            "subject": subject,
            "chapter": chapter,
            "topic": topic,
            "source_file": Path(pdf_path).name,
            "page": page_num,
            "detected_chapter": current_ch,
            "detected_topic": current_tp,
            "detected_section": current_sec,
            "scanned": False
        }

        # Run semantic paragraph chunker
        page_chunks = chunker.chunk_document(raw_text, metadata)
        all_candidate_chunks.extend(page_chunks)

    if not all_candidate_chunks:
        print(f"  [WARNING] No semantic chunks generated for {pdf_path}")
        return 0

    print(f"  [INFO] Segmented into {len(all_candidate_chunks)} candidate chunks.")
    print(f"  [INFO] Checking duplicate IDs against ChromaDB index...")

    # Unique ID checking and batching
    duplicates_skipped = 0
    inserted_count = 0

    # Prepare chunks in batches
    for i in range(0, len(all_candidate_chunks), batch_size):
        batch = all_candidate_chunks[i:i+batch_size]
        batch_ids = [c.chunk_id for c in batch]
        
        # Check against existing IDs in ChromaDB
        try:
            existing = collection.get(ids=batch_ids)
            existing_ids = set(existing["ids"]) if existing and "ids" in existing else set()
        except Exception:
            existing_ids = set()

        to_embed_texts = []
        to_embed_metadatas = []
        to_embed_ids = []

        for chunk in batch:
            if chunk.chunk_id in existing_ids:
                duplicates_skipped += 1
                continue
            to_embed_texts.append(chunk.text)
            to_embed_metadatas.append(chunk.metadata)
            to_embed_ids.append(chunk.chunk_id)

        # Batch embed and upsert
        if to_embed_texts:
            embeddings = embed_texts(to_embed_texts)
            collection.upsert(
                documents=to_embed_texts,
                embeddings=embeddings,
                metadatas=to_embed_metadatas,
                ids=to_embed_ids
            )
            inserted_count += len(to_embed_texts)

    elapsed_time = round(time.time() - start_time, 2)
    
    # Beautiful logging output summary
    print(f"  [SUCCESS] Ingestion completed in {elapsed_time}s!")
    print(f"    - Pages processed: {total_pages} (Scanned/Empty: {scanned_pages_count})")
    print(f"    - Total chunks analyzed: {len(all_candidate_chunks)}")
    print(f"    - Chunks inserted: {inserted_count}")
    print(f"    - Duplicates skipped: {duplicates_skipped}")

    return inserted_count
