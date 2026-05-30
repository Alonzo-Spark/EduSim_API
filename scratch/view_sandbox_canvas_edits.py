import json

transcript_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca\.system_generated\logs\transcript.jsonl"

out = []

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
                    if target and "SandboxCanvas.tsx" in target:
                        out.append(f"\n=========================================\nLine {line_num}: Tool {name}\n")
                        if name == "replace_file_content":
                            out.append(f"TargetContent:\n{args.get('TargetContent')}\n")
                            out.append(f"ReplacementContent:\n{args.get('ReplacementContent')}\n")
                        elif name == "multi_replace_file_content":
                            chunks = args.get("ReplacementChunks") or []
                            if isinstance(chunks, str):
                                chunks = json.loads(chunks)
                            for idx, chunk in enumerate(chunks):
                                out.append(f"--- Chunk {idx + 1} ---\n")
                                out.append(f"TargetContent:\n{chunk.get('TargetContent')}\n")
                                out.append(f"ReplacementContent:\n{chunk.get('ReplacementContent')}\n")
        except Exception as e:
            pass

with open(r"c:\model_eval\EduSim_API\scratch\sandbox_edits.txt", "w", encoding="utf-8") as f_out:
    f_out.write("".join(out))
print("Successfully wrote sandbox edits to c:\model_eval\EduSim_API\scratch\sandbox_edits.txt")
