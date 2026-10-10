import os
import subprocess
import shutil
import sys
from pathlib import Path

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

base_dir = Path(r"c:\GOOGLE ANGET")
manuals_dir = base_dir / "說明書"

# 1. Push to shihwei0809/agent-portal repo
print("=== 1. Pushing to agent-portal repo ===")
token_res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
github_token = token_res.stdout.strip()

original_cwd = os.getcwd()
os.chdir(manuals_dir)

git_dir = manuals_dir / ".git"
if git_dir.exists():
    shutil.rmtree(git_dir, ignore_errors=True)

subprocess.run(["git", "init", "-b", "main"], check=True)
subprocess.run(["git", "config", "user.name", "shihwei0809"], check=True)
subprocess.run(["git", "config", "user.email", "shihwei0809@users.noreply.github.com"], check=True)
subprocess.run(["git", "add", "-A"], check=True)
subprocess.run(["git", "commit", "-m", "update: auto-update project portal"], check=True)

url = f"https://x-access-token:{github_token}@github.com/shihwei0809/agent-portal.git"
subprocess.run(["git", "remote", "add", "origin", url], check=True)
res1 = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, text=True)

os.chdir(original_cwd)
if git_dir.exists():
    subprocess.run(["rmdir", "/s", "/q", str(git_dir)], shell=True)

print("Agent-portal push result code:", res1.returncode)
if res1.returncode != 0:
    print("Agent-portal push error:", res1.stderr)
else:
    print("Agent-portal successfully force-pushed!")

# 2. Push to main shihwei0809/google-agent repo
print("\n=== 2. Pushing main repo (google-agent) ===")
os.chdir(base_dir)
subprocess.run(["git", "add", "說明書/index.html", "說明書/_redirects", "portal_tools/build_portal.py"], check=True)
subprocess.run(["git", "commit", "-m", "fix: portal url stacking & add _redirects for cloudflare pages"], check=False)
res2 = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)

print("Google-agent main repo push result code:", res2.returncode)
if res2.returncode != 0:
    print("Google-agent push error:", res2.stderr)
else:
    print("Google-agent main repo successfully pushed!")
