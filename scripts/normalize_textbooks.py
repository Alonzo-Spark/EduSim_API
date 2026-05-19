import os
import sys
import hashlib
import json
import shutil
import zipfile
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
    HAS_FITZ = True
except ImportError:
    HAS_FITZ = False

TEXTBOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "textbooks"))
CHAPTERS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "chapters"))
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))

MAPPING_JSON = os.path.join(DATA_DIR, "filename_mappings.json")
REPORT_JSON = os.path.join(DATA_DIR, "corpus_report.json")

def get_file_hash(filepath: str) -> str:
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""

def extract_all_zips(root_dir):
    extracted_any = True
    while extracted_any:
        extracted_any = False
        for dirpath, _, files in os.walk(root_dir):
            for file in files:
                if file.lower().endswith('.zip'):
                    zip_path = os.path.join(dirpath, file)
                    extract_to = os.path.join(dirpath, file[:-4])
                    try:
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(extract_to)
                        os.remove(zip_path)  # Remove ZIP after extraction
                        extracted_any = True
                    except Exception as e:
                        print(f"[ERROR] Failed to extract {zip_path}: {e}")

CLASS_MAP = {
    "1": "1", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9", "10": "10", "11": "11", "12": "12",
    "i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10", "xi": "11", "xii": "12"
}

SUBJECTS = [
    "physics", "chemistry", "biology", "mathematics", "maths", "science", "english", "history", "geography", "civics", "economics", "evs", "environmental studies"
]

def clean_name(name):
    name = re.sub(r'[^a-zA-Z0-9]+', '_', name.lower())
    return name.strip('_')

def detect_metadata(pdf_path, filename):
    class_val = None
    subject_val = None
    chapter_val = None

    text = ""
    if HAS_FITZ:
        try:
            doc = fitz.open(pdf_path)
            # Only read the first 10 pages as instructed
            for i in range(min(10, len(doc))):
                page_text = doc[i].get_text("text")
                if page_text:
                    text += page_text + "\n"
            doc.close()
        except Exception:
            pass

    fn_lower = filename.lower()
    
    # 1. Detect Class
    class_match = re.search(r'\b(?:class|std|grade)[_\s-]*([ivx]+|\d+)\b', fn_lower)
    if class_match:
        c = class_match.group(1)
        class_val = CLASS_MAP.get(c, c)
    else:
        class_match = re.search(r'\b(?:class|std|grade)[_\s-]*([ivx]+|\d+)\b', text.lower())
        if class_match:
            c = class_match.group(1)
            class_val = CLASS_MAP.get(c, c)
        else:
            match_roman = re.search(r'\b(ix|x|xi|xii|viii|vii|vi|v|iv|iii|ii|i)\b', fn_lower)
            if match_roman:
                class_val = CLASS_MAP.get(match_roman.group(1))

    if not class_val:
        class_val = "unknown"

    # 2. Detect Subject
    for sub in SUBJECTS:
        if sub in fn_lower:
            subject_val = sub
            if subject_val == "maths": subject_val = "mathematics"
            break
    if not subject_val:
        for sub in SUBJECTS:
            if re.search(rf'\b{sub}\b', text.lower()):
                subject_val = sub
                if subject_val == "maths": subject_val = "mathematics"
                break

    if not subject_val:
        subject_val = "unknown"

    # 3. Detect Chapter (STRICT)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if len(line) > 60 or len(line) < 3:
            continue
            
        chap_match = re.match(r'^(?:chapter|unit)\s*\d+[\s:\.\-]+(.+)$', line, re.IGNORECASE)
        if chap_match:
            candidate = chap_match.group(1).strip()
            if 0 < len(candidate.split()) <= 8:
                chapter_val = candidate
                break
                
        chap_num_match = re.match(r'^(?:chapter|unit)\s*\d+$', line, re.IGNORECASE)
        if chap_num_match:
            for next_line in lines[i+1:i+5]:
                next_line = next_line.strip()
                if next_line and len(next_line.split()) <= 8 and not next_line.isdigit():
                    chapter_val = next_line
                    break
            if chapter_val:
                break

    if not chapter_val:
        fn_clean = re.sub(r'[^a-zA-Z0-9]+', ' ', filename.lower())
        fn_clean = re.sub(r'\b(?:class|std|grade)\s*(?:[ivx]+|\d+)\b', '', fn_clean)
        for sub in SUBJECTS:
            fn_clean = re.sub(rf'\b{sub}\b', '', fn_clean)
        fn_clean = fn_clean.replace('pdf', '').strip()
        
        words = fn_clean.split()
        if 0 < len(words) <= 8 and not any(w.isdigit() for w in words):
            chapter_val = "_".join(words)
        else:
            chapter_val = "full_book"

    return class_val, subject_val, chapter_val

