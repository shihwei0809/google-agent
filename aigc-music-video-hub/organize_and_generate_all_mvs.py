import os
import re
import math
import shutil
import subprocess
import sys
from pathlib import Path

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = Path(r"c:\GOOGLE ANGET\aigc-music-video-hub")
output_root = workspace_dir / "創作庫"

# Master 34 scenes
master_scenes = [
    {
        "id": 1,
        "name": "廠區遠景",
        "image": "A modern high-tech chemical refinery at night, glowing neon green and blue tubes, tall distillation towers, futuristic cyberpunk aesthetic, highly detailed, 8k.",
        "motion": "Slow drone shot panning over the refinery, neon lights pulsing along pipelines, steam rising gently, cinematic movement."
    },
    {
        "id": 2,
        "name": "反應槽近景",
        "image": "Close-up of a polished stainless steel chemical reactor, glowing blue valves, metal pipelines, high-tech industrial facility, cyber-tech aesthetic, 8k.",
        "motion": "Slow camera slide showing the pipes and valves, glowing blue liquid indicator lights blinking, subtle steam venting."
    },
    {
        "id": 3,
        "name": "分子模擬",
        "image": "Holographic interface showing advanced chemical engineering simulation of a molecule, glowing blue and green atoms connecting, dark tech laboratory, 8k.",
        "motion": "Holographic molecular design interface spinning slowly, digital chemical data streaming on screen."
    },
    {
        "id": 4,
        "name": "全息藍圖",
        "image": "A glowing 3D holographic molecular model of a complex solvent structure floating over a digital blueprint interface, digital cybernetic grid background, neon cyan and green, 8k.",
        "motion": "The holographic molecule rotating slowly with subtle camera tilt, particles floating in air."
    },
    {
        "id": 5,
        "name": "精細分裝",
        "image": "An automated high-tech chemical analysis laboratory with robotic pipette dispensing glowing cyan liquid into glass vials, futuristic cleanroom, 8k.",
        "motion": "Robotic needle dispensing liquid, liquid splashing slightly inside, camera focus shifts, high precision."
    },
    {
        "id": 6,
        "name": "QC 檢驗",
        "image": "A chemist in a white lab coat inspecting a flask of pure blue glowing solvent, advanced chemical quality control laboratory, glowing display screens, 8k.",
        "motion": "Close up of the chemist swirling the glass flask, background laboratory equipment lights blinking."
    },
    {
        "id": 7,
        "name": "無塵室入口",
        "image": "A futuristic cleanroom air shower entrance, bright yellow warning lights, industrial robotic arms, ultra-clean environment, cyberpunk neon green accents, 8k.",
        "motion": "A slow camera pushing forward into the air shower entrance, yellow lights blinking, robotic arms moving."
    },
    {
        "id": 8,
        "name": "晶圓傳送",
        "image": "A high-tech photolithography machine, robotic gripper loading a shiny silicon wafer cassette, amber safety lights, semiconductor fabrication facility, 8k.",
        "motion": "Robotic arm lifting the wafer pod, smooth mechanical movement, warning lights flashing in background."
    },
    {
        "id": 9,
        "name": "溶劑噴灑",
        "image": "A macro close-up of high-purity chemical solvent being sprayed onto a reflective silicon wafer, microscopic liquid droplets, semiconductor cleaning process, 8k.",
        "motion": "Liquid ripples and waves washing across the reflective wafer surface, slow motion spray."
    },
    {
        "id": 10,
        "name": "晶圓清洗",
        "image": "A silicon wafer spinning rapidly on a spindle, washed by glowing crystal-clear solvent, microscopic droplets flying, high-precision lab, 8k.",
        "motion": "Silicon wafer spinning fast, liquid washing across the surface, light reflecting off water droplets."
    },
    {
        "id": 11,
        "name": "烘烤乾燥",
        "image": "A silicon wafer inside a high-tech heating chamber, glowing orange heating elements, chemical vapor evaporating, precision thermal curing, 8k.",
        "motion": "Orange heating elements pulsing, thin chemical vapor rising and evaporating from the wafer."
    },
    {
        "id": 12,
        "name": "黃光區天車",
        "image": "Overhead view of an automated material handling system (AMHS) transporting wafer pods in a semiconductor fab, glowing yellow safety lights, 8k.",
        "motion": "Automated overhead hoist transport system moving along rails in yellow lit cleanroom, smooth gliding motion."
    },
    {
        "id": 13,
        "name": "DUV 雷射曝光",
        "image": "A deep ultraviolet DUV laser engraving circuit lines on a silicon wafer, glowing purple light paths, futuristic chip fabrication process, 8k.",
        "motion": "Laser beam scanning across the wafer, purple light carving nano circuits, bright sparks flashing."
    },
    {
        "id": 14,
        "name": "EUV 極紫外光顯影",
        "image": "An EUV light beam scanner projecting complex nanoscale patterns onto a silicon wafer, intense golden and purple laser glow, high-tech semiconductor fab, 8k.",
        "motion": "EUV scanner projecting circuit patterns, gold laser beams sweeping across the silicon wafer surface."
    },
    {
        "id": 15,
        "name": "電路形成",
        "image": "An extreme close up of a silicon wafer with gold and violet nanoscale circuit lines forming, glowing electric currents, advanced microprocessor, 8k.",
        "motion": "Circuit lines lighting up with electric currents, energy pulsing across the microchip tracks."
    },
    {
        "id": 16,
        "name": "晶片切割",
        "image": "An automated high-speed laser dicing machine cutting a silicon wafer into individual microchips, bright yellow sparks, precision mechanical blades, 8k.",
        "motion": "Laser cutting the wafer, yellow sparks flying, precision robotic mechanics, macro zoom."
    },
    {
        "id": 17,
        "name": "先進封裝",
        "image": "A robotic arm placing a tiny microchip onto a green substrate, advanced semiconductor packaging process, mechanical precision, glowing blue circuits, 8k.",
        "motion": "Robotic arm placing the chip, glowing blue circuits lighting up, smooth robotic assembly."
    },
    {
        "id": 18,
        "name": "終端晶片展示",
        "image": "A glowing futuristic CPU chip on a motherboard, neon pathways pulsing with cyan and violet light, high-speed computer processor, 8k.",
        "motion": "Cinematic macro zoom-in on the CPU, neon circuitry lines pulsing with data traffic."
    },
    {
        "id": 19,
        "name": "綠色工廠",
        "image": "A modern chemical plant surrounded by wind turbines and solar panels, green sunrise, clean energy theme, sustainable ESG facility, 8k.",
        "motion": "Slow camera sweep of the plant, wind turbines spinning in background, solar panels reflecting the sun."
    },
    {
        "id": 20,
        "name": "廢水回收",
        "image": "A high-tech water purification facility, clean water flowing rapidly through glass tubes, glowing green digital leaf overlay, eco-friendly tech, 8k.",
        "motion": "Clean water flowing through tubes, bubbles rising, green leaf icon pulsing on digital overlay screen."
    },
    {
        "id": 21,
        "name": "溶劑回收管線",
        "image": "Emerald green recycled solvent flowing through glass tubes in a circular loop, bubbles, sustainable chemical recycling plant, eco tech, 8k.",
        "motion": "Recycled solvent flowing rapidly, bubbles rising, glowing green indicators flashing."
    },
    {
        "id": 22,
        "name": "綠色循環標章",
        "image": "A 3D holographic green leaf icon merging with a spinning chemical molecular formula, glowing cyan and green lines, clean future tech background, 8k.",
        "motion": "Holographic leaf icon merging with formula, glowing lines rotating in 3D space."
    },
    {
        "id": 23,
        "name": "儲罐裝載",
        "image": "An automated bottling line filling containers with clear liquid, smooth mechanical nozzles, conveyor belt, high-tech industrial packaging, 8k.",
        "motion": "Bottling machine nozzles moving up and down, filling containers, conveyor belt moving."
    },
    {
        "id": 24,
        "name": "廠區安全巡檢",
        "image": "A professional chemical plant inspector wearing safety gear and a helmet, walking and inspecting pipes in a modern high-tech refinery during sunset, wind turbines and solar panels in the distance, highly detailed, 8k.",
        "motion": "Technician walking slowly and checking valves, clipboard in hand, wind turbines spinning in soft sunset background."
    },
    {
        "id": 25,
        "name": "高效能伺服器",
        "image": "Rows of server racks with neon green liquid cooling tubes, high-speed AI processors, blinking data streams, futuristic server room, 8k.",
        "motion": "Camera moving forward through server racks, liquid cooling tubes glowing, indicator lights blinking."
    },
    {
        "id": 26,
        "name": "超級電腦運算",
        "image": "Abstract visualization of massive data transferring, lines of light and data streams rushing, glowing gold and blue paths on dark background, 8k.",
        "motion": "Data streams rushing, lines of light pulsing and transferring rapidly across the screen."
    },
    {
        "id": 27,
        "name": "物流裝箱",
        "image": "Inside a modern automated warehouse, robotic forklifts carrying cargo boxes marked with green ESG logos, sleek metallic shelves, 8k.",
        "motion": "Robotic forklifts moving boxes, wheels turning, automated warehouse systems operating."
    },
    {
        "id": 28,
        "name": "高雄港裝船",
        "image": "Giant gantry cranes loading green shipping containers onto a massive cargo ship, Kaohsiung harbor during a beautiful orange sunset, golden hour, 8k.",
        "motion": "Time-lapse of cranes loading cargo, sunset reflections on ocean water."
    },
    {
        "id": 29,
        "name": "貨輪出海",
        "image": "A majestic cargo container ship sailing across the open ocean under a beautiful orange sunset sky, cinematic drone shot, 8k.",
        "motion": "Cargo ship sailing forward on ocean waves, golden sunset reflecting on water."
    },
    {
        "id": 30,
        "name": "科技微觀終幕",
        "image": "A shining microchip zooming out into a constellation of connected data points and constellations, bright golden and blue lights, epic finale, 8k.",
        "motion": "Cinematic zoom-out from microchip to global data network, lights pulsing, epic climax."
    },
    {
        "id": 31,
        "name": "ESG永續報告",
        "image": "A futuristic digital dashboard displaying ESG sustainability metrics and carbon reduction charts inside a modern corporate office, glowing green and blue graphs, high-tech interface, highly detailed, 8k.",
        "motion": "Slow camera pan across the glowing ESG dashboard, green charts showing emission decrease, numbers updating in real-time."
    },
    {
        "id": 32,
        "name": "智慧中控室",
        "image": "A futuristic intelligent chemical control room with a giant curved screen displaying real-time automation data and refinery status, blue and green neon lights, highly detailed, 8k.",
        "motion": "Camera glides through the control room, displaying glowing monitoring interface, data streaming."
    },
    {
        "id": 33,
        "name": "廠房屋頂太陽能",
        "image": "A modern chemical plant roof covered with sleek solar panels under a clear blue sky, with giant white wind turbines spinning in the green fields in the distance, highly detailed, 8k.",
        "motion": "A gentle drone lift showing sun reflections on solar panels, wind turbines rotating in soft background."
    },
    {
        "id": 34,
        "name": "未來晶片應用",
        "image": "A high-tech autonomous electric car driving through a futuristic smart city at sunset, neon light trails, transparent digital overlay highlighting the internal processor, highly detailed, 8k.",
        "motion": "Electric car speeding forward with beautiful neon trails, camera zooms into transparent processor overlay."
    }
]

