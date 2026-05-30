import json

transcript_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca\.system_generated\logs\transcript.jsonl"

with open(transcript_path, "r", encoding="utf-8") as f:
    for line_num, line in enumerate(f, 1):
        try:
            data = json.loads(line)
            content = data.get("content", "")
            # Look for App.tsx or SandboxCanvas.tsx in model content
            if content and ("export default function App" in content or "export default function SandboxCanvas" in content):
                print(f"Line {line_num}: Found code block in text content! (len: {len(content)})")
                # print first 100 characters of the block
        except Exception as e:
            pass
