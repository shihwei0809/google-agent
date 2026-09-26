#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
簡報生成工具：讀取大綱文字，利用 python-pptx 生成 16:9 孟菲斯波普風格投影片。
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

sys.stdout.reconfigure(encoding='utf-8')

OUTLINE_PATH = "input/slide_outline.txt"
OUTPUT_PATH = "output/memphis_presentation.pptx"

# 孟菲斯波普調色盤 (RGB)
BG_COLOR = RGBColor(0xFF, 0xFD, 0xF0)       # 奶油色 #FFFDF0
TEXT_COLOR = RGBColor(0x1A, 0x1A, 0x1A)     # 炭黑色 #1A1A1A
ACCENT_YELLOW = RGBColor(0xFF, 0xE0, 0x00)  # 電力黃 #FFE000
ACCENT_RED = RGBColor(0xFF, 0x4D, 0x4D)     # 珊瑚紅 #FF4D4D
ACCENT_BLUE = RGBColor(0x2E, 0x5B, 0xFF)    # 電光藍 #2E5BFF

# 裝飾用顏色池
ACCENT_COLORS = [ACCENT_YELLOW, ACCENT_RED, ACCENT_BLUE]

def load_outline():
    if not os.path.exists(OUTLINE_PATH):
        # 預設簡報大綱
        return [
            {"title": "鴻勝化學：智慧物流與品質控制", "content": ["1. 槽車物流實時調度系統", "2. TSMC N-series 高精準條碼驗證", "3. 現場操作離線優先防呆方案"]},
            {"title": "ISOTANK 物流痛點與解決方案", "content": ["1. LLM 運算幻覺問題：流速計算易出錯", "2. 解決方案：導入 Python 物流計時核心", "3. 司機與調度端即時數據同步"]},
            {"title": "未來展望：React & Supabase 升級", "content": ["1. 現代化 Web 前端架構重構", "2. Supabase RLS 資料庫層級安全防護", "3. 全面提升系統擴充性與響應速度"]}
        ]
        
    slides_data = []
    current_slide = None
    
    with open(OUTLINE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("TITLE:"):
                if current_slide:
                    slides_data.append(current_slide)
                current_slide = {"title": line[6:].strip(), "content": []}
            elif line.startswith("-") and current_slide:
                current_slide["content"].append(line[1:].strip())
                
    if current_slide:
        slides_data.append(current_slide)
        
    return slides_data

def set_slide_background(slide):
    # 用一個滿版矩形設置奶油色背景
    left = top = Inches(0)
    width = Inches(13.333)
    height = Inches(7.5)
    bg_shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    bg_shape.fill.solid()
    bg_shape.fill.fore_color.rgb = BG_COLOR
    bg_shape.line.fill.background() # 無邊框

def add_memphis_decorations(slide, slide_index):
    # 依投影片索引輪替裝飾顏色
    accent_color = ACCENT_COLORS[slide_index % len(ACCENT_COLORS)]
    
    # 1. 繪製故意偏移的幾何背景塊 (珊瑚紅/電力黃/電光藍)
    # 底部裝飾大色塊
    dec1 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.5), Inches(6.5), Inches(4.5), Inches(0.5))
    dec1.fill.solid()
    dec1.fill.fore_color.rgb = accent_color
    dec1.line.color.rgb = TEXT_COLOR
    dec1.line.width = Pt(3)
    
    # 黑色陰影大塊
    dec2 = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(6.55), Inches(4.5), Inches(0.5))
    dec2.fill.solid()
    dec2.fill.fore_color.rgb = TEXT_COLOR
    dec2.line.fill.background()
    # 送至最底層（在奶油背景之上，裝飾塊之下）
    slide.shapes._spTree.remove(dec2._element)
    slide.shapes._spTree.insert(2, dec2._element) # 奶油底在0, 裝飾1在1, 陰影在2
    
    # 右上角小圓圈裝飾
    circle = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(11.5), Inches(0.5), Inches(1.2), Inches(1.2))
    circle.fill.solid()
    circle.fill.fore_color.rgb = ACCENT_COLORS[(slide_index + 1) % len(ACCENT_COLORS)]
    circle.line.color.rgb = TEXT_COLOR
    circle.line.width = Pt(3)

def create_memphis_presentation():
    prs = Presentation()
    
    # 設置投影片比例為 16:9
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    blank_slide_layout = prs.slide_layouts[6] # 6號為空白版面
    
    slides_data = load_outline()
    
    for idx, data in enumerate(slides_data):
        slide = prs.slides.add_slide(blank_slide_layout)
        set_slide_background(slide)
        add_memphis_decorations(slide, idx)
        
        # 1. 建立標題文字方塊
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(11.5), Inches(1.5))
        tf = title_box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_title = tf.paragraphs[0]
        p_title.text = data["title"]
        p_title.font.name = "Alibaba PuHuiTi 3.0"
        p_title.font.size = Pt(40)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_COLOR
        
        # 2. 建立內容文字方塊 (使用霞鶩文楷/楷體樣式)
        content_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.8), Inches(10.5), Inches(3.5))
        tf_content = content_box.text_frame
        tf_content.word_wrap = True
        tf_content.margin_left = tf_content.margin_top = tf_content.margin_right = tf_content.margin_bottom = 0
        
        for bullet_idx, item in enumerate(data["content"]):
            p = tf_content.add_paragraph() if bullet_idx > 0 else tf_content.paragraphs[0]
            p.text = "   " + item
            p.font.name = "LXGW WenKai"
            p.font.size = Pt(22)
            p.font.color.rgb = TEXT_COLOR
            p.space_after = Pt(20) # 段落間距
            
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    prs.save(OUTPUT_PATH)
    print(f"✓ 成功生成孟菲斯風格投影片：{OUTPUT_PATH}")
    print(f"  -> 總投影片張數：{len(slides_data)} 張")

if __name__ == "__main__":
    create_memphis_presentation()
