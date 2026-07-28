import json
import subprocess
import os

config_path = "config.json"

if not os.path.exists(config_path):
    print(f"Error: {config_path} not found.")
    exit(1)

# Read config
with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# Save original values
orig_line = config.get("line", {}).get("enabled", True)
orig_email = config.get("email", {}).get("enabled", True)
orig_teams = config.get("teams", {}).get("enabled", True)

try:
    # Disable notifications
    if "line" not in config: config["line"] = {}
    if "email" not in config: config["email"] = {}
    if "teams" not in config: config["teams"] = {}
    
    config["line"]["enabled"] = False
    config["email"]["enabled"] = False
    config["teams"]["enabled"] = False
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
        
    print("Disabled notifications in config.json. Running weather_monitor.py --force...")
    # Run the monitor script
    result = subprocess.run(["python", "weather_monitor.py", "--force"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    
finally:
    # Restore original config
    config["line"]["enabled"] = orig_line
    config["email"]["enabled"] = orig_email
    config["teams"]["enabled"] = orig_teams
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("Restored original notifications settings in config.json.")
