import os
import shutil
import datetime

def do_backup():
    base_dir = r"D:\GOOGLE ANGET"
    backup_base = r"G:\我的雲端硬碟\GOOGLE ANGET\專案備份\00_最近7天收工快照"
    history_base = r"G:\我的雲端硬碟\GOOGLE ANGET\專案備份\01_歷史按月封存"
    
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    target_dir = os.path.join(backup_base, f"{date_str}_收工備份")
    
    print(f"Creating backup directory: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)
    
    folders = [
        "三合一單網頁架機伺服器",
        "三合一單自動產生器",
        "勝一三合一單產生系統",
        "勝一三合一單網頁架機伺服器"
    ]
    
    for folder in folders:
        src = os.path.join(base_dir, folder)
        dest = os.path.join(target_dir, folder)
        if os.path.exists(src):
            print(f"Backing up: {folder}")
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            
    print("Checking for backups older than 7 days...")
    cutoff = datetime.datetime.now() - datetime.timedelta(days=7)
    
    if os.path.exists(backup_base):
        for item in os.listdir(backup_base):
            item_path = os.path.join(backup_base, item)
            if os.path.isdir(item_path):
                mtime = datetime.datetime.fromtimestamp(os.path.getmtime(item_path))
                if mtime < cutoff:
                    month_folder = mtime.strftime("%Y年%m月")
                    month_path = os.path.join(history_base, month_folder)
                    os.makedirs(month_path, exist_ok=True)
                    print(f"Archiving old backup: {item} to {month_path}")
                    shutil.move(item_path, os.path.join(month_path, item))
                    
    print("Backup completed successfully.")

if __name__ == "__main__":
    do_backup()
