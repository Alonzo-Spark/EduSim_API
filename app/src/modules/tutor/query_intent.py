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
    """Returns the template structure based on intent.
    
    General educational intents (definition, relationship, characteristics, process)
    use the full topic-type fallback structure to ensure complete textbook-style output
    with Advantages, Disadvantages, Summary, and Suggested Questions.
    
    Only specialized intents (comparison, numerical, examples, formula, advantages)
    use custom minimal skeletons.
    """
    if intent == "comparison":
        return """
# Differences

| Feature | Concept A | Concept B |
|---|---|---|

# Summary

## Conclusion
"""
    elif intent == "advantages":
        return """
# Advantages

# Disadvantages

# Summary
"""
    elif intent == "numerical":
        return """
# Problem Solution

## Given Data

## Formulas Used

## Step-by-Step Calculation

## Final Answer

## Interpretation
"""
    elif intent == "examples":
        return """
# Practical Examples

## Daily Life Applications

## Industry Usage

# Summary
"""
    elif intent == "formula":
        return """
# Mathematical Formulas

## Main Formula

## Formula Explanation

# Derivation

## Step-by-Step Derivation

# Summary
"""
    else:
        # For definition, relationship, characteristics, process, detailed, textbook_strict,
        # and any other intent: use the full topic-type structure which includes
        # Characteristics, Formulas, Advantages, Disadvantages, Applications, Summary,
        # and Suggested Questions.
        return fallback_structure
