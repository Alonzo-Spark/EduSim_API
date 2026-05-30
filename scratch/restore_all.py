import json
import os

transcript_path = r"C:\Users\Aswini\.gemini\antigravity-ide\brain\6ab269ab-138f-46d6-9684-75731f582dca\.system_generated\logs\transcript.jsonl"

file_cache = {}

def get_current_content(path):
    path_norm = os.path.normpath(path)
    if path_norm in file_cache:
        return file_cache[path_norm]
    
    # Otherwise read from disk
    if os.path.exists(path_norm):
        with open(path_norm, "r", encoding="utf-8") as f:
            content = f.read()
        file_cache[path_norm] = content
        return content
    else:
        file_cache[path_norm] = ""
        return ""

def set_content(path, content):
    path_norm = os.path.normpath(path)
    file_cache[path_norm] = content

def clean_arg(val):
    if not isinstance(val, str):
        return val
    val_clean = val.strip('"\'')
    # Try double json load if needed
    if val_clean.startswith("\\n") or "\\\\" in val_clean or '\\"' in val_clean:
        try:
            val_clean = json.loads(f'"{val_clean}"')
        except Exception:
            pass
    return val_clean

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
                        target = clean_arg(args.get("TargetFile"))
                        code = clean_arg(args.get("CodeContent"))
                        if target and code is not None:
                            set_content(target, code)
                            print(f"[{line_num}] write_to_file: {target} (len: {len(str(code))})")
                            
                    elif name == "replace_file_content":
                        target = clean_arg(args.get("TargetFile"))
                        target_content = clean_arg(args.get("TargetContent"))
                        replacement_content = clean_arg(args.get("ReplacementContent"))
                        if target and target_content is not None and replacement_content is not None:
                            curr = get_current_content(target)
                            # Normalize line endings to avoid \r\n mismatches
                            curr_norm = curr.replace("\r\n", "\n")
                            target_norm = target_content.replace("\r\n", "\n")
                            replacement_norm = replacement_content.replace("\r\n", "\n")
                            
                            if target_norm in curr_norm:
                                new_content = curr_norm.replace(target_norm, replacement_norm)
                                set_content(target, new_content)
                                print(f"[{line_num}] replace_file_content: {target} (SUCCESS)")
                            else:
                                # Try matching with original endings if normalization failed
                                if target_content in curr:
                                    new_content = curr.replace(target_content, replacement_content)
                                    set_content(target, new_content)
                                    print(f"[{line_num}] replace_file_content: {target} (SUCCESS - direct match)")
                                else:
                                    print(f"[{line_num}] replace_file_content: {target} (WARNING: TargetContent not found!)")
                                    # Let's inspect the target_content and print a snippet
                                    print(f"   Target content snippet: {repr(target_content[:50])}")
                                    
                    elif name == "multi_replace_file_content":
                        target = clean_arg(args.get("TargetFile"))
                        chunks = args.get("ReplacementChunks")
                        if isinstance(chunks, str):
                            try:
                                chunks = json.loads(chunks)
                            except Exception:
                                pass
                        
                        if target and chunks:
                            curr = get_current_content(target)
                            new_content = curr
                            success_count = 0
                            for idx, chunk in enumerate(chunks):
                                tc_chunk = clean_arg(chunk.get("TargetContent"))
                                rc_chunk = clean_arg(chunk.get("ReplacementContent"))
                                
                                new_content_norm = new_content.replace("\r\n", "\n")
                                tc_norm = tc_chunk.replace("\r\n", "\n")
                                rc_norm = rc_chunk.replace("\r\n", "\n")
                                
                                if tc_norm in new_content_norm:
                                    new_content = new_content_norm.replace(tc_norm, rc_norm)
                                    success_count += 1
                                else:
                                    if tc_chunk in new_content:
                                        new_content = new_content.replace(tc_chunk, rc_chunk)
                                        success_count += 1
                                    else:
                                        print(f"[{line_num}] multi_replace_file_content: {target} chunk {idx+1} (WARNING: TargetContent not found!)")
                            
                            set_content(target, new_content)
                            print(f"[{line_num}] multi_replace_file_content: {target} ({success_count}/{len(chunks)} chunks applied)")
        except Exception as e:
            print(f"Error on line {line_num}: {e}")

# Write all modified/created files back to disk!
for path, content in file_cache.items():
    # Only write back files under model_eval (frontend / API)
    # We do NOT want to overwrite C:\\Users\\Aswini\\.gemini or standard files unless they are under model_eval
    if "model_eval" in path.lower():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as out:
            out.write(content)
        print(f"Restored file to disk: {path}")
