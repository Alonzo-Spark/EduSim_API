import re
from app.rag.curriculum_index import CurriculumIndex

# Keywords commonly indicating a request for specific topics
CLEANUP_REGEX = re.compile(r"\b(?:what|why|how|explain|derive|define|formula|sheet|simulation|solve|problem|example|of|the|a|an|in|on|with|to|is|are|was|were)\b", re.IGNORECASE)

def extract_search_terms(query: str) -> list[str]:
    """Cleans up the query to extract scientific nouns or core terms."""
    # Remove punctuation
    query_clean = re.sub(r"[^\w\s-]", "", query)
    
    # Split into words
    words = query_clean.split()
    
    # Filter out stopwords/common words
    filtered_words = [w for w in words if not CLEANUP_REGEX.match(w) and len(w) > 2]
    
    # Build candidate phrases (N-grams)
    phrases = []
    
    # Try the full string minus stopwords first
    if len(filtered_words) > 1:
        phrases.append(" ".join(filtered_words))
        
    # Bigrams
    for i in range(len(filtered_words) - 1):
        phrases.append(f"{filtered_words[i]} {filtered_words[i+1]}")
        
    # Unigrams
    phrases.extend(filtered_words)
    
    return phrases

def infer_curriculum_context(query: str) -> dict:
    """
    Analyzes free-text user query, extracts core topics,
    and returns matching canonical NCERT curriculum coordinate paths.
    """
    index = CurriculumIndex()
    
    # 1. Extract potential candidate phrases from the query
    candidates = extract_search_terms(query)
    
    # 2. Query the curriculum graph index for each candidate
    for candidate in candidates:
        match = index.lookup_topic(candidate)
        if match:
            # Found canonical syllabus node! Return coordinates
            return {
                "class": match.get("class"),
                "subject": match.get("subject"),
                "chapter": match.get("chapter"),
                "topic": match.get("topic")
            }
            
    # Graceful fallback: return empty fields (retriever falls back to full vector search)
    return {
        "class": None,
        "subject": None,
        "chapter": None,
        "topic": None
    }
