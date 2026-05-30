import json
import os

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
                    
                    if name in ["replace_file_content", "multi_replace_file_content"]:
                        target = args.get("TargetFile")
                        if target:
                            target_norm = os.path.normpath(target.strip('"\''))
                            print(f"\n=========================================")
                            print(f"Line {line_num}: Tool {name} -> Target: {target_norm}")
                            # For replace_file_content:
                            if name == "replace_file_content":
                                print(f"TargetContent: {args.get('TargetContent')}")
                                print(f"ReplacementContent: {args.get('ReplacementContent')}")
                            # For multi_replace_file_content:
                            elif name == "multi_replace_file_content":
                                chunks = args.get("ReplacementChunks") or []
                                if isinstance(chunks, str):
                                    chunks = json.loads(chunks)
                                print(f"Number of chunks: {len(chunks)}")
                                for idx, chunk in enumerate(chunks):
                                    print(f"--- Chunk {idx + 1} ---")
                                    print(f"TargetContent: {chunk.get('TargetContent')}")
                                    print(f"ReplacementContent: {chunk.get('ReplacementContent')}")
        except Exception as e:
            pass
