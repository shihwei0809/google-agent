#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import shutil
from pathlib import Path

def main():
    base_dir = Path(__file__).parent.resolve()
    dest_dir = base_dir / "assets" / "images"
    
    # 產出的圖片映射
    mappings = {
        "p1_panel3": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p1_panel3_1780575916313.png",
        "p1_panel4": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p1_panel4_1780575929405.png",
        "p2_panel1": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p2_panel1_1780575945149.png",
        "p2_panel2": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p2_panel2_1780575962388.png",
        "p2_panel3": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p2_panel3_1780575981968.png",
        "p2_panel4": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p2_panel4_1780576003802.png",
        "p3_panel1": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p3_panel1_1780576018858.png",
        "p3_panel2": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p3_panel2_1780576040301.png",
        "p3_panel3": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p3_panel3_1780576061613.png",
        "p3_panel4": r"C:\Users\C606\.gemini\antigravity\brain\09933bf5-7980-4ff6-89a3-005ab20a5257\p3_panel4_cabin_left_bubble_1780580277200.png",
    }
    
    for panel_name, src in mappings.items():
        src_path = Path(src)
        dest_path = dest_dir / f"{panel_name}.png"
        if src_path.exists():
            shutil.copy2(src_path, dest_path)
            print(f"Copied: {src_path.name} -> {dest_path}")
        else:
            print(f"❌ Source file not found: {src}")

if __name__ == "__main__":
    main()
