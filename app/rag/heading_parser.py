import re

# Regex for matching chapter headers: "Chapter 1", "CHAPTER IV", "Chapter 2: Force"
CHAPTER_PATTERN = re.compile(
    r"^\s*(?:Chapter|CHAPTER|CH)\s+([IVXLCDM]+|\d+)[\s:.-]*(.*)$", re.IGNORECASE
)

# Regex for matching section headings: "8.1 Motion", "1.2.3 Speed", "9.4 Newton's Laws"
SECTION_PATTERN = re.compile(
    r"^\s*(\d+(?:\.\d+)+)\s+(.*)$"
)

# Heuristic list of common textbook section terms to ignore
IGNORE_KEYWORDS = {
    "summary", "exercises", "questions", "activity", "introduction", "conclusion", 
    "index", "appendix", "glossary", "answers", "preface", "acknowledgement"
}

def parse_chapter_info(line: str):
    """
    Tries to match a line to a chapter header.
    Returns (chapter_number_str, chapter_name) or None.
    """
    match = CHAPTER_PATTERN.match(line.strip())
    if match:
        chapter_num = match.group(1).strip()
        chapter_name = match.group(2).strip()
        # If name is blank, we can resolve it on subsequent lines
        return chapter_num, chapter_name
    return None

def parse_section_info(line: str):
    """
    Tries to match a line to a numbered topic section (e.g., '8.2 Acceleration').
    Returns (section_number_str, section_name) or None.
    """
    match = SECTION_PATTERN.match(line.strip())
    if match:
        sec_num = match.group(1).strip()
        sec_name = match.group(2).strip()
        
        # Clean trailing periods or random symbols from the name
        sec_name = re.sub(r"^[.:\s-]+|[.:\s-]+$", "", sec_name).strip()
        
        # Ignore common non-topic headers like 'Summary' or 'Exercises'
        if sec_name.lower() in IGNORE_KEYWORDS or len(sec_name) < 3:
            return None
            
        return sec_num, sec_name
    return None

def is_valid_topic(text: str) -> bool:
    """Checks if a heading text is a clean topic rather than a paragraph."""
    text_clean = text.strip()
    if not text_clean or len(text_clean) > 80:
        return False
    if text_clean.lower() in IGNORE_KEYWORDS:
        return False
    # If the text has lots of lower-case letters but no capitalization, it is probably general text
    if sum(1 for c in text_clean if c.isupper()) == 0 and len(text_clean) > 10:
        return False
    return True
