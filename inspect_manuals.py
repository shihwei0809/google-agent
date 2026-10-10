import json
from pathlib import Path

manuals_db_path = Path(r"c:\GOOGLE ANGET\說明書\manuals_db.js")
content = manuals_db_path.read_text(encoding="utf-8")

json_text = content.replace("window.manualsData =", "").strip()
if json_text.endswith(";"):
    json_text = json_text[:-1]

try:
    manuals = json.loads(json_text)
    print(f"Total manuals in manuals_db.js: {len(manuals)}\n")
    for i, m in enumerate(manuals, 1):
        title = m.get('title', '').encode('ascii', 'ignore').decode('ascii')
        path = m.get('path', '').encode('ascii', 'ignore').decode('ascii')
        cat = m.get('category', '').encode('ascii', 'ignore').decode('ascii')
        print(f"[{i}] Path: {m.get('path')}")
        print(f"    Title Raw: {m.get('title')[:30]}...")
except Exception as e:
    print("Error parsing manuals_db.js:", e)
