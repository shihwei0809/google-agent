"""
直接在 Google Flow 專案內使用 Nano Banana 2.1 批次生成「鎖定首幀圖片」（不花影片點數）
- 確保「Flow 代理」關閉（維持直接生圖模式 Nano Banana 2.1 · 16:9）
- 依 storyboard.json 自動附加 char_female_ref.jpg / char_male_ref.jpg 鎖定臉型與服裝
- 強制鎖定男角「完全無鬍子 clean-shaven, NO beard, NO mustache」
- 所有圖片直接顯示在 Google Flow 畫布上供肉眼對照挑選，確認無走鐘後再鎖定首幀轉 360p 影片
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import auto_upload_flow as flow_core
import mv_flow_runner as runner

PROJECT_DIR = BASE_DIR / "peace_love_rnb_mv"
PROJECT_URL = "https://flow.google.com/project/52feb772-f8f7-4f41-9f14-9fb51a6f91be"


def ensure_direct_image_mode(page) -> None:
    """確保處於 Nano Banana 直接生圖模式（Flow 代理為 spark_off）"""
    try:
        agent_btn = page.locator("button[aria-label='Flow 代理'], button[aria-label='Flow Agent']").first
        if agent_btn.is_visible(timeout=2000):
            txt = agent_btn.inner_text() or ""
            if "spark_off" not in txt:
                agent_btn.click()
                print("  [模式] 已關閉「Flow 代理」，切回直接生圖模式 (Nano Banana 2.1)！")
                time.sleep(1.5)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(description="在 Google Flow 直接用 Nano Banana 2.1 批次生首幀圖片")
    parser.add_argument("--only", nargs="+", default=["s05", "s12", "s17", "s18", "s19", "s20", "s21", "s22", "s23", "s24", "s25", "s26", "s27", "s28"])
    parser.add_argument("--wait-sec", type=int, default=18, help="每鏡送出後等待生圖間隔秒數")
    args = parser.parse_args()

    sb = json.loads((PROJECT_DIR / "storyboard.json").read_text(encoding="utf-8"))
    chars_cfg = sb.get("characters", {})
    only_set = set(args.only)
    scenes = [s for s in sb["scenes"] if s["id"] in only_set]

    print(f"🎨 準備直接在 Google Flow (Nano Banana 2.1) 批次生成 {len(scenes)} 鏡首幀圖片：{', '.join(s['id'] for s in scenes)}")
    flow_core.ensure_chrome_running(PROJECT_URL)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{flow_core.CDP_PORT}")
        context = browser.contexts[0]
        page = next((pg for c in browser.contexts for pg in c.pages if "flow.google.com" in (pg.url or "")), None)
        if page is None:
            page = context.new_page()
        if PROJECT_URL not in (page.url or ""):
            page.goto(PROJECT_URL, wait_until="domcontentloaded")
            time.sleep(4.0)

        flow_core.wait_for_authenticated_flow(page)
        ensure_direct_image_mode(page)

        for idx, sc in enumerate(scenes, 1):
            sid = sc["id"]
            chars = sc.get("chars", [])
            print(f"\n[{idx}/{len(scenes)}] === [{sid}] {sc['section']} | 角色: {chars or '空鏡'} ===")

            ensure_direct_image_mode(page)
            box = page.get_by_role("textbox", name=re.compile(r"你想製作什麼內容|What do you want|prompt", re.I)).first
            box.wait_for(state="visible", timeout=15000)
            box.click(force=True)
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            time.sleep(0.3)

            for c in chars:
                ref_rel = (chars_cfg.get(c) or {}).get("ref_image")
                if ref_rel:
                    rp = PROJECT_DIR / ref_rel
                    if rp.exists():
                        runner.attach_image_new_flow_ui(page, rp, f"角色參考({c})")

            lock_prefix = ""
            if "male" in chars and "female" in chars:
                lock_prefix = "Using the exact faces, hairstyles, and outfits from the attached character reference photos (man MUST be 100% clean-shaven with NO beard, NO mustache, NO stubble). "
            elif "male" in chars:
                lock_prefix = "Using the exact face, hairstyle, and outfit from the attached male reference photo (100% clean-shaven with NO beard, NO mustache, NO stubble). "
            elif "female" in chars:
                lock_prefix = "Using the exact face, hairstyle, and outfit from the attached female reference photo. "

            prompt = f"[{sid}] " + lock_prefix + sc["keyframe_prompt_en"]
            box.click(force=True)
            page.keyboard.press("End")
            page.keyboard.insert_text(" " + prompt)
            time.sleep(0.6)

            gen_btn = page.locator("button[aria-label='開始生成'], button[aria-label='Generate']").first
            gen_btn.click(force=True)
            print(f"  ✅ [{sid}] 已送出 Nano Banana 2.1 生圖！等待 {args.wait_sec}s ...")
            time.sleep(args.wait_sec)

    print("\n🎉 全部首幀圖片已送出至 Google Flow 畫布！請直接在 Flow 頁面檢視對照挑選。")


if __name__ == "__main__":
    main()
