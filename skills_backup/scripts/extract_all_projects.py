#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專案還原工具：讀取 AI MD 檔備份，將各自對話中的程式碼、資產圖片與對話紀錄還原為獨立專案。
"""

import os
import re
import sys
import zipfile
import shutil

sys.stdout.reconfigure(encoding='utf-8')

BACKUP_DIR = "G:/我的雲端硬碟/AI MD檔備份/20260510"
OUTPUT_PARENT_DIR = "D:/GOOGLE ANGET"

# 片段代碼判定模式
PLACEHOLDER_PATTERNS = [
    r'\/\/\s*\.\.\.',
    r'\/\*\s*\.\.\.\s*\*\/',
    r'#\s*\.\.\.',
    r'<!--\s*\.\.\.\s*-->',
    r'\/\/.*原有.*欄位',
    r'\/\/.*原有欄位',
    r'\/\/.*請保留您原本的',
    r'\/\/.*在原本的.*中加入',
    r'\/\/.*在原本的.*區塊中加入',
    r'\/\/.*修改部分',
    r'\/\/.*修改邏輯',
    r'\/\/.*片段',
    r'\/\*\s*原有代碼\s*\*\/',
    r'//.*(skip|omitted)',
]

def is_snippet(code, filename):
    lines = code.split('\n')
    
    # 檢查是否含有省略符號或片段指示註解
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            return True
            
    # 若行數過少且不具備完整檔案的特徵結構
    if len(lines) < 25:
        ext = os.path.splitext(filename)[1].lower()
        if ext == '.php' and not code.strip().startswith('<?php'):
            return True
        if ext == '.html' and not ('<!doctype' in code.lower() or '<html' in code.lower()):
            return True
            
    return False

def parse_chat_files(content):
    lines = content.split('\n')
    files = {}
    current_file = None
    in_code_block = False
    code_block_lines = []
    
    for idx, line in enumerate(lines):
        # 僅在非代碼區塊中比對標題
        if not in_code_block:
            header_match = re.match(r'^#{1,5}\s+(.+)$', line)
            if header_match:
                header_text = header_match.group(1).strip()
                # 尋找含有副檔名的檔名
                file_match = re.search(r'([\w\-]+\.(?:html|css|js|gs|py|php|sql|xml|kt|kotlin|json|sh|bat|ps1))', header_text, re.IGNORECASE)
                if file_match:
                    current_file = file_match.group(1)
                continue
            
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_block_lines = []
                if not current_file:
                    # 代碼區塊無標題時，向前看 5 行是否有檔名
                    for lookback in range(max(0, idx - 5), idx):
                        file_match = re.search(r'([\w\-]+\.(?:html|css|js|gs|py|php|sql|xml|kt|kotlin|json|sh|bat|ps1))', lines[lookback], re.IGNORECASE)
                        if file_match:
                            current_file = file_match.group(1)
                            break
            else:
                in_code_block = False
                if current_file:
                    code_content = '\n'.join(code_block_lines)
                    
                    # 丟棄吞入對話框架標記的異常區塊
                    if "## Turn " in code_content or "### 👤 User" in code_content or "### 🤖 Assistant" in code_content:
                        current_file = None
                        continue
                        
                    canonical_name = current_file
                    existing_match = [k for k in files.keys() if k.lower() == canonical_name.lower()]
                    
                    if existing_match:
                        matched_key = existing_match[0]
                        # 只有當新代碼非片段，才覆蓋舊完整檔案
                        if not is_snippet(code_content, canonical_name):
                            files[matched_key] = code_content
                    else:
                        files[canonical_name] = code_content
                        
                current_file = None
        elif in_code_block:
            code_block_lines.append(line)
            
    return files

def generate_readme(project_name, files_extracted):
    readme_content = f"""# {project_name}

本專案是由 Google Gemini 聊天紀錄備份自動還原重建的獨立專案。

## 專案內容與對話紀錄
- 原始對話備份：[chat.md](chat.md) (內含完整開發歷程、QA 與思路)
- 對話圖片資產：存放於 `assets/` 目錄下

## 還原程式檔案列表
"""
    if files_extracted:
        for f, size in files_extracted.items():
            readme_content += f"- [{f}]({f}) ({size} 字元)\n"
    else:
        readme_content += "*本專案僅包含對話與資產，未提取出獨立程式碼檔案。*\n"
        
    readme_content += """
---
*本檔案由 Antigravity 專案還原工具自動產生。*
"""
    return readme_content

def main():
    if not os.path.exists(BACKUP_DIR):
        print(f"錯誤：備份目錄不存在 {BACKUP_DIR}")
        sys.exit(1)
        
    zips = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".zip")]
    print(f"找到 {len(zips)} 個專案壓縮備份。開始還原...")
    
    for f in zips:
        zip_path = os.path.join(BACKUP_DIR, f)
        project_name = os.path.splitext(f)[0]
        project_dir = os.path.join(OUTPUT_PARENT_DIR, project_name)
        
        print(f"\n📂 正在處理專案：{project_name}")
        os.makedirs(project_dir, exist_ok=True)
        
        files_extracted_info = {}
        
        try:
            with zipfile.ZipFile(zip_path) as z:
                # 1. 寫出對話紀錄 chat.md
                chat_content = z.read("chat.md").decode("utf-8")
                chat_out_path = os.path.join(project_dir, "chat.md")
                with open(chat_out_path, "w", encoding="utf-8") as out_f:
                    out_f.write(chat_content)
                print("  ✓ 已輸出對話紀錄 chat.md")
                
                # 2. 複製資產圖片
                assets_extracted = 0
                for item in z.namelist():
                    if item.startswith("assets/") and not item.endswith("/"):
                        os.makedirs(os.path.join(project_dir, "assets"), exist_ok=True)
                        dest_path = os.path.join(project_dir, item)
                        with z.open(item) as src_img, open(dest_path, "wb") as dest_img:
                            shutil.copyfileobj(src_img, dest_img)
                        assets_extracted += 1
                if assets_extracted > 0:
                    print(f"  ✓ 已還原 {assets_extracted} 張圖片資產")
                
                # 3. 提取程式碼檔案
                extracted_files = parse_chat_files(chat_content)
                for file_name, code in extracted_files.items():
                    file_out_path = os.path.join(project_dir, file_name)
                    # 建立任何必要的子資料夾（雖然通常都在根目錄）
                    os.makedirs(os.path.dirname(file_out_path) or project_dir, exist_ok=True)
                    with open(file_out_path, "w", encoding="utf-8") as out_code:
                        out_code.write(code)
                    files_extracted_info[file_name] = len(code)
                    print(f"  ✓ 提取檔案：{file_name} ({len(code)} 字元)")
                
                # 4. 產生 README.md
                readme_content = generate_readme(project_name, files_extracted_info)
                readme_path = os.path.join(project_dir, "README.md")
                with open(readme_path, "w", encoding="utf-8") as readme_f:
                    readme_f.write(readme_content)
                print("  ✓ 已建立 README.md")
                
        except Exception as e:
            print(f"  ⚠ 處理專案 {project_name} 時發生異常：{e}")
            
    print("\n🎉 所有專案還原重建完成！")

if __name__ == "__main__":
    main()