image_mapping = {
    0: "01_廠區遠景.png",
    1: "02_反應槽近景.png",
    2: "03_分子模擬.png",
    3: "04_全息藍圖.png",
    4: "05_精細分裝.png",
    5: "06_QC_檢驗.png",
    6: "07_無塵室入口.png",
    7: "08_晶圓傳送.png",
    8: "09_溶劑噴灑.png",
    9: "10_晶圓清洗.png",
    10: "11_烘烤乾燥.png",
    11: "12_黃光區天車.png",
    12: "13_DUV_雷射曝光.png",
    13: "14_EUV_極紫外光顯影.png",
    14: "15_電路形成.png",
    15: "16_晶片切割.png",
    16: "17_先進封裝.png",
    17: "18_終端晶片展示.png",
    18: "19_綠色工廠.png",
    19: "20_廢水回收.png",
    20: "21_溶劑回收管線.png",
    21: "22_綠色循環標章.png",
    22: "23_儲罐裝載.png",
    23: "24_廠區安全巡檢.png",
    24: "25_高效能伺服器.png",
    25: "26_超級電腦運算.png",
    26: "27_物流裝箱.png",
    27: "28_高雄港裝船.png",
    28: "29_貨輪出海.png",
    29: "30_科技微觀終幕.png",
    30: "31_ESG永續報告.png",
    31: "32_智慧中控室.png",
    32: "33_廠房屋頂太陽能.png",
    33: "34_未來晶片應用.png"
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

def main():
    if not output_root.exists():
        print(f"錯誤: 找不到創作庫資料夾: {output_root}")
        return

    # 1. Scan for loose MP3 files in 創作庫
    loose_mp3s = [f for f in os.listdir(output_root) if f.endswith(".mp3")]
    
    if loose_mp3s:
        print(f"發現 {len(loose_mp3s)} 個未歸類的 MP3 檔案，開始自動建立資料夾並移動...")
        for mp3 in loose_mp3s:
            song_name = os.path.splitext(mp3)[0]
            song_dir = output_root / song_name
            
            # Create folder
            song_dir.mkdir(exist_ok=True)
            
            # Move file
            src_path = output_root / mp3
            dest_path = song_dir / mp3
            
            # If target already exists, remove it first
            if dest_path.exists():
                os.remove(dest_path)
            shutil.move(str(src_path), str(dest_path))
            print(f"  [✓] 移動 {mp3} -> 創作庫/{song_name}/")
        print("未歸類 MP3 移動完畢。\n")
    else:
        print("未在 創作庫 根目錄下發現新的未歸類 MP3。\n")

    # 2. Iterate through all folders in 創作庫 and generate storyboards if needed
    print("開始掃描 創作庫 底下的歌曲資料夾並產生 Vids 故事板...")
    folders = sorted([d for d in os.listdir(output_root) if (output_root / d).is_dir()])
    
    for folder in folders:
        song_dir = output_root / folder
        
        # Find MP3 inside this folder
        mp3s_inside = [f for f in os.listdir(song_dir) if f.endswith(".mp3")]
        if not mp3s_inside:
            continue
            
        mp3_file = mp3s_inside[0]
        mp3_path = song_dir / mp3_file
        
        # Read duration
        duration = get_audio_duration(mp3_path)
        if not duration:
            print(f"  [X] 無法讀取歌曲長度: {folder}")
            continue
            
        num_scenes = math.ceil(duration / 8.0)
        time_per_scene = duration / num_scenes
        
        # Check if vids_storyboard_prompts.md already exists
        md_path = song_dir / "vids_storyboard_prompts.md"
        
        # Even if it exists, let's regenerate it to make sure it's accurate and fresh
        print(f"➔ 處理資料夾: 【{folder}】 (時長: {duration:.2f} 秒, 場景數: {num_scenes})")
        
        # Sample scenes
        sampled_scenes = []
        for i in range(num_scenes):
            idx = int(i * (len(master_scenes) - 1) / (num_scenes - 1)) if num_scenes > 1 else 0
            sampled_scenes.append((idx, master_scenes[idx]))
            
        with open(md_path, "w", encoding="utf-8") as out:
            out.write(f"# 🎬 勝一化學 AI 音樂影片 — Vids 專屬故事板提示詞 (8秒上限優化版)\n\n")
            out.write(f"本文件為 【{folder}】 專屬量身打造。\n\n")
            out.write(f"### 📊 影片參數規格：\n")
            out.write(f"* **歌曲總長度**：`{duration:.2f} 秒`\n")
            out.write(f"* **建議場景總數**：`{num_scenes} 頁` (可完美平分時間，防範 Vids 單場景 8 秒限制)\n")
            out.write(f"* **每場景播放時間**：`{time_per_scene:.2f} 秒`\n\n")
            out.write(f"---\n\n")
            out.write(f"## 📋 完整 {num_scenes} 場景提示詞與素材對照表\n\n")

            for scene_num, (orig_idx, scene) in enumerate(sampled_scenes, 1):
                out.write(f"### 📌 場景 {scene_num:02d}：{scene['name']}\n")
                out.write(f"* ⏱️ **建議播放長度**：`{time_per_scene:.2f} 秒`\n")
                
                if orig_idx in image_mapping:
                    filename = image_mapping[orig_idx]
                    out.write(f"* 🟢 **圖片狀態**：`【已生成本機圖片】` (你可以直接在資料夾內的 `圖片/` 目錄找到此檔上傳)\n")
                    out.write(f"* 📂 **圖片檔名**：`{filename}`\n")
                else:
                    out.write(f"* 🔴 **圖片狀態**：`【需在 Vids 中使用 AI 生成圖片】` (請複製下方 1. 圖片生成提示詞)\n")

                out.write(f"* ✍️ **1. 圖片生成提示詞 (Text-to-Image)**：\n")
                out.write(f"  ```text\n  {scene['image']}\n  ```\n")
                out.write(f"* ✍️ **2. 動態生成提示詞 (Image-to-Video / Motion)**：\n")
                out.write(f"  ```text\n  {scene['motion']}\n  ```\n\n")
                out.write(f"---\n\n")
        print(f"  [✓] 成功產生故事板說明檔: {md_path.name}")
        print("-" * 50)
        
    print("\n🎉 所有歌曲的故事板說明檔處理完畢！")

if __name__ == "__main__":
    main()
