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

# Locate base directory
base_dir = Path(__file__).parent.parent.resolve()
manuals_dir = base_dir / "說明書"

print("=" * 50)
print("📡 正在將專案大廳更新同步推送至 GitHub 獨立倉庫 (agent-portal)...")
print("=" * 50)

# Check if manuals_dir exists
if not manuals_dir.exists():
    print(f"❌ Error: {manuals_dir} does not exist.")
    sys.exit(1)

# Get token dynamically from gh CLI
try:
    token_res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True)
    github_token = token_res.stdout.strip()
except Exception as e:
    print(f"⚠️ 無法取得 GitHub CLI 認證 Token，將嘗試使用普通 HTTPS 推送：{str(e)}")
    github_token = None

# Change directory to manuals_dir
original_cwd = os.getcwd()
os.chdir(manuals_dir)

try:
    # 1. Clean up any existing local git repository in manuals_dir to avoid interference
    git_dir = manuals_dir / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir, ignore_errors=True)

    # 2. Initialize new temporary git repository
    subprocess.run(["git", "init", "-b", "main"], check=True)
    
    # 3. Configure local git user to avoid commit errors
    subprocess.run(["git", "config", "user.name", "shihwei0809"], check=True)
    subprocess.run(["git", "config", "user.email", "shihwei0809@users.noreply.github.com"], check=True)

    # 4. Add all files in manuals_dir
    subprocess.run(["git", "add", "-A"], check=True)

    # 5. Commit changes
    commit_msg = "update: auto-update project portal"
    subprocess.run(["git", "commit", "-m", commit_msg], check=True)

    # 6. Add remotes and push
    # Try pushing to both shihwei0809 and mathruffian-dot repos
    targets = [
        {"name": "origin-shihwei", "user": "shihwei0809"},
        {"name": "origin-mathruffian", "user": "mathruffian-dot"}
    ]

    for target in targets:
        name = target["name"]
        username = target["user"]
        
        if github_token:
            url = f"https://x-access-token:{github_token}@github.com/{username}/agent-portal.git"
            display_url = f"https://github.com/{username}/agent-portal.git"
        else:
            url = f"https://github.com/{username}/agent-portal.git"
            display_url = url

        print(f"\n🚀 正在推送至 {name} ({display_url})...")
        
        # Add remote
        subprocess.run(["git", "remote", "add", name, url], check=False)
        
        # Push to remote main branch (force push to ensure identical copy)
        result = subprocess.run(["git", "push", name, "main", "--force"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 成功推送至 {name}！")
        else:
            print(f"⚠️ 推送至 {name} 失敗。")
            # Mask token in error message if any
            err_msg = result.stderr
            if github_token:
                err_msg = err_msg.replace(github_token, "********")
            print(f"錯誤訊息:\n{err_msg}")

finally:
    # 7. Clean up .git folder to prevent parent repository from seeing it as a submodule
    git_dir = manuals_dir / ".git"
    os.chdir(original_cwd)
    if git_dir.exists():
        # Force remove on Windows using shell command to be robust against locks
        subprocess.run(["rmdir", "/s", "/q", str(git_dir)], shell=True)
        print("\n🧹 已清除臨時 Git 設定，大廳目錄已恢復為普通資料夾。")

print("=" * 50)
print("🎉 同步流程結束！")
print("=" * 50)
