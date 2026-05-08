import re
from typing import Optional
from .models import SimulationTopic


# Topic patterns with subject detection
TOPIC_PATTERNS = {
    # Physics topics
    "projectile motion": {"subject": "physics", "keywords": ["projectile", "launch", "trajectory", "angle", "range", "parabolic"]},
    "pendulum": {"subject": "physics", "keywords": ["pendulum", "swing", "oscillat", "bob", "period"]},
    "circular motion": {"subject": "physics", "keywords": ["circular", "centripetal", "angular velocity", "orbit", "centrifug"]},
    "momentum": {"subject": "physics", "keywords": ["momentum", "collision", "elastic", "inelastic", "impulse"]},
    "waves": {"subject": "physics", "keywords": ["wave", "frequency", "wavelength", "amplitude", "oscillation", "superposition"]},
    "refraction": {"subject": "physics", "keywords": ["refraction", "lens", "prism", "light", "snell", "critical angle"]},
    "simple harmonic motion": {"subject": "physics", "keywords": ["harmonic", "shm", "spring", "oscillate", "restoring force"]},
    "gravity": {"subject": "physics", "keywords": ["gravity", "gravitational", "newton", "force", "attraction"]},
    
    # Chemistry topics
    "molecular structure": {"subject": "chemistry", "keywords": ["molecule", "atom", "bond", "electron", "orbital", "structure"]},
    "chemical reaction": {"subject": "chemistry", "keywords": ["reaction", "oxidation", "reduction", "catalyst", "equilibrium"]},
    "acid-base": {"subject": "chemistry", "keywords": ["acid", "base", "ph", "buffer", "titration"]},
    "electron configuration": {"subject": "chemistry", "keywords": ["electron", "orbital", "configuration", "shell", "subshell"]},
    "bonding": {"subject": "chemistry", "keywords": ["bond", "ionic", "covalent", "metallic", "hydrogen bond"]},
    
    # Astronomy topics
    "orbital mechanics": {"subject": "astronomy", "keywords": ["orbit", "gravity", "planet", "kepler", "satellite", "elliptical"]},
    "stellar evolution": {"subject": "astronomy", "keywords": ["star", "sun", "nuclear", "fusion", "lifecycle", "main sequence"]},
    "galaxy": {"subject": "astronomy", "keywords": ["galaxy", "black hole", "dark matter", "universe", "cosmic"]},
    
    # Biology topics
    "cell biology": {"subject": "biology", "keywords": ["cell", "mitochondria", "chloroplast", "organelle", "membrane"]},
    "photosynthesis": {"subject": "biology", "keywords": ["photosynthesis", "chlorophyll", "glucose", "energy", "atp"]},
    "dna": {"subject": "biology", "keywords": ["dna", "gene", "rna", "protein", "chromosome", "helix"]},
    
    # Mathematics topics
    "functions": {"subject": "mathematics", "keywords": ["function", "graph", "equation", "polynomial", "linear", "quadratic"]},
    "calculus": {"subject": "mathematics", "keywords": ["calculus", "derivative", "integral", "limit", "rate"]},
    "trigonometry": {"subject": "mathematics", "keywords": ["trigonometry", "sine", "cosine", "angle", "triangle"]},
}

COMPLEXITY_KEYWORDS = {
    "beginner": ["simple", "basic", "introductory", "easy", "visual", "intuitive"],
    "medium": ["explain", "show", "demonstrate", "simulate", "visualize"],
    "advanced": ["complex", "detailed", "comprehensive", "advanced", "mathematical", "rigorous"],
}

GRADE_LEVELS = {
    "class 9": "9",
    "class 10": "10",
    "class 11": "11",
    "class 12": "12",
    "grade 9": "9",
    "grade 10": "10",
    "grade 11": "11",
    "grade 12": "12",
    "college": "college",
    "university": "college",
    "high school": "10",
    "secondary": "10",
}


