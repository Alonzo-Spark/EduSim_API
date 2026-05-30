import os

brain_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain"
if os.path.exists(brain_path):
    for sub in os.listdir(brain_path):
        sub_path = os.path.join(brain_path, sub)
        if os.path.isdir(sub_path):
            transcript = os.path.join(sub_path, ".system_generated", "logs", "transcript.jsonl")
            if os.path.exists(transcript):
                try:
                    with open(transcript, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    
                    found_count = 0
                    for line in lines:
                        if "AssistedModePanel" in line:
                            found_count += 1
                    
                    if found_count > 0:
                        print(f"Conversation {sub}: found 'AssistedModePanel' on {found_count} lines")
                except Exception as e:
                    print(f"Error reading {sub}: {e}")
