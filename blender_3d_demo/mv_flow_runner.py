"""
通用 AI MV 工廠 — Google Flow (2026 新版 Agent 工作區) 全自動分批生片引擎
=========================================================================
用法：
  python mv_flow_runner.py --project peace_love_mv --start 1 --end 19 --res 360p
  python mv_flow_runner.py --project my_new_mv --only s04 s09 --force --res 720p

特色（已整合所有實戰避坑修正）：
1. 支援任意 MV 專案資料夾 (--project)，自動讀取 <project>/storyboard.json 與 characters 參考圖
2. 自動適配 2026 新版 Google Flow Agent 工作區：先清空輸入框再附加圖片 chip、自動點「一律核准專案中的要求」
3. 每 6 秒自動 hover 媒體格 360p/720p 標籤觸發 <video> 掛載，生成完立即秒抓
4. 透過 Playwright APIRequestContext 帶 Cookie 直拉 MP4，100% 繞過 GCS 302 CORS 限制
5. 支援斷點續傳（已存在 >50KB 的 flow_clips/sXX_flow.mp4 自動略過，加 --force 才重跑）
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import auto_upload_flow as flow_core  # noqa: E402


def load_storyboard(project_dir: Path) -> dict:
    sb_path = project_dir / "storyboard.json"
    if not sb_path.exists():
        raise FileNotFoundError(f"找不到分鏡檔：{sb_path}")
    return json.loads(sb_path.read_text(encoding="utf-8"))


def attach_image_new_flow_ui(page, image_path: Path, label: str) -> bool:
    if not image_path.exists():
        print(f"  [警告] 找不到圖片：{image_path}")
        return False

    fname = image_path.name
    print(f"  [附加] 正在附加 {label}：{fname} ...")
    add_btn = page.get_by_role("button", name=re.compile(r"在提示詞輸入框新增素材|Add asset|Add media", re.I)).first
    add_btn.wait_for(state="visible", timeout=8000)
    add_btn.click()
    time.sleep(0.8)

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

        deadline = time.time() + 20.0
        while time.time() < deadline:
            try:
                if item_loc.is_visible(timeout=600):
                    break
                if not page.get_by_role("button", name=re.compile(r"上傳媒體|Upload media", re.I)).first.is_visible(timeout=300):
                    add_btn.click()
                    time.sleep(0.7)
            except Exception:
                pass
            time.sleep(0.8)

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


def collect_flow_video_urls_with_hover(page, max_cards: int = 4) -> list[str]:
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


def submit_scene_on_page(
    page,
    project_dir: Path,
    characters_cfg: dict,
    scene: dict,
    model: str,
    resolution: str,
    duration: int,
    no_submit: bool,
):
    sid = scene["id"]
    first_img = project_dir / scene["keyframe"] if scene.get("keyframe") else None
    has_keyframe = first_img is not None and first_img.exists()
    chars = scene.get("chars", [])

    if has_keyframe:
        mode = "frames"
    elif chars:
        mode = "ingredients"
    else:
        mode = "text"

    print(f"\n=== [{sid}] {scene.get('section', '')} ({scene['start']:.1f}s - {scene['end']:.1f}s) | 模式: {mode} ===")
    flow_core.wait_for_authenticated_flow(page)
    flow_core.ensure_in_project(page)
    time.sleep(0.8)

    new_add_btn = page.get_by_role("button", name=re.compile(r"在提示詞輸入框新增素材|Add asset", re.I)).first
    is_new_ui = False
    try:
        is_new_ui = new_add_btn.is_visible(timeout=2500)
    except Exception:
        is_new_ui = False

    if is_new_ui:
        box = page.get_by_role("textbox", name=re.compile(r"你想製作什麼內容|What do you want|prompt", re.I)).first
        box.click(force=True)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.3)

        if mode == "frames" and first_img is not None:
            attach_image_new_flow_ui(page, first_img, f"{sid} 鎖定首幀")
        elif mode == "ingredients":
            for c in chars:
                ref_rel = (characters_cfg.get(c) or {}).get("ref_image")
                if ref_rel:
                    rp = project_dir / ref_rel
                    if rp.exists():
                        attach_image_new_flow_ui(page, rp, f"角色參考({c})")

        prompt_text = build_agent_prompt(scene, mode, model, resolution, duration)
        box.click(force=True)
        page.keyboard.press("End")
        page.keyboard.insert_text(" " + prompt_text)
        print("[OK] Prompt 已附加至圖片 chip 後方！")
    else:
        flow_core.switch_to_frames_mode(page, model=model, resolution=resolution, duration=duration)
        if mode == "frames" and first_img is not None:
            flow_core.upload_frame(page, r"^開始$|^Start$", first_img, f"{sid} 首幀")
        flow_core.fill_prompt(page, scene["flow_prompt_en"])

    known_urls = set(collect_flow_video_urls_with_hover(page, max_cards=4))
    if not no_submit:
        flow_core.trigger_generate(page)
        print(f"  ✅ [{sid}] 已送出生成 ({mode} · {model} · {resolution} · {duration}s)！")
    else:
        print(f"  ✅ [{sid}] 素材與 Prompt 已填入（--no-submit 模式）！")

    out_mp4 = project_dir / scene["flow_clip"]
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    return (page, sid, known_urls, out_mp4)


def download_720p_upscaled_from_card(page, card_more_index: int, out_mp4: Path, timeout_ms: int = 120_000) -> bool:
    """點擊卡片「更多選項 → 下載 → 720p 已提升畫質」，自動等待 Google 雲端免費升頻並攔截下載檔案"""
    try:
        card_more = page.locator("button[aria-label='更多選項']").nth(card_more_index)
        card_more.click(force=True, timeout=5000)
        time.sleep(0.6)

        dl_item = page.locator("[role='menuitem']:has-text('下載'), button:has-text('下載')").first
        dl_item.hover(force=True, timeout=4000)
        time.sleep(0.6)

        hd_item = page.locator("[role='menuitem']:has-text('720p'), button:has-text('720p')").first
        if not hd_item.is_visible(timeout=2500):
            page.keyboard.press("Escape")
            return False

        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        with page.expect_download(timeout=timeout_ms) as dl_info:
            hd_item.click(force=True)
        dl = dl_info.value
        dl.save_as(str(out_mp4))
        return out_mp4.exists() and out_mp4.stat().st_size > 50_000
    except Exception as exc:
        print(f"  [提示] 720p 雲端免費升頻下載略過（將退回原始串流下載）：{exc}")
        try:
            page.keyboard.press("Escape")
            page.keyboard.press("Escape")
        except Exception:
            pass
        return False


def wait_and_download_one(page, sid: str, known_urls: set, out_mp4: Path, timeout_sec: int = 300, prefer_720p_upscale: bool = True) -> bool:
    print(f"  [監聽] 等待 [{sid}] Google Flow 影片生成完成並自動下載（上限 {timeout_sec}s）...")
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
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
        if new_urls:
            # 優先透過「更多選項 → 下載 → 720p 已提升畫質」免費抓雲端 720p 高畫質版（最新影片永遠在最前面 nth(2)）
            if prefer_720p_upscale:
                print(f"  [720p 免費升頻] 偵測到 [{sid}] 生成完成，嘗試抓取 Google 雲端 720p 已提升畫質版...")
                if download_720p_upscaled_from_card(page, card_more_index=2, out_mp4=out_mp4):
                    print(f"  🎬 [{sid}] 已自動下載 720p 雲端升頻版：{out_mp4.name} ({out_mp4.stat().st_size:,} bytes)")
                    return True
            for u in new_urls:
                if flow_core.download_video_from_page(page, u, out_mp4):
                    print(f"  🎬 [{sid}] 已自動下載：{out_mp4.name} ({out_mp4.stat().st_size:,} bytes)")
                    return True
        time.sleep(6.0)
    print(f"  ⏳ [{sid}] 逾時未偵測到 <video> 下載。")
    return False


def main():
    parser = argparse.ArgumentParser(description="通用 AI MV 工廠 — Google Flow 批次生片引擎")
    parser.add_argument("--project", required=True, help="MV 專案資料夾（內含 storyboard.json），例如 peace_love_mv")
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=999)
    parser.add_argument("--only", nargs="+", help="只跑指定鏡號，例如 --only s04 s09 s12")
    parser.add_argument("--model", choices=["omni12", "veo31lite", "auto"], default="omni12")
    parser.add_argument("--res", choices=["360p", "720p"], default="360p")
    parser.add_argument("--duration", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true", help="強制重跑已存在的 flow_clips/sXX_flow.mp4")
    parser.add_argument("--no-submit", action="store_true")
    parser.add_argument("--no-wait", action="store_true")
    parser.add_argument("--project-url", default=flow_core.FLOW_URL)
    args = parser.parse_args()

    project_dir = Path(args.project)
    if not project_dir.is_absolute():
        project_dir = (BASE_DIR / project_dir).resolve()

    data = load_storyboard(project_dir)
    scenes = data["scenes"]
    characters_cfg = data.get("characters", {})

    if args.only:
        only_set = set(args.only)
        selected = [s for s in scenes if s["id"] in only_set]
    else:
        selected = [s for i, s in enumerate(scenes) if args.start <= (i + 1) <= args.end]

    if not args.force:
        selected = [
            s for s in selected
            if not ((project_dir / s["flow_clip"]).exists() and (project_dir / s["flow_clip"]).stat().st_size > 50_000)
        ]

    if not selected:
        print(f"✅ [{project_dir.name}] 所有選定分鏡均已有 Google Flow 影片！")
        return

    print(f"🚀 [{data.get('title', project_dir.name)}] 準備在 Google Flow 依序生成 {len(selected)} 鏡 ({args.model} · {args.res} · {args.duration}s)")
    flow_core.ensure_chrome_running(args.project_url)

    done_ids: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{flow_core.CDP_PORT}")
        context = browser.contexts[0] if browser.contexts else browser.new_context()

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
                project_dir=project_dir,
                characters_cfg=characters_cfg,
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

    print("\n" + "=" * 64)
    print(f"  🎬 完成下載：{len(done_ids)} / {len(selected)} 鏡 ({', '.join(done_ids)})")
    print(f"  👉 組裝指令：python mv_builder.py --project {project_dir.name}")
    print("=" * 64)


if __name__ == "__main__":
    main()
