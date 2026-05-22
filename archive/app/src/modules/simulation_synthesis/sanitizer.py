import json
import re

def sanitize_json(raw_output: str) -> dict:
    """
    Cleans and parses raw JSON output from the LLM.
    Handles markdown code fences and extracts the first valid JSON structure.
    """
    cleaned = raw_output.strip()
    
    # Strategy 1: Look for markdown code fences
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    else:
        # Strategy 2: Extract content between the first { and last }
        # This handles cases where the AI adds text before or after the JSON
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end+1]
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Fallback: Provide a snippet of the failed parsing for debugging
        raise ValueError(f"Failed to parse AI output as JSON: {e}\nCleaned snippet: {cleaned[:100]}...")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred while parsing JSON: {e}")
