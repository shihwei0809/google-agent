"""
《Peace and Love》MV 專用 — Google Flow (新版 Agent 工作區) 全自動分批生片與下載腳本
===================================================================================
- 直接連線本機 Chrome CDP (Port 9222)，支援 2026 新版 Google Flow 專案介面：
  - 右側工作階段輸入框「你想製作什麼內容？」+「在提示詞輸入框新增素材 (+)」+「開始生成 (→)」
  - 同時相容舊版「開始 / 結束」影格介面
- 人物一致性雙重鎖定：
  1. 若該鏡已有鎖定首幀 (keyframes/sXX.jpg) → 自動上傳該首幀作為起始畫面
  2. 若該鏡尚未產首幀但含人物 (chars) → 自動上傳 refs/char_female_ref.jpg 與/或 refs/char_male_ref.jpg 作為角色參考圖
  3. 純空鏡 (s05, s19) → 直接送出電影級 Prompt
- 自動監聽專案內新產生的 <video> 並下載至 flow_clips/sXX_flow.mp4（支援斷點續傳）
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

MV_DIR = Path(__file__).resolve().parent
PARENT_DIR = MV_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import auto_upload_flow as flow_core  # noqa: E402

STORYBOARD_PATH = MV_DIR / "storyboard.json"
FLOW_CLIPS_DIR = MV_DIR / "flow_clips"


def load_scenes() -> list[dict]:
    data = json.loads(STORYBOARD_PATH.read_text(encoding="utf-8"))
    return data["scenes"]


def attach_image_new_flow_ui(page, image_path: Path, label: str) -> bool:
    """新版 Google Flow 右側 Agent 面板：若專案內已有同名檔直接選取，否則上傳後等待出現再點「新增至提示詞」"""
    if not image_path.exists():
        print(f"  [警告] 找不到圖片：{image_path}")
        return False

    fname = image_path.name
    print(f"  [附加] 正在附加 {label}：{fname} ...")
    add_btn = page.get_by_role("button", name=re.compile(r"在提示詞輸入框新增素材|Add asset|Add media", re.I)).first
    add_btn.wait_for(state="visible", timeout=8000)
    add_btn.click()
    time.sleep(0.8)

    # 先檢查專案素材庫是否已經有同名檔案（例如重複使用的 char_female_ref.jpg / s01.jpg）
    item_loc = page.get_by_role("option", name=re.compile(re.escape(fname), re.I)).first
    already_exists = False
    try:
        already_exists = item_loc.is_visible(timeout=1200)
    except Exception:
        already_exists = False

    if not already_exists:
        print(f"    ↳ 專案尚無 {fname}，執行上傳媒體...")
        upload_btn = page.get_by_role("button", name=re.compile(r"上傳媒體|Upload media|Upload", re.I)).first
        upload_btn.wait_for(state="visible", timeout=8000)
        uploaded = False
        try:
            with page.expect_file_chooser(timeout=4000) as fc_info:
                upload_btn.click()
            fc_info.value.set_files(str(image_path))
            uploaded = True
        except Exception:
            flow_core.inject_file_hook(page)
            upload_btn.click()
            time.sleep(0.6)
            hooked = page.locator("input.__flow_file_input_hook, input[type='file']")
            if hooked.count() > 0:
                hooked.last.set_input_files(str(image_path))
                uploaded = True

        if not uploaded:
            raise RuntimeError(f"無法觸發「上傳媒體」檔案選擇器（{label}）")

        # 上傳後等待浮出選單出現該檔名（或若選單自動關閉則重新打開選單）
        deadline = time.time() + 20.0
        while time.time() < deadline:
            try:
                if item_loc.is_visible(timeout=600):
                    break
                # 若選單被自動關掉了，重新點開一次
                if not page.get_by_role("button", name=re.compile(r"上傳媒體|Upload media", re.I)).first.is_visible(timeout=300):
                    add_btn.click()
                    time.sleep(0.7)
            except Exception:
                pass
            time.sleep(0.8)

    # 點選目標檔名項目（在新版 Flow 中點擊項目本身可能即自動加入並關閉選單；若仍有「新增至提示詞」按鈕再點一次）
    item_loc.wait_for(state="visible", timeout=10000)
    item_loc.click()
    time.sleep(0.6)

    confirm_btn = page.get_by_role("button", name=re.compile(r"新增至提示詞|Add to prompt", re.I)).first
    try:
        if confirm_btn.is_visible(timeout=1200):
            confirm_btn.click()
            time.sleep(0.8)
    except Exception:
        pass

    # 確保浮出選單已關閉
    try:
        if page.get_by_role("button", name=re.compile(r"上傳媒體|Upload media", re.I)).first.is_visible(timeout=300):
            page.keyboard.press("Escape")
            time.sleep(0.3)
    except Exception:
        pass

    print(f"  [OK] {label} ({fname}) 已成功附加至提示詞！")
    return True


def build_agent_prompt(scene: dict, mode: str, model: str, resolution: str, duration: int) -> str:
    model_name = "Omni 1.2 Flash" if model == "omni12" else ("Veo 3.1 Lite" if model == "veo31lite" else "Omni 1.2 Flash")
    if mode == "frames":
        prefix = (
            f"Do not ask questions. Immediately generate 1 cinematic 16:9 video ({duration} seconds, {resolution}, {model_name}) "
            f"using the attached image as the exact start frame. Maintain exact character face, hair, and clothing consistency. "
        )
    elif mode == "ingredients":
        prefix = (
            f"Do not ask questions. Immediately generate 1 cinematic 16:9 video ({duration} seconds, {resolution}, {model_name}) "
            f"using the attached character reference sheet(s) as exact visual identity lock (keep the exact same face, hairstyle, and outfit). "
        )
    else:
        prefix = f"Do not ask questions. Immediately generate 1 cinematic 16:9 video ({duration} seconds, {resolution}, {model_name}). "
    return prefix + scene["flow_prompt_en"]


def submit_scene_on_page(
    page,
    scene: dict,
    model: str,
    resolution: str,
    duration: int,
    no_submit: bool,
):
    sid = scene["id"]
    first_img = MV_DIR / scene["keyframe"]
    has_keyframe = first_img.exists()
    chars = scene.get("chars", [])

    if has_keyframe:
        mode = "frames"
    elif chars:
        mode = "ingredients"
    else:
        mode = "text"

    print(f"\n=== [{sid}] {scene['section']} ({scene['start']:.1f}s - {scene['end']:.1f}s) | 模式: {mode} ===")
    flow_core.wait_for_authenticated_flow(page)
    flow_core.ensure_in_project(page)
    time.sleep(1.0)

    # 判斷是否為新版右側 Agent 介面
    new_add_btn = page.get_by_role("button", name=re.compile(r"在提示詞輸入框新增素材|Add asset", re.I)).first
    is_new_ui = False
    try:
        is_new_ui = new_add_btn.is_visible(timeout=2500)
    except Exception:
        is_new_ui = False

    if is_new_ui:
        # 先清空輸入框（絕不可在附加圖片後按 Ctrl+A Backspace，否則會把剛附加的圖片 chip 刪掉！）
        box = page.get_by_role("textbox", name=re.compile(r"你想製作什麼內容|What do you want|prompt", re.I)).first
        box.click(force=True)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.3)

        if mode == "frames":
            attach_image_new_flow_ui(page, first_img, f"{sid} 鎖定首幀")
        elif mode == "ingredients":
            ref_map = {
                "female": MV_DIR / "refs" / "char_female_ref.jpg",
                "male": MV_DIR / "refs" / "char_male_ref.jpg",
            }
            for c in chars:
                rp = ref_map.get(c)
                if rp and rp.exists():
                    attach_image_new_flow_ui(page, rp, f"角色參考({c})")

        prompt_text = build_agent_prompt(scene, mode, model, resolution, duration)
        box.click(force=True)
        page.keyboard.press("End")
        page.keyboard.insert_text(" " + prompt_text)
        print("[OK] Prompt 已附加至圖片 chip 後方！")
    else:
        # 舊版 Frames UI 相容路徑
        flow_core.switch_to_frames_mode(page, model=model, resolution=resolution, duration=duration)
        if mode == "frames":
            flow_core.upload_frame(page, r"^開始$|^Start$", first_img, f"{sid} 首幀")
        flow_core.fill_prompt(page, scene["flow_prompt_en"])

    known_urls = set(collect_flow_video_urls_with_hover(page, max_cards=4))
    if not no_submit:
        flow_core.trigger_generate(page)
        print(f"  ✅ [{sid}] 已送出生成 ({mode} · {model} · {resolution} · {duration}s)！")
    else:
        print(f"  ✅ [{sid}] 素材與 Prompt 已填入（--no-submit 模式）！")

    out_mp4 = MV_DIR / scene["flow_clip"]
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    return (page, sid, known_urls, out_mp4)


def collect_flow_video_urls_with_hover(page, max_cards: int = 4) -> list[str]:
    """新版 Google Flow 媒體格預設僅顯示縮圖，須 hover 卡片上的 360p/720p 標籤才會掛載 <video>"""
    urls = list(flow_core.collect_video_urls(page))
    try:
        badges = page.locator("span:text-is('360p'), div:text-is('360p'), span:text-is('720p'), div:text-is('720p')")
        cnt = min(badges.count(), max_cards)
        for i in range(cnt):
            try:
                badges.nth(i).hover(force=True, timeout=1500)
                time.sleep(0.55)
                for u in flow_core.collect_video_urls(page):
                    if u not in urls:
                        urls.append(u)
            except Exception:
                continue
    except Exception:
        pass
    return urls


def wait_and_download_one(page, sid: str, known_urls: set, out_mp4: Path, timeout_sec: int = 300) -> bool:
    print(f"  [監聽] 等待 [{sid}] Google Flow 影片生成完成並自動下載（上限 {timeout_sec}s）...")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        # 若 Flow Agent 彈出「要開始生成這 1 部影片嗎？」核准按鈕，自動點選「一律核准專案中的要求」或「核准」
        for pat in [r"一律核准專案中的要求|Always approve", r"^核准$|^Approve$"]:
            try:
                abtn = page.get_by_role("button", name=re.compile(pat, re.I)).first
                if abtn.is_visible(timeout=300):
                    abtn.click()
                    print(f"  [自動核准] 已點擊「{pat}」，開始扣點生成！")
                    time.sleep(1.5)
                    break
            except Exception:
                pass
        cur_urls = collect_flow_video_urls_with_hover(page, max_cards=4)
        new_urls = [u for u in cur_urls if u not in known_urls]
        for u in new_urls:
            if flow_core.download_video_from_page(page, u, out_mp4):
                print(f"  🎬 [{sid}] 已自動下載：{out_mp4.name} ({out_mp4.stat().st_size:,} bytes)")
                return True
        time.sleep(6.0)
    print(f"  ⏳ [{sid}] 逾時未偵測到 <video> 下載，請在 Chrome 專案畫面確認是否需手動確認或繼續等待。")
    return False


def main():
    parser = argparse.ArgumentParser(description="《Peace and Love》MV Google Flow 批次生片器")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=19)
    parser.add_argument("--only", nargs="+", help="只跑指定鏡號，例如 --only s01 s02 s03")
    parser.add_argument("--model", choices=["omni12", "veo31lite", "auto"], default="omni12")
    parser.add_argument("--res", choices=["360p", "720p"], default="360p")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-submit", action="store_true")
    parser.add_argument("--no-wait", action="store_true")
    parser.add_argument("--project-url", default=flow_core.FLOW_URL)
    args = parser.parse_args()

    scenes = load_scenes()
    FLOW_CLIPS_DIR.mkdir(parents=True, exist_ok=True)

    if args.only:
        only_set = set(args.only)
        selected = [s for s in scenes if s["id"] in only_set]
    else:
        selected = [s for i, s in enumerate(scenes) if args.start <= (i + 1) <= args.end]

    if not args.force:
        selected = [
            s for s in selected
            if not ((MV_DIR / s["flow_clip"]).exists() and (MV_DIR / s["flow_clip"]).stat().st_size > 50_000)
        ]

    if not selected:
        print("✅ 所有選定分鏡均已有 Google Flow 影片！")
        return

    print(f"🚀 準備在 Google Flow 依序生成 {len(selected)} 鏡 ({args.model} · {args.res} · {args.duration}s)")
    flow_core.ensure_chrome_running(args.project_url)

    done_ids: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{flow_core.CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()

        # 找到已開啟的 flow.google.com 分頁
        page = None
        for c in browser.contexts:
            for pg in c.pages:
                if "flow.google.com" in (pg.url or ""):
                    page = pg
                    break
            if page:
                break
        if page is None:
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(args.project_url, wait_until="domcontentloaded")

        for scene in selected:
            pg, sid, known, out_mp4 = submit_scene_on_page(
                page=page,
                scene=scene,
                model=args.model,
                resolution=args.res,
                duration=args.duration,
                no_submit=args.no_submit,
            )
            if not args.no_submit and not args.no_wait:
                if wait_and_download_one(pg, sid, known, out_mp4, timeout_sec=args.timeout):
                    done_ids.append(sid)
            time.sleep(2.0)

    print("\n" + "=" * 62)
    print(f"  🎬 完成下載：{len(done_ids)} / {len(selected)} 鏡 ({', '.join(done_ids)})")
    print("  👉 執行 `python peace_love_mv/build_peace_love_mv.py` 即可組裝最終 1080p MV！")
    print("=" * 62)


if __name__ == "__main__":
    main()
