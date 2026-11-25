"""
100% 零人工介入全自動管線（支援 Colab Web Component / Shadow DOM & Nested Output Iframes）：
1. 連線本機已登入 Google 之 Chrome CDP (Port 9222) 開啟 colab_t4_voice_clone.ipynb（內建預設 T4 GPU + BreezyVoice）
2. 點擊 #runtime-menu-button -> 全部執行，並穿透 Shadow DOM 自動點擊「仍要執行」
3. 跨所有 iframe 與 Shadow DOM 自動攔截 Cell 3 的 <input type="file">，一次塞入 ref.wav + inbound_voice_jobs.json
4. 自動接管下載 cloned_audio_ready.zip -> 解壓至 audio_myvoice/ -> 自動壓出獨立成片：
   第1部_儲槽進貨與卸料篇_本人原聲克隆終極版.mp4（保留原女聲版不覆蓋）
"""

import re
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import auto_upload_flow as f

SOP_DIR = BASE_DIR / "tank_inbound_sop"
WORK_DIR = SOP_DIR / "_work"
DL_DIR = WORK_DIR / "colab_dl"
MYVOICE_DIR = SOP_DIR / "audio_myvoice"
REF_WAV = SOP_DIR / "ref.wav"
JOBS_JSON = SOP_DIR / "inbound_voice_jobs.json"
OUT_VIDEO = SOP_DIR / "第1部_儲槽進貨與卸料篇_本人原聲克隆終極版.mp4"

COLAB_URL = "https://colab.research.google.com/github/shihwei0809/google-agent/blob/main/.agents/skills/sop-cinema-video/templates/colab_t4_voice_clone.ipynb"


def click_shadow_text(pg, regex_str: str) -> str | None:
    """穿透 Colab Shadow DOM 點擊符合正規表達式的按鈕（如『仍要執行』、『確定』、『允許』）。"""
    return pg.evaluate(
        """(pat) => {
            const re = new RegExp(pat, 'i');
            const cands = [];
            const walk = (root) => {
                root.querySelectorAll('button, mwc-button, md-text-button, md-filled-button, paper-button, [role="button"], .goog-menuitem').forEach(el => {
                    const txt = (el.innerText || el.textContent || '').trim();
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0 && re.test(txt) && txt.length < 30) {
                        cands.push({el, txt});
                    }
                });
                root.querySelectorAll('*').forEach(el => { if (el.shadowRoot) walk(el.shadowRoot); });
            };
            walk(document);
            if (cands.length > 0) {
                cands[cands.length - 1].el.click();
                return cands[cands.length - 1].txt;
            }
            return null;
        }""",
        regex_str,
    )


def trigger_run_all(pg) -> None:
    print("[Colab] 點擊 #runtime-menu-button -> 全部執行 ...")
    try:
        pg.locator("#runtime-menu-button").click(timeout=10000)
        time.sleep(1.0)
        clicked = click_shadow_text(pg, r"^全部執行$|^Run all$")
        if clicked:
            print(f"[Colab] 已點選選單：{clicked}")
        else:
            pg.keyboard.press("Escape")
            time.sleep(0.3)
            pg.keyboard.press("Control+F9")
    except Exception:
        pg.keyboard.press("Control+F9")

    # 連續偵測並點擊「仍要執行 (Run anyway)」等確認視窗
    for _ in range(10):
        time.sleep(1.2)
        hit = click_shadow_text(pg, r"仍要執行|Run anyway|^連線$|^Connect$")
        if hit:
            print(f"[Colab] 自動點擊彈窗確認：{hit}")


def find_downloaded_zip(start_ts: float) -> Path | None:
    search_dirs = [DL_DIR, Path.home() / "Downloads"]
    for d in search_dirs:
        if not d.exists():
            continue
        if list(d.glob("*cloned_audio_ready*.crdownload")):
            continue
        cands = sorted(d.glob("*cloned_audio_ready*.zip"), key=lambda x: x.stat().st_mtime, reverse=True)
        for c in cands:
            if c.stat().st_mtime >= start_ts and c.stat().st_size > 30_000:
                return c
    return None


