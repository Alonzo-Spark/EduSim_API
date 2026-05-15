import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from rag.generator import generate_llm_text
from utils.usage_tracker import get_total_usage

def test_usage_tracking():
    print("Testing Usage Tracking...")
    
    # Initial usage
    initial_usage = get_total_usage()
    print(f"Initial Usage: {initial_usage}")
    
    # Mock some usage if possible or just run a real one (fastest is to use a dummy response but the generator calls the real API)
    # I'll just manually call log_usage to verify the tracker works
    from utils.usage_tracker import log_usage
    log_usage("test-model", 10, 20, 30)
    
    # New usage
    new_usage = get_total_usage()
    print(f"New Usage: {new_usage}")
    
    if new_usage["total_tokens"] > initial_usage["total_tokens"]:
        print("✅ Usage tracking works!")
    else:
        print("❌ Usage tracking failed!")

if __name__ == "__main__":
    test_usage_tracking()
