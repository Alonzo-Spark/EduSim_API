import os
import zipfile
import shutil

TEXTBOOKS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "textbooks"))

def extract_zip(zip_path, extract_to):
    """Safely extract a zip file preserving folder structure."""
    try:
        print(f"[INFO] Extracting {os.path.basename(zip_path)} -> {extract_to} ...")
        os.makedirs(extract_to, exist_ok=True)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"[OK] Successfully extracted {os.path.basename(zip_path)}.")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to extract {os.path.basename(zip_path)}: {e}")
        return False

def scan_and_extract_recursive(target_dir):
    """Scan directory recursively for ZIP archives and extract them."""
    has_new_extractions = False
    
    # We list all zip files in the target directory recursively
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if file.lower().endswith(".zip"):
                zip_path = os.path.join(root, file)
                # Name the extraction directory after the zip file
                dir_name = os.path.splitext(file)[0]
                extract_to = os.path.join(root, dir_name)
                
                # Check if we already extracted this zip file
                if os.path.exists(extract_to) and len(os.listdir(extract_to)) > 0:
                    continue
                
                success = extract_zip(zip_path, extract_to)
                if success:
                    has_new_extractions = True
                    
    # If we extracted new files, they might contain nested ZIPs, so we recurse once more
    if has_new_extractions:
        print("[INFO] Rescanning for nested archives...")
        scan_and_extract_recursive(target_dir)

def main():
    print(f"=== Starting Archive Extraction Pipeline ===")
    print(f"Textbook Directory: {TEXTBOOKS_DIR}")
    if not os.path.exists(TEXTBOOKS_DIR):
        print(f"[ERROR] Target directory does not exist: {TEXTBOOKS_DIR}")
        return
        
    scan_and_extract_recursive(TEXTBOOKS_DIR)
    print("=== Extraction Pipeline Finished successfully! ===")

if __name__ == "__main__":
    main()
