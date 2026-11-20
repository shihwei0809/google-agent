"""
一鍵操控本機 Chrome (Port 9222) 自動上傳首尾幀與 Prompt 至 Google Flow
- 免 API Key，直接使用已登入 Google 帳號的 Flow 免費 / PRO 點數
- 繞過內建瀏覽器沙盒限制，全程在本機桌面 Chrome 執行
"""

import argparse
import base64
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
    "bpm_shot01": {
        "label": "🚗 BPM 分鏡 01：私車公用出差行車與 ETag 佐證",
        "first": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot01_first.png",
        "last": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot01_last.png",
        "out_mp4": BASE_DIR / "bpm_sop" / "flow_clips" / "shot01_flow.mp4",
        "prompt": (
            "Clean modern corporate 3D animation, smooth camera tracking a silver sedan driving along a sunny "
            "Taiwan highway passing underneath a glowing blue eTag electronic toll gantry, transitioning smoothly "
            "to arriving cleanly at a modern steel material factory gate with a digital route map display, "
            "bright daylight, crisp professional explainer video style, 4k."
        ),
    },
    "bpm_shot05": {
        "label": "🚄 BPM 分鏡 05：高鐵 A01 與停車場 A06 交通對比",
        "first": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot05_first.png",
        "last": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot05_last.png",
        "out_mp4": BASE_DIR / "bpm_sop" / "flow_clips" / "shot05_flow.mp4",
        "prompt": (
            "Clean modern corporate 3D animation transition, starting at a bright high-speed rail station platform "
            "as a sleek streamlined bullet train arrives, smoothly gliding to a modern parking garage exit kiosk "
            "with a rising green barrier gate and glowing receipt card, bright professional explainer style, 4k."
        ),
    },
    "bpm_shot08": {
        "label": "📋 BPM 分鏡 08：正本交件（申請人 → 人事核對 → 會計審核）",
        "first": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot08_first.png",
        "last": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot08_last.png",
        "out_mp4": BASE_DIR / "bpm_sop" / "flow_clips" / "shot08_flow.mp4",
        "prompt": (
            "Clean modern corporate office animation, starting with an employee neatly organizing printed BPM expense "
            "forms and paper receipts on a desk, smoothly transitioning to a three-step glass workflow visualization "
            "showing Applicant handing originals to HR for verification stamp, then forwarding to Accounting for final "
            "approval, warm bright office lighting, crisp 4k."
        ),
    },
    "bpm_c02": {
        "label": "🖥️ 方案 C 分鏡 C02：進入 EPM 與選取本人出差單",
        "first": BASE_DIR / "bpm_sop_plan_c" / "flow_frames" / "bpm_c02_first.png",
        "last": BASE_DIR / "bpm_sop_plan_c" / "flow_frames" / "bpm_c02_last.png",
        "out_mp4": BASE_DIR / "bpm_sop_plan_c" / "flow_clips" / "c02_flow.mp4",
        "prompt": (
            "Clean modern corporate 3D explainer animation, smooth zoom toward a glowing glass desktop monitor "
            "displaying a sleek blue BPM expense portal icon, then smoothly opening floating translucent trip selector "
            "cards where an animated cursor highlights and selects the employee's matching business trip record, "
            "crisp clean corporate tech aesthetic, soft studio lighting, 4k."
        ),
    },
    "bpm_c03": {
        "label": "🔀 方案 C 分鏡 C03：私車 A05 與 eTag A07 雙軌分流",
        "first": BASE_DIR / "bpm_sop_plan_c" / "flow_frames" / "bpm_c03_first.png",
        "last": BASE_DIR / "bpm_sop_plan_c" / "flow_frames" / "bpm_c03_last.png",
        "out_mp4": BASE_DIR / "bpm_sop_plan_c" / "flow_clips" / "c03_flow.mp4",
        "prompt": (
            "Clean modern corporate 3D infographic animation, starting with a glowing mileage odometer and sedan icon "
            "flowing into a blue left track labeled A05, while a glowing highway eTag wave splits smoothly into a "
            "separate green right track labeled A07, emphasizing two distinct parallel glass cards floating cleanly "
            "side by side in a dark slate studio, crisp 4k."
        ),
    },
    "bpm_c05": {
        "label": "✅ 方案 C 分鏡 C05：明細總額對齊、上傳與先存再送",
        "first": BASE_DIR / "bpm_sop_plan_c" / "flow_frames" / "bpm_c05_first.png",
        "last": BASE_DIR / "bpm_sop_plan_c" / "flow_frames" / "bpm_c05_last.png",
        "out_mp4": BASE_DIR / "bpm_sop_plan_c" / "flow_clips" / "c05_flow.mp4",
        "prompt": (
            "Clean modern corporate 3D motion graphics animation, starting with floating invoice and map screenshot "
            "documents flying neatly into a glowing digital upload folder beside a balanced scale icon, smoothly "
            "transforming into three illuminated emerald milestone pills lighting up in sequence: Save, Submit, "
            "and Approved Ticket Badge, crisp dark tech studio, 4k."
        ),
    },
    "bpm_b_intro": {
        "label": "🎬 路線 B 過場 01：主角開車出差＋手機路線截圖",
        "first": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot01_first.png",
        "last": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot01_last.png",
        "out_mp4": BASE_DIR / "bpm_sop" / "flow_clips" / "b01_intro_flow.mp4",
        "prompt": (
            "35mm電影鏡頭寫實微電影風格，晴朗台灣清晨陽光下，32歲身穿淺藍牛津襯衫與深色西裝褲、"
            "胸前掛著員工識別證的台灣男性工程師駕駛銀色商務房車平穩駛過國道 eTag 門架，"
            "鏡頭低角度流暢推進並無縫轉場至主角抵達現代化廠區大門旁，"
            "微笑拿出手機檢視去回程地圖路線截圖與 eTag 紀錄，自然日光光斑與細膩皮膚衣物紋理，4K。"
        ),
    },
    "bpm_b_bridge": {
        "label": "🎬 路線 B 過場 02：里程與 eTag 混淆退件反轉",
        "first": BASE_DIR / "bpm_sop_plan_c" / "flow_frames" / "bpm_c03_first.png",
        "last": BASE_DIR / "bpm_sop_plan_c" / "flow_frames" / "bpm_c03_last.png",
        "out_mp4": BASE_DIR / "bpm_sop" / "flow_clips" / "b02_bridge_flow.mp4",
        "prompt": (
            "35mm電影寫實職場微電影，延續同一位穿淺藍牛津襯衫與識別證的台灣男性工程師，"
            "坐在明亮現代辦公桌前皺眉看著螢幕跳出退件提醒，隨即靈光一閃點頭微笑，"
            "雙手俐落將桌上的私車里程紀錄卡與高速公路 eTag 憑證清楚分置左右兩側，"
            "暖色窗光與桌面螢幕柔光對比，鏡頭緩慢推進特寫手部與神情轉變，無雜亂文字，4K。"
        ),
    },
    "bpm_b_outro": {
        "label": "🎬 路線 B 過場 03：正本交人事核對 → 轉會計核准",
        "first": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot08_first.png",
        "last": BASE_DIR / "bpm_sop" / "flow_frames" / "bpm_shot08_last.png",
        "out_mp4": BASE_DIR / "bpm_sop" / "flow_clips" / "b03_outro_flow.mp4",
        "prompt": (
            "35mm暖色日光商業微電影，同一位穿淺藍牛津襯衫的台灣男性工程師把裝訂整齊的報銷申請單、"
            "實體發票與高鐵車票正本雙手遞給櫃檯前親切微笑的人事同仁核對，"
            "鏡頭流暢平移轉場至會計主管檢視無誤後蓋下綠色核准章並點頭微笑，"
            "寫實辦公室玻璃景深與自然肌膚光影，無失真亂碼字，4K。"
        ),
    },
}

