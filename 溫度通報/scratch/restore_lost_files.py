import os
import shutil

# Paths
recovered_gdrive_src = "c:/GOOGLE ANGET/溫度通報/scratch/recovered_gdrive_0.py"
recovered_fish_src = "c:/GOOGLE ANGET/溫度通報/scratch/recovered_fish_0.py"

dest_gdrive = "c:/GOOGLE ANGET/isotank-training/backup_to_gdrive.py"
dest_fish = "c:/GOOGLE ANGET/isotank-training/generate_narration_fish.py"

print("Restoring backup_to_gdrive.py...")
if os.path.exists(recovered_gdrive_src):
    # Read the recovered file
    with open(recovered_gdrive_src, "r", encoding="utf-8") as f:
        gdrive_content = f.read()
    
    # Check if last line was truncated
    if "請將彈出的壓縮檔拖拉到 Goog" in gdrive_content:
        # Complete the truncated line
        gdrive_content = gdrive_content.replace(
            'print("\\n完成！請將彈出的壓縮檔拖拉到 Goog',
            'print("\\n完成！請將彈出的壓縮檔拖拉到 Google Drive 完成備份。")'
        )
    
    # Write to destination
    os.makedirs(os.path.dirname(dest_gdrive), exist_ok=True)
    with open(dest_gdrive, "w", encoding="utf-8") as f:
        f.write(gdrive_content)
    print("  [OK] Restored backup_to_gdrive.py to", dest_gdrive)
else:
    print("  [ERROR] recovered_gdrive_0.py not found")

print("Restoring generate_narration_fish.py...")
if os.path.exists(recovered_fish_src):
    # Read the recovered file
    with open(recovered_fish_src, "r", encoding="utf-8") as f:
        fish_content = f.read()
        
    # Write to destination
    os.makedirs(os.path.dirname(dest_fish), exist_ok=True)
    with open(dest_fish, "w", encoding="utf-8") as f:
        f.write(fish_content)
    print("  [OK] Restored generate_narration_fish.py to", dest_fish)
else:
    print("  [ERROR] recovered_fish_0.py not found")
