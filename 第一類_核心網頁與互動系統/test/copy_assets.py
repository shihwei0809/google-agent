import shutil
import os

def copy_assets():
    # Source paths
    brain_dir = r"C:\Users\C606-PC\.gemini\antigravity\brain\07cfe0a2-c15c-4a90-a8e2-a6f2d685f69b"
    
    # Destination paths
    dest_chars_dir = r"d:\GOOGLE ANGET\test\assets\characters"
    dest_images_dir = r"d:\GOOGLE ANGET\test\assets\images"
    
    os.makedirs(dest_chars_dir, exist_ok=True)
    os.makedirs(dest_images_dir, exist_ok=True)
    
    # Image mappings: (source_filename_prefix, dest_filepath)
    mappings = [
        # Characters
        ("sakura_profile", os.path.join(dest_chars_dir, "sakura.png")),
        ("taiga_profile", os.path.join(dest_chars_dir, "taiga.png")),
        ("papa_profile", os.path.join(dest_chars_dir, "papa.png")),
        ("mama_profile", os.path.join(dest_chars_dir, "mama.png")),
        # Page 1
        ("p1_panel1", os.path.join(dest_images_dir, "p1_panel1.png")),
        ("p1_panel2", os.path.join(dest_images_dir, "p1_panel2.png")),
        ("p1_panel3", os.path.join(dest_images_dir, "p1_panel3.png")),
        ("p1_panel4", os.path.join(dest_images_dir, "p1_panel4.png")),
        # Page 2
        ("p2_panel1", os.path.join(dest_images_dir, "p2_panel1.png")),
        ("p2_panel2", os.path.join(dest_images_dir, "p2_panel2.png")),
        ("p2_panel3", os.path.join(dest_images_dir, "p2_panel3.png")),
        ("p2_panel4", os.path.join(dest_images_dir, "p2_panel4.png")),
        # Page 3
        ("p3_panel1", os.path.join(dest_images_dir, "p3_panel1.png")),
        ("p3_panel2", os.path.join(dest_images_dir, "p3_panel2.png")),
        ("p3_panel3", os.path.join(dest_images_dir, "p3_panel3.png")),
        ("p3_panel4", os.path.join(dest_images_dir, "p3_panel4.png")),
    ]
    
    # Search in brain_dir for matching files
    files = os.listdir(brain_dir)
    
    copied_count = 0
    for prefix, dest_path in mappings:
        found = False
        for f in files:
            if f.startswith(prefix) and f.endswith(".png"):
                src_path = os.path.join(brain_dir, f)
                shutil.copy2(src_path, dest_path)
                print(f"Copied: {f} -> {dest_path}")
                copied_count += 1
                found = True
                break
        if not found:
            print(f"WARNING: No matching file found for prefix '{prefix}' in {brain_dir}")
            
    print(f"Asset copying complete. Total files copied: {copied_count}")

if __name__ == "__main__":
    copy_assets()
