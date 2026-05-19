import os
import sys
import hashlib
import json
import shutil
from pathlib import Path

# Add backend root to load path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.curriculum_extractor import TextbookExtractor

TEXTBOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "textbooks"))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
CURRICULUM_JSON = os.path.join(DATA_DIR, "generated_curriculum.json")
MAPPING_JSON = os.path.join(DATA_DIR, "filename_mappings.json")
CACHE_JSON = os.path.join(DATA_DIR, ".curriculum_cache.json")

def get_file_hash(filepath: str) -> str:
    """Calculates SHA256 of file for incremental scanning cache."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""

def load_cache() -> dict:
    if os.path.exists(CACHE_JSON):
        try:
            with open(CACHE_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_cache(cache: dict):
    with open(CACHE_JSON, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def generate_standard_name(class_name: str, subject: str, count: int = 1) -> str:
    # "Class 9" -> "class_9"
    c_num = "".join(filter(str.isdigit, class_name))
    c_label = f"class_{c_num}" if c_num else "class_unknown"
    s_label = subject.lower().replace(" ", "_")
    
    suffix = f"_{count}" if count > 1 else ""
    return f"{c_label}_{s_label}{suffix}.pdf"

def main():
    print("=== Starting Curriculum Intelligence Ingestion Pipeline ===")
    print(f"Textbook root: {TEXTBOOKS_DIR}")
    
    os.makedirs(DATA_DIR, exist_ok=True)
    cache = load_cache()
    
    # 1. Discover all PDFs in top-level directory (avoids scanning duplicate extracted part files)
    pdf_files = []
    for file in os.listdir(TEXTBOOKS_DIR):
        if file.lower().endswith(".pdf"):
            pdf_files.append(os.path.join(TEXTBOOKS_DIR, file))
                
    print(f"[INFO] Discovered {len(pdf_files)} PDF textbook files.")
    
    curriculums = []
    name_mappings = {}
    used_standard_names = {}
    
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        print(f"\n[SCAN] Processing textbook: {filename} ...")
        
        file_hash = get_file_hash(pdf_path)
        cached_data = cache.get(file_hash) if file_hash else None
        
        class_name = None
        subject = None
        chapters = []
        
        if cached_data:
            print(f"[CACHE] Incremental hit! Loading pre-extracted metadata for {filename}.")
            class_name = cached_data.get("class")
            subject = cached_data.get("subject")
            chapters = cached_data.get("chapters", [])
        else:
            # Load and parse via TextbookExtractor
            extractor = TextbookExtractor(pdf_path)
            if extractor.open():
                try:
                    class_name, subject = extractor.detect_class_and_subject()
                    chapters = extractor.extract_chapters_and_topics()
                    
                    # Store in cache
                    if file_hash:
                        cache[file_hash] = {
                            "class": class_name,
                            "subject": subject,
                            "chapters": chapters
                        }
                except Exception as ex:
                    print(f"[ERROR] Exception during PyMuPDF parse for {filename}: {ex}")
                    class_name, subject = extractor.detect_class_and_subject()
                finally:
                    extractor.close()
            else:
                print(f"[WARNING] Could not open {filename} to parse structure. Using filename fallback classification.")
                class_name, subject = extractor.detect_class_and_subject()
                
        if not class_name or not subject:
            class_name, subject = "Class 9", "Science"
            
        # 2. Standard auto-renaming logic
        standard_base = generate_standard_name(class_name, subject)
        
        # Avoid naming collisions
        count = 1
        standard_name = standard_base
        while standard_name in used_standard_names:
            count += 1
            standard_name = generate_standard_name(class_name, subject, count)
            
        used_standard_names[standard_name] = pdf_path
        
        # Physically rename file on disk if it isn't already renamed
        new_pdf_path = os.path.join(TEXTBOOKS_DIR, standard_name)
        if pdf_path != new_pdf_path:
            try:
                # If target standard file already exists (e.g. from previous run), delete it first to avoid permission blocks
                if os.path.exists(new_pdf_path):
                    os.remove(new_pdf_path)
                shutil.move(pdf_path, new_pdf_path)
                print(f"[OK] Renamed {filename} -> {standard_name}")
                name_mappings[filename] = standard_name
            except Exception as e:
                print(f"[ERROR] Failed renaming {filename} to {standard_name}: {e}")
                new_pdf_path = pdf_path
                name_mappings[filename] = filename
        else:
            name_mappings[filename] = filename
            
        curriculums.append({
            "class": class_name,
            "subject": subject,
            "book": subject,
            "pdf": os.path.basename(new_pdf_path),
            "chapters": chapters
        })
        
        print(f"[STATUS] Detected: {class_name} | {subject} | {len(chapters)} Chapters found.")
        
    # 3. Save Cache, generated curriculum structure JSON and file mappings JSON
    save_cache(cache)
    
    with open(CURRICULUM_JSON, "w", encoding="utf-8") as f:
        json.dump(curriculums, f, indent=2)
        
    with open(MAPPING_JSON, "w", encoding="utf-8") as f:
        json.dump(name_mappings, f, indent=2)
        
    print(f"\n[OK] Successfully wrote unified NCERT curriculum graph to: {CURRICULUM_JSON}")
    print(f"[OK] Successfully wrote original-to-renamed file mapping to: {MAPPING_JSON}")
    print("=== Curriculum Ingestion Finished Successfully ===")

if __name__ == "__main__":
    main()