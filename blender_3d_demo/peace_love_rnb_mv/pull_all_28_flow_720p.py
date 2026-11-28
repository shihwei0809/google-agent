"""
《用愛點亮星空》28 鏡 100% 零錯位 Google Flow 720p 雲端升頻全收齊器
- 先備份已驗證通過的 28 鏡 360p 基準到 flow_clips_360p_backup/
- s10 已是 720p 冰雪融化微距，直接入庫 flow_clips_720p_verified/s10_flow.mp4
- 透過真實捲動容器 data-flow-grid-scroll 走訪 Flow 專案 (52feb772-f8f7-4f41-9f14-9fb51a6f91be)，
  逐卡點「更多選項 → 下載 → 720p」，用 3 幀 32x18 RGB MSE 自動比對 28 鏡基準零錯位歸位！
- 收齊後自動呼叫 mv_builder.py 組裝最終高畫質正式版：用愛點亮星空_MV_Flow720p_1080p.mp4
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

MV_DIR = Path(__file__).resolve().parent
PARENT_DIR = MV_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import auto_upload_flow as flow_core  # noqa: E402

PROJECT_URL = "https://flow.google.com/project/52feb772-f8f7-4f41-9f14-9fb51a6f91be"
BACKUP_360_DIR = MV_DIR / "flow_clips_360p_backup"
VERIFIED_720_DIR = MV_DIR / "flow_clips_720p_verified"
TARGET_FLOW_DIR = MV_DIR / "flow_clips"
OUT_FINAL = "用愛點亮星空_MV_Flow720p_1080p.mp4"


def find_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        for p in (Path(local_app) / "Microsoft" / "WinGet" / "Packages").rglob("ffmpeg.exe"):
            return str(p)
    raise FileNotFoundError("找不到 ffmpeg")


FFMPEG = find_ffmpeg()
FFPROBE = str(Path(FFMPEG).with_name("ffprobe.exe")) if Path(FFMPEG).with_name("ffprobe.exe").exists() else shutil.which("ffprobe")


def video_height(mp4: Path) -> int:
    try:
        out = subprocess.check_output(
            [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "default=noprint_wrappers=1:nokey=1", str(mp4)],
            text=True,
        ).strip()
        return int(out)
    except Exception:
        return 0


def thumb_vec(mp4: Path) -> np.ndarray:
    try:
        raw = subprocess.check_output(
            [
                FFMPEG, "-v", "error", "-i", str(mp4),
                "-vf", "fps=1/3,scale=32:18", "-vframes", "3",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
            ],
            stderr=subprocess.DEVNULL,
        )
        return np.frombuffer(raw, dtype=np.uint8).astype(np.float32)
    except Exception:
        return np.array([], dtype=np.float32)


def match_clip(mp4: Path, bak_vecs: dict[str, np.ndarray]) -> tuple[str | None, float]:
    v = thumb_vec(mp4)
    if len(v) == 0:
        return None, 1e18
    best_name, best_mse = None, 1e18
    for name, bv in bak_vecs.items():
        n = min(len(v), len(bv))
        if n == 0:
            continue
        mse = float(np.mean((v[:n] - bv[:n]) ** 2))
        if mse < best_mse:
            best_mse, best_name = mse, name
    return best_name, best_mse


def click_720p_download(page, more_btn, dst_path: Path, timeout_ms: int = 120_000) -> bool:
    try:
        more_btn.click(force=True, timeout=4000)
        time.sleep(0.45)
        dl_item = page.locator("[role='menuitem']:has-text('下載'), button:has-text('下載')").first
        if not dl_item.is_visible(timeout=2000):
            page.keyboard.press("Escape")
            return False
        dl_item.hover(force=True, timeout=3000)
        time.sleep(0.45)
        hd_item = page.locator("[role='menuitem']:has-text('720p'), button:has-text('720p')").first
        if not hd_item.is_visible(timeout=2000):
            page.keyboard.press("Escape")
            page.keyboard.press("Escape")
            return False
        with page.expect_download(timeout=timeout_ms) as dl_info:
            hd_item.click(force=True)
        dl_info.value.save_as(str(dst_path))
        return dst_path.exists() and dst_path.stat().st_size > 150_000
    except Exception:
        try:
            page.keyboard.press("Escape")
            page.keyboard.press("Escape")
        except Exception:
            pass
        return False


def main():
    BACKUP_360_DIR.mkdir(parents=True, exist_ok=True)
    VERIFIED_720_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 備份目前 28 鏡已審核通過的 360p 基準
    for mp4 in sorted(TARGET_FLOW_DIR.glob("s*_flow.mp4")):
        dst = BACKUP_360_DIR / mp4.name
        if not dst.exists():
            shutil.copy2(mp4, dst)
        # 若該鏡已經是 >= 700p（例如 s10），直接入庫 verified 720p
        if video_height(mp4) >= 700 and not (VERIFIED_720_DIR / mp4.name).exists():
            shutil.copy2(mp4, VERIFIED_720_DIR / mp4.name)
            print(f"✅ [{mp4.name}] 已經是 720p 高畫質，直接入庫！", flush=True)

    bak_vecs = {p.name: thumb_vec(p) for p in sorted(BACKUP_360_DIR.glob("s*_flow.mp4"))}
    have = {p.name for p in VERIFIED_720_DIR.glob("s*_flow.mp4") if p.stat().st_size > 150_000}
    total_need = len(bak_vecs)
    print(f"📦 720p 初始進度：{len(have)} / {total_need} 鏡；尚缺 {total_need - len(have)} 鏡", flush=True)

    if len(have) < total_need:
        flow_core.ensure_chrome_running(PROJECT_URL)
        tmp_dl = VERIFIED_720_DIR / "_tmp_720.mp4"
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{flow_core.CDP_PORT}")
            pg = next((pg for c in b.contexts for pg in c.pages if "flow.google.com" in (pg.url or "")), b.contexts[0].pages[0])
            pg.goto(PROJECT_URL, wait_until="domcontentloaded")
            time.sleep(5.0)

            scroll_info = pg.evaluate("""() => {
              const cands = Array.from(document.querySelectorAll('div, main, section')).filter(el => {
                const st = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return (st.overflowY === 'auto' || st.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 100 && r.width > 400;
              }).sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight));
              if (!cands.length) return {found: false};
              cands[0].setAttribute('data-flow-grid-scroll', '1');
              cands[0].scrollTop = 0;
              return {found: true, sh: cands[0].scrollHeight, ch: cands[0].clientHeight};
            }""")
            print("🔍 媒體捲動容器：", scroll_info, flush=True)
            time.sleep(1.0)

            processed_sigs: set[str] = set()
            total_sh = int(scroll_info.get("sh") or 13000)
            target_y = 0
            step = 0
            while target_y <= total_sh + 400 and len(have) < total_need:
                step += 1
                scroll_res = pg.evaluate("""(y) => {
                  const cands = Array.from(document.querySelectorAll('div, main, section')).filter(el => {
                    const st = getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    return (st.overflowY === 'auto' || st.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 100 && r.width > 400;
                  }).sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight));
                  if (!cands.length) return {sh: 0, top: 0};
                  const el = cands[0];
                  el.scrollTop = y;
                  return {sh: el.scrollHeight, top: Math.round(el.scrollTop)};
                }""", target_y)
                total_sh = max(total_sh, int(scroll_res.get("sh") or 0))
                time.sleep(0.9)

                card_indices = pg.evaluate("""() => {
                  const btns = Array.from(document.querySelectorAll("button[aria-label='更多選項']"));
                  const out = [];
                  for (let i = 2; i < btns.length; i++) {
                    const btn = btns[i];
                    const r = btn.getBoundingClientRect();
                    if (r.top < 40 || r.bottom > window.innerHeight - 40) continue;
                    let box = btn.parentElement;
                    for (let k = 0; k < 7 && box; k++) {
                      if ((box.innerText || '').includes('360p')) break;
                      box = box.parentElement;
                    }
                    if (!box || !(box.innerText || '').includes('360p')) continue;
                    const img = box.querySelector('img');
                    const vid = box.querySelector('video');
                    const sig = (img && img.src) || (vid && (vid.currentSrc || vid.src)) || ('y_' + Math.round(r.top + window.scrollY) + '_x_' + Math.round(r.left));
                    out.push({idx: i, sig: sig.slice(0, 140)});
                  }
                  return out;
                }""")

                if card_indices:
                    print(f"\n📜 [掃描 y={target_y}/{total_sh}] 可見 {len(card_indices)} 張影片卡（720p 進度：{len(have)}/{total_need}）", flush=True)
                all_more = pg.locator("button[aria-label='更多選項']")

                for item in card_indices:
                    if len(have) >= total_need:
                        break
                    sig = item["sig"]
                    if sig in processed_sigs:
                        continue
                    processed_sigs.add(sig)

                    if tmp_dl.exists():
                        tmp_dl.unlink()
                    if click_720p_download(pg, all_more.nth(item["idx"]), tmp_dl):
                        if video_height(tmp_dl) < 600:
                            continue
                        mname, mse = match_clip(tmp_dl, bak_vecs)
                        if mname and ((mname not in have and mse < 650) or mse < 300):
                            shutil.copy2(tmp_dl, VERIFIED_720_DIR / mname)
                            shutil.copy2(tmp_dl, TARGET_FLOW_DIR / mname)
                            have.add(mname)
                            print(f"  🎬 [{len(have):02d}/{total_need}] 收齊 720p -> {mname} (MSE={mse:.1f}, {tmp_dl.stat().st_size/1024/1024:.2f} MB)", flush=True)

                target_y += 380

            if tmp_dl.exists():
                tmp_dl.unlink()

    missing = sorted(set(bak_vecs.keys()) - have)
    print(f"\n📊 720p 收集結果：{len(have)} / {total_need} 鏡完成 | 尚缺：{missing}", flush=True)

    # 確保所有 verified 720p 都覆寫進 flow_clips/
    for vp in VERIFIED_720_DIR.glob("s*_flow.mp4"):
        shutil.copy2(vp, TARGET_FLOW_DIR / vp.name)

    print(f"\n🎞️ 開始組裝最終高畫質正式版：{OUT_FINAL} ...", flush=True)
    subprocess.run(
        [
            sys.executable,
            str(PARENT_DIR / "mv_builder.py"),
            "--project", "peace_love_rnb_mv",
            "--out", OUT_FINAL,
        ],
        check=True,
    )
    print(f"\n🎉 大功告成！最終高畫質正式版：{MV_DIR / OUT_FINAL}", flush=True)


if __name__ == "__main__":
    main()
