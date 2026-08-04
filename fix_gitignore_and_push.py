import subprocess
from pathlib import Path

# 1. Update .gitignore
gitignore_path = Path(r"c:\GOOGLE ANGET\.gitignore")
if gitignore_path.exists():
    lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    new_lines = [l for l in lines if 'projects' not in l and '說明書/projects' not in l]
    gitignore_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print("Updated .gitignore: removed projects/ ignore rule!")

# 2. Force add 說明書/projects/ to git in root repo
base_dir = Path(r"c:\GOOGLE ANGET")
print("Force adding 說明書/projects/ to git...")
subprocess.run(["git", "add", "-f", "說明書/projects"], cwd=base_dir, check=True)
subprocess.run(["git", "add", "說明書/index.html", "說明書/_redirects", "portal_tools/build_portal.py", ".gitignore"], cwd=base_dir, check=True)

# 3. Commit and push
commit_msg = "feat: add static projects to 說明書/projects/ for Cloudflare Pages deployment"
subprocess.run(["git", "commit", "-m", commit_msg], cwd=base_dir, check=False)

print("Pushing to main google-agent repository...")
res = subprocess.run(["git", "push", "origin", "main"], cwd=base_dir, capture_output=True, text=True)

print("Push result code:", res.returncode)
if res.returncode == 0:
    print("✅ Successfully committed and pushed all static projects to google-agent repository!")
else:
    print("Push error:", res.stderr)
