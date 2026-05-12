import re


def detect_subject(query: str) -> str:
    """
    Lightweight keyword-based subject routing to avoid LLM overhead.
    Returns: 'physics', 'chemistry', or 'maths'. Defaults to 'physics'.
    """
    q = query.lower()
    
    # Physics keywords
    physics_keywords = [
        "force", "motion", "gravity", "velocity", "acceleration", 
        "newton", "momentum", "energy", "power", "work", 
        "optics", "light", "sound", "wave", "current", "voltage"
    ]
    
    # Chemistry keywords
    chemistry_keywords = [
        "atom", "molecule", "bond", "reaction", "acid", "base",
        "ph", "electron", "proton", "neutron", "periodic table",
        "molar", "oxidation", "reduction", "gas law", "compound"
    ]
    
    # Maths keywords
    maths_keywords = [
        "algebra", "geometry", "calculus", "trigonometry", "equation",
        "polynomial", "derivative", "integral", "matrix", "vector",
        "probability", "statistics", "triangle", "circle", "area"
    ]
    
    # Simple scoring
    physics_score = sum(1 for k in physics_keywords if k in q)
    chemistry_score = sum(1 for k in chemistry_keywords if k in q)
    maths_score = sum(1 for k in maths_keywords if k in q)
    
    scores = {
        "physics": physics_score,
        "chemistry": chemistry_score,
        "maths": maths_score
    }
    
    best_match = max(scores, key=scores.get)
    
    # Default to physics if no strong match
    if scores[best_match] == 0:
        return "physics"
        
    return best_match
