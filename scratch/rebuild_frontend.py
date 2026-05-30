import json
import os

transcript_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca\.system_generated\logs\transcript.jsonl"

file_contents = {}

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
                    
                    if name == "write_to_file":
                        target = args.get("TargetFile")
                        code = args.get("CodeContent")
                        if target and code:
                            # Clean up quotes
                            target_clean = target.strip('"\'')
                            if isinstance(code, str):
                                code_clean = code.strip('"\'')
                                # Re-evaluate escaped sequences if it's double-encoded
                                if code_clean.startswith("\\n") or "\\\\" in code_clean:
                                    try:
                                        code_clean = json.loads(f'"{code_clean}"')
                                    except Exception:
                                        pass
                            else:
                                code_clean = code
                            
                            target_norm = os.path.normpath(target_clean)
                            file_contents[target_norm] = code_clean
                            print(f"Captured write_to_file for {target_norm} (len: {len(str(code_clean))})")
        except Exception as e:
            pass

# Write them back!
for path, code in file_contents.items():
    # Make sure parent directories exist
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as out:
        out.write(str(code))
    print(f"Successfully restored: {path}")
