import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = "C:/Users/C606/.gemini/antigravity/brain/67c9bb43-912c-4bfa-b1e1-f212cc4744fe/.system_generated/logs/transcript.jsonl"

print("Log path:", os.path.abspath(log_path))

edits = []
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
            tool_calls = step.get("tool_calls", [])
            for tc in tool_calls:
                name = tc.get("name")
                args = tc.get("args", {})
                # args might be a string in some systems or a dict
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        pass
                if isinstance(args, dict):
                    target = args.get("TargetFile") or args.get("AbsolutePath")
                    if target and "weather_monitor.py" in target:
                        edits.append((step.get("step_index"), name, args))
        except Exception as e:
            pass

print(f"Found {len(edits)} tool calls modifying/viewing weather_monitor.py:")
for idx, name, args in edits:
    print(f"Step {idx}: {name}")
    # Print keys
    print("  Keys:", list(args.keys()))
    if name in ("write_to_file", "replace_file_content", "multi_replace_file_content"):
        # print some info about what was written
        desc = args.get("Description") or args.get("Instruction")
        print(f"  Description: {desc}")
