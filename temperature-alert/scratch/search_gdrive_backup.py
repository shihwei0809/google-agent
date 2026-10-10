import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = "C:/Users/C606/.gemini/antigravity/brain/67c9bb43-912c-4bfa-b1e1-f212cc4744fe/.system_generated/logs/transcript.jsonl"

hits = []
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        if "backup_to_gdrive.py" in line or "backup_to_gdrive" in line:
            try:
                step = json.loads(line)
                hits.append((step.get("step_index"), step.get("type"), step))
            except:
                pass

print(f"Found {len(hits)} matching steps in transcript.jsonl:")
for idx, stype, step in hits:
    print(f"Step {idx} ({stype}):")
    # check tool calls
    tc = step.get("tool_calls", [])
    if tc:
        for t in tc:
            print(f"  Tool call: {t.get('name')}")
            args = t.get("args", {})
            if isinstance(args, str):
                try: args = json.loads(args)
                except: pass
            if isinstance(args, dict):
                print(f"  TargetFile: {args.get('TargetFile') or args.get('AbsolutePath')}")
                if "CodeContent" in args or "ReplacementContent" in args:
                    print("  Has content code!")
    # check content
    content = step.get("content", "")
    if content:
        print(f"  Content length: {len(content)}")
        if "backup_to_gdrive.py" in content:
            print("  Found file name in content!")
