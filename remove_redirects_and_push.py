import subprocess
from pathlib import Path

manuals_dir = Path(r"c:\GOOGLE ANGET\說明書")
redirects_file = manuals_dir / "_redirects"

if redirects_file.exists():
    redirects_file.unlink()
    print("Removed _redirects file from 說明書/")

base_dir = Path(r"c:\GOOGLE ANGET")
subprocess.run(["git", "rm", "說明書/_redirects"], cwd=base_dir, check=False)
subprocess.run(["git", "add", "-A"], cwd=base_dir, check=True)
subprocess.run(["git", "commit", "-m", "fix: remove _redirects force rewrite to fix static asset routing on Cloudflare Pages"], cwd=base_dir, check=False)

print("Pushing fix to google-agent repository...")
res = subprocess.run(["git", "push", "origin", "main"], cwd=base_dir, capture_output=True, text=True)

print("Push result code:", res.returncode)
if res.returncode == 0:
    print("✅ Successfully removed _redirects and pushed to main repo!")
else:
    print("Push error:", res.stderr)
