import os
import json

path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca\.system_generated\messages"
if os.path.exists(path):
    for filename in os.listdir(path):
        if filename.endswith(".json"):
            filepath = os.path.join(path, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check structure
                # The data might be a message object. Let's look for write_to_file
                data_str = json.dumps(data)
                if "AssistedModePanel" in data_str:
                    print(f"Found AssistedModePanel in message file: {filename}")
                    # Let's inspect if it contains untruncated content
                    # We can search for the tool call
                    if "tool_calls" in data_str:
                        print("Message has tool_calls!")
                    # Check if '<truncated' is in it
                    if "<truncated" in data_str:
                        print("Message file IS truncated!")
                    else:
                        print("Message file IS NOT truncated!")
            except Exception as e:
                print(f"Error reading {filename}: {e}")
else:
    print("Messages path does not exist.")
