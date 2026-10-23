import os, sys, shutil, subprocess, re
from datetime import datetime, timedelta

src_root = r"C:\GOOGLE ANGET"
today_str = datetime.now().strftime("%Y%m%d")
backup_base = r"G:\我的雲端硬碟\GOOGLE ANGET\專案備份"
snapshot_root = os.path.join(backup_base, "00_最近7天收工快照")
archive_root = os.path.join(backup_base, "01_歷史按月封存")
dest_root = os.path.join(snapshot_root, f"{today_str}_收工備份")

os.makedirs(dest_root, exist_ok=True)

print("=" * 45)
print(f"[AutoSync] Scanning modified projects & files (Last 24h)...")
print(f"Source: {src_root}")
print(f"Destination: {dest_root}")
print("=" * 45)

cutoff_time = datetime.now() - timedelta(hours=24)

# 1. 備份根目錄檔案 (如 HANDOVER.md, xlsx 等修改檔案)
ignored_dirs = {"node_modules", "venv", ".venv", ".git", ".netlify", ".wrangler", ".firebase", "專案備份"}

copied_targets = set()

for item in os.listdir(src_root):
    item_path = os.path.join(src_root, item)
    if item in ignored_dirs:
        continue
    
    if os.path.isfile(item_path):
        mtime = datetime.fromtimestamp(os.path.getmtime(item_path))
        if mtime >= cutoff_time or item == "HANDOVER.md":
            dest_file = os.path.join(dest_root, item)
            shutil.copy2(item_path, dest_file)
            print(f"[Backup] Copied root file: {item}")
    elif os.path.isdir(item_path):
        # 檢查資料夾內是否有近期修改的檔案
        has_modified = False
        for root, dirs, files in os.walk(item_path):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            for f in files:
                f_path = os.path.join(root, f)
                try:
                    if datetime.fromtimestamp(os.path.getmtime(f_path)) >= cutoff_time:
                        has_modified = True
                        break
                except:
                    pass
            if has_modified:
                break
        
        if has_modified:
            dest_folder = os.path.join(dest_root, item)
            print(f"[Backup] Syncing modified folder: {item}")
            # 使用 robocopy 進行鏡像傳輸
            cmd = f'robocopy "{item_path}" "{dest_folder}" /E /R:1 /W:1 /XD .git node_modules venv .venv .netlify .wrangler .firebase /XF *.zip *.avi /NDL /NFL /NJH /NJS'
            subprocess.run(cmd, shell=True)

print("=" * 45)
print(f"[AutoSync] Backup successfully completed into {dest_root} !")
print("=" * 45)

# 2. 滾動封存防爆機制：檢查 00_最近7天收工快照，超過 7 天者自動移至 01_歷史按月封存
print("\n" + "=" * 45)
print("[Rolling Archive] Checking 00_最近7天收工快照 for folders older than 7 days...")
rolling_cutoff = datetime.now() - timedelta(days=7)

if os.path.exists(snapshot_root):
    for f in os.listdir(snapshot_root):
        folder_path = os.path.join(snapshot_root, f)
        if not os.path.isdir(folder_path):
            continue
        m = re.search(r"(\d{8})", f)
        if m:
            try:
                f_date = datetime.strptime(m.group(1), "%Y%m%d")
                if f_date < rolling_cutoff:
                    month_name = f"{f_date.year}年{f_date.month:02d}月"
                    target_month_dir = os.path.join(archive_root, month_name)
                    os.makedirs(target_month_dir, exist_ok=True)
                    dest_archive_path = os.path.join(target_month_dir, f)
                    if os.path.exists(dest_archive_path):
                        dest_archive_path = os.path.join(target_month_dir, f + "_archived")
                    shutil.move(folder_path, dest_archive_path)
                    print(f"[Archived] Moved {f} -> 01_歷史按月封存\\{month_name}")
                else:
                    print(f"[Keep] {f} (Within 7 days)")
            except Exception as e:
                print(f"[Warning] Error parsing {f}: {e}")

print("[Rolling Archive] 00_最近7天收工快照 status verified clean.")
print("=" * 45)
