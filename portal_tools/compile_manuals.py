import json
import os
import re
import sys
from pathlib import Path

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# 1. Dynamically locate the base directory of the project (parent of portal_tools)
base_dir = Path(__file__).parent.parent.resolve()
manuals_dir = base_dir / "說明書"
index_html_path = manuals_dir / "index.html"

categories = {
    "第一類_核心網頁與互動系統": "第一類 核心網頁與互動系統",
    "第二類_生產管理與API串接": "第二類 生產管理與API串接",
    "第三類_AI代理與指南企劃": "第三類 AI代理與指南企劃"
}

def compile_manuals():
    if not index_html_path.exists():
        print(f"❌ Error: {index_html_path} does not exist.")
        return
        
    manuals_list = []
    
    # 1. Walk through directories and parse markdown files
    for folder_name, cat_title in categories.items():
        folder_path = manuals_dir / folder_name
        if not folder_path.exists():
            print(f"⚠️ Warning: Folder {folder_name} does not exist.")
            continue
            
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.md'):
                    full_path = Path(root) / file
                    rel_path = full_path.relative_to(manuals_dir).as_posix()
                    
                    try:
                        content = full_path.read_text(encoding="utf-8")
                        
                        # Extract title from the first heading (# Title)
                        title = file
                        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                        if title_match:
                            title = title_match.group(1).strip()
                            
                        # Clean up formatting for the portal search database
                        manuals_list.append({
                            "title": title,
                            "category": cat_title,
                            "path": rel_path,
                            "content": content
                        })
                        print(f"Parsed: {rel_path} -> {title}")
                    except Exception as e:
                        print(f"❌ Error parsing {rel_path}: {str(e)}")
                        
    # 2. Update manuals/index.html
    try:
        html_content = index_html_path.read_text(encoding="utf-8")
        
        # Serialize to JSON safely without double-escaping valid JSON backslashes
        json_data = json.dumps(manuals_list, ensure_ascii=False).replace('</script>', '<\\/script>')
        replacement_line = f"        const manualsData = {json_data};"
        
        # Locate the manualsData array definition in the HTML file
        # It's usually a line looking like: const manualsData = [...];
        pattern = r'^\s*const\s+manualsData\s*=\s*\[.*\]\s*;\s*$'
        
        lines = html_content.splitlines()
        updated = False
        
        for i, line in enumerate(lines):
            if "const manualsData =" in line:
                lines[i] = replacement_line
                updated = True
                break
                
        if updated:
            index_html_path.write_text("\n".join(lines), encoding="utf-8")
            print(f"\n🎉 Successfully compiled {len(manuals_list)} manuals and updated {index_html_path.name}!")
        else:
            print("❌ Error: Could not find the line containing 'const manualsData =' inside index.html.")
            
    except Exception as e:
        print(f"❌ Error writing to index.html: {str(e)}")

if __name__ == "__main__":
    compile_manuals()
