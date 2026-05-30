import json
import os

transcript_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca\.system_generated\logs\transcript.jsonl"

target_lines = [169, 175, 239]

out_lines = []

with open(transcript_path, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        if line_num in target_lines:
            data = json.loads(line)
            content = data.get("content", "")
            out_lines.append(f"\n=========================================\nLine {line_num} Content (len: {len(content)}):\n")
            parts = content.split("```")
            for part in parts:
                if part.strip().startswith("tsx") or part.strip().startswith("typescript") or "export default" in part:
                    out_lines.append("--- Code Block Found ---\n" + part + "\n------------------------\n")

with open(r"c:\model_eval\EduSim_API\scratch\output_view.txt", "w", encoding="utf-8") as out:
    out.write("".join(out_lines))
print("Successfully wrote output to c:\model_eval\EduSim_API\scratch\output_view.txt")
