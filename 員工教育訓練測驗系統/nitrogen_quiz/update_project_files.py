import os
import re
import json
import asyncio
from PIL import Image, ImageDraw, ImageFont
import edge_tts

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SLIDES_DIR = os.path.join(BASE_DIR, "slides")
FONT_PATH = "C:\\Windows\\Fonts\\msjh.ttc"  # 微軟正黑體

# 確保輸出目錄存在
os.makedirs(SLIDES_DIR, exist_ok=True)

# 簡報內容定義 (用於生成靜態 PNG 與 MP3)
SLIDES_DATA = [
    {
        "title": "儲槽氮氣閥與氮封系統作動原理",
        "subtitle": "確保製程安全與儲槽壓力的核心屏障",
        "state": "normal",
        "bullets": [
            "1. 瞭解儲槽壓力平衡的重要性，防範超壓或真空。",
            "2. 掌握供氮閥與洩氮閥「自力式反饋」作動機制。",
            "3. 熟悉安全呼吸閥與緊急洩壓人孔的物理防護機制。"
        ],
        "say": "各位同仁好，歡迎參加本次教育訓練。今天我們要學習的是「儲槽氮氣閥與氮封系統之作動原理」。氮封系統是石化及化學工廠中，保護儲槽安全、防止火災爆炸及防止物料變質的重要安全設施。請大家仔細學習其作動機制。"
    },
    {
        "title": "什麼是氮氣覆蓋(氮封)系統？",
        "subtitle": "阻隔氧氣、控制壓力、保護物料",
        "state": "normal",
        "bullets": [
            "1. 防止燃燒爆炸：充入惰性氮氣排除儲槽內氧氣，消除燃燒爆炸三要素。",
            "2. 物料品質保護：阻絕外部空氣與水氣進入，防止化學品氧化或變質。",
            "3. 結構安全保障：維持極微量正壓，避免溫度變化或進出料造成槽體破裂或吸扁。"
        ],
        "say": "氮封系統的主要目的，是在儲槽頂部的氣相空間充入惰性氮氣，維持微正壓。這樣做有三個核心作用：第一，排除氧氣，避免形成爆炸性混合氣體；第二，防止外部空氣及水氣進入，避免物料氧化、受潮或變質；第三，透過精密閥門控制，避免儲槽因溫度變化或物料進出而發生超壓變形或真空癟罐。"
    },
    {
        "title": "供氮閥 (Regulator) 作動原理",
        "subtitle": "儲槽壓力低於設定值時，自動補充氮氣",
        "state": "supply",
        "bullets": [
            "1. 槽壓下降：當儲槽進行出料操作，或氣溫驟降時，內部氣體體積收縮使壓力降低。",
            "2. 閥芯開啟：槽內壓力低於供氮閥設定值時，控制膜片受壓減小，彈簧推動閥芯開啟。",
            "3. 氮氣補充：高壓氮氣源源不斷進入儲槽，直至壓力回升到設定平衡點後自動閥關。"
        ],
        "say": "供氮閥是一種自力式微壓調節閥。當儲槽進行出料操作，或夜間氣溫下降使槽內氣體收縮時，儲槽內的壓力會開始下降。當槽內壓力低於供氮閥的設定點時，控制膜片受壓減小，彈簧推動閥芯開啟，氮氣隨之流入槽內。當槽內壓力回升到設定值時，膜片克服彈簧力，帶動閥芯關閉，停止供氮。"
    },
    {
        "title": "洩氮閥 (Vent Valve) 作動原理",
        "subtitle": "儲槽壓力高於設定值時，自動排出氣體",
        "state": "vent",
        "bullets": [
            "1. 槽壓升高：當儲槽進料（泵入）或日照輻射升溫時，槽內氣相空間被壓縮且膨脹。",
            "2. 閥門開啟：槽內壓力高於洩氮閥設定值時，高壓推動膜片克服彈簧張力而開啟閥芯。",
            "3. 超壓排放：多餘氮氣或油氣安全排至大氣或回收系統，直至壓力降回設定點後關閉。"
        ],
        "say": "與供氮閥相反，洩氮閥負責槽內超壓時的排氣。當儲槽進行進料操作，或日間太陽曝曬使槽內溫度升高時，槽內壓力會上升。當壓力高於洩氮閥的設定點時，槽內壓力推動膜片克服彈簧張力，使閥門開啟，將槽內多餘的氮氣或混合氣體排出。當槽內壓力降回設定值時，閥門自動關閉，維持系統微正壓。"
    },
    {
        "title": "雙重安全保障機制",
        "subtitle": "安全呼吸閥與緊急防護",
        "state": "vacuum",
        "bullets": [
            "1. 安全呼吸閥真空防護：若氮氣閥故障且槽壓極低，真空閥座開啟引入空氣防止癟罐。",
            "2. 呼吸閥超壓防護：若槽壓異常高且洩氮閥卡死，超壓閥座開啟對外排氣防止脹裂。",
            "3. 緊急洩壓人孔：當遇到外部大火等極端熱源導致壓力暴增時，頂蓋開啟進行大排量洩壓。"
        ],
        "say": "為了防止供氮閥或洩氮閥故障，儲槽設有雙重防護機制。第一重是安全呼吸閥，在槽內壓力達到極限高壓或真空值時，分別向外排氣或向內吸入空氣，防止儲槽破裂或吸扁。第二重是緊急洩爆人孔，當遭遇外部大火導致槽內急劇升壓時，洩爆人孔會瞬間開啟，進行大排量洩壓，是儲槽的最終安全保障。"
    },
    {
        "title": "教育訓練總結與課後測驗",
        "subtitle": "掌握微壓控制，守護製程安全",
        "state": "normal",
        "bullets": [
            "1. 降壓補氮：槽壓降低時，供氮閥自力開啟補氮，維持微正壓保護。",
            "2. 升壓洩氮：槽壓上升時，洩氮閥自力開啟排氣，避免槽體脹裂過載。",
            "3. 機械防護：呼吸閥與緊急洩壓孔作為最後物理保險，確保本質安全。"
        ],
        "say": "本次課程我們學習了氮封系統「降壓補充、升壓排放」的自力式反饋原理，以及呼吸閥與緊急洩爆孔的雙重安全保護機制。請同仁務必熟記各閥門的作動方向與目的。簡報播放已結束，請點擊下方按鈕，填寫姓名並開始進行課後測驗，祝大家順利通過！"
    }
]

