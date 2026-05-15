import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

USAGE_FILE = Path("data/usage_logs.json")
_log_lock = Lock()

def log_usage(model: str, prompt_tokens: int, completion_tokens: int, total_tokens: int):
    """Logs LLM token usage to a JSON file."""
    print(f"DEBUG: [LLM Usage] Model: {model} | Prompt: {prompt_tokens} | Completion: {completion_tokens} | Total: {total_tokens}")
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens
    }

    with _log_lock:
        data = []
        if USAGE_FILE.exists():
            try:
                with open(USAGE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = []
        
        data.append(entry)
        
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def get_total_usage():
    """Calculates total token usage across all logs."""
    if not USAGE_FILE.exists():
        return {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "requests": 0}
    
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "requests": 0}

    totals = {
        "total_tokens": sum(entry.get("total_tokens", 0) for entry in data),
        "prompt_tokens": sum(entry.get("prompt_tokens", 0) for entry in data),
        "completion_tokens": sum(entry.get("completion_tokens", 0) for entry in data),
        "requests": len(data)
    }
    return totals
