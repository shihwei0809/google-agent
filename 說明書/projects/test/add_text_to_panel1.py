#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# 強制 UTF-8 輸出
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def draw_vertical_text(draw, text_cols, start_x, start_y, font, fill_color, col_spacing=35, char_spacing=4):
    """
    在指定位置繪製直排中文（由右至左）
    """
    for col_idx, col_text in enumerate(text_cols):
        # 每一行往左偏移 col_spacing
        x = start_x - col_idx * col_spacing
        y = start_y
        for char in col_text:
            # 取得字元大小以計算間距
            bbox = font.getbbox(char)
            char_w = bbox[2] - bbox[0] if bbox else 24
            char_h = bbox[3] - bbox[1] if bbox else 24
            
            # 微調標點符號的置中 (直排的標點符號通常需要靠右或置中)
            x_offset = 0
            y_offset = 0
            if char in ["，", "。", "！", "？", "…"]:
                x_offset = char_w // 4
                
            # 繪製單個字
            draw.text((x + x_offset, y + y_offset), char, font=font, fill=fill_color)
            y += char_h + char_spacing

def main():
    base_dir = Path(__file__).parent.resolve()
    img_path = base_dir / "assets" / "images" / "p1_panel1.png"
    output_path = img_path  # 直接覆寫原圖
    
    if not img_path.exists():
        print(f"❌ 找不到圖片: {img_path}")
        return 1
        
    print(f"🎨 正在讀取圖片: {img_path}")
    img = Image.open(img_path)
    draw = ImageDraw.Draw(img)
    
    # 載入 Windows 系統字型 (微軟正黑體粗體)
    font_path = "C:\\Windows\\Fonts\\msjhbd.ttc"
    if not Path(font_path).exists():
        font_path = "C:\\Windows\\Fonts\\msjh.ttc"  # 備用微軟正黑體
    
    try:
        # 設定字型大小，縮小至 17px 以完全容納於對話框內
        font_large = ImageFont.truetype(font_path, 17)
        font_small = ImageFont.truetype(font_path, 15)
        print("✅ 成功載入微軟正黑體。")
    except Exception as e:
        print(f"⚠️ 無法載入正黑體，改用預設字型: {e}")
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # 1. 繪製 Papa 的對話 (左上角對話框)
    # 對話：讓爸爸看看地圖，嗯，好像是走這邊？
    papa_cols = [
        "讓爸爸看看地圖，",
        "嗯，好像是走這邊？"
    ]
    # 左上角對話框範圍: x: 198~315 (中線約 256), y: 45~255
    draw_vertical_text(
        draw=draw,
        text_cols=papa_cols,
        start_x=272,   # 右側列 x 座標 (左側列會在 248)
        start_y=65,    # 向上提至 y=65
        font=font_large,
        fill_color=(0, 0, 0), # 黑色字
        col_spacing=24,
        char_spacing=2
    )

    # 2. 繪製 Sakura (小妤) 的對話 (右上角對話框)
    # 對話：耶！大阪我們來了！第一站先去哪裡？
    sakura_cols = [
        "耶！大阪我們來了！",
        "第一站先去哪裡？"
    ]
    # 右上角對話框範圍: x: 695~835 (中線約 765), y: 45~250
    draw_vertical_text(
        draw=draw,
        text_cols=sakura_cols,
        start_x=782,   # 右側列 x 座標 (左側列會在 758)
        start_y=65,    # 向上提至 y=65
        font=font_large,
        fill_color=(0, 0, 0),
        col_spacing=24,
        char_spacing=2
    )
    
    # 3. 翻譯右側的日文效果音 "ドキワク！" (doki-waku) 為 "興奮！"
    # 原圖位置大約在 x: 880~980, y: 660~900
    # 我們可以稍微覆蓋原本的字，或者直接在上方疊加
    # 這裡我們用一個紅色粗體字來畫 "好期待！" 或 "興奮！"
    # 由於背景比較複雜，直接畫字可能不夠明顯，我們可以用大一點的字加一點點白色描邊
    # 但為求乾淨，我們先在對話框內填入字即可，SFX 留給原圖的動感。
    
    # 儲存圖片
    img.save(output_path)
    print(f"🎉 第一張漫畫圖片修飾完成！已寫入 {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