# 測驗題目定義
QUESTIONS_DATA = [
    {
        "q": "關於儲槽氮封系統的主要目的，以下何者錯誤？",
        "opts": [
            "A. 充入惰性氮氣以排除氧氣，防止火災與爆炸",
            "B. 防止外部空氣與水分進入，保護槽內物料不變質",
            "C. 使儲槽內部維持微正壓，保護槽體結構安全",
            "D. 為了冷卻槽內液體，降低儲槽的整體操作溫度"
        ],
        "a": "D"
    },
    {
        "q": "當儲槽進行「出料（泵出）」或「溫度降低」時，儲槽壓力會如何變化？此時哪一個閥門會自動開啟？",
        "opts": [
            "A. 儲槽壓力上升；洩氮閥開啟",
            "B. 儲槽壓力下降；供氮閥開啟",
            "C. 儲槽壓力上升；供氮閥開啟",
            "D. 儲槽壓力下降；洩氮閥開啟"
        ],
        "a": "B"
    },
    {
        "q": "氮封系統中的供氮閥與洩氮閥，通常採用何種形式的閥門來達到自動控制？",
        "opts": [
            "A. 需要外部電源驅動的電動球閥",
            "B. 需要氣源信號控制的氣動調節閥",
            "C. 無需外部動力、利用儲槽壓力自我反饋的自力式調節閥",
            "D. 需要人工手動操作的閘閥"
        ],
        "a": "C"
    },
    {
        "q": "當槽內壓力因異常狀況急劇升高，且洩氮閥來不及排放時，下列哪一個安全防護設施會首先發揮排氣作用以防止儲槽超壓破裂？",
        "opts": [
            "A. 安全呼吸閥 (Breather Valve)",
            "B. 緊急洩爆人孔 (Emergency Vent)",
            "C. 供氮閥 (Nitrogen Supply Valve)",
            "D. 排泥閥 (Drain Valve)"
        ],
        "a": "A"
    },
    {
        "q": "為了避免儲槽在極端真空狀態下被大氣壓「吸扁（癟罐）」，安全呼吸閥的真空閥座在達到設定真空度時會進行什麼作動？",
        "opts": [
            "A. 關閉閥門，完全封鎖槽內氣體",
            "B. 開啟閥門，允許外部空氣進入槽內以平衡壓力",
            "C. 開啟供氮閥，以超高壓注入更多氮氣",
            "D. 開啟排泥閥，把槽內液體排出"
        ],
        "a": "B"
    }
]

