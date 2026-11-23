"""透過本機 Chrome CDP 上傳 v2 修正版 2 張首幀至專案並送出 2 段生成（20 點）"""
import sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import auto_upload_flow as f

PROJECT_URL = "https://flow.google.com/project/90188ed6-68b8-4a67-93d7-25870ae5713e"
FRAMES = [
    BASE_DIR / "tank_inbound_sop" / "flow_frames" / "b01_intro_v2.png",
    BASE_DIR / "tank_inbound_sop" / "flow_frames" / "b03_outro_v2.png",
]
PROMPT = (
    "請只針對我剛剛最新上傳的這 2 張圖片（b01_intro_v2.png 與 b03_outro_v2.png），"
    "使用 Omni 1.2 Flash、360p、10 秒、各 1 部生成 2 段 16:9 寫實企業工安影片（共 20 點，不要生成文字）：\n"
    "1. v01_v2（以最新清晨油罐槽車與柱上接地捲盤照片 b01_intro_v2.png 為首幀，10 秒）：35mm 紀錄片風格平穩跟拍，"
    "操作員先低頭核對檢點夾板，接著巡視輪檔、滅火器與柱上接地捲盤連至槽車底盤的靜電接地線，確認安全無誤後點頭示意。\n"
    "2. v03_v2（以最新滿配雙罐防毒面具與黑色耐酸鹼圍裙拆管照片 b03_outro_v2.png 為首幀，10 秒）：溫暖夕陽 35mm 平滑橫移運鏡，"
    "戴著防毒面具、護目鏡、黑圍裙與綠長手套的操作員先確認壓力表指針歸零，雙手穩妥鎖緊不鏽鋼快速接頭保護蓋，"
    "接著起身環視潔淨無滴漏的卸貨區並向遠方槽車點頭示意放行。\n請立即送出 20 點授權讓我核准。"
)

def main():
    f.ensure_chrome_running(PROJECT_URL)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{f.CDP_PORT}")
        ctx = b.contexts[0]
        pg = next((x for x in ctx.pages if "flow.google.com" in (x.url or "")), None) or ctx.pages[0]
        if PROJECT_URL not in (pg.url or ""):
            pg.goto(PROJECT_URL, wait_until="domcontentloaded")
        time.sleep(3)

        # 上傳 2 張 v2 首幀
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
        print("[Upload] 已上傳 b01_intro_v2.png & b03_outro_v2.png，等待 8 秒完成同步...")
        time.sleep(8)

        # 填入 Prompt 並送出
        box = pg.locator('[contenteditable="true"], textarea:not([name="g-recaptcha-response"])').locator("visible=true").last
        box.click()
        pg.keyboard.insert_text(PROMPT)
        time.sleep(1.2)
        pg.locator('button[aria-label="開始生成"]').first.click()
        print("[Send] 已送出 v2 雙鏡生成指令，等待 20 點核准按鈕出現...")

        # 自動輪詢最多 45 秒點擊「核准」
        approved = False
        for _ in range(30):
            time.sleep(1.5)
            btn = pg.get_by_role("radio", name="核准").or_(pg.get_by_role("button", name="核准")).last
            try:
                if btn.is_visible() and btn.is_enabled():
                    btn.click()
                    print("[Approve] 已自動點擊「核准」(20 點)！")
                    approved = True
                    break
            except Exception:
                pass
        if not approved:
            print("[Note] 45 秒內未見可點擊的核准鈕，請於右側 Flow 面板確認。")
        time.sleep(4)
        pg.screenshot(path=str(BASE_DIR / "tank_inbound_sop" / "_work" / "flow_v2_status.png"))

if __name__ == "__main__":
    main()
