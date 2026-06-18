import os
import re
import shutil

# Target Directories in current workspace
workspace_dir = r"c:\GOOGLE ANGET\ai anget"
clipping_dir = os.path.join(workspace_dir, "Clipping")
creation_dir = os.path.join(workspace_dir, "創作庫")
kb_dir = os.path.join(workspace_dir, "知識庫")
proj_cards_dir = os.path.join(kb_dir, "專案卡")

# Source Files
root_dir = r"c:\GOOGLE ANGET"
project_records_path = os.path.join(root_dir, "PROJECT_RECORDS.md")

# Ensure target directories exist
os.makedirs(clipping_dir, exist_ok=True)
os.makedirs(creation_dir, exist_ok=True)
os.makedirs(kb_dir, exist_ok=True)
os.makedirs(proj_cards_dir, exist_ok=True)

def parse_project_records(records_path):
    if not os.path.exists(records_path):
        print(f"Error: {records_path} does not exist.")
        return []
        
    with open(records_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find all h3 headings under 核心專案清單
    projects = []
    # Split by ###
    parts = content.split("### ")
    for part in parts[1:]:
        lines = part.strip().split("\n")
        title_line = lines[0]
        # Match title and folder/tag if any
        # e.g., "1. 軟管對刷稽核系統 (hongsheng-web)"
        title_match = re.match(r"\d+\.\s*(.+?)(?:\s*\((.+?)\))?$", title_line.strip())
        if title_match:
            title = title_match.group(1).strip()
            folder_ref = title_match.group(2).strip() if title_match.group(2) else ""
        else:
            title = title_line.strip()
            folder_ref = ""
            
        desc_lines = []
        tech_stack = ""
        features = []
        
        for line in lines[1:]:
            line_str = line.strip()
            if line_str.startswith("- **用途**：") or line_str.startswith("- **用途**:"):
                desc_lines.append(line_str.replace("- **用途**：", "").replace("- **用途**:", ""))
            elif line_str.startswith("- **技術棧**：") or line_str.startswith("- **技術棧**:"):
                tech_stack = line_str.replace("- **技術棧**：", "").replace("- **技術棧**:", "")
            elif line_str.startswith("- **功能特色**：") or line_str.startswith("- **功能特色**:"):
                features_block = line_str.replace("- **功能特色**：", "").replace("- **功能特色**:", "")
                features.append(features_block)
            elif line_str.startswith("- ") or line_str.startswith("* "):
                features.append(line_str[2:])
            elif line_str and not line_str.startswith("#"):
                desc_lines.append(line_str)
                
        projects.append({
            "title": title,
            "folder": folder_ref,
            "description": " ".join(desc_lines),
            "tech_stack": tech_stack,
            "features": features
        })
    return projects

def copy_reference_files():
    # Files to copy to Clipping
    refs = [
        "C50110-INV-02-01_text.txt",
        "沖繩自由行規劃_2大2小.md",
        "09-AntiGravity專屬懶人包.md",
        "ANTIGRAVITY.md",
        "SKILL.md",
        "鴻勝化學_系統主題歌曲腳本.md"
    ]
    for filename in refs:
        src = os.path.join(root_dir, filename)
        dst = os.path.join(clipping_dir, filename)
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                print(f"Copied reference {filename} to Clipping/")
            except Exception as e:
                print(f"Error copying {filename}: {e}")

def main():
    print("Parsing PROJECT_RECORDS.md...")
    projects = parse_project_records(project_records_path)
    print(f"Found {len(projects)} projects.")
    
    copy_reference_files()
    
    # Generate Project Cards
    index_content = "# 🗂️ 專案總覽索引 (Project Hub)\n\n"
    index_content += "此索引由 AI 自動生成，用來導覽本機的所有開發專案。點擊下方連結可進入各專案的知識卡片：\n\n"
    index_content += "| 專案名稱 | 技術棧 | 關聯目錄 | 專案卡片 |\n"
    index_content += "| --- | --- | --- | --- |\n"
    
    for p in projects:
        card_filename = f"{p['title'].replace(' ', '_')}.md"
        card_path = os.path.join(proj_cards_dir, card_filename)
        
        # Write Project Card
        card_content = f"# 📌 {p['title']}\n\n"
        card_content += f"- **專案類型**: 核心開發專案\n"
        if p['folder']:
            card_content += f"- **本機目錄**: `c:\\GOOGLE ANGET\\{p['folder']}`\n"
        if p['tech_stack']:
            card_content += f"- **技術棧**: `{p['tech_stack']}`\n"
        card_content += "\n## 📝 專案用途\n"
        card_content += f"{p['description']}\n\n"
        
        if p['features']:
            card_content += "## ✨ 功能特色\n"
            for feat in p['features']:
                card_content += f"- {feat}\n"
            card_content += "\n"
            
        card_content += "## 🔗 相關資源與連結\n"
        if p['folder']:
            card_content += f"- [本機專案資料夾](file:///c:/GOOGLE%20ANGET/{p['folder'].replace(' ', '%20')})\n"
        card_content += f"- [返回專案總覽索引]([[Index]])\n"
        
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(card_content)
        print(f"Generated Project Card: {card_filename}")
        
        # Add entry to Index
        folder_link = f"`{p['folder']}`" if p['folder'] else "無"
        index_content += f"| {p['title']} | {p['tech_stack'] or 'N/A'} | {folder_link} | [[專案卡/{p['title'].replace(' ', '_')}\\|查看卡片]] |\n"
        
    # Write global Index.md
    index_path = os.path.join(kb_dir, "Index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)
    print("Generated global Index.md in 知識庫/")
    
    print("\nVault setup completed successfully!")

if __name__ == "__main__":
    main()
