import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = Path(os.path.dirname(os.path.abspath(__file__)))
output_root = workspace_dir / "創作庫"
images_dir = workspace_dir / "圖片"

# The 60 default shared image filenames to skip rendering
default_images = {
    "01_廠區遠景.png", "02_反應槽近景.png", "03_分子模擬.png", "04_全息藍圖.png",
    "05_精細檢驗.png", "06_QC_檢驗.png", "07_無塵室入口.png", "08_晶圓傳送.png",
    "09_溶劑噴灑.png", "10_晶圓清洗.png", "11_烘烤乾燥.png", "12_黃光區天車.png",
    "13_DUV_雷射曝光.png", "14_EUV_極紫外光顯影.png", "15_電路形成.png", "16_晶片切割.png",
    "17_先進封裝.png", "18_終端晶片展示.png", "19_綠色工廠.png", "20_廢水回收.png",
    "21_溶劑回收管線.png", "22_綠色循環標章.png", "23_自動灌裝生產線.png", "24_廠區安全巡檢.png",
    "25_儲罐裝載.png", "26_超級電腦運算.png", "27_物流裝箱.png", "28_高雄港裝船.png",
    "29_貨輪出海.png", "30_科技微觀終幕.png", "31_ESG永續報告.png", "32_智慧中控室.png",
    "33_廠房屋頂太陽能.png", "34_未來晶片應用.png", "35_研發化驗室.png", "36_高效能伺服器.png",
    "37_全球智慧物流.png", "38_晶片立體封裝.png", "39_碳中和監測.png", "40_高分子純化.png",
    "41_環境安全監測.png", "42_綠色包裝桶裝.png", "43_晶圓載具清洗.png", "44_雲端運算中心.png",
    "45_綠能儲能設備.png", "46_微小缺陷檢測.png", "47_配方自動混合.png", "48_低碳精餾製程.png",
    "49_晶圓表面烘烤.png", "50_科技與綠能共榮.png", "51_吊掛isotank.png", "52_無人搬運車.png",
    "53_冷卻塔與循環水.png", "54_超純水純化.png", "55_低碳綠色供應鏈.png", "56_超低溫化學儲存.png",
    "57_電子顯微鏡分析.png", "58_智慧防護與安全.png", "59_雨水回收綠化.png", "60_碳捕集與利用.png"
}

def is_legacy_song(song_dir):
    mp3s = [f for f in os.listdir(song_dir) if f.endswith(".mp3")]
    if not mp3s:
        return False
    mp3_path = song_dir / mp3s[0]
    mtime = mp3_path.stat().st_mtime
    mtime_dt = datetime.fromtimestamp(mtime)
    today = datetime.now().date()
    return mtime_dt.date() < today

def get_audio_duration(audio_path):
    cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)]
    result = subprocess.run(cmd, capture_output=True)
    duration_str = result.stdout.decode('utf-8', errors='ignore').strip()
    if duration_str:
        try:
            return float(duration_str)
        except ValueError:
            pass
    return 0

