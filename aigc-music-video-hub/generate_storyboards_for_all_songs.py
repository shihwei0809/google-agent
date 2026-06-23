import os
import re
import math
import sys
import subprocess

# Configure sys.stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

workspace_dir = os.path.dirname(os.path.abspath(__file__))
output_root = os.path.join(workspace_dir, "創作庫")

# Master 30 scenes
master_scenes = [   {   'id': 1,
        'image': 'A modern high-tech chemical refinery at night, glowing neon green and blue tubes, tall distillation '
                 'towers, futuristic green energy refinery, sunset lighting, clean eco-friendly facility, highly '
                 'detailed, photorealistic, 8k.',
        'motion': 'Slow drone shot panning over the refinery, neon lights pulsing along pipelines, steam rising '
                  'gently, cinematic smooth movement.',
        'name': '廠區遠景'},
    {   'id': 2,
        'image': 'Close-up of a polished stainless steel chemical reactor, glowing blue valves, metal pipelines, '
                 'high-tech industrial facility, futuristic green energy refinery, sunset lighting, clean eco-friendly '
                 'facility, highly detailed, photorealistic, 8k.',
        'motion': 'Slow camera slide showing the pipes and valves, glowing blue liquid indicator lights blinking, '
                  'subtle steam venting, smooth flow.',
        'name': '反應槽近景'},
    {   'id': 3,
        'image': 'Holographic interface showing advanced chemical engineering simulation of a molecule, glowing blue '
                 'and green atoms connecting, dark tech laboratory, futuristic cleanroom aesthetic, neon green and '
                 'blue accents, highly detailed, photorealistic, 8k.',
        'motion': 'Holographic molecular design interface spinning slowly, digital chemical data streaming on screen, '
                  'gentle camera rotation.',
        'name': '分子模擬'},
    {   'id': 4,
        'image': 'A glowing 3D holographic molecular model of a complex solvent structure floating over a digital '
                 'blueprint interface, digital cybernetic grid background, neon cyan and green, futuristic cleanroom '
                 'aesthetic, highly detailed, photorealistic, 8k.',
        'motion': 'The holographic molecule rotating slowly with subtle camera tilt, particles floating in air, gentle '
                  'panning.',
        'name': '全息藍圖'},
    {   'id': 5,
        'image': 'An automated high-tech chemical analysis laboratory with robotic pipette dispensing glowing cyan '
                 'liquid into glass vials, futuristic cleanroom aesthetic, neon green and blue accents, highly '
                 'detailed, photorealistic, 8k.',
        'motion': 'Robotic needle dispensing liquid, liquid splashing slightly inside, camera focus shifts, slow and '
                  'high precision, no morphing.',
        'name': '精細檢驗'},
    {   'id': 6,
        'image': 'A chemist in a white lab coat inspecting a flask of pure blue glowing solvent, advanced chemical '
                 'quality control laboratory, glowing display screens, futuristic cleanroom aesthetic, neon green and '
                 'blue accents, highly detailed, photorealistic, 8k.',
        'motion': 'Close up of the chemist swirling the glass flask slowly, background laboratory equipment lights '
                  'blinking gently.',
        'name': 'QC 檢驗'},
    {   'id': 7,
        'image': 'A futuristic cleanroom air shower entrance, bright yellow warning lights, industrial robotic arms, '
                 'ultra-clean environment, cyberpunk neon green accents, highly detailed, photorealistic, 8k.',
        'motion': 'A slow camera pushing forward into the air shower entrance, yellow lights blinking gently, robotic '
                  'arms moving slowly.',
        'name': '無塵室入口'},
    {   'id': 8,
        'image': 'A high-tech photolithography machine, robotic gripper loading a shiny silicon wafer cassette, amber '
                 'safety lights, semiconductor fabrication facility, futuristic cleanroom aesthetic, neon green and '
                 'blue accents, highly detailed, photorealistic, 8k.',
        'motion': 'Robotic arm lifting the wafer pod, smooth mechanical movement, warning lights flashing slowly in '
                  'background.',
        'name': '晶圓傳送'},
    {   'id': 9,
        'image': 'A macro close-up of high-purity chemical solvent being sprayed onto a reflective silicon wafer, '
                 'microscopic liquid droplets, semiconductor cleaning process, futuristic cleanroom aesthetic, neon '
                 'green and blue accents, highly detailed, photorealistic, 8k.',
        'motion': 'Liquid ripples and waves washing across the reflective wafer surface, slow motion spray, smooth '
                  'liquid flow.',
        'name': '溶劑噴灑'},
    {   'id': 10,
        'image': 'A silicon wafer spinning rapidly on a spindle, washed by glowing crystal-clear solvent, microscopic '
                 'droplets flying, high-precision lab, futuristic cleanroom aesthetic, neon green and blue accents, '
                 'highly detailed, photorealistic, 8k.',
        'motion': 'Silicon wafer spinning fast, liquid washing across the surface, light reflecting off water '
                  'droplets, smooth high-speed rotation.',
        'name': '晶圓清洗'},
    {   'id': 11,
        'image': 'A silicon wafer inside a high-tech heating chamber, soft glowing orange thermographic heating '
                 'elements, chemical vapor evaporating gently, precision thermal curing, futuristic cleanroom '
                 'aesthetic, highly detailed, photorealistic, 8k.',
        'motion': 'Orange heating elements pulsing, thin chemical vapor rising and evaporating from the wafer slowly, '
                  'gentle heat haze.',
        'name': '烘烤乾燥'},
    {   'id': 12,
        'image': 'Overhead view of an automated material handling system (AMHS) transporting wafer pods in a '
                 'semiconductor fab, glowing yellow safety lights, futuristic cleanroom aesthetic, highly detailed, '
                 'photorealistic, 8k.',
        'motion': 'Automated overhead hoist transport system moving along rails in yellow lit cleanroom, smooth '
                  'gliding motion, slow panning.',
        'name': '黃光區天車'},
    {   'id': 13,
        'image': 'A deep ultraviolet DUV laser engraving circuit lines on a silicon wafer, glowing purple light paths, '
                 'futuristic chip fabrication process, futuristic cleanroom aesthetic, neon green and blue accents, '
                 'highly detailed, photorealistic, 8k.',
        'motion': 'Laser beam scanning across the wafer, purple light carving nano circuits, glowing purple circuit '
                  'paths forming cleanly, no sparks.',
        'name': 'DUV 雷射曝光'},
    {   'id': 14,
        'image': 'An EUV light beam scanner projecting complex nanoscale patterns onto a silicon wafer, intense golden '
                 'and purple laser glow, high-tech semiconductor fab, futuristic cleanroom aesthetic, neon green and '
                 'blue accents, highly detailed, photorealistic, 8k.',
        'motion': 'EUV scanner projecting circuit patterns, gold laser beams sweeping across the silicon wafer surface '
                  'smoothly, no sparks.',
        'name': 'EUV 極紫外光顯影'},
    {   'id': 15,
        'image': 'An extreme close up of a silicon wafer with gold and violet nanoscale circuit lines forming, glowing '
                 'electric currents, advanced microprocessor, futuristic cleanroom aesthetic, neon green and blue '
                 'accents, highly detailed, photorealistic, 8k.',
        'motion': 'Circuit lines lighting up with electric currents, energy pulsing across the microchip tracks '
                  'smoothly, no sparks.',
        'name': '電路形成'},
    {   'id': 16,
        'image': 'An automated high-speed laser dicing machine cutting a silicon wafer into individual microchips, '
                 'high-precision water cooling mist, precision mechanical blades, futuristic cleanroom aesthetic, neon '
                 'green and blue accents, highly detailed, photorealistic, 8k.',
        'motion': 'Laser cutting the wafer, liquid cooling mist, clean laser dicing process, precision robotic '
                  'mechanics, macro zoom, no sparks.',
        'name': '晶片切割'},
    {   'id': 17,
        'image': 'A robotic arm placing a tiny microchip onto a green substrate, advanced semiconductor packaging '
                 'process, mechanical precision, glowing blue circuits, futuristic cleanroom aesthetic, neon green and '
                 'blue accents, highly detailed, photorealistic, 8k.',
        'motion': 'Robotic arm placing the chip, glowing blue circuits lighting up, smooth robotic assembly, slow '
                  'zoom.',
        'name': '先進封裝'},
    {   'id': 18,
        'image': 'A glowing futuristic CPU chip on a motherboard, neon pathways pulsing with cyan and violet light, '
                 'high-speed computer processor, futuristic AI server room, neon blue and green liquid cooling, highly '
                 'detailed, photorealistic, 8k.',
        'motion': 'Cinematic macro zoom-in on the CPU, neon circuitry lines pulsing with data traffic, steady camera '
                  'movement.',
        'name': '終端晶片展示'},
    {   'id': 19,
        'image': 'A modern chemical plant surrounded by wind turbines and solar panels, green sunrise, clean energy '
                 'theme, sustainable ESG facility, futuristic green energy refinery, highly detailed, photorealistic, '
                 '8k.',
        'motion': 'Slow camera sweep of the plant, wind turbines spinning slowly in background, solar panels '
                  'reflecting the sun.',
        'name': '綠色工廠'},
    {   'id': 20,
        'image': 'A high-tech water purification facility, clean water flowing rapidly through glass tubes, glowing '
                 'green digital leaf overlay, eco-friendly tech, futuristic green energy refinery, highly detailed, '
                 'photorealistic, 8k.',
        'motion': 'Clean water flowing through tubes, bubbles rising slowly, green leaf icon pulsing on digital '
                  'overlay screen.',
        'name': '廢水回收'},
    {   'id': 21,
        'image': 'Emerald green recycled solvent flowing through glass tubes in a circular loop, bubbles, sustainable '
                 'chemical recycling plant, eco tech, futuristic green energy refinery, highly detailed, '
                 'photorealistic, 8k.',
        'motion': 'Recycled solvent flowing rapidly, bubbles rising, glowing green indicators flashing slowly.',
        'name': '溶劑回收管線'},
    {   'id': 22,
        'image': 'A 3D holographic green leaf icon merging with a spinning chemical molecular formula, glowing cyan '
                 'and green lines, clean future tech background, futuristic cleanroom aesthetic, highly detailed, '
                 'photorealistic, 8k.',
        'motion': 'Holographic leaf icon merging with formula, glowing lines rotating slowly in 3D space.',
        'name': '綠色循環標章'},
    {   'id': 23,
        'image': 'A professional corporate photograph of a large chemical Isotank container being lifted and hung by a giant yellow gantry crane onto a white transport truck container bed inside a modern clean refinery facility, bright daylight, blue sky, photorealistic, 8k.',
        'motion': 'Automated transport vehicle adjusting the tank container, loading bay crane lifting the container slowly, smooth flow.',
        'name': '吊掛isotank'},
    {   'id': 24,
        'image': 'A professional chemical plant inspector wearing safety gear and a helmet, walking and inspecting '
                 'pipes in a modern high-tech refinery during sunset, wind turbines and solar panels in the distance, '
                 'futuristic green energy refinery, highly detailed, photorealistic, 8k.',
        'motion': 'Technician walking slowly and checking valves, clipboard in hand, wind turbines spinning in soft '
                  'sunset background.',
        'name': '廠區安全巡檢'},
    {   'id': 25,
        'image': 'A professional corporate photograph of a white chemical tanker truck loading and unloading liquid into giant green and steel storage tanks using hoses in a modern chemical refinery, bright daylight, photorealistic, 8k.',
        'motion': 'Liquid flowing through hoses, truck engine idling, slow panning camera.',
        'name': '儲罐裝載'},
    {   'id': 26,
        'image': 'Abstract visualization of massive data transferring, lines of light and data streams rushing, '
                 'glowing gold and blue paths on dark background, futuristic AI server room, highly detailed, '
                 'photorealistic, 8k.',
        'motion': 'Data streams rushing, lines of light pulsing and transferring slowly and steadily across the '
                  'screen.',
        'name': '超級電腦運算'},
    {   'id': 27,
        'image': 'Inside a modern automated warehouse, robotic forklifts carrying cargo boxes marked with green ESG '
                 'logos, sleek metallic shelves, futuristic green energy refinery, highly detailed, photorealistic, '
                 '8k.',
        'motion': 'Robotic forklifts moving boxes, wheels turning, automated warehouse systems operating slowly.',
        'name': '物流裝箱'},
    {   'id': 28,
        'image': 'Giant gantry cranes loading green shipping containers onto a massive cargo ship, Kaohsiung harbor '
                 'during a beautiful orange sunset, golden hour, clean environment, highly detailed, photorealistic, '
                 '8k.',
        'motion': 'Slow pan of cranes loading cargo, sunset reflections on ocean water, smooth camera motion.',
        'name': '高雄港裝船'},
    {   'id': 29,
        'image': 'A majestic cargo container ship sailing across the open ocean under a beautiful orange sunset sky, '
                 'cinematic drone shot, clean environment, highly detailed, photorealistic, 8k.',
        'motion': 'Cargo ship sailing forward on ocean waves, golden sunset reflecting on water, slow drone pan.',
        'name': '貨輪出海'},
    {   'id': 30,
        'image': 'A shining microchip zooming out into a constellation of connected data points and constellations, '
                 'bright golden and blue lights, epic finale, futuristic AI server room, highly detailed, '
                 'photorealistic, 8k.',
        'motion': 'Cinematic slow zoom-out from microchip to global data network, lights pulsing, smooth transition.',
        'name': '科技微觀終幕'},
    {   'id': 31,
        'image': 'A futuristic digital dashboard displaying ESG sustainability metrics and carbon reduction charts '
                 'inside a modern corporate office, glowing green and blue graphs, high-tech interface, modern '
                 'corporate office, highly detailed, photorealistic, 8k.',
        'motion': 'Slow camera pan across the glowing ESG dashboard, green charts showing emission decrease, numbers '
                  'updating in real-time.',
        'name': 'ESG永續報告'},
    {   'id': 32,
        'image': 'A futuristic intelligent chemical control room with a giant curved screen displaying real-time '
                 'automation data and refinery status, blue and green neon lights, futuristic green energy refinery, '
                 'highly detailed, photorealistic, 8k.',
        'motion': 'Camera glides slowly through the control room, displaying glowing monitoring interface, data '
                  'streaming.',
        'name': '智慧中控室'},
    {   'id': 33,
        'image': 'A modern chemical plant roof covered with sleek solar panels under a clear blue sky, with giant '
                 'white wind turbines spinning in the green fields in the distance, futuristic green energy refinery, '
                 'highly detailed, photorealistic, 8k.',
        'motion': 'A gentle drone lift showing sun reflections on solar panels, wind turbines rotating slowly in '
                  'background.',
        'name': '廠房屋頂太陽能'},
    {   'id': 34,
        'image': 'A high-tech autonomous electric car driving through a futuristic smart city at sunset, neon light '
                 'trails, transparent digital overlay highlighting the internal processor, highly detailed, '
                 'photorealistic, 8k. Clean aesthetic, no fire, no sparks.',
        'motion': 'Electric car speeding forward with beautiful neon trails, camera zooms slowly into transparent '
                  'processor overlay.',
        'name': '未來晶片應用'},
    {   'id': 35,
        'image': 'A modern chemical research laboratory, chemists in clean suits analyzing high-purity formulas under '
                 'blue lighting, advanced spectrometers, futuristic cleanroom aesthetic, neon green and blue accents, '
                 'highly detailed, photorealistic, 8k. Cleanroom environment, no sparks, no flames.',
        'motion': 'Chemist adjusting laboratory equipment, liquid dropping into a beaker slowly, glowing screens '
                  'updating.',
        'name': '研發化驗室'},
    {   'id': 36,
        'image': 'Rows of server racks with neon green liquid cooling tubes, high-speed AI processors, blinking data streams, futuristic AI server room, neon blue and green liquid cooling, highly detailed, photorealistic, 8k.',
        'motion': 'Camera moving forward slowly through server racks, liquid cooling tubes glowing, indicator lights blinking.',
        'name': '高效能伺服器'},
    {   'id': 37,
        'image': 'Holographic digital globe displaying trade and logistics routes from Kaohsiung port to global '
                 'technology centers, neon light paths, clean environment, highly detailed, photorealistic, 8k. No '
                 'fire, no sparks.',
        'motion': 'Holographic globe rotating slowly, data lines pulsing along shipping routes.',
        'name': '全球智慧物流'},
    {   'id': 38,
        'image': 'A close-up of a high-performance stacked 3D IC package, neon micro-channels glowing with blue and '
                 'violet currents, futuristic cleanroom aesthetic, neon green and blue accents, highly detailed, '
                 'photorealistic, 8k. Clean digital design, no sparks.',
        'motion': 'Glowing energy tracks lighting up across the stacked microchip layers slowly.',
        'name': '晶片立體封裝'},
    {   'id': 39,
        'image': 'Real-time sustainability dashboard showing zero-emission data and energy efficiency metrics in the '
                 'chemical plant, glowing green leaf accents, modern corporate office, highly detailed, '
                 'photorealistic, 8k.',
        'motion': 'Soft pan across the monitoring interface, carbon reduction graphs updating slowly.',
        'name': '碳中和監測'},
    {   'id': 40,
        'image': 'Futuristic distillation column with glowing cyan liquid flowing inside, showing high-precision '
                 'filtration at the molecular level, futuristic cleanroom aesthetic, neon green and blue accents, '
                 'highly detailed, photorealistic, 8k. Cleanroom environment, no sparks.',
        'motion': 'Liquid flowing through high-tech filtration columns slowly, small bubbles rising.',
        'name': '高分子純化'},
    {   'id': 41,
        'image': 'Smart sensor nodes blinking green in a cleanroom, digital overlay displaying air quality index and '
                 'particle count, futuristic cleanroom aesthetic, neon green and blue accents, highly detailed, '
                 'photorealistic, 8k.',
        'motion': 'Sensor lights pulsing gently, digital stats updating on the overlay, smooth panning.',
        'name': '環境安全監測'},
    {   'id': 42,
        'image': 'Robotic arms filling and sealing metallic drums marked with green recycling logos on an automated '
                 'conveyor line, futuristic green energy refinery, highly detailed, photorealistic, 8k.',
        'motion': 'Robotic arm stamping the logo, conveyor belt moving drums forward slowly.',
        'name': '綠色包裝桶裝'},
    {   'id': 43,
        'image': 'Automated machine washing a Front Opening Unified Pod (FOUP) wafer carrier with high-pressure '
                 'solvent spray, glowing blue status lights, futuristic cleanroom aesthetic, neon green and blue '
                 'accents, highly detailed, photorealistic, 8k.',
        'motion': 'Spray nozzles spraying liquid inside the FOUP carrier, steam clearing slowly.',
        'name': '晶圓載具清洗'},
    {   'id': 44,
        'image': 'Rows of high-density server cabinets, pulsing blue LED lights, liquid cooling tubes running along '
                 'the racks, futuristic AI server room, highly detailed, photorealistic, 8k.',
        'motion': 'Camera moving down the server aisle slowly, status indicator lights flashing gently.',
        'name': '雲端運算中心'},
    {   'id': 45,
        'image': 'High-capacity battery storage systems adjacent to a solar array, modern industrial design, clean '
                 'green fields, futuristic green energy refinery, highly detailed, photorealistic, 8k.',
        'motion': 'Slow drone pan showing battery modules and solar panels reflecting sunlight, smooth camera flow.',
        'name': '綠能儲能設備'},
    {   'id': 46,
        'image': 'High-magnification optical scanner inspecting a silicon wafer surface for nanoscale defects, glowing '
                 'scanning laser line, futuristic cleanroom aesthetic, neon green and blue accents, highly detailed, '
                 'photorealistic, 8k. No sparks, no fire.',
        'motion': 'Laser scanning line sweeping across the wafer slowly, glowing green grid overlay.',
        'name': '微小缺陷檢測'},
    {   'id': 47,
        'image': 'Automated mixing system blending electronic chemicals inside a glass vessel, swirling colorful '
                 'liquid, high-tech lab, futuristic cleanroom aesthetic, highly detailed, photorealistic, 8k.',
        'motion': 'Liquid blending in a vortex inside the vessel, bubbles circulating slowly.',
        'name': '配方自動混合'},
    {   'id': 48,
        'image': 'Advanced distillation tower operating under sunset, solar panels mounted on the walls, eco-friendly '
                 'energy integration, futuristic green energy refinery, highly detailed, photorealistic, 8k.',
        'motion': 'Slow pan of the distillation towers with sunset clouds moving slowly, solar panels reflecting the '
                  'sky.',
        'name': '低碳精餾製程'},
    {   'id': 49,
        'image': 'Wafer placed on a hotplate in a photolithography track, soft orange thermal glow, chemical solvent '
                 'evaporating, futuristic cleanroom aesthetic, highly detailed, photorealistic, 8k. Cleanroom '
                 'environment, no flames, no sparks.',
        'motion': 'Orange heating elements glowing, subtle vapor rising and dispersing slowly.',
        'name': '晶圓表面烘烤'},
    {   'id': 50,
        'image': 'An inspiring closing shot of the high-tech chemical plant surrounded by lush green forests and a '
                 'clear blue sky, solar panels and wind turbines operating, futuristic green energy refinery, highly '
                 'detailed, photorealistic, 8k.',
        'motion': 'Slow drone rising, showing the clean facility harmonized with the surrounding green landscape, '
                  'smooth flight.',
        'name': '科技與綠能共榮'}]

