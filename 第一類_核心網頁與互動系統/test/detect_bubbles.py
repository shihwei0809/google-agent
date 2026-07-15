#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from PIL import Image
from pathlib import Path

def find_white_bubbles(image_path):
    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    
    # 建立拜訪矩陣
    visited = [[False for _ in range(height)] for _ in range(width)]
    bubbles = []
    
    # 尋找白色區域 (R > 250, G > 250, B > 250)
    for x in range(0, width, 4):  # 步長為 4 加速掃描
        for y in range(0, height, 4):
            if visited[x][y]:
                continue
            
            r, g, b = img.getpixel((x, y))
            if r >= 245 and g >= 245 and b >= 245:
                # 執行 BFS 尋找連通區塊
                queue = [(x, y)]
                visited[x][y] = True
                pixels = []
                
                min_x, max_x = x, x
                min_y, max_y = y, y
                
                while queue:
                    curr_x, curr_y = queue.pop(0)
                    pixels.append((curr_x, curr_y))
                    
                    # 更新邊界
                    if curr_x < min_x: min_x = curr_x
                    if curr_x > max_x: max_x = curr_x
                    if curr_y < min_y: min_y = curr_y
                    if curr_y > max_y: max_y = curr_y
                    
                    # 搜尋鄰近像素 (間隔 4 像素以加速連通)
                    for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4)]:
                        nx, ny = curr_x + dx, curr_y + dy
                        if 0 <= nx < width and 0 <= ny < height and not visited[nx][ny]:
                            nr, ng, nb = img.getpixel((nx, ny))
                            if nr >= 245 and ng >= 245 and nb >= 245:
                                visited[nx][ny] = True
                                queue.append((nx, ny))
                
                # 計算面積和長寬比
                area = len(pixels) * 16  # 估算面積
                if 2000 < area < 100000:  # 排除背景跟極小雜訊
                    bubbles.append({
                        "min_x": min_x,
                        "min_y": min_y,
                        "max_x": max_x,
                        "max_y": max_y,
                        "center_x": (min_x + max_x) // 2,
                        "center_y": (min_y + max_y) // 2,
                        "width": max_x - min_x,
                        "height": max_y - min_y,
                        "area": area
                    })
    
    # 按照 x 座標從右到左排序 (符合漫畫閱讀順序)
    bubbles.sort(key=lambda b: b["center_x"], reverse=True)
    return bubbles

def main():
    base_dir = Path(__file__).parent.resolve()
    images_dir = base_dir / "assets" / "images"
    
    results = {}
    for i in range(1, 4):
        for j in range(1, 5):
            panel_id = f"p{i}_panel{j}"
            img_path = images_dir / f"{panel_id}.png"
            if img_path.exists():
                bubbles = find_white_bubbles(img_path)
                results[panel_id] = bubbles
                print(f"[{panel_id}] 偵測到 {len(bubbles)} 個對話框:")
                for idx, b in enumerate(bubbles):
                    print(f"  #{idx+1}: 中心({b['center_x']}, {b['center_y']}), 寬高({b['width']}, {b['height']}), BBox: ({b['min_x']}, {b['min_y']}, {b['max_x']}, {b['max_y']})")
            else:
                print(f"❌ 找不到 {img_path}")
                
    # 寫入設定檔以便後續腳本直接讀取
    with open(base_dir / "detected_bubbles.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n📝 偵測結果已存入 detected_bubbles.json")

if __name__ == "__main__":
    main()
