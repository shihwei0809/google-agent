import re
from pathlib import Path

index_path = Path(r"c:\GOOGLE ANGET\說明書\index.html")
content = index_path.read_text(encoding="utf-8")

# Extract projectsData array text
start_idx = content.find("const projectsData = [")
end_idx = content.find("];", start_idx)

if start_idx != -1 and end_idx != -1:
    js_text = content[start_idx:end_idx+2]
    # Find all { title: "...", launchUrl: "...", manualTitle: "..." }
    pattern = r'title:\s*"([^"]+)".*?launchUrl:\s*"([^"]+)".*?manualTitle:\s*"([^"]+)"'
    matches = re.findall(pattern, js_text, re.DOTALL)
    print(f"Total system cards in index.html: {len(matches)}\n")
    for i, (t, u, m) in enumerate(matches, 1):
        print(f"[{i}] Title: {t}")
        print(f"    Launch URL:  {u}")
        print(f"    Manual Title: {m}\n")
else:
    print("Could not locate projectsData array in index.html")