# ── 1. 繪製精美的靜態簡報圖檔 ──────────────────────────
def generate_slide_images():
    print("🎨 開始繪製簡報圖片...")
    for idx, slide in enumerate(SLIDES_DATA):
        # 建立 1280x720 畫布 (暗色漸層)
        img = Image.new("RGB", (1280, 720), (15, 23, 42))
        draw = ImageDraw.Draw(img)
        
        # 繪製背景漸層效果 (以同心圓或多層矩形模擬)
        for i in range(720):
            r = int(15 + (15 * i / 720))
            g = int(23 + (18 * i / 720))
            b = int(42 + (17 * i / 720))
            draw.line([(0, i), (1280, i)], fill=(r, g, b))
            
        # 載入字型
        font_title = ImageFont.truetype(FONT_PATH, 38)
        font_sub = ImageFont.truetype(FONT_PATH, 22)
        font_body = ImageFont.truetype(FONT_PATH, 20)
        font_meta = ImageFont.truetype(FONT_PATH, 14)

        # 頂部裝飾列
        draw.text((60, 40), "儲槽氮氣閥與氮封系統安全教育訓練", font=font_meta, fill=(99, 102, 241))
        draw.text((1120, 40), f"PAGE {idx+1} / 6", font=font_meta, fill=(156, 163, 175))
        draw.line([(60, 65), (1220, 65)], fill=(255, 255, 255, 20), width=1)

        # 標題與副標題
        draw.text((60, 90), f"0{idx+1}. {slide['title']}", font=font_title, fill=(255, 255, 255))
        draw.text((60, 145), slide["subtitle"], font=font_sub, fill=(129, 140, 248))

        # 左側文字卡片 (毛玻璃卡片效果)
        card_box = [60, 200, 640, 660]
        draw.rounded_rectangle(card_box, radius=16, fill=(30, 41, 59), outline=(255, 255, 255, 10), width=1)
        
        # 寫入文字要領
        y_cursor = 240
        for bullet in slide["bullets"]:
            # 自動折行處理 (簡單長度折行)
            text_lines = []
            words = bullet
            line = ""
            for char in words:
                line += char
                if len(line) >= 23:
                    text_lines.append(line)
                    line = ""
            if line:
                text_lines.append(line)
                
            for line in text_lines:
                draw.text((90, y_cursor), line, font=font_body, fill=(203, 213, 225))
                y_cursor += 32
            y_cursor += 15

        # 右側繪製儲槽 P&ID 示意圖
        draw_tank_diagram(draw, 720, 200, slide["state"])

        # 儲存檔案
        filename = f"slide_{idx+1:02d}.png"
        filepath = os.path.join(SLIDES_DIR, filename)
        img.save(filepath, "PNG")
        print(f"   ✓ 已生成 {filename}")

