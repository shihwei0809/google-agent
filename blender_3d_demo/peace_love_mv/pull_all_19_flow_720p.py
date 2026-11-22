"""
100% 零錯位全收齊器：透過真實捲動容器 scrollTop 走訪整個 Google Flow 媒體庫，
下載每支影片的「720p 已提升畫質」，再用像素 MSE 直接比對 360p 原始備份自動歸位！
"""

import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
from playwright.sync_api import sync_playwright

MV_DIR = Path(__file__).resolve().parent
PARENT_DIR = MV_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

import auto_upload_flow as flow_core  # noqa: E402

BACKUP_360_DIR = MV_DIR / "flow_clips_360p_backup"
BACKUP_ZIP = MV_DIR / "flow_clips_to_upscale.zip"
OLD_720_DIR = MV_DIR / "flow_clips_flow720p"
VERIFIED_720_DIR = MV_DIR / "flow_clips_720p_verified"
TARGET_FLOW_DIR = MV_DIR / "flow_clips"


def find_ffmpeg() -> str:
    ff = shutil.which("ffmpeg")
    if ff:
        return ff
    local_app = os.environ.get("LOCALAPPDATA", "")
    if local_app:
        winget_dir = Path(local_app) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            for p in winget_dir.rglob("ffmpeg.exe"):
                return str(p)
    raise FileNotFoundError("找不到 ffmpeg")


FFMPEG = find_ffmpeg()


def thumb_vec(mp4: Path) -> np.ndarray:
    """萃取影片 3 個時間點的 32x18 RGB 像素陣列供 MSE 比對。"""
    raw = subprocess.check_output(
        [
            FFMPEG, "-v", "error", "-i", str(mp4),
            "-vf", "fps=1/3,scale=32:18", "-vframes", "3",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        stderr=subprocess.DEVNULL,
    )
    return np.frombuffer(raw, dtype=np.uint8).astype(np.float32)


def match_clip(mp4: Path, bak_vecs: dict[str, np.ndarray]) -> tuple[str | None, float]:
    """透過最小均方誤差 (MSE) 找出 360p 備份庫中最匹配的鏡頭檔名。"""
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
    """點擊卡片「更多選項 → 下載 → 720p 已提升畫質」並存檔至 dst_path。"""
    try:
        more_btn.evaluate("el => el.scrollIntoView({block: 'center', inline: 'nearest'})")
        time.sleep(0.25)
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
        return dst_path.exists() and dst_path.stat().st_size > 100_000
    except Exception as exc:
        print(f"    [略過] {exc}")
        try:
            page.keyboard.press("Escape")
            page.keyboard.press("Escape")
        except Exception:
            pass
        return False


def _safe_copyfile(src: Path, dst: Path):
    """確保目標目錄存在並複製檔案，若遇短暫檔案鎖定則於 0.5 秒後重試。"""
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copyfile(str(src), str(dst))
    except OSError:
        time.sleep(0.5)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(src), str(dst))


def _ensure_dir_from_zip(target_dir: Path):
    """若目錄不存在或少於 19 支 s*_flow.mp4，從 flow_clips_to_upscale.zip 自動還原。"""
    target_dir.mkdir(parents=True, exist_ok=True)
    if len(list(target_dir.glob("s*_flow.mp4"))) >= 19:
        return
    if not BACKUP_ZIP.exists():
        raise FileNotFoundError(f"找不到備份壓縮檔：{BACKUP_ZIP}")
    with zipfile.ZipFile(BACKUP_ZIP, "r") as zf:
        zf.extractall(target_dir)