BPM_BATCH_THEMES = ["bpm_shot01", "bpm_shot05", "bpm_shot08"]
BPM_PLAN_C_THEMES = ["bpm_c02", "bpm_c03", "bpm_c05"]
BPM_ROUTE_B_THEMES = ["bpm_b_intro", "bpm_b_bridge", "bpm_b_outro"]


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
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(f"http://127.0.0.1:{port}/json/version", timeout=1.5) as resp:
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


def switch_to_frames_mode(page, model: str = "omni12", resolution: str = "360p", duration: int = 10):
    print(f"[4/6] 切換為「影片 -> 影格 · {model} · {resolution} · {duration} 秒 · x 1」省點模式...")
    start_btn = page.get_by_role("button", name=re.compile(r"^開始$|^Start$", re.I)).first
    trigger_btn = page.get_by_role("button", name=re.compile(r"設定觸發條件|圖片|影片|Image|Video|Omni|Veo", re.I)).first
    try:
        if start_btn.is_visible(timeout=1500) and trigger_btn.is_visible(timeout=1000):
            trigger_text = trigger_btn.inner_text() or ""
            if (
                re.search(rf"{duration}\s*(?:秒|s)", trigger_text, re.I)
                and re.search(r"x\s*1\b", trigger_text, re.I)
                and (resolution == "auto" or resolution.lower() in trigger_text.lower())
            ):
                print(f"[OK] 目前已經是 {resolution} · {duration} 秒 · x 1 模式。")
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
            if opt.is_visible(timeout=1500):
                opt.click()
                time.sleep(0.35)
        except Exception:
            pass

    # 嘗試選擇模型 (Omni 1.2 Flash 或 Veo 3.1 - Lite)
    model_patterns = {
        "omni12": r"Omni\s*1\.2\s*Flash|Omni\s*1\.2",
        "veo31lite": r"Veo\s*3\.1\s*-?\s*Lite|Veo\s*3\.1",
    }
    if model in model_patterns:
        pat = re.compile(model_patterns[model], re.I)
        for locator_fn in [
            lambda: page.get_by_role("combobox", name=re.compile(r"模型|Model", re.I)).first,
            lambda: page.locator("button:has-text('Veo'), button:has-text('Omni'), [role='menuitemradio'], [role='option'], [role='radio']").filter(has_text=pat).first,
        ]:
            try:
                el = locator_fn()
                if el.is_visible(timeout=1200):
                    el.click()
                    time.sleep(0.35)
                    choice = page.get_by_role("option", name=pat).or_(page.locator("[role='menuitem'], [role='menuitemradio'], button").filter(has_text=pat)).first
                    if choice.is_visible(timeout=1000):
                        choice.click()
                        time.sleep(0.3)
                    break
            except Exception:
                pass

    # 嘗試選擇解析度 (360p 省點 / 720p)
    if resolution in ("360p", "720p"):
        res_pat = re.compile(rf"\b{resolution}\b", re.I)
        for res_loc in [
            page.get_by_role("radio", name=res_pat).first,
            page.get_by_role("button", name=res_pat).first,
            page.locator("[role='option'], [role='menuitemradio']").filter(has_text=res_pat).first,
        ]:
            try:
                if res_loc.is_visible(timeout=1000):
                    res_loc.click()
                    time.sleep(0.3)
                    break
            except Exception:
                pass

    # 調整影片長度為指定秒數 (預設 10 秒)
    try:
        slider = page.get_by_role("slider", name=re.compile(r"長度|Duration|Length", re.I)).first
        if slider.is_visible(timeout=2000):
            slider.focus()
            for _ in range(15):
                body_text = page.locator("body").inner_text()
                m = re.search(r"(?:長度|Duration|Length)\s*[·・:]?\s*(\d+)\s*(?:秒|s)", body_text, re.I)
                if m:
                    cur_sec = int(m.group(1))
                    if cur_sec == duration:
                        break
                    slider.press("ArrowRight" if cur_sec < duration else "ArrowLeft")
                    time.sleep(0.25)
                else:
                    slider.press("End")
                    time.sleep(0.3)
                    break
    except Exception as exc:
        print(f"[警告] 設定影片長度為 {duration} 秒時略過：{exc}")

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


