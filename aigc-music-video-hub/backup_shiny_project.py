import os
import zipfile
import subprocess
import shutil
import sys
from pathlib import Path

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')


# Paths
workspace_dir = Path(r"c:\GOOGLE ANGET\aigc-music-video-hub")
root_dir = Path(r"c:\GOOGLE ANGET")
app_data_storyboard = Path(r"C:\Users\C606\.gemini\antigravity\brain\1fbc98e7-45ee-4615-8fed-18e169439f7f\shiny_music_video_assets.md")
zip_output_path = root_dir / "勝一化學_AI音樂影片專案備份.zip"

def main():
    print("==================================================")
    print("   勝一化學 AI 音樂影片專案 備份工具")
    print("==================================================")
    
    # 1. Copy storyboard file to workspace for zipping
    local_storyboard = workspace_dir / "shiny_music_video_assets.md"
    if app_data_storyboard.exists():
        shutil.copy2(app_data_storyboard, local_storyboard)
        print("✅ 已複製影片故事板 (shiny_music_video_assets.md)")
    
    # Files to include in the root of the zip
    files_to_zip = [
        "勝一化學_純淨之光_MV.mp4",
        "勝一化學_Suno音樂合輯.mp3",
        "local_shiny_bgm.wav",
        "generate_mv.py",
        "local_generator.py",
        "rename_images.py",
        "merge_songs.py",
        "shiny_music_video_assets.md"
    ]
    
    print("\n正在壓縮專案檔案與生成的媒體素材...")
    try:
        with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Zip root files
            for f in files_to_zip:
                fpath = workspace_dir / f
                if fpath.exists():
                    zf.write(fpath, f)
                    print(f"  + {f} ({fpath.stat().st_size // 1024} KB)")
                else:
                    print(f"  (跳過) 找不到檔案: {f}")
            
            # Zip 圖片/ directory
            images_dir = workspace_dir / "圖片"
            if images_dir.exists():
                for img in images_dir.glob("*.png"):
                    archive_name = os.path.join("圖片", img.name)
                    zf.write(img, archive_name)
                print(f"  + 圖片/ 資料夾 (共 {len(list(images_dir.glob('*.png')))} 張概念圖)")
                
        size_mb = zip_output_path.stat().st_size / 1024 / 1024
        print(f"\n📦 壓縮打包完成！檔名: {zip_output_path.name} ({size_mb:.2f} MB)")
        
        # 2. Open Google Drive in browser and show zip file in Explorer
        url = "https://drive.google.com/drive/my-drive"
        print("\n🌐 正在打開 Google Drive 瀏覽器頁面...")
        os.startfile(url)
        
        print("📂 正在打開本機檔案總管...")
        # Open explorer and highlight the zip file
        subprocess.Popen(f'explorer /select,"{zip_output_path}"')
        
        print("\n==================================================")
        print("  請將彈出視窗中被選取的 `勝一化學_AI音樂影片專案備份.zip` ")
        print("  拖拉上傳至瀏覽器打開的 Google Drive 雲端硬碟中！")
        print("==================================================")
        
    except Exception as e:
        print(f"❌ 壓縮備份失敗: {e}")
        
    # Clean up copied storyboard in workspace to avoid git clutter if undesired,
    # but keeping it is fine as it's part of the workspace.

if __name__ == "__main__":
    main()
