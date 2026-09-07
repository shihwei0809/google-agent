# -*- coding: utf-8 -*-
"""
鴻勝化學 QC 看板本機伺服器 (根目錄代理啟動器)
自動定位 2_PWA_App版 目錄並啟動 Web 伺服器
"""
import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
pwa_dir = os.path.join(root_dir, "2_PWA_App版")

if not os.path.exists(pwa_dir):
    # 防呆：若路徑編碼有異，動態搜尋包含 2_PWA 的資料夾
    candidates = [d for d in os.listdir(root_dir) if "2_PWA" in d and os.path.isdir(os.path.join(root_dir, d))]
    if candidates:
        pwa_dir = os.path.join(root_dir, candidates[0])

if os.path.exists(pwa_dir):
    os.chdir(pwa_dir)
    sys.path.insert(0, pwa_dir)
    import run_server
    run_server.run()
else:
    print(f"找不到 PWA 目錄: {pwa_dir}")
    input("按 Enter 鍵結束...")
