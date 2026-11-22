"""
從目前開啟的 Google Flow 專案中，將 19 鏡 360p 影片透過 MD5 精準配對，
全自動點擊「更多選項 → 下載 → 720p 已提升畫質」免費下載 Google 雲端 720p 版！
"""

import hashlib
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

MV_DIR = Path(__file__).resolve().parent
PARENT_DIR = MV_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import auto_upload_flow as flow_core  # noqa: E402

BACKUP_360_DIR = MV_DIR / "flow_clips_360p_backup"
OUT_720_DIR = MV_DIR / "flow_clips_flow720p"
TARGET_FLOW_DIR = MV_DIR / "flow_clips"


def md5_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def load_backup_hashes() -> dict[str, str]:
    """回傳 {md5_hex: 'sXX_flow.mp4'}"""
    mapping: dict[str, str] = {}
    for p in sorted(BACKUP_360_DIR.glob("s*_flow.mp4")):
        h = md5_bytes(p.read_bytes())
        mapping[h] = p.name
    return mapping


def click_720p_download_for_card(page, more_btn, dst_path: Path, timeout_ms: int = 120_000) -> bool:
    try:
        more_btn.click(force=True, timeout=5000)
        time.sleep(0.5)
        dl_item = page.locator("[role='menuitem']:has-text('下載'), button:has-text('下載')").first
        dl_item.hover(force=True, timeout=4000)
        time.sleep(0.5)
        hd_item = page.locator("[role='menuitem']:has-text('720p'), button:has-text('720p')").first
        if not hd_item.is_visible(timeout=2500):
            page.keyboard.press("Escape")
            return False
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        with page.expect_download(timeout=timeout_ms) as dl_info:
            hd_item.click(force=True)
        dl_info.value.save_as(str(dst_path))
        return dst_path.exists() and dst_path.stat().st_size > 100_000
    except Exception as exc:
        print(f"    [警告] 720p 下載失敗：{exc}")
        try:
            page.keyboard.press("Escape")
            page.keyboard.press("Escape")
        except Exception:
            pass
        return False


def main():
    hash_to_name = load_backup_hashes()
    print(f"📦 已載入 {len(hash_to_name)} 個 360p 原始分鏡指紋，準備從 Google Flow 精準抓取 720p 免費升頻版...")
    OUT_720_DIR.mkdir(parents=True, exist_ok=True)

    downloaded: set[str] = {p.name for p in OUT_720_DIR.glob("s*_flow.mp4") if p.stat().st_size > 100_000}
    if downloaded:
        print(f"⚡ 已有快取 720p：{sorted(downloaded)}")

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{flow_core.CDP_PORT}")
        pg = [pg for c in b.contexts for pg in c.pages if "flow.google.com" in (pg.url or "")][0]

        seen_urls: set[str] = set()
        # 捲動主媒體區（最多 10 輪，每輪向下捲動 700px 以載入虛擬捲動清單內的較早卡片）
        for scroll_round in range(10):
            if len(downloaded) >= len(hash_to_name):
                break
            all_more = pg.locator("button[aria-label='更多選項']")
            total_btns = all_more.count()
            print(f"\n🔍 [捲動輪次 {scroll_round+1}] 畫面偵測到 {max(0, total_btns - 2)} 張卡片（已完成 {len(downloaded)}/{len(hash_to_name)}）...")

            for idx in range(2, total_btns):
                if len(downloaded) >= len(hash_to_name):
                    break
                btn = all_more.nth(idx)
                try:
                    btn.hover(force=True, timeout=2500)
                    time.sleep(0.55)
                except Exception:
                    continue

                cur_urls = flow_core.collect_video_urls(pg)
                cand_urls = [u for u in cur_urls if u not in seen_urls]
                if not cand_urls:
                    continue

                matched_name = None
                for u in reversed(cand_urls):
                    seen_urls.add(u)
                    try:
                        resp = pg.context.request.get(u, timeout=30_000)
                        if resp.ok:
                            h = md5_bytes(resp.body())
                            if h in hash_to_name:
                                matched_name = hash_to_name[h]
                                break
                    except Exception:
                        continue

                if not matched_name:
                    continue
                if matched_name in downloaded:
                    print(f"  [略過] {matched_name}（已有 720p）")
                    continue

                print(f"  🎯 精準配對為 [{matched_name}] → 觸發 720p 雲端免費升頻下載...")
                dst = OUT_720_DIR / matched_name
                if click_720p_download_for_card(pg, btn, dst):
                    print(f"    ✅ 已下載 720p：{matched_name} ({dst.stat().st_size / (1024*1024):.2f} MB)")
                    downloaded.add(matched_name)
                    (TARGET_FLOW_DIR / matched_name).write_bytes(dst.read_bytes())
                time.sleep(0.8)

            # 向下捲動主媒體格容器（避開右側聊天面板）
            pg.mouse.move(480, 480)
            pg.mouse.wheel(0, 850)
            time.sleep(1.5)

    print(f"\n🎉 完成 720p 雲端升頻下載：{len(downloaded)} / {len(hash_to_name)} 鏡")
    if downloaded:
        print("🎞️ 立即重新組裝《Peace and Love》Flow 720p 高畫質＋修正時間軸版 MV...")
        subprocess.run(
            [
                sys.executable, "-u", str(PARENT_DIR / "mv_builder.py"),
                "--project", "peace_love_mv",
                "--rebuild-clips",
                "--out", "Peace_and_Love_MV_Flow720p_1080p.mp4",
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
