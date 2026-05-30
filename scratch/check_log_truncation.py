import json

transcript_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca\.system_generated\logs\transcript.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        try:
            data = json.loads(line)
            if "tool_calls" in data:
                for tc in data["tool_calls"]:
                    name = tc.get("name")
                    args = tc.get("args", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except Exception:
                            pass
                    
                    target = args.get("TargetFile", "")
                    if target and "AssistedModePanel" in target:
                        code = args.get("CodeContent", "")
                        print(f"Line {line_num} CodeContent Length: {len(code)}")
                        print(f"Ends with: {repr(code[-50:])}")
        except Exception as e:
            pass