def remove_empty_folders(path):
    deleted = set()
    for dirpath, dirnames, filenames in os.walk(path, topdown=False):
        if not os.listdir(dirpath):
            try:
                os.rmdir(dirpath)
                deleted.add(dirpath)
            except OSError:
                pass

def main():
    print("=== EduSim PDF Normalization Pipeline ===")
    
    os.makedirs(CHAPTERS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    print("[1] Extracting ZIP archives recursively...")
    extract_all_zips(TEXTBOOKS_DIR)
    
    print("[2] Discovering PDFs...")
    all_pdfs = []
    for dirpath, _, files in os.walk(TEXTBOOKS_DIR):
        for file in files:
            if file.lower().endswith('.pdf'):
                all_pdfs.append(os.path.join(dirpath, file))
                
    print(f"    Found {len(all_pdfs)} PDFs.")
    
    print("[3] Removing duplicates & Processing...")
    seen_hashes = set()
    
    report = {
        "total_pdfs_found": len(all_pdfs),
        "duplicates_skipped": 0,
        "failed_pdfs": 0,
        "renamed_pdfs": 0,
        "unknown_metadata": 0
    }
    
    mappings = {}
    
    for pdf_path in all_pdfs:
        filename = os.path.basename(pdf_path)
        
        file_hash = get_file_hash(pdf_path)
        if not file_hash or file_hash in seen_hashes:
            print(f"    [SKIP] Duplicate or unreadable: {filename}")
            report["duplicates_skipped"] += 1
            # Remove duplicate file from disk to save space
            try:
                os.remove(pdf_path)
            except Exception:
                pass
            continue
            
        seen_hashes.add(file_hash)
        
        try:
            c, s, ch = detect_metadata(pdf_path, filename)
            
            if c == "unknown" or s == "unknown":
                report["unknown_metadata"] += 1
                
            clean_c = clean_name(c)
            clean_s = clean_name(s)
            clean_ch = clean_name(ch)
            
            new_name = f"class_{clean_c}_{clean_s}_{clean_ch}.pdf"
            
            counter = 1
            final_name = new_name
            while os.path.exists(os.path.join(CHAPTERS_DIR, final_name)):
                final_name = f"class_{clean_c}_{clean_s}_{clean_ch}_{counter}.pdf"
                counter += 1
                
            out_path = os.path.join(CHAPTERS_DIR, final_name)
            shutil.copy2(pdf_path, out_path)
            
            mappings[filename] = final_name
            report["renamed_pdfs"] += 1
            print(f"    [OK] {filename} -> {final_name}")
            
        except Exception as e:
            print(f"    [ERROR] Failed processing {filename}: {e}")
            report["failed_pdfs"] += 1
            
    print("[4] Generating JSON reports...")
    with open(MAPPING_JSON, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, indent=2)
        
    with open(REPORT_JSON, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        
    print("[5] Cleaning up folders...")
    remove_empty_folders(TEXTBOOKS_DIR)
    
    print("=== Pipeline Complete ===")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
