"""使用已驗證的 720p 下載管線，從 Google Flow 媒體庫抓取第 2 部 3 段最新 720p 影片並首幀像素比對歸位"""
import subprocess
import sys
import time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import auto_upload_flow as f
from build_tank_outbound_video import find_ffmpeg

PROJECT_URL = "https://flow.google.com/project/90188ed6-68b8-4a67-93d7-25870ae5713e"
OUT_DIR = BASE_DIR / "tank_outbound_sop"
FRAMES_DIR = OUT_DIR / "flow_frames"
CLIPS_DIR = OUT_DIR / "flow_clips"
WORK_DIR = OUT_DIR / "_work"

TARGETS = {
    "b01_outbound_intro.mp4": FRAMES_DIR / "b01_outbound_first.png",
    "b02_outbound_isotank.mp4": FRAMES_DIR / "b02_outbound_isotank_first.png",
    "b03_outbound_outro.mp4": FRAMES_DIR / "b03_outbound_outro_first.png",
}


def img_vec(img: Image.Image):
    im = img.convert("RGB").resize((32, 18), Image.Resampling.BILINEAR)
    return list(im.getdata())


def mse(v1, v2) -> float:
    return sum((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2 for a, b in zip(v1, v2)) / (len(v1) * 3)


def first_frame_vec(ffmpeg_exe: str, mp4_path: Path):
    tmp_jpg = WORK_DIR / f"_probe_{mp4_path.stem}.jpg"
    subprocess.run(
        [ffmpeg_exe, "-y", "-i", str(mp4_path), "-vframes", "1", "-q:v", "2", str(tmp_jpg)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    vec = img_vec(Image.open(tmp_jpg))
    tmp_jpg.unlink(missing_ok=True)
    return vec


def click_720p_download(page, more_btn, dst_path: Path, timeout_ms: int = 120_000) -> bool:
    try:
        more_btn.evaluate("el => el.scrollIntoView({block: 'center', inline: 'nearest'})")
        time.sleep(0.3)
        more_btn.click(force=True, timeout=4000)
        time.sleep(0.5)
        dl_item = page.locator("[role='menuitem']:has-text('下載'), button:has-text('下載')").first
        if not dl_item.is_visible(timeout=2500):
            page.keyboard.press("Escape")
            return False
        dl_item.hover(force=True, timeout=3000)
        time.sleep(0.5)
        hd_item = page.locator("[role='menuitem']:has-text('720p'), button:has-text('720p')").first
        if not hd_item.is_visible(timeout=2500):
            # 若無 720p 退回 360p/原始
            hd_item = page.locator("[role='menuitem']:has-text('360p'), [role='menuitem']:has-text('原始')").first
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


def main():
    CLIPS_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_exe = find_ffmpeg()
    ref_vecs = {k: img_vec(Image.open(p)) for k, p in TARGETS.items()}

    f.ensure_chrome_running(PROJECT_URL)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{f.CDP_PORT}")
        pg = next((pg for c in b.contexts for pg in c.pages if "flow.google.com" in (pg.url or "")), None) or b.contexts[0].pages[0]
        if PROJECT_URL not in (pg.url or ""):
            pg.goto(PROJECT_URL, wait_until="domcontentloaded")
        # 等待媒體格載入完成，再切到「影片」分頁避開靜態圖片卡
        pg.locator("button[aria-label='更多選項']").nth(2).wait_for(state="attached", timeout=25000)
        time.sleep(1.5)
        try:
            pg.get_by_text("影片", exact=True).first.click()
            time.sleep(2.5)
        except Exception:
            pass

        # 跳過已下載且 >500KB 的鏡頭
        matched = {
            k: 0.0 for k in TARGETS
            if (CLIPS_DIR / k).exists() and (CLIPS_DIR / k).stat().st_size > 500_000
        }
        if matched:
            print(f"[Skip] 已有 720p 實片：{list(matched.keys())}")

        # 依既有 pull_all_19_flow_720p 邏輯找出所有 360p/720p 影片卡
        card_indices = pg.evaluate("""() => {
          const btns = Array.from(document.querySelectorAll("button[aria-label='更多選項']"));
          const out = [];
          for (let i = 2; i < btns.length; i++) {
            const btn = btns[i];
            let box = btn.parentElement;
            for (let k = 0; k < 6 && box; k++) {
              const t = box.innerText || '';
              if (t.includes('360p') || t.includes('720p')) break;
              box = box.parentElement;
            }
            const t = box ? (box.innerText || '') : '';
            if (t.includes('360p') || t.includes('720p')) {
              out.push(i);
            }
          }
          return out;
        }""")
        print(f"[Flow] 偵測到 {len(card_indices)} 張影片卡，開始補齊剩餘 720p 升頻影片...")
        all_more = pg.locator("button[aria-label='更多選項']")

        for pos, btn_idx in enumerate(card_indices[:8]):
            if len(matched) >= 3:
                break
            tmp_mp4 = WORK_DIR / f"_dl_720p_{pos}.mp4"
            tmp_mp4.unlink(missing_ok=True)
            print(f"  [{pos+1}] 下載 720p 中 (card idx={btn_idx})...")
            if not click_720p_download(pg, all_more.nth(btn_idx), tmp_mp4):
                continue
            vec = first_frame_vec(ffmpeg_exe, tmp_mp4)
            best_name, best_err = None, 1e18
            for tname, rvec in ref_vecs.items():
                if tname in matched:
                    continue
                err = mse(rvec, vec)
                if err < best_err:
                    best_err, best_name = err, tname
            print(f"      -> 最佳匹配：{best_name} (MSE={best_err:.1f}, {tmp_mp4.stat().st_size/1024/1024:.2f} MB)")
            if best_name and best_err < 2500:
                dst = CLIPS_DIR / best_name
                dst.write_bytes(tmp_mp4.read_bytes())
                matched[best_name] = best_err
            tmp_mp4.unlink(missing_ok=True)

        print(f"[Result] 已歸位 {len(matched)} / 3 支 720p 影片：{list(matched.keys())}")
        if len(matched) < 3:
            raise RuntimeError(f"僅歸位 {len(matched)}/3 支影片，尚缺：{set(TARGETS.keys()) - set(matched.keys())}")


if __name__ == "__main__":
    main()