def main() -> None:
    if not REF_WAV.exists() or not JOBS_JSON.exists():
        raise FileNotFoundError(f"找不到 {REF_WAV} 或 {JOBS_JSON}")

    DL_DIR.mkdir(parents=True, exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    start_ts = time.time()

    f.ensure_chrome_running(COLAB_URL)

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{f.CDP_PORT}")
        ctx = b.contexts[0]
        pg = next((x for x in ctx.pages if "colab.research.google.com" in (x.url or "")), None)
        if pg is None:
            pg = ctx.new_page()
            pg.goto(COLAB_URL, wait_until="domcontentloaded")
        elif "colab_t4_voice_clone" not in (pg.url or ""):
            pg.goto(COLAB_URL, wait_until="domcontentloaded")
        else:
            pg.reload(wait_until="domcontentloaded")

        pg.bring_to_front()

        cdp = ctx.new_cdp_session(pg)
        cdp.send("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": str(DL_DIR.resolve())})

        print("[Colab] 等待 #runtime-menu-button 載入完成...")
        pg.locator("#runtime-menu-button").wait_for(state="visible", timeout=45000)
        time.sleep(3.0)

        trigger_run_all(pg)

        uploaded_done = False
        zip_path: Path | None = None
        deadline = time.time() + 1800  # 最多等待 30 分鐘
        last_log = 0.0
        dl_holder: list[Path] = []

        def _on_download(dl):
            dst = DL_DIR / dl.suggested_filename
            print(f"[Download] 攔截到瀏覽器下載：{dl.suggested_filename} -> {dst}")
            dl.save_as(str(dst))
            dl_holder.append(dst)

        pg.on("download", _on_download)

        while time.time() < deadline:
            # 0. 快速偵測「無法指派後端」或任何 Cell 發生 RuntimeError/Traceback，立即退出不空等
            try:
                body_txt = pg.locator("body").inner_text(timeout=1500)
                if "無法指派後端" in body_txt or "沒有任何包含 GPU 的後端可使用" in body_txt or "Cannot connect to GPU backend" in body_txt:
                    pg.screenshot(path=str(WORK_DIR / "colab_no_gpu.png"))
                    raise RuntimeError("Colab 目前仍回報「無法指派後端：沒有任何包含 GPU 的後端可使用」（免費 T4 GPU 配額尚在冷卻中）。")
                for fr in pg.frames[1:]:
                    ft = fr.locator("body").inner_text(timeout=300)
                    if "Traceback (most recent call last)" in ft and ("RuntimeError" in ft or "ModuleNotFoundError" in ft or "BadZipFile" in ft or "TypeError" in ft):
                        pg.screenshot(path=str(WORK_DIR / "colab_cell_error.png"))
                        raise RuntimeError(f"Colab Cell 執行報錯：\n{ft[-800:]}")
            except RuntimeError:
                raise
            except Exception:
                pass

            # 1. 跨所有 iframe（含深層 output iframe）偵測 <input type="file">
            if not uploaded_done:
                for fr in pg.frames:
                    try:
                        finp = fr.locator('input[type="file"]')
                        if finp.count() > 0:
                            print("[Upload] 偵測到 Cell 3 上傳元件！自動塞入 ref.wav + inbound_voice_jobs.json ...")
                            finp.first.set_input_files([str(REF_WAV), str(JOBS_JSON)])
                            uploaded_done = True
                            print("[Upload] 已成功自動送出 ref.wav + inbound_voice_jobs.json！")
                            break
                    except Exception:
                        pass

            # 2. 處理偶發彈窗（仍要執行 / 允許下載多檔）
            hit = click_shadow_text(pg, r"仍要執行|Run anyway|^允許$|^Allow$")
            if hit:
                print(f"[Colab] 自動點擊彈窗：{hit}")

            # 3. 檢查 ZIP 下載完成
            if dl_holder and dl_holder[-1].exists() and dl_holder[-1].stat().st_size > 30_000:
                zip_path = dl_holder[-1]
                break
            cand_zip = find_downloaded_zip(start_ts)
            if cand_zip:
                zip_path = cand_zip
                break

            if time.time() - last_log >= 25:
                last_log = time.time()
                st = "已自動上傳 ref.wav + JSON，T4 GPU 正在跑 BreezyVoice 克隆與 Whisper 挑音..." if uploaded_done else "T4 GPU 正在安裝 BreezyVoice 環境與模型，等待 Cell 3 上傳框出現..."
                print(f"[Progress] {int(time.time() - start_ts)}s | {st}")
                try:
                    pg.screenshot(path=str(WORK_DIR / "colab_live_status.png"))
                except Exception:
                    pass

            time.sleep(2.5)

        if not zip_path:
            pg.screenshot(path=str(WORK_DIR / "colab_timeout_status.png"))
            raise TimeoutError("等待 cloned_audio_ready.zip 逾時，請檢查 _work/colab_timeout_status.png")

    print(f"\n[Success] 已自動下載克隆音檔包：{zip_path} ({zip_path.stat().st_size / 1024:.1f} KB)")
    if MYVOICE_DIR.exists():
        shutil.rmtree(MYVOICE_DIR)
    MYVOICE_DIR.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.namelist():
            if member.lower().endswith(".mp3") and "shot" in Path(member).name.lower():
                target = MYVOICE_DIR / Path(member).name
                target.write_bytes(zf.read(member))
                print(f"  -> 解壓音檔：{target.name}")

    mp3s = sorted(MYVOICE_DIR.glob("shot*.mp3"))
    if len(mp3s) < 8:
        raise RuntimeError(f"解壓後音檔不足 8 個（目前 {len(mp3s)} 個）：{[x.name for x in mp3s]}")

    print(f"\n[VideoBuild] 開始合成「本人原聲克隆終極版」：{OUT_VIDEO.name} ...")
    subprocess.run(
        [
            sys.executable,
            str(BASE_DIR / "build_tank_inbound_video.py"),
            "--cinema",
            "--audio-dir", str(MYVOICE_DIR),
            "--out-video", str(OUT_VIDEO),
        ],
        check=True,
    )
    print(f"\n🎉 全自動一條龍完成！成品：{OUT_VIDEO}")


if __name__ == "__main__":
    main()
