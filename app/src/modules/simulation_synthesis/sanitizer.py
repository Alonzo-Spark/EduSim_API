import json
import re

def sanitize_json(raw_output: str) -> dict:
    """
    Cleans and parses raw JSON output from the LLM.
    Strips markdown code fences and handles potential trailing characters.
    """
    cleaned = raw_output.strip()
    
    # Remove markdown code fences if present
    fenced = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1).strip()
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse AI output as JSON: {e}\nRaw output: {raw_output}")
    except Exception as e:
        raise ValueError(f"An unexpected error occurred while parsing JSON: {e}")
