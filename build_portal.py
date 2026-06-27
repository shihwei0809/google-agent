import os
import shutil
import sys
from pathlib import Path

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

base_dir = Path(r"C:\GOOGLE ANGET")
manuals_dir = base_dir / "說明書"
projects_target_dir = manuals_dir / "projects"

# 1. Ensure target directory exists and clean it up
if projects_target_dir.exists():
    print("Cleaning up old projects copy directory...")
    shutil.rmtree(projects_target_dir)
projects_target_dir.mkdir(parents=True, exist_ok=True)

# Define static web projects to copy
web_projects = [
    {"name": "flowchart-web", "src": base_dir / "flowchart-web"},
    {"name": "hongsheng-web", "src": base_dir / "hongsheng-web"},
    {"name": "isotank-training", "src": base_dir / "isotank-training"},
    {"name": "isotank-hf-demo", "src": base_dir / "isotank-hf-demo"},
    {"name": "test", "src": base_dir / "test"},
    {"name": "互動式網站", "src": base_dir / "互動式網站"},
    {"name": "padlet-board", "src": base_dir / "padlet-board"},
    {"name": "hr_quiz_v2", "src": base_dir / "員工教育訓練測驗系統" / "hr_quiz_v2"}
]

# Copy ignore patterns
def ignore_patterns(path, names):
    ignored = []
    for name in names:
        # Ignore env, git, node, venv, and large media files to prevent security/space issues
        if name in ['.git', 'node_modules', 'venv', '.env', '.firebase', '.netlify', '__pycache__']:
            ignored.append(name)
        elif name.endswith(('.zip', '.mp4', '.pptx', '.pdf', '.doc', '.pyc')):
            # We skip heavy binaries unless they are small SVG or mp3 audios
            ignored.append(name)
    return ignored

# 2. Copy projects to manuals/projects/
for proj in web_projects:
    src_path = proj["src"]
    dest_path = projects_target_dir / proj["name"]
    
    if not src_path.exists():
        print(f"Warning: Source project {proj['name']} does not exist. Skipping.")
        continue
    
    print(f"Copying {proj['name']} to manuals/projects/...")
    shutil.copytree(src_path, dest_path, ignore=ignore_patterns)

print("✅ All static web projects successfully copied to manuals/projects/")

# 3. Update return badges inside manuals/projects/<name>/index.html
# Since they are now in manuals/projects/<name>/index.html, they need to go up 2 levels (../../index.html) to go back to lobby
for proj in web_projects:
    dest_index = projects_target_dir / proj["name"] / "index.html"
    if not dest_index.exists():
        continue
    
    content = dest_index.read_text(encoding="utf-8")
    
    # Replace relative path back to lobby from ../說明書/index.html to ../../index.html
    if "../說明書/index.html" in content:
        content = content.replace("../說明書/index.html", "../../index.html")
        dest_index.write_text(content, encoding="utf-8")
        print(f"✅ Adjusted return URL in copied project: {proj['name']}/index.html")

# 4. Update launchUrls inside manuals/index.html to point to ./projects/ instead of ../
portal_html_path = manuals_dir / "index.html"
if portal_html_path.exists():
    content = portal_html_path.read_text(encoding="utf-8")
    
    # We replace the launchUrls in projectsData
    replacements = {
        'launchUrl: "../flowchart-web/index.html"': 'launchUrl: "./projects/flowchart-web/index.html"',
        'launchUrl: "../hongsheng-web/index.html"': 'launchUrl: "./projects/hongsheng-web/index.html"',
        'launchUrl: "../isotank-training/index.html"': 'launchUrl: "./projects/isotank-training/index.html"',
        'launchUrl: "../isotank-hf-demo/index.html"': 'launchUrl: "./projects/isotank-hf-demo/index.html"',
        'launchUrl: "../test/index.html"': 'launchUrl: "./projects/test/index.html"',
        'launchUrl: "../互動式網站/index.html"': 'launchUrl: "./projects/互動式網站/index.html"',
        'launchUrl: "../padlet-board/index.html"': 'launchUrl: "./projects/padlet-board/index.html"',
        'launchUrl: "../影片生成/hr_quiz_v2/index.html"': 'launchUrl: "./projects/hr_quiz_v2/index.html"'
    }
    
    updated = False
    for old_str, new_str in replacements.items():
        if old_str in content:
            content = content.replace(old_str, new_str)
            updated = True
            
    if updated:
        portal_html_path.write_text(content, encoding="utf-8")
        print("✅ Updated manuals/index.html projectsData launchUrls to point to ./projects/ path.")

print("\n🎉 Portal build complete! You can now deploy '說明書' directory to Netlify.")
