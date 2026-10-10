import ast
import os

recovered_gdrive_src = "c:/GOOGLE ANGET/溫度通報/scratch/recovered_gdrive_0.py"
recovered_fish_src = "c:/GOOGLE ANGET/溫度通報/scratch/recovered_fish_0.py"

dest_gdrive = "c:/GOOGLE ANGET/isotank-training/backup_to_gdrive.py"
dest_fish = "c:/GOOGLE ANGET/isotank-training/generate_narration_fish.py"

def decode_and_save(src_path, dest_path, is_gdrive=False):
    if not os.path.exists(src_path):
        print(f"[ERROR] Source {src_path} not found")
        return
    
    with open(src_path, "r", encoding="utf-8") as f:
        raw_content = f.read().strip()
    
    # Try ast.literal_eval
    try:
        # Check if it is already wrapped in quotes. If not, wrap it.
        # But wait! If it contains newlines, wrapping in single double-quotes might fail, 
        # so triple double-quotes is better.
        if not (raw_content.startswith('"') or raw_content.startswith("'")):
            raw_content = '"""' + raw_content + '"""'
        decoded = ast.literal_eval(raw_content)
    except Exception as e:
        print(f"[ERROR] ast.literal_eval failed for {src_path}: {e}")
        return

    # Check if last line was truncated
    if is_gdrive:
        if "請將彈出的壓縮檔拖拉到 Goog" in decoded:
            decoded = decoded.replace(
                'print("\\n完成！請將彈出的壓縮檔拖拉到 Goog',
                'print("\\n完成！請將彈出的壓縮檔拖拉到 Google Drive 完成備份。")'
            )

    # Ensure directories exist
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "w", encoding="utf-8") as f:
        f.write(decoded)
    print(f"[OK] Decoded and saved to {dest_path}")

decode_and_save(recovered_gdrive_src, dest_gdrive, is_gdrive=True)
decode_and_save(recovered_fish_src, dest_fish)
