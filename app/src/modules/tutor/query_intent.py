import re

def detect_query_intent(question: str) -> str:
    """Detects the specific intent behind a user's question."""
    q = question.lower()
    
    # 1. Difference / Comparison
    if re.search(r'\b(difference|compare|vs|versus|distinguish)\b', q):
        return "comparison"
        
    # 2. Definition
    if re.search(r'\b(what is|define|definition|meaning of)\b', q):
        return "definition"
        
    # 3. Relationship
    if re.search(r'\b(relationship|relation|relate|connection)\b', q):
        return "relationship"
        
    # 4. Advantages / Disadvantages
    if re.search(r'\b(advantage|disadvantage|pros|cons|benefit|drawback)\b', q):
        return "advantages"
        
    # 5. Real-world Examples
    if re.search(r'\b(example|real world|practical application|industry example)\b', q):
        return "examples"
        
    # 6. Formula / Derivation
    if re.search(r'\b(formula|derive|derivation|equation)\b', q):
        return "formula"
        
    # 7. Characteristics / Features
    if re.search(r'\b(characteristic|feature|property|properties|traits)\b', q):
        return "characteristics"
        
    # 8. Process / Working
    if re.search(r'\b(working|process|how does|mechanism|steps of)\b', q):
        return "process"
        
    # 9. Numerical / Solve
    if re.search(r'\b(solve|calculate|numerical|find the value|compute)\b', q):
        return "numerical"
        
    # 10. Textbook Strict
    if re.search(r'\b(from textbook|according to textbook|textbook says|exact textbook)\b', q):
        return "textbook_strict"
        
    # 11. Detailed Explanation (Fallback)
    return "detailed"

def get_intent_structure(intent: str, fallback_structure: str) -> str:
    """Returns the template structure strictly based on intent."""
    if intent == "comparison":
        return """
# Introduction

## Definition

## Key Concepts

# Characteristics

## Important Properties
(Provide a comparison table of features between the concepts here)

# Summary

## Key Takeaways
"""
    elif intent == "definition":
        return """
# Introduction

## Definition

## Key Concepts
"""
    elif intent == "relationship":
        return """
# Introduction

## Definition

## Key Concepts

# Formula

## Main Formula

## Formula Explanation
"""
    elif intent == "advantages":
        return """
# Introduction

## Definition

# Characteristics

## Important Properties
(Provide an advantages and disadvantages markdown table here)

# Summary

## Key Takeaways
"""
    elif intent == "examples":
        return """
# Introduction

## Definition

# Example

## Solved Numerical

# Applications

## Real-World Applications

## Industry Usage
"""
    elif intent == "formula":
        return """
# Introduction

## Definition

# Formula

## Main Formula

## Formula Explanation

## Derivation
"""
    elif intent == "characteristics":
        return """
# Introduction

## Definition

# Characteristics

## Important Properties
"""
    elif intent == "process":
        return """
# Introduction

## Definition

## Key Concepts

# Characteristics

## Important Properties
"""
    elif intent == "numerical":
        return """
# Introduction

## Definition

# Formula

## Main Formula

# Example

## Solved Numerical
"""
    else:
        # Fallback to the detailed educational textbook notes structure
        return fallback_structure
