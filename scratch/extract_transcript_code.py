import json
import os

transcript_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca\.system_generated\logs\transcript.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        try:
            data = json.loads(line)
            # Look for tool calls in model responses
            if "tool_calls" in data:
                for tc in data["tool_calls"]:
                    name = tc.get("name")
                    args = tc.get("args", {})
                    # The args might be a string that needs parsing
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            pass
                    
                    if name in ["write_to_file", "replace_file_content", "multi_replace_file_content"]:
                        target = args.get("TargetFile") or args.get("TargetFile")
                        print(f"Line {line_num}: Tool {name} -> Target: {target}")
        except Exception as e:
            pass
