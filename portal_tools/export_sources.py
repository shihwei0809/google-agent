import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure UTF-8 output
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# 1. Dynamically locate the base directory of the project (parent of portal_tools)
base_dir = Path(__file__).parent.parent.resolve()
manuals_dir = base_dir / "說明書"
backup_dir = manuals_dir / "sources_backup"

# Create the backup directory if it doesn't exist
backup_dir.mkdir(parents=True, exist_ok=True)

# 2. Define the files to export, grouping them by project
files_to_export = [
    # N系列BARCODE出貨核對 (GAS)
    {
        "project": "N系列BARCODE出貨核對",
        "filename": "Code.gs",
        "src": base_dir / "N系列BARCODE出貨核對" / "Code.gs",
        "lang": "javascript"
    },
    {
        "project": "N系列BARCODE出貨核對",
        "filename": "Index.html",
        "src": base_dir / "N系列BARCODE出貨核對" / "Index.html",
        "lang": "html"
    },
    {
        "project": "N系列BARCODE出貨核對",
        "filename": "Query.html",
        "src": base_dir / "N系列BARCODE出貨核對" / "Query.html",
        "lang": "html"
    },
    
    # n系列GAS-轉-APK-離線核對上傳 (Android)
    {
        "project": "n系列GAS-轉-APK-離線核對上傳",
        "filename": "MainActivity.kt",
        "src": base_dir / "n系列GAS-轉-APK-離線核對上傳" / "BARCODEout-20260601" / "app" / "src" / "main" / "java" / "com" / "example" / "barcode_out" / "MainActivity.kt",
        "lang": "kotlin"
    },
    {
        "project": "n系列GAS-轉-APK-離線核對上傳",
        "filename": "NetworkHelper.kt",
        "src": base_dir / "n系列GAS-轉-APK-離線核對上傳" / "BARCODEout-20260601" / "app" / "src" / "main" / "java" / "com" / "example" / "barcode_out" / "NetworkHelper.kt",
        "lang": "kotlin"
    },
    
    # 溫度通報
    {
        "project": "溫度通報",
        "filename": "weather_monitor.py",
        "src": base_dir / "溫度通報" / "weather_monitor.py",
        "lang": "python"
    },
    {
        "project": "溫度通報",
        "filename": "config.json",
        "src": base_dir / "溫度通報" / "config.json",
        "lang": "json"
    },
    {
        "project": "溫度通報",
        "filename": "Code.gs",
        "src": base_dir / "溫度通報" / "Code.gs",
        "lang": "javascript"
    }
]

print(f"Starting source code export process in: {base_dir}")
print(f"Backup target directory: {backup_dir}\n")

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
exported_count = 0

for item in files_to_export:
    src_file = item["src"]
    if not src_file.exists():
        print(f"⚠️ Warning: File not found: {src_file} (Skipping)")
        continue
    
    # Generate backup markdown filename
    safe_project_name = item["project"].replace("-", "_")
    target_md_name = f"{safe_project_name}_{item['filename']}.md"
    target_md_path = backup_dir / target_md_name
    
    try:
        # Read content from source file
        content = src_file.read_text(encoding="utf-8")
        
        # Format the markdown file content
        md_output = f"""# Source Code Backup - {item['project']} - {item['filename']}

> [!NOTE]
> *   **原始本機路徑**: [{src_file.name}](file:///{src_file.as_posix().replace(' ', '%20')})
> *   **自動備份時間**: `{timestamp}`
> *   **語言類型**: `{item['lang']}`

``` {item['lang']}
{content}
```
"""
        
        # Write to target markdown backup file
        target_md_path.write_text(md_output, encoding="utf-8")
        print(f"✅ Successfully exported: {item['filename']} -> {target_md_name}")
        exported_count += 1
        
    except Exception as e:
        print(f"❌ Error exporting {item['filename']}: {str(e)}")

print(f"\n🎉 Source code export complete! Successfully backed up {exported_count} files.")
