"""
一鍵操控本機 Chrome (Port 9222) 自動上傳首尾幀與 Prompt 至 Google Flow
- 免 API Key，直接使用已登入 Google 帳號的 Flow 免費 / PRO 點數
- 繞過內建瀏覽器沙盒限制，全程在本機桌面 Chrome 執行
"""

import argparse
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = BASE_DIR / ".chrome_flow_profile"
CDP_PORT = 9222
FLOW_URL = "https://flow.google.com/"

THEMES = {
    "kids": {
        "label": "🎈 兒童卡通玩具王國版 (Kids 3D)",
        "first": BASE_DIR / "kids_first_frame.png",
        "last": BASE_DIR / "kids_last_frame.png",
        "prompt": (
            "Playful fast FPV camera flight diving from high above a colorful 3D animated toy city street, "
            "flying underneath bright rainbow bridges with balloons, gliding past cute cartoon cars and stopping "
            "right in front of an adorable little kid hero wearing a star helmet and cape in the center of the street, "
            "Pixar 3D animation style, joyful bright daylight, 4k."
        ),
    },
    "cyberpunk": {
        "label": "⚡ 賽博龐克霓虹雨夜版 (Cyberpunk)",
        "first": BASE_DIR / "cyberpunk_first_frame.png",
        "last": BASE_DIR / "cyberpunk_last_frame.png",
        "prompt": (
            "Fast FPV drone shot diving steeply from high above the rainy cyberpunk street canyon, "
            "flying underneath the neon holographic skybridges at high speed, banking smoothly along the wet asphalt road "
            "and pulling up to a sudden stop right in front of the armored cyber-warrior with a glowing cyan visor "
            "standing in the center of the street, cinematic neon reflections, volumetric rain mist, 4k photorealistic."
        ),
    },
    "wuxia": {
        "label": "⚔️ 奇幻武俠仙俠古街版 (Fantasy Wuxia)",
        "first": BASE_DIR / "wuxia_first_frame.png",
        "last": BASE_DIR / "wuxia_last_frame.png",
        "prompt": (
            "Fast FPV drone shot diving steeply from high above the misty ancient Chinese wuxia street canyon at night, "
            "soaring underneath the ornate wooden corridor bridges lit by warm red and golden lanterns, banking smoothly "
            "along the wet stone pavement and pulling up to a sudden stop right in front of the martial arts warrior "
            "with a spirit sword on his back, cinematic moonlight and lantern glow, atmospheric fog, 4k photorealistic."
        ),
    },
    "white": {
        "label": "🧊 Blender 原始白模版 (Greybox)",
        "first": BASE_DIR / "fpv_first_frame.png",
        "last": BASE_DIR / "fpv_last_frame.png",
        "prompt": (
            "Playful fast FPV camera flight diving from high above a colorful 3D animated toy city street, "
            "flying underneath bright rainbow bridges with balloons, gliding past cute cartoon cars and stopping "
            "right in front of an adorable little kid hero wearing a star helmet and cape in the center of the street, "
            "Pixar 3D animation style, joyful bright daylight, 4k."
        ),
    },
}


def find_browser_exe() -> str:
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    raise FileNotFoundError("找不到 Chrome 或 Edge 瀏覽器，請先安裝 Google Chrome。")


