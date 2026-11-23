"""
階段 1（0 點數免扣點）：透過本機 Chrome CDP 在 Google Flow 專案中生成並固定
2 張主角三視圖定妝照圖片（全程滿配 PPE，嚴禁生成影片）。
"""

import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import auto_upload_flow as f

PROJECT_URL = "https://flow.google.com/project/90188ed6-68b8-4a67-93d7-25870ae5713e"
WORK_DIR = BASE_DIR / "tank_inbound_sop" / "_work"
STATUS_PNG = WORK_DIR / "flow_character_sheets_status.png"

CHARACTER_SHEET_PROMPT = """【僅生成 2 張靜態角色定妝照圖片，嚴禁生成影片、嚴禁消耗影片點數！】
請先幫我建立以下 2 張 16:9 橫式寫實企業工安主角「人物模板定妝照（概念藝術圖片）」，用來鎖定後續所有分鏡的人物外觀與完整 PPE 防護裝備：

1. 檔名「定妝照_標準滿配PPE三視圖」：
   - 主角為同一位 30 歲台灣男性化工廠資材課操作員，畫面為「正面全身、側面全身、背面全身」三視圖並排（16:9 橫式，乾淨淺灰工業攝影棚背景，35mm 寫實光影，畫面中不要出現任何文字）。
   - 必須固定以下全身 PPE 穿戴（全程戴妥、不露口鼻，確保後續所有鏡頭 100% 一致）：
     (1) 亮黃色工業安全帽（黑色 Y 型下巴帶扣緊）
     (2) 透明防化學噴濺全包覆護目鏡
     (3) 雙罐式半面體化學防毒面具（緊密戴在口鼻上，絕不掛在脖子）
     (4) 深藍色長袖防靜電工作服 ＋ 螢光黃反光背心
     (5) 綠色長筒耐酸鹼橡膠防護手套（包覆袖口）
     (6) 黑色鋼頭安全鞋

2. 檔名「定妝照_拆管圍裙與高處安全帶三視圖」：
   - 嚴格延續第 1 張完全相同的人物外觀，頭戴亮黃色安全帽（扣緊下巴帶）、透明防化學護目鏡、口鼻緊密戴妥雙罐防毒面具、深藍色防靜電工作服、螢光黃反光背心與綠色長筒耐化手套。
   - 展示兩種作業加掛裝備之並排全身圖（16:9 橫式，乾淨淺灰工業攝影棚背景，無任何文字）：
     - 左側：加穿「黑色耐酸鹼 PVC 防護圍裙」（用於拆接化學管線作業）
     - 右側：加穿「背負式全身防墜安全帶與金屬雙大掛勾」（用於 ISO TANK 2 公尺高處作業）

再次確認：本次僅建立這 2 張靜態圖片模板，不要生成任何影片。"""


def main():
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    f.ensure_chrome_running(PROJECT_URL)

    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{f.CDP_PORT}")
        ctx = b.contexts[0]
        pg = next((x for x in ctx.pages if "flow.google.com" in (x.url or "")), None) or ctx.pages[0]
        if PROJECT_URL not in (pg.url or ""):
            pg.goto(PROJECT_URL, wait_until="domcontentloaded")
            time.sleep(4)
        pg.bring_to_front()

        if "accounts.google.com" in (pg.url or ""):
            print("[Error] Google Flow 要求重新登入，請先在 Chrome 完成登入。")
            pg.screenshot(path=str(STATUS_PNG))
            sys.exit(2)

        # 記錄原本頁面上的圖片數量，方便判斷新圖片是否生成
        before_imgs = pg.locator("img").count()

        # 填入純生圖定妝照 Prompt
        box = pg.locator('[contenteditable="true"], textarea:not([name="g-recaptcha-response"])').locator("visible=true").last
        box.wait_for(state="visible", timeout=15000)
        box.click()
        pg.keyboard.press("Control+A")
        pg.keyboard.press("Backspace")
        pg.keyboard.insert_text(CHARACTER_SHEET_PROMPT)
        time.sleep(1.0)

        send_btn = pg.locator('button[aria-label="開始生成"]').first
        send_btn.wait_for(state="visible", timeout=10000)
        send_btn.click()
        print("[Send] 已送出 2 張主角定妝照（0 點數純生圖）指令至 Flow Agent...")

        # 輪詢最多 120 秒等待完成，並監看是否誤跳影片扣點確認
        deadline = time.time() + 120
        rejected_video = False
        while time.time() < deadline:
            time.sleep(2.0)

            # 檢查是否有授權選項出現
            approve_btn = pg.get_by_role("radio", name="核准").or_(pg.get_by_role("button", name="核准")).last
            reject_btn = pg.get_by_role("radio", name="拒絕").or_(pg.get_by_role("button", name="拒絕")).last
            try:
                if approve_btn.is_visible() and approve_btn.is_enabled():
                    panel_text = pg.locator("body").inner_text()
                    # 若對話最後段明確要求扣除影片點數，立即拒絕
                    tail_text = panel_text[-600:]
                    if ("消耗" in tail_text and "點" in tail_text) or ("影片" in tail_text and "要開始生成" in tail_text):
                        print("[Guard] 偵測到 Flow Agent 誤將指令當成扣點影片生成，立即點擊「拒絕」！")
                        if reject_btn.is_visible() and reject_btn.is_enabled():
                            reject_btn.click()
                        rejected_video = True
                        break
                    else:
                        print("[Confirm] 偵測到非扣點工具呼叫確認，點擊「核准」...")
                        approve_btn.click()
            except Exception:
                pass

            # 檢查「停止」按鈕是否還在（表示 Agent 還在工作）
            stop_btn = pg.locator('button[aria-label="停止"], button:has-text("停止")')
            is_running = False
            try:
                for i in range(stop_btn.count()):
                    if stop_btn.nth(i).is_visible():
                        is_running = True
                        break
            except Exception:
                pass

            after_imgs = pg.locator("img").count()
            if not is_running and time.time() > (deadline - 110):
                # Agent 回應已結束，再多等 3 秒讓圖片縮圖渲染
                time.sleep(3.0)
                after_imgs = pg.locator("img").count()
                print(f"[Done] Agent 已完成回應，頁面圖片數量：{before_imgs} -> {after_imgs}")
                break

        pg.screenshot(path=str(STATUS_PNG))
        print(f"[Screenshot] 已儲存狀態截圖：{STATUS_PNG}")
        if rejected_video:
            sys.exit(3)


if __name__ == "__main__":
    main()