def analyze_prompt(prompt: str) -> SimulationTopic:
    """
    Analyze a user prompt to extract topic, subject, complexity, and grade level.
    
    Args:
        prompt: Natural language prompt from user
        
    Returns:
        SimulationTopic with detected information
    """
    prompt_lower = prompt.lower()
    
    # Detect topic
    detected_topic: Optional[str] = None
    detected_subject: Optional[str] = None
    
    for topic, info in TOPIC_PATTERNS.items():
        if any(kw in prompt_lower for kw in info["keywords"]):
            detected_topic = topic
            detected_subject = info["subject"]
            break
    
    # Fallback to subject detection
    if not detected_subject:
        if any(word in prompt_lower for word in ["physics", "motion", "force", "velocity", "wave", "light"]):
            detected_subject = "physics"
        elif any(word in prompt_lower for word in ["chemistry", "molecule", "atom", "bond", "reaction", "element"]):
            detected_subject = "chemistry"
        elif any(word in prompt_lower for word in ["astronomy", "space", "planet", "star", "galaxy", "orbit"]):
            detected_subject = "astronomy"
        elif any(word in prompt_lower for word in ["biology", "cell", "gene", "dna", "organism", "life"]):
            detected_subject = "biology"
        elif any(word in prompt_lower for word in ["math", "equation", "function", "graph", "algebra", "geometry"]):
            detected_subject = "mathematics"
        else:
            detected_subject = "physics"  # Default
    
    # Detect complexity
    complexity = "medium"  # Default
    for level, keywords in COMPLEXITY_KEYWORDS.items():
        if any(kw in prompt_lower for kw in keywords):
            complexity = level
            break
    
    # Detect grade level
    grade_level: Optional[str] = None
    for grade_pattern, grade_value in GRADE_LEVELS.items():
        if grade_pattern in prompt_lower:
            grade_level = grade_value
            break
    
    # Create result topic
    topic_obj = SimulationTopic(
        topic=detected_topic or f"{detected_subject.title()} Simulation",
        subject=detected_subject,
        subtopic=None,
        complexity=complexity,
        grade_level=grade_level,
    )
    
    return topic_obj


def generate_title_from_topic(topic: SimulationTopic) -> str:
    """Generate a descriptive title from detected topic."""
    parts = [topic.topic]
    
    if topic.complexity != "medium":
        parts.append(f"({topic.complexity.capitalize()} Level)")
    
    if topic.grade_level:
        parts.append(f"Grade {topic.grade_level}")
    
    return " ".join(parts)


def extract_learning_objectives(prompt: str, topic: SimulationTopic) -> list[str]:
    """
    Extract or infer learning objectives from prompt and topic.
    
    Args:
        prompt: User prompt
        topic: Detected topic information
        
    Returns:
        List of learning objectives
    """
    objectives = []
    prompt_lower = prompt.lower()
    
    # Add topic-specific objectives
    objectives.append(f"Understand and visualize {topic.topic.lower()}")
    
    # Add based on keywords
    if any(word in prompt_lower for word in ["explain", "understand", "learn"]):
        objectives.append("Build conceptual understanding through interactive exploration")
    
    if any(word in prompt_lower for word in ["derive", "formula", "equation", "calculate"]):
        objectives.append("Apply mathematical formulas and calculations")
    
    if any(word in prompt_lower for word in ["visualize", "see", "observe", "watch"]):
        objectives.append("Observe physical phenomena through visual simulation")
    
    if any(word in prompt_lower for word in ["experiment", "investigate", "test", "vary"]):
        objectives.append("Conduct virtual experiments and hypothesis testing")
    
    if any(word in prompt_lower for word in ["compare", "contrast", "different", "effect"]):
        objectives.append("Compare different scenarios and analyze effects")
    
    return objectives or ["Develop understanding through interactive simulation"]


def extract_related_concepts(topic: SimulationTopic) -> list[str]:
    """
    Extract related concepts based on topic.
    
    Args:
        topic: Detected topic information
        
    Returns:
        List of related concepts
    """
    related_map = {
        "projectile motion": ["kinematics", "vectors", "gravity", "parabolic trajectory"],
        "pendulum": ["simple harmonic motion", "periodic motion", "restoring force", "energy"],
        "circular motion": ["centripetal force", "angular velocity", "tangential velocity"],
        "momentum": ["conservation laws", "forces", "impulse-momentum theorem"],
        "waves": ["superposition", "interference", "diffraction", "resonance"],
        "refraction": ["reflection", "snell's law", "critical angle", "total internal reflection"],
        "molecular structure": ["bonding", "electron configuration", "quantum mechanics"],
        "chemical reaction": ["equilibrium", "rate of reaction", "activation energy"],
        "orbital mechanics": ["kepler's laws", "escape velocity", "gravitational force"],
        "cell biology": ["photosynthesis", "respiration", "protein synthesis"],
    }
    
    topic_lower = topic.topic.lower()
    for key, related in related_map.items():
        if key in topic_lower:
            return related
    
    # Default general concepts
    return ["Conservation Laws", "Energy", "Forces", "Motion"]