def draw_tank_diagram(draw, x_offset, y_offset, state):
    # 槽體坐標定位 (寬380, 高380)
    tx = x_offset + 50
    ty = y_offset + 80
    tw = 260
    th = 280
    
    # 1. 繪製儲槽主體 (Dome top tank)
    # 頂部半圓弧, 左右垂直壁, 底部平底圓角
    # 繪製半透明氣體微光
    draw.rounded_rectangle([tx, ty, tx+tw, ty+th], radius=15, fill=(30, 41, 59, 100), outline=(100, 116, 139), width=4)
    # 頂部穹頂裝飾
    draw.chord([tx, ty-40, tx+tw, ty+40], 180, 360, fill=(30, 41, 59), outline=(100, 116, 139), width=4)
    # 重新描邊蓋掉底線
    draw.line([(tx+2, ty), (tx+tw-2, ty)], fill=(30, 41, 59), width=6)
    
    # 2. 依狀態繪製物料液面 (水藍色)
    liquid_y = ty + 150 # 正常
    if state == "supply":
        liquid_y = ty + 210 # 低液位
    elif state == "vent":
        liquid_y = ty + 90 # 高液位
    elif state == "vacuum":
        liquid_y = ty + 240 # 極低液位
        
    draw.rounded_rectangle([tx+4, liquid_y, tx+tw-4, ty+th-4], radius=12, fill=(14, 165, 233))
    
    # 3. 標示氣體與液體標籤文字
    font_lbl = ImageFont.truetype(FONT_PATH, 13)
    draw.text((tx + tw//2, ty + 40), "氣相氮氣層 (N₂)", font=font_lbl, fill=(148, 163, 184), anchor="mm")
    draw.text((tx + tw//2, (liquid_y + ty + th)//2), "槽內液體物料", font=font_lbl, fill=(255, 255, 255, 180), anchor="mm")

    # 4. 繪製管道
    # 進氮管 (左側)
    draw.line([(x_offset, ty-30), (tx+40, ty-30)], fill=(71, 85, 105), width=4)
    draw.line([(tx+40, ty-30), (tx+40, ty-10)], fill=(71, 85, 105), width=4)
    
    # 洩氮管 (右側)
    draw.line([(tx+tw-40, ty-10), (tx+tw-40, ty-50)], fill=(71, 85, 105), width=4)
    draw.line([(tx+tw-40, ty-50), (x_offset+tw+120, ty-50)], fill=(71, 85, 105), width=4)
    
    # 5. 繪製閥門圖示與高亮狀態
    # 供氮閥 (左側進氮管上)
    v1_x, v1_y = tx+40, ty-30
    draw_valve_symbol(draw, v1_x, v1_y, "green" if state == "supply" else "gray")
    
    # 洩氮閥 (右側洩氮管上)
    v2_x, v2_y = tx+tw-40, ty-50
    draw_valve_symbol(draw, v2_x, v2_y, "red" if state == "vent" else "gray")

    # 呼吸閥 (槽頂中心)
    v3_x, v3_y = tx+tw//2, ty-15
    draw.rectangle([v3_x-15, v3_y-10, v3_x+15, v3_y], fill=(71, 85, 105), outline=(51, 65, 85))
    draw.chord([v3_x-15, v3_y-20, v3_x+15, v3_y-5], 180, 360, fill=((59, 130, 246) if state == "vacuum" else (148, 163, 184)))
    
    # 6. 繪製狀態文字與箭頭
    if state == "supply":
        # 進氮流向箭頭
        draw.line([(x_offset+10, ty-30), (v1_x-10, ty-30)], fill=(16, 185, 129), width=4)
        draw.polygon([(v1_x-10, ty-35), (v1_x-2, ty-30), (v1_x-10, ty-25)], fill=(16, 185, 129))
        draw.text((x_offset+20, ty-50), "補充氮氣 (OPEN)", font=font_lbl, fill=(16, 185, 129))
        
        # 出料箭頭
        draw.line([(tx+20, ty+th), (tx+20, ty+th+25)], fill=(239, 68, 68), width=4)
        draw.polygon([(tx+15, ty+th+20), (tx+20, ty+th+27), (tx+25, ty+th+20)], fill=(239, 68, 68))
        draw.text((tx+30, ty+th+10), "物料出料中", font=font_lbl, fill=(239, 68, 68))
        
    elif state == "vent":
        # 排氣流向箭頭
        draw.line([(v2_x+10, ty-50), (x_offset+tw+100, ty-50)], fill=(239, 68, 68), width=4)
        draw.polygon([(x_offset+tw+95, ty-55), (x_offset+tw+103, ty-50), (x_offset+tw+95, ty-45)], fill=(239, 68, 68))
        draw.text((v2_x+15, ty-70), "洩放氮封氣 (OPEN)", font=font_lbl, fill=(239, 68, 68))
        
        # 進料箭頭
        draw.line([(tx+20, ty+th+25), (tx+20, ty+th)], fill=(16, 185, 129), width=4)
        draw.polygon([(tx+15, ty+th+8), (tx+20, ty+th+1), (tx+25, ty+th+8)], fill=(16, 185, 129))
        draw.text((tx+30, ty+th+10), "物料進料中", font=font_lbl, fill=(16, 185, 129))
        
    elif state == "vacuum":
        # 呼吸閥吸氣箭頭 (藍色)
        draw.line([(v3_x-25, ty-15), (v3_x-5, ty-15)], fill=(59, 130, 246), width=3)
        draw.polygon([(v3_x-8, ty-18), (v3_x-2, ty-15), (v3_x-8, ty-12)], fill=(59, 130, 246))
        draw.text((v3_x-100, ty-40), "極端負壓: 呼吸閥吸氣", font=font_lbl, fill=(59, 130, 246))

    # 繪製壓力錶
    gx, gy = tx + tw + 20, ty + 40
    draw.circle((gx, gy), 20, fill=(30, 41, 59), outline=(148, 163, 184), width=2)
    # 繪製刻度指標 (依狀態轉動)
    angle = 30 # 正常
    if state == "supply":
        angle = -15
    elif state == "vent":
        angle = 75
    elif state == "vacuum":
        angle = -60
        
    # 計算指針端點
    import math
    rad = math.radians(angle - 90)
    px = gx + 15 * math.cos(rad)
    py = gy + 15 * math.sin(rad)
    draw.line([(gx, gy), (px, py)], fill=(245, 158, 11), width=2)
    draw.circle((gx, gy), 3, fill=(255, 255, 255))
    draw.text((gx, gy+28), "300 mmH₂O" if state=="normal" else ("30 mmH₂O" if state=="supply" else ("750 mmH₂O" if state=="vent" else "-100 mmH₂O")), font=font_lbl, fill=(255,255,255), anchor="mm")

def draw_valve_symbol(draw, cx, cy, status):
    # 繪製控制閥符號 (兩個三角形頂點相連)
    color = (16, 185, 129) if status == "green" else ((239, 68, 68) if status == "red" else (148, 163, 184))
    
    # 橫向閥體
    draw.polygon([(cx-12, cy-8), (cx, cy), (cx-12, cy+8)], fill=color, outline=(51, 65, 85))
    draw.polygon([(cx+12, cy-8), (cx, cy), (cx+12, cy+8)], fill=color, outline=(51, 65, 85))
    draw.circle((cx, cy), 3, fill=(255, 255, 255))
    
    # 頂部執行機構膜片
    draw.line([(cx, cy), (cx, cy-12)], fill=(148, 163, 184), width=2)
    draw.ellipse([cx-10, cy-16, cx+10, cy-12], fill=color, outline=(51, 65, 85))


# ── 2. 生成配音 MP3 音檔 ──────────────────────────
async def generate_speech_mp3s():
    print("🎙 開始生成旁白語音檔 (edge-tts)...")
    voice = "zh-TW-HsiaoChenNeural"  # 女聲
    rate = "+0%"
    
    for idx, slide in enumerate(SLIDES_DATA):
        filename = f"slide_{idx+1:02d}.mp3"
        filepath = os.path.join(SLIDES_DIR, filename)
        text = slide["say"]
        
        print(f"   🎙 生成 {filename} ...", end=" ", flush=True)
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(filepath)
            size = os.path.getsize(filepath)
            print(f"✓ ({size/1024:.0f} KB)")
        except Exception as e:
            print(f"❌ 失敗: {e}")


# ── 3. 清理多餘的舊投影片與音檔 ────────────────────────
def cleanup_old_files():
    print("🗑 清理舊檔案 (7 到 20 頁)...")
    for idx in range(7, 21):
        png_name = f"slide_{idx:02d}.png"
        mp3_name = f"slide_{idx:02d}.mp3"
        
        png_path = os.path.join(SLIDES_DIR, png_name)
        mp3_path = os.path.join(SLIDES_DIR, mp3_name)
        
        if os.path.exists(png_path):
            os.remove(png_path)
            print(f"   Deleted {png_name}")
        if os.path.exists(mp3_path):
            os.remove(mp3_path)
            print(f"   Deleted {mp3_name}")


# ── 4. 修改主網頁 index.html 及 index_with_mp3.html ──────────
def update_main_html_files():
    print("📝 更新 index.html 與 index_with_mp3.html 檔案...")
    
    # 題目 JSON 陣列格式化字串
    js_qs = json.dumps([
        {
            "q": q["q"],
            "opts": q["opts"],
            "a": q["a"]
        } for q in QUESTIONS_DATA
    ], ensure_ascii=False, indent=2)
    
    # 簡報 JSON 陣列格式化字串
    js_slides = json.dumps([
        {
            "img": f"slides/slide_{i+1:02d}.png",
            "label": f"第 {i+1} 頁｜{s['title']}",
            "say": s["say"]
        } for i, s in enumerate(SLIDES_DATA)
    ], ensure_ascii=False, indent=2)

    # 1. 更新 index.html
    index_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 替換 Title/Subtitle/簡報數
        content = re.sub(r"<title>.*?</title>", "<title>員工教育訓練測驗系統 — 儲槽氮氣閥作動原理</title>", content)
        content = content.replace("簡報共 <strong>20頁</strong>", "簡報共 <strong>6頁</strong>")
        content = content.replace("1 / 20", "1 / 6")
        content = content.replace("已作答 0 / 10 題", "已作答 0 / 5 題")
        content = content.replace("QS.length+' 題'", "QS.length+' 題'")
        content = content.replace("10 題）", "5 題）")
        
        # 替換 JS 變數 SLIDES
        # 定位 let SLIDES = [ ... ];
        slides_pattern = r"let SLIDES\s*=\s*\[[\s\S]*?\];"
        content = re.sub(slides_pattern, f"let SLIDES = {js_slides};", content)
        
        # 替換 JS 變數 QS
        # 定位 let QS=[ ... ];
        qs_pattern = r"let QS\s*=\s*\[[\s\S]*?\];"
        content = re.sub(qs_pattern, f"let QS = {js_qs};", content)
        
        # 存檔
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("   ✓ index.html 已更新")

    # 2. 更新 index_with_mp3.html
    index_mp3_path = os.path.join(BASE_DIR, "index_with_mp3.html")
    if os.path.exists(index_mp3_path):
        with open(index_mp3_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        content = re.sub(r"<title>.*?</title>", "<title>員工教育訓練測驗系統 — 儲槽氮氣閥作動原理</title>", content)
        content = content.replace("簡報共 <strong>20頁</strong>", "簡報共 <strong>6頁</strong>")
        content = content.replace("1 / 20", "1 / 6")
        content = content.replace("已作答 0 / 10 題", "已作答 0 / 5 題")
        content = content.replace("10 題）", "5 題）")
        
        # 替換 JS 變數 SLIDES
        slides_pattern = r"let SLIDES\s*=\s*\[[\s\S]*?\];"
        content = re.sub(slides_pattern, f"let SLIDES = {js_slides};", content)
        
        # 替換 JS 變數 QS
        qs_pattern = r"let QS\s*=\s*\[[\s\S]*?\];"
        content = re.sub(qs_pattern, f"let QS = {js_qs};", content)
        
        with open(index_mp3_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("   ✓ index_with_mp3.html 已更新")

# ── 主流程 ──────────────────────────────────────────
async def main():
    print("🚀 啟動儲槽氮氣閥教育訓練素材建置程序...")
    print("-" * 50)
    
    # 1. 繪製精美靜態簡報圖檔
    generate_slide_images()
    
    # 2. 生成配音 MP3 音檔
    await generate_speech_mp3s()
    
    # 3. 清理舊檔案
    cleanup_old_files()
    
    # 4. 修改網頁 fallback 資料
    update_main_html_files()
    
    print("-" * 50)
    print("🎉 恭喜！所有教育訓練檔案、考題、簡報圖片、動畫設置與旁白音檔均已成功建置！")

if __name__ == "__main__":
    asyncio.run(main())