image_mapping = {
    0: "01_廠區遠景.png",
    1: "02_反應槽近景.png",
    2: "03_分子模擬.png",
    3: "04_全息藍圖.png",
    4: "05_精細檢驗.png",
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
    22: "23_吊掛isotank.png",
    23: "24_廠區安全巡檢.png",
    24: "25_儲罐裝載.png",
    25: "26_超級電腦運算.png",
    26: "27_物流裝箱.png",
    27: "28_高雄港裝船.png",
    28: "29_貨輪出海.png",
    29: "30_科技微觀終幕.png",
    30: "31_ESG永續報告.png",
    31: "32_智慧中控室.png",
    32: "33_廠房屋頂太陽能.png",
    33: "34_未來晶片應用.png",
    34: "35_研發化驗室.png",
    35: "25_高效能伺服器.png",
    36: "37_全球智慧物流.png",
    37: "38_晶片立體封裝.png",
    38: "39_碳中和監測.png",
    39: "40_高分子純化.png",
    40: "41_環境安全監測.png",
    41: "42_綠色包裝桶裝.png",
    42: "43_晶圓載具清洗.png",
    43: "44_雲端運算中心.png",
    44: "45_綠能儲能設備.png",
    45: "46_微小缺陷檢測.png",
    46: "47_配方自動混合.png",
    47: "48_低碳精餾製程.png",
    48: "49_晶圓表面烘烤.png",
    49: "50_科技與綠能共榮.png"
}