def collect_video_urls(page) -> list[str]:
    try:
        return page.evaluate(
            """
            () => {
              const out = [];
              document.querySelectorAll('video').forEach(v => {
                const s = v.currentSrc || v.src || '';
                if (s) out.push(s);
                v.querySelectorAll('source').forEach(srcEl => {
                  if (srcEl.src) out.push(srcEl.src);
                });
              });
              return Array.from(new Set(out));
            }
            """
        )
    except Exception:
        return []


def download_video_from_page(page, url: str, dest: Path) -> bool:
    try:
        b64_data = page.evaluate(
            """
            async (videoUrl) => {
              const resp = await fetch(videoUrl);
              if (!resp.ok) throw new Error('HTTP ' + resp.status);
              const buf = await resp.arrayBuffer();
              const bytes = new Uint8Array(buf);
              let bin = '';
              const chunk = 0x8000;
              for (let i = 0; i < bytes.length; i += chunk) {
                bin += String.fromCharCode(...bytes.subarray(i, i + chunk));
              }
              return btoa(bin);
            }
            """,
            url,
        )
        raw = base64.b64decode(b64_data)
        if len(raw) < 50_000:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        return True
    except Exception as exc:
        print(f"[警告] 下載影片失敗 ({url[:60]}...): {exc}")
        return False


