import os
import shutil
import sys
from pathlib import Path

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

src_dir = Path(r"c:\GOOGLE ANGET\aigc-music-video-hub")
dest_dir = Path(r"G:\我的雲端硬碟\aigc-music-video-hub")

EXCLUDE_DIRS = {".git", "venv", ".gemini", "node_modules", "__pycache__"}

def sync_folder(src, dest):
    if not src.exists():
        print(f"錯誤: 來源資料夾 {src} 不存在")
        return
        
    dest.mkdir(parents=True, exist_ok=True)
    
    copied_files = 0
    skipped_files = 0
    
    for item in os.listdir(src):
        src_item = src / item
        dest_item = dest / item
        
        # Exclude directories
        if src_item.is_dir() and item in EXCLUDE_DIRS:
            continue
            
        if src_item.is_dir():
            # Recursively sync subdirectory
            sub_copied, sub_skipped = sync_folder(src_item, dest_item)
            copied_files += sub_copied
            skipped_files += sub_skipped
        else:
            # File sync
            # Check if copy is needed
            need_copy = True
            if dest_item.exists():
                try:
                    src_stat = src_item.stat()
                    dest_stat = dest_item.stat()
                    # Skip if size is the same and destination is newer or equal
                    if src_stat.st_size == dest_stat.st_size and abs(src_stat.st_mtime - dest_stat.st_mtime) < 2:
                        need_copy = False
                except Exception:
                    pass
            
            if need_copy:
                try:
                    # If destination exists and is read-only, remove it first
                    if dest_item.exists():
                        os.remove(dest_item)
                    shutil.copy2(src_item, dest_item)
                    copied_files += 1
                except Exception as e:
                    print(f"  [X] 複製失敗 {item}: {e}")
            else:
                skipped_files += 1
                
    return copied_files, skipped_files

def main():
    print("==================================================")
    # Check if Google Drive is mounted
    gdrive_root = Path(r"G:\我的雲端硬碟")
    if not gdrive_root.exists():
        print("❌ 錯誤: 找不到 Google 雲端硬碟路徑 (G:\\我的雲端硬碟)")
        print("請確保 Google Drive 電腦版應用程式已啟動且硬碟已掛載。")
        print("==================================================")
        return

    print("🚀 開始同步整個專案資料夾到 Google 雲端硬碟...")
    print(f"來源: {src_dir}")
    print(f"目的地: {dest_dir}")
    print(f"排除資料夾: {list(EXCLUDE_DIRS)}")
    print("--------------------------------------------------")
    
    try:
        copied, skipped = sync_folder(src_dir, dest_dir)
        print("--------------------------------------------------")
        print(f"🎉 同步完成！")
        print(f"  - 新增/更新檔案: {copied} 個")
        print(f"  - 未變更跳過檔案: {skipped} 個")
    except Exception as e:
        print(f"❌ 同步過程中發生錯誤: {e}")
    print("==================================================")

if __name__ == "__main__":
    main()
