#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將所有漫畫畫格對話框修飾為繁體中文 (智慧型動態字型縮放版)
"""

import sys
import json
import subprocess
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# 強制 UTF-8 輸出
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# 智慧文字分段與佈局優化函數
def segment_text(text_list, max_chars_per_col, join_all=True):
    if join_all:
        full_text = "".join(text_list)
        segment_list = [full_text]
    else:
        segment_list = text_list

    cols = []
    for segment in segment_list:
        if not segment:
            continue
        words = []
        i = 0
        while i < len(segment):
            chunk = segment[i:i+max_chars_per_col]
            if i + max_chars_per_col < len(segment):
                next_char = segment[i + max_chars_per_col]
                if next_char in ["，", "。", "！", "？", "、", "」", "』", "”", "；", "："]:
                    chunk += next_char
                    i += 1
            words.append(chunk)
            i += max_chars_per_col
            
        if len(words) > 1 and len(words[-1]) <= 2:
            combined = words[-2] + words[-1]
            mid = len(combined) // 2
            words[-2] = combined[:mid]
            words[-1] = combined[mid:]
            
        cols.extend(words)
    return cols

def get_optimal_layout(W, H, text_list, max_font_size=55, min_font_size=16):
    best_score = -999
    best_f = min_font_size
    best_cols = text_list
    
    for join_all in [False, True]:
        for max_len in range(4, 15):
            cols = segment_text(text_list, max_len, join_all=join_all)
            num_cols = len(cols)
            if num_cols == 0:
                continue
            max_chars = max(len(col) for col in cols)
            if max_chars == 0:
                continue
                
            f_limit = min_font_size
            for f in range(min_font_size, max_font_size + 1):
                col_spacing = f * 1.15
                w_txt = (num_cols - 1) * col_spacing + f
                h_txt = max_chars * f + (max_chars - 1) * 2
                
                # 橢圓對話框擬合檢查
                if (w_txt / W)**2 + (h_txt / H)**2 <= 0.82:
                    f_limit = f
                else:
                    break
            
            # 計算分數，取得字型大小與排版美觀的平衡
            score = f_limit
            if max_len < 5:
                score -= 8
            if max_len < 4:
                score -= 15
            if join_all:
                score += 2
                
            if score > best_score:
                best_score = score
                best_f = f_limit
                best_cols = cols
                
    return best_cols, best_f


# 直排文字繪製函數 (自動計算垂直與水平置中)
def draw_vertical_dialogue(draw, text_cols, center_x, center_y, font, fill_color, font_size, col_spacing=24, char_spacing=2):
    num_cols = len(text_cols)
    
    # 計算每一列的高度以及總高
    col_heights = []
    for col in text_cols:
        h = 0
        for char in col:
            bbox = font.getbbox(char)
            char_h = bbox[3] - bbox[1] if bbox else font_size
            h += char_h + char_spacing
        col_heights.append(h - char_spacing) # 扣掉最後一個間距
    
    # 計算直排文字的總寬度 (右到左)
    total_width = (num_cols - 1) * col_spacing + font_size
    
    # 決定起始繪製的 x 座標 (最右側列的位置)
    start_x = center_x + (total_width - font_size) // 2
    
    for col_idx, col_text in enumerate(text_cols):
        current_x = start_x - col_idx * col_spacing
        
        # 計算此列的垂直起始座標 (置中)
        col_h = col_heights[col_idx]
        current_y = center_y - col_h // 2
        
        for char in col_text:
            bbox = font.getbbox(char)
            char_w = bbox[2] - bbox[0] if bbox else font_size
            char_h = bbox[3] - bbox[1] if bbox else font_size
            
            # 微調標點符號的直排置中位移
            x_offset = 0
            y_offset = 0
            if char in ["，", "。", "！", "？", "…", "—"]:
                x_offset = font_size // 4
                
            draw.text((current_x + x_offset, current_y + y_offset), char, font=font, fill=fill_color)
            current_y += char_h + char_spacing

# 各畫格對話框座標配置 (手動根據偵測結果精確對齊)
PANEL_CONFIGS = {
    "p1_panel1": [
        {"bbox": (716, 48, 856, 260), "text": ["耶！大阪我們來了！", "第一站先去哪裡？"]},
        {"bbox": (212, 60, 320, 256), "text": ["讓爸爸看看地圖，", "嗯，好像是走這邊？"]}
    ],
    "p1_panel2": [
        {"bbox": (740, 64, 1000, 256), "text": ["別急，媽媽已經", "查好最有名的一家了！"]},
        {"bbox": (388, 36, 708, 352), "text": ["哇！好大的螃蟹！", "爸爸，我肚子餓了，", "我想吃章魚燒！"]}
    ],
    "p1_panel3": [
        {"bbox": (748, 40, 996, 292), "text": ["哈哈哈，小融你也吃太急了", "吧，嘴巴都要噴火了！"]},
        {"bbox": (540, 68, 724, 272), "text": ["好燙！呼呼！", "但是超好吃！"]},
        {"bbox": (60, 52, 220, 316), "text": ["小心燙啊！", "水，快喝水！"]}
    ],
    "p1_panel4": [
        {"bbox": (684, 40, 960, 224), "text": ["大阪的第一天就這麼完美，", "明天還有大阪城呢！"]},
        {"bbox": (88, 56, 368, 252), "text": ["今晚一定要吃飽睡好，", "明天要走很多路喔！"]}
    ],
    "p2_panel1": [
        {"bbox": (740, 36, 1000, 264), "text": ["宏志，你把地圖拿反了啦！", "那邊才是天守閣！"]},
        {"bbox": (28, 52, 292, 280), "text": ["咦？大阪城天守閣到底在哪", "個方向？明明地圖寫著直走…"]}
    ],
    "p2_panel2": [], # 無白色對話框，保留原圖特效
    "p2_panel3": [
        {"bbox": (16, 316, 160, 560), "text": ["衝啊！我要當第一名", "爬到頂樓！"]},
        {"bbox": (488, 68, 664, 340), "text": ["小融……", "等等爸爸……"]},
        {"bbox": (688, 36, 824, 288), "text": ["這樓梯也", "太多了吧……"]},
        {"bbox": (864, 32, 996, 260), "text": ["哈哈，老公加油！", "堅持下去！"]}
    ],
    "p2_panel4": [
        {"bbox": (812, 44, 988, 276), "text": ["爬上來真的", "很值得，"]},
        {"bbox": (472, 72, 664, 236), "text": ["爸爸你也別再", "喘了，看鏡頭", "笑一個！"]},
        {"bbox": (48, 40, 328, 372), "text": ["哇，風景好漂亮！", "大阪市區都在我們腳下呢！"]},
        {"bbox": (836, 316, 980, 516), "text": ["耶！好高喔！"]},
        {"bbox": (60, 544, 180, 668), "text": ["呼，好熱啊！", "但是這裡視野最棒了！"]}
    ],
    "p3_panel1": [
        {"bbox": (40, 60, 220, 320), "text": ["是瑪利歐！我要去", "超級任天堂世界玩！"]},
        {"bbox": (812, 60, 972, 304), "text": ["我要去哈利波特園區", "喝奶油啤酒！快走快走！"]}
    ],
    "p3_panel2": [
        {"bbox": (56, 48, 444, 380), "text": ["救命啊！", "我為什麼會在這裡！"]},
        {"bbox": (668, 68, 984, 380), "text": ["超好玩！太刺激了！", "爸爸你張開眼睛看啦！"]},
        {"bbox": (472, 24, 624, 220), "text": ["好快喔！", "太爽快了！"]},
        {"bbox": (40, 456, 284, 748), "text": ["哇！還要再玩！"]}
    ],
    "p3_panel3": [
        {"bbox": (76, 64, 264, 348), "text": ["我的腿已經不是我的了，", "但孩子們開心就值得了。"]},
        {"bbox": (780, 72, 944, 328), "text": ["今天買了好多紀念品，", "真是滿載而歸！"]}
    ],
    "p3_panel4": [
        {"bbox": (36, 32, 420, 304), "text": ["五天四夜過得好快，這次", "大阪之旅真的太棒了，", "下次還要再來！"]}
    ]
}

def main():
    base_dir = Path(__file__).parent.resolve()
    images_dir = base_dir / "assets" / "images"
    
    # 載入 Windows 系統字型 (微軟正黑體粗體)
    font_path = "C:\\Windows\\Fonts\\msjhbd.ttc"
    if not Path(font_path).exists():
        font_path = "C:\\Windows\\Fonts\\msjh.ttc"
        
    print("🎨 開始修飾並填入直排繁體中文...")
    for panel_id, configs in PANEL_CONFIGS.items():
        img_path = images_dir / f"{panel_id}.png"
        if not img_path.exists():
            print(f"❌ 找不到 {panel_id}.png")
            continue
            
        if not configs:
            print(f"➡️ 跳過 {panel_id}.png (無白色對話框)")
            continue
            
        img = Image.open(img_path)
        draw = ImageDraw.Draw(img)
        
        for cfg in configs:
            min_x, min_y, max_x, max_y = cfg["bbox"]
            center_x = (min_x + max_x) // 2
            center_y = (min_y + max_y) // 2
            
            # 1. 塗白對話框內部 (覆蓋原有日/英文)
            inset = 4
            draw.ellipse(
                [min_x + inset, min_y + inset, max_x - inset, max_y - inset], 
                fill=(255, 255, 255)
            )
            
            # 若為清空用的對話框，跳過文字繪製
            if not cfg["text"]:
                continue
                
            # 2. 智慧動態計算字型大小與排版佈局
            w = max_x - min_x
            h = max_y - min_y
            text_cols, font_size = get_optimal_layout(w, h, cfg["text"])
            
            # 3. 載入字型
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception:
                font = ImageFont.load_default()
                
            # 4. 繪製置中直排繁體中文
            col_spacing = int(font_size * 1.15)
            draw_vertical_dialogue(
                draw=draw,
                text_cols=text_cols,
                center_x=center_x,
                center_y=center_y,
                font=font,
                fill_color=(0, 0, 0),
                font_size=font_size,
                col_spacing=col_spacing,
                char_spacing=2
            )
            print(f"    * 區塊 BBox {cfg['bbox']}: 動態字級設定為 {font_size}px, 排版分列: {text_cols}")
            
        img.save(img_path)
        print(f"✅ 修飾完成: {panel_id}.png")
        
    print("\n🎉 所有漫畫圖片直排繁體中文修飾完成！")
    return 0

if __name__ == "__main__":
    sys.exit(main())