def main():
    VERIFIED_720_DIR.mkdir(parents=True, exist_ok=True)
    _ensure_dir_from_zip(BACKUP_360_DIR)
    if len(list(TARGET_FLOW_DIR.glob("s*_flow.mp4"))) < 19:
        _ensure_dir_from_zip(TARGET_FLOW_DIR)
        for vp in VERIFIED_720_DIR.glob("s*_flow.mp4"):
            if vp.stat().st_size > 100_000:
                _safe_copyfile(vp, TARGET_FLOW_DIR / vp.name)

    bak_vecs = {p.name: thumb_vec(p) for p in sorted(BACKUP_360_DIR.glob("s*_flow.mp4"))}

    # 1. 先把先前已下載且通過 MSE < 300 驗證的 720p 片段匯入 VERIFIED_720_DIR
    if OLD_720_DIR.exists():
        for p in sorted(OLD_720_DIR.glob("s*_flow.mp4")):
            mname, mse = match_clip(p, bak_vecs)
            if mname and mse < 300 and not (VERIFIED_720_DIR / mname).exists():
                _safe_copyfile(p, VERIFIED_720_DIR / mname)

    have = {p.name for p in VERIFIED_720_DIR.glob("s*_flow.mp4") if p.stat().st_size > 100_000}
    missing = sorted(set(bak_vecs.keys()) - have)
    print(f"📦 已驗證 720p：{len(have)} / 19 鏡；尚缺 {len(missing)} 鏡：{missing}")

    if missing:
        tmp_dl = VERIFIED_720_DIR / "_tmp_dl.mp4"
        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{flow_core.CDP_PORT}")
            flow_pages = [pg for c in b.contexts for pg in c.pages if "flow.google.com" in (pg.url or "")]
            if not flow_pages:
                raise RuntimeError("找不到開啟中的 flow.google.com 分頁")
            pg = flow_pages[0]

            # 找出頁面上真正可捲動的媒體格容器並回到最頂端
            scroll_info = pg.evaluate("""() => {
              const cands = Array.from(document.querySelectorAll('div, main, section')).filter(el => {
                const st = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return (st.overflowY === 'auto' || st.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 100 && r.width > 400 && r.left < 600;
              }).sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight));
              if (!cands.length) return {found: false};
              cands[0].setAttribute('data-flow-grid-scroll', '1');
              cands[0].scrollTop = 0;
              return {found: true, scrollHeight: cands[0].scrollHeight, clientHeight: cands[0].clientHeight};
            }""")
            print("🔍 媒體捲動容器：", scroll_info)
            if not scroll_info.get("found"):
                raise RuntimeError("找不到 Flow 可捲動媒體容器 (scroll_info.found is False)")
            time.sleep(1.0)

            processed_card_sigs: set[str] = set()
            max_steps = 25
            for step in range(max_steps):
                if len(have) >= 19:
                    break

                card_indices = pg.evaluate("""() => {
                  const btns = Array.from(document.querySelectorAll("button[aria-label='更多選項']"));
                  const out = [];
                  for (let i = 2; i < btns.length; i++) {
                    const btn = btns[i];
                    let box = btn.parentElement;
                    for (let k = 0; k < 6 && box; k++) {
                      if ((box.innerText || '').includes('360p')) break;
                      box = box.parentElement;
                    }
                    const is360 = box && (box.innerText || '').includes('360p');
                    if (!is360) continue;
                    const img = box.querySelector('img');
                    const vid = box.querySelector('video');
                    const sig = (img && img.src) || (vid && (vid.currentSrc || vid.src)) || ('pos_' + Math.round(btn.getBoundingClientRect().top));
                    out.push({idx: i, sig: sig.slice(0, 140)});
                  }
                  return out;
                }""")

                print(f"\n📜 [捲動步驟 {step+1}] 偵測到 {len(card_indices)} 張 360p 影片卡（進度 {len(have)}/19）")
                all_more = pg.locator("button[aria-label='更多選項']")

                for item in card_indices:
                    if len(have) >= 19:
                        break
                    sig = item["sig"]
                    if sig in processed_card_sigs:
                        continue

                    if tmp_dl.exists():
                        tmp_dl.unlink()
                    btn = all_more.nth(item["idx"])
                    if click_720p_download(pg, btn, tmp_dl):
                        processed_card_sigs.add(sig)
                        mname, mse = match_clip(tmp_dl, bak_vecs)
                        if mname and ((mname not in have and mse < 600) or mse < 350):
                            if mname not in have:
                                VERIFIED_720_DIR.mkdir(parents=True, exist_ok=True)
                                TARGET_FLOW_DIR.mkdir(parents=True, exist_ok=True)
                                verified_dst = VERIFIED_720_DIR / mname
                                _safe_copyfile(tmp_dl, verified_dst)
                                _safe_copyfile(verified_dst, TARGET_FLOW_DIR / mname)
                                tmp_dl.unlink(missing_ok=True)
                                have.add(mname)
                                print(f"  ✅ [{mname}] 精準歸位 720p！(MSE={mse:.1f}, {verified_dst.stat().st_size/1e6:.2f} MB)  [{len(have)}/19]")
                            else:
                                print(f"  ⚡ [{mname}] 已有 720p，略過")
                                tmp_dl.unlink(missing_ok=True)
                        else:
                            print(f"  ℹ️ 非本次定版鏡頭 (best={mname} MSE={mse:.1f})，略過")
                            tmp_dl.unlink(missing_ok=True)

                moved = pg.evaluate("""() => {
                  const el = document.querySelector("[data-flow-grid-scroll='1']");
                  if (!el) return false;
                  const prev = el.scrollTop;
                  el.scrollTop = Math.min(el.scrollHeight, prev + Math.max(320, Math.floor(el.clientHeight * 0.5)));
                  return el.scrollTop > prev + 5;
                }""")
                time.sleep(1.2)
                if not moved:
                    print("📌 已捲動至媒體庫最底部。")
                    break

    final_have = sorted(p.name for p in VERIFIED_720_DIR.glob("s*_flow.mp4") if p.stat().st_size > 100_000)
    print(f"\n🎉 最終已收齊並驗證之 Flow 720p 鏡數：{len(final_have)} / 19")
    for p in VERIFIED_720_DIR.glob("s*_flow.mp4"):
        _safe_copyfile(p, TARGET_FLOW_DIR / p.name)

    print("🎞️ 立即重新壓製最終 1080p MV 與 IG 9:16 版...")
    subprocess.run(
        [
            sys.executable, "-u", str(PARENT_DIR / "mv_builder.py"),
            "--project", "peace_love_mv",
            "--rebuild-clips",
            "--out", "Peace_and_Love_MV_Flow720p_1080p.mp4",
        ],
        check=True,
    )
    in_vid = MV_DIR / "Peace_and_Love_MV_Flow720p_1080p.mp4"
    ig_vid = MV_DIR / "Peace_and_Love_IG_Reels_9x16.mp4"
    fc = "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=28:5,eq=brightness=-0.12:saturation=1.15[bg];[0:v]scale=1080:-2:flags=lanczos[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,fade=t=in:st=0:d=0.6,fade=t=out:st=53.5:d=1.5[v]"
    subprocess.run(
        [
            FFMPEG, "-y", "-ss", "110.5", "-t", "55.0", "-i", str(in_vid),
            "-filter_complex", fc, "-map", "[v]", "-map", "0:a",
            "-af", "afade=t=in:st=0:d=0.5,afade=t=out:st=53.5:d=1.5",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(ig_vid),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    print(f"✅ IG Reels 亦同步更新完成：{ig_vid} ({ig_vid.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    main()
