import re

def detect_topic_type(query: str, context: str = "") -> str:
    """Classifies a topic into allowed educational types based on query and context."""
    text = (query + " " + context).lower()
    
    keywords = {
        "physics": ["force", "motion", "gravity", "velocity", "acceleration", "speed", "distance", "displacement", "momentum", "friction", "inertia", "newton", "work", "energy", "power", "wave", "sound", "frequency", "amplitude", "wavelength", "echo", "ultrasound", "light", "reflection", "refraction", "mirror", "lens", "optics", "prism", "electricity", "voltage", "resistance", "circuit", "battery", "magnet", "temperature", "heat", "thermal", "conduction", "convection", "radiation", "atom", "nuclear", "radioactivity", "electron", "proton", "neutron"],
        "maths": ["algebra", "equation", "polynomial", "geometry", "triangle", "circle", "rectangle", "square", "perimeter", "area", "volume", "trigonometry", "sin", "cos", "tan", "angle", "calculus", "derivative", "integration", "integral", "differentiation", "limit", "coordinate geometry", "graph", "slope", "statistics", "probability", "mean", "median", "mode", "matrix", "vector", "percentage", "ratio", "proportion", "profit", "loss", "interest", "number system", "prime number", "rational number"],
        "chemistry": ["molecule", "compound", "element", "mixture", "solution", "reaction", "oxidation", "reduction", "combustion", "acid", "base", "ph", "neutralization", "bond", "ionic", "covalent", "periodic table", "metal", "nonmetal", "solid", "liquid", "gas", "evaporation", "condensation", "hydrocarbon", "carbon", "organic", "mole", "molarity"],
        "biology": ["cell", "nucleus", "mitochondria", "dna", "gene", "genetics", "chromosome", "heredity", "heart", "brain", "lungs", "kidney", "digestive", "respiratory", "circulatory", "plant", "photosynthesis", "transpiration", "animal", "vertebrate", "invertebrate", "ecosystem", "food chain", "environment", "biodiversity", "respiration", "nutrition", "reproduction", "bacteria", "virus", "fungi", "evolution", "adaptation", "disease", "immunity", "vaccine"],
        "history": ["history", "war", "battle", "empire", "dynasty", "king", "queen", "revolution", "movement", "treaty", "civilization", "ancient", "medieval", "modern", "gandhi", "independence", "rebellion", "century", "era", "freedom"],
        "social_science": ["geography", "civics", "economics", "constitution", "democracy", "government", "parliament", "election", "rights", "duties", "citizen", "population", "resource", "agriculture", "industry", "trade", "transport"]
    }
    
    scores = {topic: sum(1 for k in kws if re.search(r'\b' + k + r'\b', text)) for topic, kws in keywords.items()}
    
    best_match = max(scores, key=scores.get)
    if scores[best_match] == 0:
        return "general"
        
    return best_match

def get_dynamic_sections(topic_type: str) -> str:
    """Returns formatting sections based on the detected topic type."""
    
    base_structure = """
# Introduction

## Definition

## Key Concepts
"""

    advantages_structure = """
---

# Advantages and Disadvantages

| Type | Description |
|---|---|
"""
    
    applications_structure = """
---

# Applications

## Real-World Applications

## Industry Usage
"""

    summary_structure = """
---

# Important Notes

## Key Takeaways

---

# Summary

## Quick Revision Points

---

# Suggested Questions

1. Question 1
2. Question 2
3. Question 3
"""

    if topic_type in ["physics"]:
        specific_structure = """
---

# Characteristics

## Important Properties

---

# Mathematical Formulas

## Main Formula

## Formula Explanation

## Derivation

---

# Detailed Example

## Solved Numerical
"""
        return base_structure + specific_structure + advantages_structure + applications_structure + summary_structure

    elif topic_type in ["maths"]:
        specific_structure = """
---

# Mathematical Equations

## Core Equation

## Proof / Derivation

---

# Detailed Example

## Step-by-Step Calculation

## Common Mistakes
"""
        return base_structure + specific_structure + applications_structure + summary_structure

    elif topic_type in ["chemistry"]:
        specific_structure = """
---

# Chemical Properties

## Characteristics

---

# Chemical Reactions and Formulas

## Main Reaction / Formula

## Explanation
"""
        return base_structure + specific_structure + advantages_structure + applications_structure + summary_structure

    elif topic_type in ["biology"]:
        specific_structure = """
---

# Characteristics and Processes

## Important Properties

## Biological Mechanisms

---

# Structure and Diagram Description

## Components
"""
        return base_structure + specific_structure + advantages_structure + applications_structure + summary_structure

    elif topic_type in ["history", "social_science"]:
        specific_structure = """
---

# Historical Context / Background

## Timeline of Events

---

# Key Figures and Movements

## Significant Contributions

---

# Impact and Significance

## Short-term Impact

## Long-term Consequences
"""
        return base_structure + specific_structure + summary_structure

    else:
        # General topics
        specific_structure = """
---

# Characteristics

## Important Properties

## Types
"""
        return base_structure + specific_structure + advantages_structure + applications_structure + summary_structure
