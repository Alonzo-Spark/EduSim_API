import os
import fitz  # PyMuPDF
import re
import json
from app.rag.heading_parser import parse_chapter_info, parse_section_info, is_valid_topic

CLASS_MAP = {
    "i": "Class 1", "ii": "Class 2", "iii": "Class 3", "iv": "Class 4", "v": "Class 5",
    "vi": "Class 6", "vii": "Class 7", "viii": "Class 8", "ix": "Class 9", "x": "Class 10",
    "xi": "Class 11", "xii": "Class 12",
    "1": "Class 1", "2": "Class 2", "3": "Class 3", "4": "Class 4", "5": "Class 5",
    "6": "Class 6", "7": "Class 7", "8": "Class 8", "9": "Class 9", "10": "Class 10",
    "11": "Class 11", "12": "Class 12"
}

def clean_class_name(raw: str) -> str:
    raw_lower = raw.lower().strip()
    # Match direct digit
    match = re.search(r"class\s*(\d+)", raw_lower)
    if match:
        return f"Class {match.group(1)}"
    # Match roman numeral
    match_roman = re.search(r"\b(ix|x|xi|xii|viii|vii|vi|v|iv|iii|ii|i)\b", raw_lower)
    if match_roman:
        val = match_roman.group(1)
        if val in CLASS_MAP:
            return CLASS_MAP[val]
    return "Class 9" # Default fallback

def clean_subject_name(raw: str) -> str:
    raw_lower = raw.lower()
    if "phys" in raw_lower:
        return "Physics"
    if "chem" in raw_lower:
        return "Chemistry"
    if "biol" in raw_lower or "bio" in raw_lower:
        return "Biology"
    if "math" in raw_lower:
        return "Mathematics"
    if "sci" in raw_lower:
        return "Science"
    if "evs" in raw_lower:
        return "Environmental Studies"
    return "Science" # Default fallback

def extract_meta_from_filename(filename: str):
    """Fallback classifier based on filename heuristics."""
    name_clean = filename.replace("_", " ").replace("-", " ").lower()
    
    # Class detection
    class_val = None
    for key, label in CLASS_MAP.items():
        if f"class {key}" in name_clean or f"class_{key}" in name_clean:
            class_val = label
            break
            
    if not class_val:
        # Match standalone Roman numerals or numbers in filename
        match_roman = re.search(r"\b(ix|x|xi|xii|viii|vii|vi|v|iv)\b", name_clean)
        if match_roman:
            class_val = CLASS_MAP[match_roman.group(1)]
        else:
            match_num = re.search(r"\b(4|5|6|7|8|9|10|11|12)\b", name_clean)
            if match_num:
                class_val = f"Class {match_num.group(1)}"
                
    # Subject detection
    subject_val = None
    if "phys" in name_clean:
        subject_val = "Physics"
    elif "chem" in name_clean:
        subject_val = "Chemistry"
    elif "biol" in name_clean or "bio" in name_clean:
        subject_val = "Biology"
    elif "math" in name_clean:
        subject_val = "Mathematics"
    elif "sci" in name_clean:
        subject_val = "Science"
    elif "evs" in name_clean:
        subject_val = "Environmental Studies"
        
    return class_val, subject_val

class TextbookExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.filename = os.path.basename(pdf_path)
        self.doc = None
        
    def open(self):
        try:
            self.doc = fitz.open(self.pdf_path)
            return True
        except Exception as e:
            print(f"[ERROR] PyMuPDF could not open {self.filename}: {e}")
            return False
            
    def close(self):
        if self.doc:
            self.doc.close()
            
    def detect_class_and_subject(self):
        """Extract first 20 pages text to detect class and subject, using filename as fallback."""
        file_class, file_sub = extract_meta_from_filename(self.filename)
        
        if not self.doc:
            return file_class or "Class 9", file_sub or "Science"
            
        full_text = ""
        limit = min(20, len(self.doc))
        for i in range(limit):
            try:
                full_text += self.doc[i].get_text()
            except Exception:
                pass
                
        # Heuristic search in text
        detected_class = None
        class_matches = re.findall(r"class\s+(?:ix|x|xi|xii|viii|vii|vi|v|\d+)", full_text, re.IGNORECASE)
        if class_matches:
            detected_class = clean_class_name(class_matches[0])
            
        detected_sub = None
        sub_keywords = ["physics", "chemistry", "biology", "science", "mathematics", "maths", "evs"]
        for kw in sub_keywords:
            if re.search(rf"\b{kw}\b", full_text, re.IGNORECASE):
                detected_sub = clean_subject_name(kw)
                break
                
        final_class = detected_class or file_class or "Class 9"
        final_sub = detected_sub or file_sub or "Science"
        return final_class, final_sub

    def extract_chapters_and_topics(self):
        """
        Dual-layer chapter & section discovery:
        1. Scan first 15 pages for 'Contents' index table, parsing numbered lists.
        2. Fallback: Scan headers/lines of every single page recursively.
        """
        chapters = []
        if not self.doc:
            return chapters
            
        # Strategy 1: Table of Contents (TOC) parsing
        toc_text = ""
        toc_pages = []
        for idx in range(min(15, len(self.doc))):
            page_text = self.doc[idx].get_text()
            if "contents" in page_text.lower() or "index" in page_text.lower():
                toc_pages.append(idx)
                toc_text += page_text
                
        # Parse toc_text if found
        current_chapter = None
        if toc_text:
            lines = toc_text.split("\n")
            for line in lines:
                line = line.strip()
                # Try chapter match
                chap_info = parse_chapter_info(line)
                if chap_info:
                    chap_num, chap_name = chap_info
                    # If chapter name is empty, we will populate it
                    current_chapter = {
                        "chapter_number": int(chap_num) if chap_num.isdigit() else chap_num,
                        "chapter_name": chap_name or f"Chapter {chap_num}",
                        "topics": []
                    }
                    chapters.append(current_chapter)
                    continue
                    
                # Try topic match
                sec_info = parse_section_info(line)
                if sec_info and current_chapter:
                    sec_num, sec_name = sec_info
                    if is_valid_topic(sec_name) and sec_name not in current_chapter["topics"]:
                        current_chapter["topics"].append(sec_name)
                        
        # Strategy 2 Fallback: If no chapters found in TOC, scan the entire book page-by-page
        if not chapters:
            current_chapter = None
            for idx in range(len(self.doc)):
                try:
                    page_text = self.doc[idx].get_text()
                    lines = page_text.split("\n")
                    for line in lines:
                        line = line.strip()
                        chap_info = parse_chapter_info(line)
                        if chap_info:
                            chap_num, chap_name = chap_info
                            # Clean up chap_name if it contains trailing text
                            chap_name = chap_name.split("  ")[0].strip()
                            current_chapter = {
                                "chapter_number": int(chap_num) if chap_num.isdigit() else chap_num,
                                "chapter_name": chap_name or f"Chapter {chap_num}",
                                "topics": []
                            }
                            # Check if chapter already added to avoid duplicates
                            if not any(c["chapter_name"] == current_chapter["chapter_name"] for c in chapters):
                                chapters.append(current_chapter)
                            continue
                            
                        sec_info = parse_section_info(line)
                        if sec_info and current_chapter:
                            sec_num, sec_name = sec_info
                            # Get correct chapter reference from our active chapters list
                            active_chap = next((c for c in chapters if c["chapter_name"] == current_chapter["chapter_name"]), None)
                            if active_chap and is_valid_topic(sec_name) and sec_name not in active_chap["topics"]:
                                active_chap["topics"].append(sec_name)
                except Exception:
                    pass
                    
        # Final cleanups of duplicates & placeholder lists
        cleaned_chapters = []
        for c in chapters:
            if not c["chapter_name"] or c["chapter_name"].strip() == "" or c["chapter_name"].isdigit():
                continue
            # If no topics extracted, let's provision standard textbook chapter sub-headings
            if not c["topics"]:
                c["topics"] = ["Introduction", "Concepts Overview", "Summary Practice"]
            cleaned_chapters.append(c)
            
        # Self-healing standard fallback mapping for NCERT syllabus if PDF was scanned or failed parsing
        if not cleaned_chapters:
            cl, subj = self.detect_class_and_subject()
            fallback_chapters = []
            
            if "Class 9" in cl:
                if subj == "Physics":
                    fallback_chapters = [
                        {"chapter_number": 8, "chapter_name": "Motion", "topics": ["Introduction", "Describing Motion", "Speed and Velocity", "Rate of Change of Velocity", "Graphical Representation of Motion", "Equations of Motion", "Uniform Circular Motion"]},
                        {"chapter_number": 9, "chapter_name": "Force and Laws of Motion", "topics": ["Introduction", "Balanced and Unbalanced Forces", "First Law of Motion", "Inertia and Mass", "Second Law of Motion", "Third Law of Motion", "Conservation of Momentum"]},
                        {"chapter_number": 10, "chapter_name": "Gravitation", "topics": ["Introduction", "Gravitation", "Universal Law of Gravitation", "Free Fall", "Acceleration due to Gravity", "Mass and Weight", "Thrust and Pressure", "Archimedes' Principle", "Relative Density"]},
                        {"chapter_number": 11, "chapter_name": "Work and Energy", "topics": ["Introduction", "Work", "Energy", "Kinetic Energy", "Potential Energy", "Law of Conservation of Energy", "Rate of Doing Work"]},
                        {"chapter_number": 12, "chapter_name": "Sound", "topics": ["Introduction", "Production of Sound", "Propagation of Sound", "Reflection of Sound", "Range of Hearing", "Ultrasound", "Structure of Human Ear"]}
                    ]
                elif subj == "Biology":
                    fallback_chapters = [
                        {"chapter_number": 5, "chapter_name": "The Fundamental Unit of Life", "topics": ["Introduction", "What are Living Organisms Made of", "Cell Structure", "Plasma Membrane", "Cell Wall", "Nucleus", "Cytoplasm", "Cell Organelles"]},
                        {"chapter_number": 6, "chapter_name": "Tissues", "topics": ["Introduction", "Are Plants and Animals Made of Same Tissues", "Plant Tissues", "Meristematic Tissue", "Permanent Tissue", "Animal Tissues", "Epithelial Tissue", "Connective Tissue", "Muscular Tissue", "Nervous Tissue"]}
                    ]
                elif subj == "Mathematics":
                    fallback_chapters = [
                        {"chapter_number": 1, "chapter_name": "Number Systems", "topics": ["Introduction", "Irrational Numbers", "Real Numbers and Decimal Expansions", "Operations on Real Numbers", "Laws of Exponents"]},
                        {"chapter_number": 2, "chapter_name": "Polynomials", "topics": ["Introduction", "Polynomials in One Variable", "Zeroes of a Polynomial", "Remainder Theorem", "Factorisation of Polynomials", "Algebraic Identities"]}
                    ]
            elif "Class 10" in cl:
                if subj == "Physics":
                    fallback_chapters = [
                        {"chapter_number": 10, "chapter_name": "Light - Reflection and Refraction", "topics": ["Introduction", "Reflection of Light", "Spherical Mirrors", "Image Formation", "Mirror Formula", "Refraction of Light", "Refractive Index", "Lens Formula", "Power of Lens"]},
                        {"chapter_number": 12, "chapter_name": "Electricity", "topics": ["Introduction", "Electric Current and Circuit", "Electric Potential", "Ohm's Law", "Factors affecting Resistance", "Resistors in Series and Parallel", "Heating Effect of Electric Current", "Electric Power"]}
                    ]
                elif subj == "Mathematics":
                    fallback_chapters = [
                        {"chapter_number": 3, "chapter_name": "Pair of Linear Equations in Two Variables", "topics": ["Introduction", "Graphical Method of Solution", "Algebraic Methods of Solving", "Substitution Method", "Elimination Method"]}
                    ]
            
            # General fallback if subject not explicitly configured in dictionary
            if not fallback_chapters:
                fallback_chapters = [
                    {"chapter_number": 1, "chapter_name": "Syllabus Core Concepts", "topics": ["Overview", "Foundational Principles", "Summary Exercise"]}
                ]
            cleaned_chapters = fallback_chapters
            
        return cleaned_chapters
