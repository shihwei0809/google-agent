import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

base_dir = r"d:\GOOGLE ANGET"

subprojects = []

for item in os.listdir(base_dir):
    full_path = os.path.join(base_dir, item)
    if os.path.isdir(full_path) and not item.startswith('.') and item not in ['old', 'venv', 'node_modules', 'scratch', 'temp']:
        # If it's a category folder or a subproject
        if item.startswith('第一類') or item.startswith('第二類') or item.startswith('第三類') or item == '說明書':
            for sub in os.listdir(full_path):
                sub_path = os.path.join(full_path, sub)
                if os.path.isdir(sub_path) and not sub.startswith('.'):
                    subprojects.append(sub_path)
        else:
            subprojects.append(full_path)

print("=== 專案操作手冊 (Word/PDF) 全域盤點清單 ===")

missing_manual_projects = []

for idx, p in enumerate(subprojects, 1):
    rel = os.path.relpath(p, base_dir)
    files = os.listdir(p) if os.path.exists(p) else []
    
    docx_files = [f for f in files if f.endswith('.docx') and not f.startswith('~$')]
    pdf_files = [f for f in files if f.endswith('.pdf')]
    
    has_docx = len(docx_files) > 0
    has_pdf = len(pdf_files) > 0
    
    docx_status = "✅ " + ", ".join(docx_files) if has_docx else "❌ 缺少 Word (.docx)"
    pdf_status = "✅ " + ", ".join(pdf_files) if has_pdf else "❌ 缺少 PDF (.pdf)"
    
    print(f"{idx}. [{rel}]")
    print(f"   - Word: {docx_status}")
    print(f"   - PDF:  {pdf_status}")
    
    if not has_docx or not has_pdf:
        missing_manual_projects.append((rel, p, has_docx, has_pdf))

print(f"\n需要補齊 Word/PDF 手冊的專案數量：{len(missing_manual_projects)}")
