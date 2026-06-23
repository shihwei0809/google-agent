import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = Path(r"c:\GOOGLE ANGET\aigc-music-video-hub")
output_root = workspace_dir / "創作庫"

template_shanyi = workspace_dir / "勝一化學_純淨之光_MV.mp4"
template_changbin = workspace_dir / "《彰濱的科技之翼》—電音版.mp4"

def is_legacy_song(song_dir):
    mp3s = [f for f in os.listdir(song_dir) if f.endswith(".mp3")]
    if not mp3s:
        return False
    mp3_path = song_dir / mp3s[0]
    mtime = mp3_path.stat().st_mtime
    mtime_dt = datetime.fromtimestamp(mtime)
    today = datetime.now().date()
    return mtime_dt.date() < today

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

def get_audio_duration(audio_path):
    cmd = ["ffmpeg", "-i", str(audio_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return None

def apply_template(template_path, audio_path, output_path, duration):
    # Mux template video loop with the audio track
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",
        "-i", str(template_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
    ]
    if duration:
        cmd.extend(["-t", f"{duration:.3f}"])
    else:
        cmd.append("-shortest")
    cmd.append(str(output_path))
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore', check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  [X] FFmpeg 合成失敗: {e.stderr}")
        return False

def main():
    print("==================================================")
    print("🎬 開始偵測並生成缺少的 AI 音樂影片 (MV)...")
    print("==================================================")
    
    if not template_shanyi.exists() and not template_changbin.exists():
        print("❌ 錯誤: 找不到任何母片影片！")
        return
        
    folders = sorted([d for d in os.listdir(output_root) if (output_root / d).is_dir()])
    
    rendered_count = 0
    skipped_count = 0
    
    for folder in folders:
        song_dir = output_root / folder
        
        # Find MP3 inside this folder
        mp3s = [f for f in os.listdir(song_dir) if f.endswith(".mp3")]
        if not mp3s:
            continue
            
        mp3_file = mp3s[0]
        mp3_path = song_dir / mp3_file
        
        # Check if MV already exists
        output_mv_path = song_dir / f"{folder}_MV.mp4"
        
        # Check if local images directory exists and contains images
        local_img_dir = song_dir / "圖片"
        imgs = [f for f in os.listdir(local_img_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))] if local_img_dir.exists() else []
        has_imgs = len(imgs) > 0
        
        # Check if legacy song (MP3 created before today)
        legacy = is_legacy_song(song_dir)
        
        # Check if they are just default/shared images
        is_only_defaults = has_imgs and all(img in default_images for img in imgs)
        
        # New songs with empty or only-default images => delete any existing MV, skip
        if not has_imgs or (is_only_defaults and not legacy):
            if output_mv_path.exists():
                try:
                    os.remove(output_mv_path)
                    reason = "圖片資料夾為空" if not has_imgs else "僅包含預設共用圖片(新歌)"
                    print(f"  [✓] {reason}，已刪除該歌曲舊 MV: {output_mv_path.name}")
                except Exception as e:
                    print(f"  [X] 刪除舊 MV 失敗: {e}")
            continue
        
        if output_mv_path.exists():
            skipped_count += 1
            continue
        
        # Legacy song with images => use template MV
        if legacy:
            folder_lower = folder.lower()
            if any(kw in folder_lower for kw in ["彰濱", "鴻勝", "虹昇", "智慧流動", "網格交響", "流動軌跡", "流向", "去化", "格外"]):
                template_path = template_changbin
                template_name = "彰濱版電音母片"
            else:
                template_path = template_shanyi
                template_name = "勝一版純淨母片"
                
            if not template_path.exists():
                print(f"  [!] 無法處理 {folder}：找不到對應的 {template_name}")
                continue
                
            duration = get_audio_duration(mp3_path)
            print(f"➔ 舊歌缺少影片: 【{folder}】")
            print(f"  音軌長度: {duration:.2f} 秒 | 套用模版: {template_name}")
            
            if apply_template(template_path, mp3_path, output_mv_path, duration):
                print(f"  [✓] 成功生成: {output_mv_path.name}")
                rendered_count += 1
            else:
                print(f"  [X] 生成失敗: {folder}")
        else:
            # New song with custom images => remind user to run custom renderer
            print(f"  [!] 新歌缺少客製化 MV: 【{folder}】，請執行 render_all_custom_mvs.py 進行渲染。")
            continue
            
    print("--------------------------------------------------")
    print(f"🎉 影片生成任務完成！")
    print(f"  - 新增渲染 MV 影片: {rendered_count} 個")
    print(f"  - 已存在跳過: {skipped_count} 個")
    print("==================================================")

if __name__ == "__main__":
    main()
