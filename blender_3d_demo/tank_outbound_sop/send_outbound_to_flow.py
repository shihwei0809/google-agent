"""透過本機 Chrome CDP 上傳第 2 部出貨篇 3 張首幀至 Google Flow 專案並送出 3 段生成（共 30 點）"""
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import auto_upload_flow as f

PROJECT_URL = "https://flow.google.com/project/90188ed6-68b8-4a67-93d7-25870ae5713e"
OUT_DIR = BASE_DIR / "tank_outbound_sop"
FRAMES = [
    OUT_DIR / "flow_frames" / "b01_outbound_first.png",
    OUT_DIR / "flow_frames" / "b02_outbound_isotank_first.png",
    OUT_DIR / "flow_frames" / "b03_outbound_outro_first.png",
]

PROMPT = (
    "請只針對我剛剛最新上傳的這 3 張圖片（b01_outbound_first.png、b02_outbound_isotank_first.png、b03_outbound_outro_first.png），"
    "使用 Omni 1.2 Flash、360p、10 秒、各 1 部生成 3 段 16:9 寫實企業工安影片（共 30 點，不要生成任何文字與字幕）：\n"
    "1. b01_outbound_intro（以 b01_outbound_first.png 為首幀，10 秒）：35mm 紀錄片風格平穩推鏡，"
    "滿配 PPE 的台灣作業員先低頭核對出貨通知單夾板，接著蹲身確認輪檔、滅火器與柱上接地捲盤連至不鏽鋼槽車底盤的靜電接地夾，起身確認無誤後點頭示意開始灌裝。\n"
    "2. b02_outbound_isotank（以 b02_outbound_isotank_first.png 為首幀，10 秒）：35mm 穩定環繞運鏡，"
    "穿戴完整 PPE 與背負式安全帶且掛勾確實扣在防墜桿上的作業員，仔細檢查 ISO TANK 頂部氮氣軟管接頭並確認壓力錶指針正常，展現專業嚴謹的工安作業節奏。\n"
    "3. b03_outbound_outro（以 b03_outbound_outro_first.png 為首幀，10 秒）：溫暖午後陽光 35mm 平穩拉遠運鏡，"
    "兩名滿配 PPE 的作業員確認槽車閥門與潔淨無滴漏的地面、所有軟管與設備皆歸位後，互相點頭並比出 OK 手勢，指揮不鏽鋼化學槽車平穩駛向遠方地磅站。\n"
    "請立即送出 30 點授權讓我核准。"
)


def main():
    missing = [str(p) for p in FRAMES if not p.exists()]
    if missing:
        raise FileNotFoundError(f"缺少首幀圖檔：{missing}")

    f.ensure_chrome_running(PROJECT_URL)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{f.CDP_PORT}")
        ctx = b.contexts[0]
        pg = next((x for x in ctx.pages if "flow.google.com" in (x.url or "")), None) or ctx.pages[0]
        if PROJECT_URL not in (pg.url or ""):
            pg.goto(PROJECT_URL, wait_until="domcontentloaded")
        time.sleep(3)

        # 上傳 3 張首幀
        file_inputs = pg.locator('input[type="file"]')
        if file_inputs.count() == 0:
            pg.locator('button[aria-label="新增媒體選單"]').first.click()
            time.sleep(1.5)
            file_inputs = pg.locator('input[type="file"]')
        if file_inputs.count() > 0:
            file_inputs.first.set_input_files([str(x) for x in FRAMES])
        else:
            with pg.expect_file_chooser(timeout=6000) as fc:
                pg.locator('[role="menuitem"], .cdk-overlay-pane button').filter(has_text="上傳").first.click()
            fc.value.set_files([str(x) for x in FRAMES])
        print("[Upload] 已上傳第 2 部 3 張首幀，等待 10 秒完成同步...")
        time.sleep(10)

        # 填入 Prompt 並送出
        box = pg.locator('[contenteditable="true"], textarea:not([name="g-recaptcha-response"])').locator("visible=true").last
        box.click()
        pg.keyboard.insert_text(PROMPT)
        time.sleep(1.2)
        pg.locator('button[aria-label="開始生成"]').first.click()
        print("[Send] 已送出第 2 部 3 鏡生成指令，等待 30 點核准按鈕出現...")

        approved = False
        for _ in range(35):
            time.sleep(1.5)
            btn = pg.get_by_role("radio", name="核准").or_(pg.get_by_role("button", name="核准")).last
            try:
                if btn.is_visible() and btn.is_enabled():
                    btn.click()
                    print("[Approve] 已自動點擊「核准」(30 點)！")
                    approved = True
                    break
            except Exception:
                pass
        if not approved:
            print("[Note] 未自動偵測到核准鈕，請於右側 Flow 面板手動確認。")
        time.sleep(4)
        work_dir = OUT_DIR / "_work"
        work_dir.mkdir(parents=True, exist_ok=True)
        shot_path = work_dir / "flow_outbound_status.png"
        pg.screenshot(path=str(shot_path))
        print(f"[Done] 已保存 Flow 狀態截圖：{shot_path}")


if __name__ == "__main__":
    main()