def get_audio_duration(audio_path):
    cmd = ["ffmpeg", "-i", audio_path]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        return hours * 3600 + minutes * 60 + seconds
    return None

def main():
    if not os.path.exists(output_root):
        print(f"錯誤: 找不到創作庫資料夾: {output_root}")
        return

    mp3_files = [f for f in os.listdir(workspace_dir) if f.endswith(".mp3") and f != "勝一化學_Suno音樂合輯.mp3"]
    print(f"開始為 {len(mp3_files)} 首歌曲產生各自的 VIDS 故事板說明檔...\n")

    for mp3 in mp3_files:
        song_name = os.path.splitext(mp3)[0]
        song_dir = os.path.join(output_root, song_name)
        dest_mp3_path = os.path.join(song_dir, mp3)

        if not os.path.exists(song_dir):
            os.makedirs(song_dir, exist_ok=True)

        duration = get_audio_duration(dest_mp3_path)
        if not duration:
            src_mp3_path = os.path.join(workspace_dir, mp3)
            duration = get_audio_duration(src_mp3_path)
            
        if not duration:
            print(f"  [X] 無法讀取歌曲長度: {song_name}")
            continue

        # Vids max scene limit is 8 seconds.
        # N = ceil(duration / 8.0)
        num_scenes = math.ceil(duration / 8.0)
        time_per_scene = duration / num_scenes

        print(f"➔ 處理歌曲: 【{song_name}】")
        print(f"  時長: {duration:.2f} 秒 | 為了不超過 8 秒限制，需要 {num_scenes} 個場景 | 每頁顯示 {time_per_scene:.2f} 秒")

        # Sample N scenes from the 30 master scenes evenly
        sampled_scenes = []
        for i in range(num_scenes):
            # linear interpolation index
            idx = int(i * (len(master_scenes) - 1) / (num_scenes - 1))
            sampled_scenes.append((idx, master_scenes[idx]))

        # Write vids_storyboard_prompts.md in the song folder
        md_path = os.path.join(song_dir, "vids_storyboard_prompts.md")
        with open(md_path, "w", encoding="utf-8") as out:
            out.write(f"# 🎬 勝一化學 AI 音樂影片 — Vids 專屬故事板提示詞 (8秒上限優化版)\n\n")
            out.write(f"本文件為 【{song_name}】 專屬量身打造。\n\n")
            out.write(f"### 📊 影片參數規格：\n")
            out.write(f"* **歌曲總長度**：`{duration:.2f} 秒`\n")
            out.write(f"* **建議場景總數**：`{num_scenes} 頁` (可完美平分時間，防範 Vids 單場景 8 秒限制)\n")
            out.write(f"* **每場景播放時間**：`{time_per_scene:.2f} 秒`\n\n")
            out.write(f"---\n\n")
            out.write(f"## 📋 完整 {num_scenes} 場景提示詞與素材對照表\n\n")

            for scene_num, (orig_idx, scene) in enumerate(sampled_scenes, 1):
                out.write(f"### 📌 場景 {scene_num:02d}：{scene['name']}\n")
                out.write(f"* ⏱️ **建議播放長度**：`{time_per_scene:.2f} 秒`\n")
                
                # Check if this scene has a pre-generated local image
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

        print(f"  [✓] 成功寫入故事板說明檔: {os.path.basename(md_path)}")
        print("-" * 50)

    print("\n🎉 所有歌曲的獨立 Vids 故事板說明檔生成完畢！")

if __name__ == "__main__":
    main()