def render_slideshow(song_dir, folder_name):
    md_path = song_dir / "vids_storyboard_prompts.md"
    if not md_path.exists():
        print(f"    [!] 找不到故事板 MD 檔案: {md_path.name}")
        return False
        
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Read duration
    duration_match = re.search(r"歌曲總長度.*?`(.*?) 秒`", content)
    if duration_match:
        duration = float(duration_match.group(1))
    else:
        print("    [!] 無法從故事板中解析長度")
        return False

    # Find MP3 file in the directory
    mp3_files = [f for f in os.listdir(song_dir) if f.endswith(".mp3")]
    if not mp3_files:
        print("    [!] 找不到 MP3 檔案")
        return False
    mp3_name = mp3_files[0]
    mp3_path = song_dir / mp3_name
    
    # Recalculate duration from MP3 to be precise
    audio_duration = get_audio_duration(mp3_path)
    if audio_duration > 0:
        duration = audio_duration

    # Find all image filenames
    image_filenames = re.findall(r"圖片檔名.*?`(.*?)`", content)
    if not image_filenames:
        # Try with "本機對照圖片"
        image_filenames = re.findall(r"本機對照圖片.*?`(.*?)`", content)
        if not image_filenames:
            # Retry with Chinese character pattern if any
            image_filenames = re.findall(r"圖片狀態.*?你可以直接在資料夾內的.*?圖片.*?目錄找到此檔上傳.*?檔案名稱為.*?`(.*?)`", content)
            if not image_filenames:
                print("    [!] 無法從故事板解析圖片檔名列表")
                return False
        
    # Check if local images directory exists and contains files
    local_img_dir = song_dir / "圖片"
    if not local_img_dir.exists():
        print(f"    [!] 找不到歌曲專屬圖片資料夾: {local_img_dir.name}")
        return False
        
    local_images = [f for f in os.listdir(local_img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not local_images:
        print(f"    [!] 歌曲專屬圖片資料夾是空的")
        return False

    # Check if they are just default/shared images
    is_only_defaults = all(img in default_images for img in local_images)
    if is_only_defaults and (song_dir / f"{folder_name}_MV.mp4").exists():
        print(f"    [!] 該歌曲僅包含預設共用圖片，不符合合成自訂 MV 規格")
        return False

    # Check if all storyboard image files exist locally
    missing_images = []
    for img in image_filenames:
        img_path = local_img_dir / img
        if not img_path.exists():
            missing_images.append(img)
            
    if missing_images:
        print(f"    [!] 圖片資料夾中缺少故事板指定的圖片: {missing_images}")
        return False

    num_images = len(image_filenames)
    duration_per_image = duration / num_images

    # Generate slideshow_inputs.txt
    inputs_txt_path = song_dir / "slideshow_inputs.txt"
    with open(inputs_txt_path, "w", encoding="utf-8") as out:
        for img in image_filenames:
            img_path = local_img_dir / img
            escaped_path = str(img_path).replace("'", "'\\''").replace("\\", "/")
            out.write(f"file '{escaped_path}'\n")
            out.write(f"duration {duration_per_image:.4f}\n")
            
        # Repeat the last file once at the end without duration (ffmpeg concat demuxer requirement)
        last_img = image_filenames[-1]
        last_img_path = local_img_dir / last_img
        escaped_last_path = str(last_img_path).replace("'", "'\\''").replace("\\", "/")
        out.write(f"file '{escaped_last_path}'\n")

    output_mv_path = song_dir / f"{folder_name}_MV.mp4"
    
    # Render with FFmpeg
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(inputs_txt_path),
        "-i", str(mp3_path),
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(output_mv_path)
    ]
    
    try:
        subprocess.run(cmd, capture_output=True, check=True)
        # Clean up temp concat file
        if inputs_txt_path.exists():
            os.remove(inputs_txt_path)
        return True
    except subprocess.CalledProcessError as e:
        print(f"    [X] FFmpeg 渲染失敗: {e.stderr.decode('utf-8', errors='ignore')[-500:]}")
        if inputs_txt_path.exists():
            os.remove(inputs_txt_path)
        return False

def main():
    print("==================================================")
    print("🎬 開始在 [aigc-music-video-hub] 專案渲染所有客製化投影片 MV...")
    print("==================================================")
    
    folders = sorted([d for d in os.listdir(output_root) if (output_root / d).is_dir()])
    
    success_count = 0
    fail_count = 0
    
    for idx, folder in enumerate(folders, 1):
        song_dir = output_root / folder
        print(f"[{idx}/{len(folders)}] 正在處理: 【{folder}】")
        
        output_mv_path = song_dir / f"{folder}_MV.mp4"
        
        # Check if local images directory exists and contains images
        local_img_dir = song_dir / "圖片"
        imgs = [f for f in os.listdir(local_img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if local_img_dir.exists() else []
        has_imgs = len(imgs) > 0
        
        # Check if legacy song
        legacy = is_legacy_song(song_dir)
        
        # Check if they are just default/shared images
        is_only_defaults = has_imgs and all(img in default_images for img in imgs)
        
        if not has_imgs or (is_only_defaults and not legacy):
            reason = "圖片資料夾不存在或為空" if not has_imgs else "僅包含預設共用圖片(且為新歌)"
            print(f"  [!] {reason}，不進行 MV 渲染。")
            if output_mv_path.exists():
                try:
                    os.remove(output_mv_path)
                    print(f"  [✓] 已刪除不合規格的舊 MV 影片: {output_mv_path.name}")
                except Exception as e:
                    print(f"  [X] 刪除舊 MV 失敗: {e}")
            fail_count += 1
            continue
            
        # For legacy songs with only default images, skip slideshow rendering but DO NOT delete existing MV
        if legacy and is_only_defaults:
            if not output_mv_path.exists():
                print(f"  [!] 雖然為舊歌且僅含預設檔名，但因缺少影片，強制啟動投影片渲染...")
            else:
                print(f"  [~] 以前產生的舊歌且僅有預設圖片，跳過自訂投影片渲染（保留其模板母片影片）")
                continue
            
        if output_mv_path.exists() and "--force" not in sys.argv:
            print(f"  [✓] 影片已存在，跳過渲染 (使用已存在檔案)")
            success_count += 1
            continue
            
        # Render custom slideshow (always overwrite if reached here)
        if render_slideshow(song_dir, folder):
            print(f"  [✓] 成功生成投影片 MV")
            success_count += 1
        else:
            print(f"  [X] 無法生成投影片 MV")
            if not legacy and output_mv_path.exists():
                try:
                    os.remove(output_mv_path)
                    print(f"  [✓] 渲染失敗，已刪除可能損壞或不正確的 MV 影片: {output_mv_path.name}")
                except:
                    pass
            fail_count += 1
            
    print("--------------------------------------------------")
    print(f"🎉 任務完成！")
    print(f"  - 成功生成: {success_count} 個")
    print(f"  - 跳過或失敗: {fail_count} 個")
    print("==================================================")

if __name__ == "__main__":
    main()
