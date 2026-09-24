#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
影像處理指令工具：分析 input/ 中的圖片解析度、比例，並提供基礎裁剪與縮放功能。
"""

import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

def analyze_image(img_path):
    try:
        with Image.open(img_path) as img:
            w, h = img.size
            ratio = round(w / h, 2)
            print(f"影像：{os.path.basename(img_path)}")
            print(f"  尺寸：{w}x{h} px")
            print(f"  長寬比：{ratio} (16:9約為1.78, 4:3約為1.33, 1:1為1.00)")
            return w, h, ratio
    except Exception as e:
        print(f"解析影像 {img_path} 失敗：{e}")
        return None

def main():
    input_dir = "input"
    if not os.path.exists(input_dir):
        print(f"錯誤：找不到目錄 {input_dir}")
        return
        
    imgs = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not imgs:
        print("未在 input/ 中找到任何圖片檔案。")
        return
        
    print(f"在 input/ 內共找到 {len(imgs)} 張圖片：")
    for img_name in imgs:
        img_path = os.path.join(input_dir, img_name)
        analyze_image(img_path)

if __name__ == "__main__":
    main()
