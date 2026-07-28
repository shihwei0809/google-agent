import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
log_path = "C:/Users/C606/.gemini/antigravity/brain/67c9bb43-912c-4bfa-b1e1-f212cc4744fe/.system_generated/logs/transcript.jsonl"

target_steps = [1154, 1171]

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
            step_idx = step.get("step_index")
            if step_idx in target_steps:
                print(f"=== STEP {step_idx} ===")
                tool_calls = step.get("tool_calls", [])
                for tc in tool_calls:
                    print(f"Tool: {tc.get('name')}")
                    args = tc.get("args", {})
                    if isinstance(args, str):
                        args = json.loads(args)
                    print(json.dumps(args, indent=2, ensure_ascii=False))
        except Exception as e:
            pass