def wait_and_download_flow_videos(submitted_pages: list, timeout_sec: int = 300) -> list[str]:
    pending = [
        (pg, key, known)
        for (pg, key, known) in submitted_pages
        if THEMES[key].get("out_mp4") is not None
    ]
    if not pending:
        return []

    print(f"\n[監聽] 等待 Google Flow 生成 {len(pending)} 支影片並自動下載 (最多 {timeout_sec} 秒)...")
    done_keys: list[str] = []
    deadline = time.time() + timeout_sec

    while pending and time.time() < deadline:
        still_waiting = []
        for pg, key, known in pending:
            out_mp4: Path = THEMES[key]["out_mp4"]
            cur_urls = collect_video_urls(pg)
            new_urls = [u for u in cur_urls if u not in known]
            downloaded = False
            for u in reversed(new_urls):
                if download_video_from_page(pg, u, out_mp4):
                    print(f"  ✅ [{key}] Google Flow 影片已自動下載：{out_mp4} ({out_mp4.stat().st_size:,} bytes)")
                    done_keys.append(key)
                    downloaded = True
                    break
            if not downloaded:
                still_waiting.append((pg, key, known))
        pending = still_waiting
        if pending:
            time.sleep(4.0)

    for _pg, key, _known in pending:
        print(f"  ⏳ [{key}] 超過 {timeout_sec} 秒尚未偵測到成品，請於 Chrome 視窗確認進度。")
    return done_keys


