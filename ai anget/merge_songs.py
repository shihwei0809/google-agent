import os
import subprocess

# Paths
workspace_dir = r"c:\GOOGLE ANGET\ai anget"
output_file = os.path.join(workspace_dir, "勝一化學_Suno音樂合輯.mp3")

# List of files in the order of creation/topic
files_to_merge = [
    "純淨的脈動 (The Pulse of Purity).mp3",
    "純淨的脈動 (The Pulse of Purity) (1).mp3",
    "純淨之光.mp3",
    "純淨之光 (1).mp3",
    "純淨之光-男女合唱.mp3",
    "純淨之光-男女合唱 (1).mp3"
]

def main():
    # Verify all files exist
    existing_files = []
    for f in files_to_merge:
        full_path = os.path.join(workspace_dir, f)
        if os.path.exists(full_path):
            existing_files.append(full_path)
            print(f"找到檔案: {f}")
        else:
            print(f"警告: 找不到檔案 {f}")
            
    if not existing_files:
        print("沒有找到任何可合併的檔案。")
        return
        
    # Write inputs.txt for ffmpeg
    inputs_txt_path = os.path.join(workspace_dir, "inputs.txt")
    with open(inputs_txt_path, "w", encoding="utf-8") as out:
        for fpath in existing_files:
            # Escape single quotes for ffmpeg format
            escaped_path = fpath.replace("'", "'\\''")
            out.write(f"file '{escaped_path}'\n")
            
    print(f"\n正在使用 ffmpeg 合併 {len(existing_files)} 首歌曲...")
    
    # Run ffmpeg command
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
        "-i", inputs_txt_path, "-c", "copy", output_file
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("合併成功！")
        print(f"輸出檔案已儲存至: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg 合併失敗！")
        print(f"錯誤訊息: {e.stderr}")
    finally:
        # Clean up inputs.txt
        if os.path.exists(inputs_txt_path):
            os.remove(inputs_txt_path)

if __name__ == "__main__":
    main()
