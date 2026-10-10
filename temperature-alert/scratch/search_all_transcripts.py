import os
import json

brain_dir = "C:/Users/C606/.gemini/antigravity/brain"
print("Brain dir:", os.path.abspath(brain_dir))

hits = []
for folder in os.listdir(brain_dir):
    folder_path = os.path.join(brain_dir, folder)
    if not os.path.isdir(folder_path):
        continue
    log_path = os.path.join(folder_path, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "backup_to_gdrive.py" in line:
                        step = json.loads(line)
                        tool_calls = step.get("tool_calls", [])
                        for tc in tool_calls:
                            args = tc.get("args", {})
                            if isinstance(args, str):
                                try: args = json.loads(args)
                                except: pass
                            if isinstance(args, dict):
                                content = args.get("CodeContent") or args.get("ReplacementContent")
                                if content and ("backup_to_gdrive.py" in str(args.get("TargetFile")) or "backup_to_gdrive.py" in str(args.get("AbsolutePath"))):
                                    hits.append((folder, step.get("step_index"), tc.get("name"), content))
                                elif content and "backup_to_gdrive" in content:
                                    hits.append((folder, step.get("step_index"), tc.get("name"), content))
        except Exception as e:
            pass

print(f"Found {len(hits)} occurrences with code content:")
for idx, (folder, step, name, content) in enumerate(hits):
    print(f"Hit {idx}: Folder {folder}, Step {step}, Tool {name}")
    # Write the content of the first hit to check it
    out_file = f"scratch/recovered_gdrive_{idx}.py"
    with open(out_file, "w", encoding="utf-8") as out:
        out.write(content)
    print(f"  Saved content to {out_file}")
