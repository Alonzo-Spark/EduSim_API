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
# Differences

| Feature | Concept A | Concept B |
|---|---|---|

# Summary

## Conclusion
"""
    elif intent == "definition":
        return """
# Definition

## Concise Meaning

# Key Points

## Important Highlights
"""
    elif intent == "relationship":
        return """
# Relationship Explanation

## Connecting Concepts

# Connecting Formulas / Principles

## Mathematical or Theoretical Link
"""
    elif intent == "advantages":
        return """
# Advantages and Disadvantages

| Type | Description |
|---|---|
"""
    elif intent == "examples":
        return """
# Practical Examples

## Daily Life Applications

## Industry Usage
"""
    elif intent == "formula":
        return """
# Mathematical Formulas

## Main Formula

## Formula Explanation

# Derivation

## Step-by-Step Derivation
"""
    elif intent == "characteristics":
        return """
# Characteristics and Features

## Important Properties
"""
    elif intent == "process":
        return """
# Process / Working Mechanism

## Step-by-Step Explanation

# Important Components

## Key Elements Involved
"""
    elif intent == "numerical":
        return """
# Problem Solution

## Given Data

## Formulas Used

## Step-by-Step Calculation

## Final Answer
"""
    else:
        # Fallback to the detailed educational textbook notes structure
        return fallback_structure
