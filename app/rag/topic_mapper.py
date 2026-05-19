import re
import difflib

# Topic synonym mappings to align informal terms with NCERT syllabus terms
TOPIC_SYNONYMS = {
    "first law": "Newton's First Law of Motion",
    "second law": "Newton's Second Law of Motion",
    "third law": "Newton's Third Law of Motion",
    "f=ma": "Newton's Second Law of Motion",
    "friction": "Frictional Force",
    "gravity": "Gravitation",
    "g": "Acceleration due to Gravity",
    "kinetic energy": "Work and Kinetic Energy",
    "potential energy": "Potential Energy",
    "speed": "Speed and Velocity",
    "velocity": "Speed and Velocity",
    "motion": "Equations of Motion",
}

def clean_term(term: str) -> str:
    """Standardizes string casing and spacing."""
    return re.sub(r"\s+", " ", term.strip().lower())

def find_best_canonical_match(query_topic: str, canonical_topics: list[str]) -> str | None:
    """
    Finds the closest matching canonical topic name using string similarity.
    Returns the exact match or None.
    """
    clean_query = clean_term(query_topic)
    
    # 1. Direct Synonyms mapping
    for informal, canonical in TOPIC_SYNONYMS.items():
        if informal in clean_query:
            # Check if this exact canonical name exists in the list
            matched = difflib.get_close_matches(canonical, canonical_topics, n=1, cutoff=0.7)
            if matched:
                return matched[0]

    # 2. Exact word search match
    for topic in canonical_topics:
        if clean_term(topic) in clean_query or clean_query in clean_term(topic):
            return topic

    # 3. Fuzzy string distance comparison
    matches = difflib.get_close_matches(query_topic, canonical_topics, n=1, cutoff=0.55)
    if matches:
        return matches[0]
        
    return None
