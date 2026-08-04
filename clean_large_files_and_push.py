import os
import subprocess
from pathlib import Path

manuals_dir = Path(r"c:\GOOGLE ANGET\說明書")
projects_dir = manuals_dir / "projects"

# 1. Remove large files > 1MB (.exe, .webm, .mp3, .xlsm, .xlsx) from 說明書/projects
deleted_count = 0
for p in projects_dir.glob("**/*"):
    if p.is_file():
        # Exclude large binary files
        if p.suffix.lower() in ['.exe', '.webm', '.xlsm', '.xlsx', '.zip', '.rar'] or p.stat().st_size > 2 * 1024 * 1024:
            try:
                p.unlink()
                deleted_count += 1
                print(f"Removed large file: {p.name}")
            except Exception as e:
                print(f"Error removing {p.name}: {e}")

print(f"Removed {deleted_count} large/binary files from 說明書/projects/")

# 2. Update build_portal.py ignore rules so large files are never copied to 說明書/projects/
build_portal_py = Path(r"c:\GOOGLE ANGET\portal_tools\build_portal.py")
content = build_portal_py.read_text(encoding="utf-8")
content = content.replace("elif name.endswith(('.zip', '.mp4', '.pptx', '.pdf', '.doc', '.pyc')):", "elif name.endswith(('.zip', '.mp4', '.pptx', '.pdf', '.doc', '.pyc', '.exe', '.webm', '.xlsm', '.xlsx')):")
build_portal_py.write_text(content, encoding="utf-8")

# 3. Commit and push to git
base_dir = Path(r"c:\GOOGLE ANGET")
subprocess.run(["git", "add", "-A"], cwd=base_dir, check=True)
subprocess.run(["git", "commit", "-m", "fix: remove large binary files (>25MB Cloudflare limit) from 說明書/projects"], cwd=base_dir, check=False)

print("Pushing cleaned assets to google-agent repository...")
res = subprocess.run(["git", "push", "origin", "main"], cwd=base_dir, capture_output=True, text=True)

print("Push result code:", res.returncode)
if res.returncode == 0:
    print("✅ Cleaned repository pushed successfully!")
else:
    print("Push error:", res.stderr)
