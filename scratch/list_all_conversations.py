import os

brain_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain"
if os.path.exists(brain_path):
    print("Found brain path! Searching subdirectories for transcript.jsonl...")
    for sub in os.listdir(brain_path):
        sub_path = os.path.join(brain_path, sub)
        if os.path.isdir(sub_path):
            transcript = os.path.join(sub_path, ".system_generated", "logs", "transcript.jsonl")
            if os.path.exists(transcript):
                size = os.path.getsize(transcript)
                print(f"Conversation {sub} -> transcript size: {size} bytes")
                # Quick check if AssistedModePanel is in it
                try:
                    with open(transcript, "r", encoding="utf-8") as f:
                        content = f.read()
                    if "AssistedModePanel" in content:
                        print(f"   *** MATCH! AssistedModePanel found in conversation {sub}!")
                except Exception as e:
                    print(f"   Error reading {sub}: {e}")
else:
    print("Brain path does not exist.")