def upload_single_theme(
    context,
    theme_key: str,
    project_url: str,
    no_submit: bool,
    open_new_tab: bool = False,
    model: str = "omni12",
    resolution: str = "360p",
    duration: int = 10,
):
    theme = THEMES[theme_key]
    print(f"\n=== Google Flow 本機全自動上傳 CLI：{theme['label']} ===")

    target_page = None
    if not open_new_tab:
        for pg in context.pages:
            if "flow.google.com" in (pg.url or "") or "accounts.google.com" in (pg.url or ""):
                target_page = pg
                break
    if target_page is None:
        target_page = context.new_page() if open_new_tab or not context.pages else context.pages[0]
        target_page.goto(project_url, wait_until="domcontentloaded")

    target_page.bring_to_front()
    wait_for_authenticated_flow(target_page)
    ensure_in_project(target_page)
    switch_to_frames_mode(target_page, model=model, resolution=resolution, duration=duration)

    print("[上傳] 開始自動上傳 Start / End 首尾幀...")
    upload_frame(target_page, r"^開始$|^Start$", theme["first"], "首幀 (Start)")
    upload_frame(target_page, r"^結束$|^End$", theme["last"], "尾幀 (End)")
    fill_prompt(target_page, theme["prompt"])

    known_video_urls = set(collect_video_urls(target_page))
    if not no_submit:
        trigger_generate(target_page)
        print(f"  ✅ [{theme_key}] 已送出生成 ({model} · {resolution} · {duration} 秒 · x 1)！")
    else:
        print(f"  ✅ [{theme_key}] 首尾幀與 Prompt 已填入！")
    return (target_page, theme_key, known_video_urls)


def main():
    parser = argparse.ArgumentParser(description="一鍵自動上傳首尾幀與 Prompt 至本機 Chrome Google Flow")
    parser.add_argument(
        "--theme",
        choices=list(THEMES.keys()) + ["bpm_all", "bpm_plan_c", "bpm_route_b"],
        default="kids",
        help="選擇風格或 BPM 情境分鏡 (預設 kids；bpm_all / bpm_plan_c / bpm_route_b 可批次送出)",
    )
    parser.add_argument("--project-url", default=FLOW_URL, help="目標 Google Flow 網址")
    parser.add_argument("--model", choices=["omni12", "veo31lite", "auto"], default="omni12", help="Google Flow 影片模型")
    parser.add_argument("--res", choices=["360p", "720p"], default="360p", help="解析度（360p 僅耗 10 點/10秒，下載可免費升 720p）")
    parser.add_argument("--duration", type=int, default=10, help="生成秒數（預設 10 秒）")
    parser.add_argument("--no-submit", action="store_true", help="僅填入首尾幀與 Prompt，不自動點擊開始生成")
    parser.add_argument("--no-wait", action="store_true", help="送出生成後立即結束，不等待自動下載 MP4")
    args = parser.parse_args()

    if args.theme == "bpm_all":
        theme_keys = BPM_BATCH_THEMES
    elif args.theme == "bpm_plan_c":
        theme_keys = BPM_PLAN_C_THEMES
    elif args.theme == "bpm_route_b":
        theme_keys = BPM_ROUTE_B_THEMES
    else:
        theme_keys = [args.theme]
    ensure_chrome_running(args.project_url)

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()

        submitted = []
        for idx, key in enumerate(theme_keys):
            info = upload_single_theme(
                context,
                key,
                args.project_url,
                args.no_submit,
                open_new_tab=(idx > 0),
                model=args.model,
                resolution=args.res,
                duration=args.duration,
            )
            submitted.append(info)
            if idx + 1 < len(theme_keys):
                time.sleep(1.5)

        downloaded_keys = []
        if not args.no_submit and not args.no_wait:
            downloaded_keys = wait_and_download_flow_videos(submitted, timeout_sec=300)

        print("\n" + "=" * 62)
        if not args.no_submit:
            print(f"  ✅ 已全自動送出 {len(theme_keys)} 支影片至 Google Flow 生成佇列！")
            if downloaded_keys:
                print(f"  📥 已自動下載完成：{', '.join(downloaded_keys)}")
            else:
                print("  👉 請切換到 Chrome 視窗查看生成進度，完成後可將 MP4 放進 bpm_sop/flow_clips/！")
        else:
            print(f"  ✅ 已完成 {len(theme_keys)} 組首尾幀與 Prompt 填入！")
            print("  👉 請切換到 Chrome 視窗確認縮圖無誤後點擊「開始生成」！")
        print("=" * 62)


if __name__ == "__main__":
    main()