def is_cdp_ready(port: int = CDP_PORT) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def ensure_chrome_running(target_url: str):
    if is_cdp_ready(CDP_PORT):
        print(f"[1/5] 已偵測到本機 Chrome 除錯埠 (Port {CDP_PORT})，直接接管連線。")
        return

    browser_exe = find_browser_exe()
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[1/5] 正在啟動本機 Chrome ({Path(browser_exe).name}) ...")
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen(
        [
            browser_exe,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={PROFILE_DIR}",
            "--no-first-run",
            "--no-default-browser-check",
            target_url,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    for _ in range(30):
        if is_cdp_ready(CDP_PORT):
            print("[OK] 本機 Chrome 已就緒。")
            return
        time.sleep(0.5)
    raise RuntimeError(f"無法連線到 Chrome Port {CDP_PORT}，請關閉其他鎖定相同設定檔的 Chrome 後重試。")


def wait_for_authenticated_flow(page):
    print("[2/5] 檢查 Google Flow 登入狀態...")
    try:
        page.wait_for_load_state("networkidle", timeout=4000)
    except Exception:
        pass
    time.sleep(1.5)

    deadline = time.time() + 300
    prompted = False
    tried_cta = False

    while time.time() < deadline:
        url = page.url or ""
        if "flow.google.com" in url and "/about" not in url and "accounts.google.com" not in url:
            # 確認頁面確實已進入登入後工作區（有專案列表、建立專案或工具列）
            try:
                authed_marker = page.locator(
                    "a[href*='/project/'], button:has-text('新專案'), button:has-text('建立專案'), "
                    "button:has-text('New project'), button[aria-label*='帳戶'], button:has-text('設定觸發條件')"
                ).first
                if authed_marker.is_visible(timeout=800):
                    print(f"[OK] 已進入已登入的 Google Flow：{url}")
                    return
            except Exception:
                pass

        if "/about" in url and not tried_cta:
            for role in ("button", "link"):
                try:
                    cta = page.get_by_role(role, name=re.compile(r"試用 Google Flow|使用 Google Flow 建立|Create with Flow|Get started", re.I)).first
                    if cta.is_visible(timeout=800):
                        cta.click()
                        tried_cta = True
                        time.sleep(2.0)
                        break
                except Exception:
                    pass

        if not prompted:
            print("================================================================")
            print("  [等待登入] 請在剛跳出的 Chrome 視窗登入你的 Google 帳號。")
            print("  （登入狀態會儲存在 .chrome_flow_profile，下次打開免重複登入）")
            print("================================================================")
            prompted = True
        time.sleep(2.0)

    raise TimeoutError("等待 Google 帳號登入逾時（超過 5 分鐘）。")


def ensure_in_project(page):
    if "/project/" in (page.url or ""):
        return
    print("[3/5] 正在開啟或建立 Flow 專案...")
    time.sleep(1.5)
    if "/project/" in (page.url or ""):
        return

    for pattern in [r"新增專案|建立專案|New project|Create project|\+ 新建", r"建立|New|Create"]:
        try:
            btn = page.get_by_role("button", name=re.compile(pattern, re.I)).first
            if btn.is_visible(timeout=1500):
                btn.click()
                page.wait_for_url(re.compile(r".*/project/.*"), timeout=12000)
                print(f"[OK] 已進入專案：{page.url}")
                return
        except Exception:
            pass

    # 若未自動建新專案，嘗試點擊第一個現有專案連結
    try:
        proj_link = page.locator("a[href*='/project/']").first
        if proj_link.is_visible(timeout=2000):
            proj_link.click()
            page.wait_for_url(re.compile(r".*/project/.*"), timeout=10000)
            print(f"[OK] 已開啟既有專案：{page.url}")
    except Exception:
        pass


def switch_to_frames_mode(page):
    print("[4/6] 切換為「影片 -> 影格 (首尾幀) · 10 秒 · x 1」模式...")
    start_btn = page.get_by_role("button", name=re.compile(r"^開始$|^Start$", re.I)).first
    trigger_btn = page.get_by_role("button", name=re.compile(r"設定觸發條件|圖片|影片|Image|Video", re.I)).first
    try:
        if start_btn.is_visible(timeout=1500) and trigger_btn.is_visible(timeout=1000):
            trigger_text = trigger_btn.inner_text() or ""
            if re.search(r"10\s*(?:秒|s)", trigger_text, re.I) and re.search(r"x\s*1\b", trigger_text, re.I):
                print("[OK] 目前已經是首尾幀 (10 秒 · x 1) 模式。")
                return
    except Exception:
        pass

    # 點擊模式切換設定按鈕 (如「設定觸發條件」或含 圖片/影片 字樣)
    clicked = False
    for selector in [
        trigger_btn,
        page.locator("button:has-text('圖片'), button:has-text('影片'), button:has-text('Video'), button:has-text('Image')").first,
    ]:
        try:
            if selector.is_visible(timeout=1500):
                selector.click()
                clicked = True
                break
        except Exception:
            continue

    if not clicked:
        print("[警告] 找不到模式切換按鈕，嘗試直接檢查畫面上是否有「開始」按鈕。")
        return

    time.sleep(0.6)
    for role_pattern in [r"^影片$|^Video$", r"^影格$|^Frames$", r"^x\s*1$"]:
        try:
            opt = page.get_by_role("radio", name=re.compile(role_pattern, re.I)).first
            if opt.is_visible(timeout=2000):
                opt.click()
                time.sleep(0.4)
        except Exception:
            pass

    # 調整影片長度為 10 秒
    try:
        slider = page.get_by_role("slider", name=re.compile(r"長度|Duration|Length", re.I)).first
        if slider.is_visible(timeout=2000):
            slider.focus()
            for _ in range(12):
                body_text = page.locator("body").inner_text()
                m = re.search(r"(?:長度|Duration|Length)\s*[·・:]?\s*(\d+)\s*(?:秒|s)", body_text, re.I)
                if m:
                    cur_sec = int(m.group(1))
                    if cur_sec == 10:
                        break
                    slider.press("ArrowRight" if cur_sec < 10 else "ArrowLeft")
                    time.sleep(0.25)
                else:
                    slider.press("End")
                    time.sleep(0.3)
                    break
    except Exception as exc:
        print(f"[警告] 設定影片長度為 10 秒時略過：{exc}")

    page.keyboard.press("Escape")
    time.sleep(0.5)


def inject_file_hook(page):
    page.evaluate(
        """
        () => {
          window.__flowInterceptedInputs = [];
          if (!window.__flowClickHooked) {
            window.__flowClickHooked = true;
            const origClick = HTMLInputElement.prototype.click;
            HTMLInputElement.prototype.click = function(...args) {
              if (this.type === 'file') {
                this.classList.add('__flow_file_input_hook');
                this.style.display = 'none';
                if (!this.isConnected) document.body.appendChild(this);
                window.__flowInterceptedInputs.push(this);
                return;
              }
              return origClick.apply(this, args);
            };
          }
        }
        """
    )


def upload_frame(page, slot_pattern: str, image_path: Path, label: str):
    if not image_path.exists():
        raise FileNotFoundError(f"找不到圖片檔案：{image_path}")

    print(f"      正在上傳 {label}：{image_path.name} ...")
    slot_btn = page.get_by_role("button", name=re.compile(slot_pattern, re.I)).first
    slot_btn.wait_for(state="visible", timeout=8000)
    slot_btn.click()
    time.sleep(0.8)

    upload_btn = page.get_by_role("button", name=re.compile(r"上傳媒體|Upload media|Upload", re.I)).first
    upload_btn.wait_for(state="visible", timeout=8000)

    uploaded = False
    # 做法 A：先嘗試原生 filechooser 攔截
    try:
        with page.expect_file_chooser(timeout=3000) as fc_info:
            upload_btn.click()
        fc = fc_info.value
        fc.set_files(str(image_path))
        uploaded = True
    except Exception:
        pass

    # 做法 B：若為 Angular 隱藏或記憶體內建立的 input，透過 prototype hook 攔截並塞入檔案
    if not uploaded:
        inject_file_hook(page)
        upload_btn.click()
        time.sleep(0.6)
        hooked = page.locator("input.__flow_file_input_hook")
        if hooked.count() > 0:
            hooked.last.set_input_files(str(image_path))
            uploaded = True
        else:
            any_file_input = page.locator("input[type='file']")
            if any_file_input.count() > 0:
                any_file_input.last.set_input_files(str(image_path))
                uploaded = True

    if not uploaded:
        raise RuntimeError(f"無法觸發「上傳媒體」檔案選擇器（{label}）。")

    # 等待上傳完成並確認是否需要點擊新素材縮圖關閉 Modal
    time.sleep(2.8)
    close_btn = page.get_by_role("button", name=re.compile(r"^關閉$|^Close$", re.I)).first
    try:
        if close_btn.is_visible(timeout=1200):
            # 切換至「上傳的項目」分頁或直接點最新縮圖
            uploaded_tab = page.get_by_role("tab", name=re.compile(r"上傳的項目|Uploaded", re.I)).first
            if uploaded_tab.is_visible(timeout=500):
                uploaded_tab.click()
                time.sleep(0.6)
            # 點擊第一個可見的圖片縮圖卡片
            thumb = page.locator("[role='dialog'] img, mat-dialog-container img, .cdk-overlay-pane img").first
            if thumb.is_visible(timeout=2500):
                thumb.click()
                time.sleep(0.8)
    except Exception:
        pass

    print(f"[OK] {label} 上傳處理完成！")


def fill_prompt(page, prompt_text: str):
    print("[5/6] 填入 FPV 運鏡 Prompt ...")
    box = page.get_by_role("textbox", name=re.compile(r"你想製作什麼內容|What do you want|prompt", re.I)).first
    if not box.is_visible(timeout=2000):
        box = page.locator("textarea, [contenteditable='true']").last
    box.click(force=True)
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.insert_text(prompt_text)
    print("[OK] Prompt 已填入！")


def trigger_generate(page):
    print("[6/6] 自動點擊「開始生成」按鈕產生影片 ...")
    time.sleep(0.8)
    gen_btn = page.get_by_role("button", name=re.compile(r"開始生成|Generate|建立影片", re.I)).first
    gen_btn.wait_for(state="visible", timeout=8000)
    gen_btn.click(force=True)
    print("[OK] 已觸發 Google Flow 開始生成影片！")


def main():
    parser = argparse.ArgumentParser(description="一鍵自動上傳首尾幀與 Prompt 至本機 Chrome Google Flow")
    parser.add_argument("--theme", choices=list(THEMES.keys()), default="kids", help="選擇風格套件 (預設 kids)")
    parser.add_argument("--project-url", default=FLOW_URL, help="目標 Google Flow 網址")
    parser.add_argument("--no-submit", action="store_true", help="僅填入首尾幀與 Prompt，不自動點擊開始生成")
    args = parser.parse_args()

    theme = THEMES[args.theme]
    print(f"\n=== Google Flow 本機全自動上傳 CLI：{theme['label']} ===")

    ensure_chrome_running(args.project_url)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()

        # 優先尋找已經開著的 flow.google.com 分頁
        target_page = None
        for pg in context.pages:
            if "flow.google.com" in (pg.url or "") or "accounts.google.com" in (pg.url or ""):
                target_page = pg
                break
        if target_page is None:
            target_page = context.pages[0] if context.pages else context.new_page()
            target_page.goto(args.project_url, wait_until="domcontentloaded")

        target_page.bring_to_front()
        wait_for_authenticated_flow(target_page)
        ensure_in_project(target_page)
        switch_to_frames_mode(target_page)

        print("[上傳] 開始自動上傳 Start / End 首尾幀...")
        upload_frame(target_page, r"^開始$|^Start$", theme["first"], "首幀 (Start)")
        upload_frame(target_page, r"^結束$|^End$", theme["last"], "尾幀 (End)")
        fill_prompt(target_page, theme["prompt"])

        if not args.no_submit:
            trigger_generate(target_page)
            print("\n" + "=" * 62)
            print("  ✅ 全自動上傳並送出生成！Google Flow 正在為你產生影片。")
            print("  👉 請切換到 Chrome 視窗查看影片生成進度與成品！")
            print("=" * 62)
        else:
            print("\n" + "=" * 62)
            print("  ✅ 全自動上傳完成！首幀、尾幀與 Prompt 都已填入 Google Flow。")
            print("  👉 請切換到 Chrome 視窗確認圖片縮圖無誤，按下白色「→」開始生成！")
            print("=" * 62)


if __name__ == "__main__":
    main()
