"""
將 actor_library/actors.json 中的 6 位固定演員批次上傳至 Google Flow「角色 (Characters)」分頁。
用法：
  python actor_library/upload_to_flow_characters.py
  python actor_library/upload_to_flow_characters.py --project-url https://flow.google.com/project/<id>
  python actor_library/upload_to_flow_characters.py --only f25 m25
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

LIB_DIR = Path(__file__).resolve().parent
BASE_DIR = LIB_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import auto_upload_flow as flow_core  # noqa: E402

DEFAULT_PROJECT_URL = "https://flow.google.com/project/52feb772-f8f7-4f41-9f14-9fb51a6f91be"


def open_characters_tab(page):
    """進入左側『角色』分頁（若已在角色編輯器內則先點返回/完成）"""
    back_btn = page.locator("button[aria-label='返回']").first
    try:
        if back_btn.is_visible(timeout=800):
            back_btn.click()
            time.sleep(1.2)
    except Exception:
        pass

    tab = page.get_by_text("角色", exact=True).first
    try:
        if tab.is_visible(timeout=4000):
            tab.click()
            time.sleep(2.0)
    except Exception:
        pass


def open_new_character_creator(page) -> bool:
    """確保進入『新角色』上傳畫面（支援 0 個角色自動進入，或已有角色時點新增按鈕）"""
    up_btn = page.get_by_role("button", name=re.compile(r"^上傳$|^Upload$", re.I)).first
    try:
        if up_btn.is_visible(timeout=2000):
            return True
    except Exception:
        pass

    # 若已有角色列表，點擊「新增角色 / 新角色 / 建立角色 / +」按鈕
    candidates = [
        page.get_by_role("button", name=re.compile(r"新增角色|新角色|建立角色|New character|Add character", re.I)).first,
        page.locator("button:has-text('新角色'), button:has-text('新增角色'), button:has-text('建立')").first,
        page.locator("button[aria-label='新增媒體選單']").first,
    ]
    for btn in candidates:
        try:
            if btn.is_visible(timeout=1200):
                btn.click()
                time.sleep(1.5)
                if up_btn.is_visible(timeout=2000):
                    return True
                # 若是下拉選單，再點「角色」或「新角色」
                menu_char = page.locator("[role='menuitem']:has-text('角色'), button:has-text('新角色')").first
                if menu_char.is_visible(timeout=1200):
                    menu_char.click()
                    time.sleep(1.5)
                    if up_btn.is_visible(timeout=2500):
                        return True
        except Exception:
            continue
    return False


def upload_one_actor(page, actor: dict) -> bool:
    aid = actor["id"]
    display_name = f"{aid} {actor['name_zh']}"
    ref_path = (LIB_DIR / actor["ref_image"]).resolve()
    if not ref_path.exists():
        print(f"  [略過] 找不到定裝照：{ref_path}")
        return False

    print(f"\n=== 上傳角色 [{display_name}] ({ref_path.name}) ===")
    if not open_new_character_creator(page):
        print("  [錯誤] 無法進入「新角色」上傳介面！")
        return False

    up_btn = page.get_by_role("button", name=re.compile(r"^上傳$|^Upload$", re.I)).first
    with page.expect_file_chooser(timeout=10000) as fc_info:
        up_btn.click()
    fc_info.value.set_files(str(ref_path))

    # 等待角色名稱欄位出現（代表上傳完成）
    name_input = page.locator("input[aria-label='角色名稱'], input[placeholder='角色名稱']").first
    name_input.wait_for(state="visible", timeout=25000)
    time.sleep(1.0)

    # 填入角色名稱
    name_input.click(force=True)
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    name_input.fill(display_name)
    page.keyboard.press("Enter")
    time.sleep(0.6)

    # 填入角色個性 / 鎖臉描述
    bio_box = page.locator("textarea[aria-label='角色個性'], textarea[placeholder*='描述角色']").first
    try:
        if bio_box.is_visible(timeout=2000):
            bio_text = f"{actor['appearance_zh']}\n\nIdentity Lock: {actor['anchor_en']}"
            bio_box.click(force=True)
            bio_box.fill(bio_text)
            time.sleep(0.5)
    except Exception as exc:
        print(f"  [提示] 略過角色個性填寫：{exc}")

    # 點擊「完成」儲存
    done_btn = page.get_by_role("button", name=re.compile(r"^完成$|^Done$", re.I)).first
    done_btn.wait_for(state="visible", timeout=8000)
    done_btn.click()
    time.sleep(2.5)
    print(f"  ✅ [{display_name}] 已成功建立並儲存至 Google Flow 角色庫！")
    return True


def main():
    parser = argparse.ArgumentParser(description="批次上傳 actor_library 角色至 Google Flow 角色庫")
    parser.add_argument("--project-url", default=DEFAULT_PROJECT_URL)
    parser.add_argument("--only", nargs="+", help="只上傳指定代號，例如 --only f25 m25")
    parser.add_argument("--screenshot", default="", help="完成後截圖儲存路徑")
    args = parser.parse_args()

    data = json.loads((LIB_DIR / "actors.json").read_text(encoding="utf-8"))
    actors = data["actors"]
    if args.only:
        only_set = set(args.only)
        actors = [a for a in actors if a["id"] in only_set]

    flow_core.ensure_chrome_running(args.project_url)
    uploaded = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{flow_core.CDP_PORT}")
        page = None
        for c in browser.contexts:
            for pg in c.pages:
                if "flow.google.com" in (pg.url or ""):
                    page = pg
                    break
            if page:
                break
        if page is None:
            page = browser.contexts[0].new_page()

        page.goto(args.project_url, wait_until="domcontentloaded")
        time.sleep(4.5)
        open_characters_tab(page)

        # 若前面測試留下一筆「未命名的角色」，先看頁面上是否已經存在已命名角色以免重複
        existing_text = page.locator("body").inner_text() or ""

        for actor in actors:
            display_name = f"{actor['id']} {actor['name_zh']}"
            if display_name in existing_text:
                print(f"  [已存在] {display_name} 已在 Flow 角色庫中，自動略過。")
                uploaded.append(actor["id"])
                continue
            if upload_one_actor(page, actor):
                uploaded.append(actor["id"])
            time.sleep(1.2)

        if args.screenshot:
            Path(args.screenshot).parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=args.screenshot)
            print(f"[截圖] 已儲存角色庫畫面：{args.screenshot}")

    print(f"\n🎉 完成上傳：{len(uploaded)} / {len(actors)} 位 ({', '.join(uploaded)})")


if __name__ == "__main__":
    main()
