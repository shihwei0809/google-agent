import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = "C:/Users/C606/.gemini/antigravity/brain/67c9bb43-912c-4bfa-b1e1-f212cc4744fe/.system_generated/logs/transcript.jsonl"

target_steps = [1209]

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
            step_idx = step.get("step_index")
            if step_idx in target_steps:
                tool_calls = step.get("tool_calls", [])
                for tc in tool_calls:
                    args = tc.get("args", {})
                    if isinstance(args, str):
                        args = json.loads(args)
                    out_path = os.path.join(SCRIPT_DIR, f"step_{step_idx}_args.json")
                    with open(out_path, "w", encoding="utf-8") as out:
                        json.dump(args, out, indent=2, ensure_ascii=False)
                    print(f"Successfully wrote step {step_idx} args to {out_path}")
        except Exception as e:
            print("General error:", e)
