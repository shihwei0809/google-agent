import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(SCRIPT_DIR, "..", "weather_monitor.py")

print("Checking:", os.path.abspath(file_path))

# Try reading as UTF-8
try:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    print("Successfully read as UTF-8!")
    # Check if there are garbage chars
    # We look for some known Chinese strings we expect in the code
    if "正常" in content:
        print("UTF-8 contains '正常'")
    else:
        print("UTF-8 DOES NOT contain '正常'")
except UnicodeDecodeError as e:
    print("Failed to read as UTF-8:", e)

# Try reading as CP950 (Big5)
try:
    with open(file_path, "r", encoding="cp950") as f:
        content_big5 = f.read()
    print("Successfully read as CP950!")
    if "正常" in content_big5:
        print("CP950 contains '正常'")
    else:
        print("CP950 DOES NOT contain '正常'")
except UnicodeDecodeError as e:
    print("Failed to read as CP950:", e)
