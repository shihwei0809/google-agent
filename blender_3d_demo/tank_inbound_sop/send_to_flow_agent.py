"""
透過本機 Chrome (CDP Port 9222) 直接對 Google Flow Agent 面板送出
第 1 部《儲槽進貨與卸料篇》3 張真人首幀 + 批次生成指令（Omni 1.2 Flash / 360p / 10s / x1）
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

import sys
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
import auto_upload_flow as f

PROJECT_URL = "https://flow.google.com/project/90188ed6-68b8-4a67-93d7-25870ae5713e"
FRAMES_DIR = BASE_DIR / "tank_inbound_sop" / "flow_frames"
WORK_DIR = BASE_DIR / "tank_inbound_sop" / "_work"

FRAMES = [
    FRAMES_DIR / "b01_intro_first.png",
    FRAMES_DIR / "b02_bridge_first.png",
    FRAMES_DIR / "b03_outro_first.png",
]

AGENT_PROMPT = """請使用我剛剛上傳的這 3 張現場照片作為各段影片的首幀（嚴格延續畫面中同一位穿戴亮黃色安全帽、透明護目鏡、深藍防靜電工作服與螢光黃反光背心的台灣男性現場操作員外觀與寫實 35mm 電影風格），幫我依序生成 3 段 16:9 橫式寫實企業工安影片（模型請選 Omni 1.2 Flash、解析度 360p、每段 10 秒、每次張數 x1，畫面不要生成任何文字）：

1. 檔名 v01（以第 1 張清晨油罐槽車入廠照片為首幀，10 秒）：電影感平穩跟拍，操作員先低頭核對進貨檢點夾板並確認滅火器狀態，接著轉身以標準俐落手勢引導銀白色化學油罐槽車緩慢停妥於黃黑標線卸貨車位內，最後俯身將輪檔固定輪胎並把綠色靜電接地線夾妥於槽車接地銅柱。

2. 檔名 v02（以第 2 張正午 ISO TANK 頂部照片為首幀，10 秒）：35mm 工業電影升鏡與微推鏡，操作員穩健站立於兩公尺以上之 ISO TANK 頂部防滑走道，雙手將背負式全身安全帶的金屬大掛勾確實扣緊於上方不鏽鋼防墜桿並拉動測試確認牢靠，接著專注檢查頂部氮氣軟管接頭與閥門。

3. 檔名 v03（以第 3 張傍晚夕陽卸貨口照片為首幀，10 秒）：溫暖金橘色夕陽下的平滑橫移運鏡，操作員蹲身確認壓力表指針歸零完成洩壓後，俐落將化學品軟管蓋上保護塞頭並扣緊掛耳，起身將接地線與輪檔收納歸位，最後拿著檢點夾板站在安全黃線外微笑揮手示意放行，背景銀白色槽車緩緩駛離前往地磅。

請直接開始生成這 3 段影片。"""


def main():
    prompt_only = "--prompt-only" in sys.argv
    f.ensure_chrome_running(PROJECT_URL)
    with sync_playwright() as p:
        b = p.chromium.connect_over_cdp(f"http://127.0.0.1:{f.CDP_PORT}")
        ctx = b.contexts[0]
        pg = next((x for x in ctx.pages if "flow.google.com" in (x.url or "")), None) or ctx.pages[0]
        if PROJECT_URL not in (pg.url or ""):
            pg.goto(PROJECT_URL, wait_until="domcontentloaded")
        pg.bring_to_front()
        time.sleep(2)

        if not prompt_only:
            # 1. 上傳 3 張首幀至專案（優先找隱藏 input[type=file]，否則點上方「新增媒體選單」上傳）
            file_inputs = pg.locator('input[type="file"]')
            if file_inputs.count() > 0:
                print(f"[Upload] 偵測到 {file_inputs.count()} 個 file input，直接批次上傳 3 張首幀...")
                file_inputs.first.set_input_files([str(x) for x in FRAMES])
                time.sleep(5)
            else:
                print("[Upload] 點擊上方「新增媒體選單」...")
                pg.locator('button[aria-label="新增媒體選單"]').first.click()
                time.sleep(1.5)
                file_inputs = pg.locator('input[type="file"]')
                if file_inputs.count() > 0:
                    file_inputs.first.set_input_files([str(x) for x in FRAMES])
                    time.sleep(5)
                else:
                    up_btn = pg.get_by_text("上傳", exact=False).first
                    with pg.expect_file_chooser(timeout=6000) as fc_info:
                        up_btn.click()
                    fc_info.value.set_files([str(x) for x in FRAMES])
                    time.sleep(6)
            pg.screenshot(path=str(WORK_DIR / "flow_after_upload.png"))

        # 2. 填入 Agent Prompt（排除隱藏的 g-recaptcha-response）
        box = pg.locator('[contenteditable="true"], textarea:not([name="g-recaptcha-response"])').locator("visible=true").last
        box.click()
        pg.keyboard.insert_text(AGENT_PROMPT)
        time.sleep(1.5)
        pg.screenshot(path=str(WORK_DIR / "flow_agent_before_send.png"))

        # 3. 點擊開始生成
        send_btn = pg.locator('button[aria-label="開始生成"]').first
        send_btn.click()
        print("[Send] 已送出 Agent 生成指令！")
        time.sleep(8)
        pg.screenshot(path=str(WORK_DIR / "flow_agent_after_send.png"))
        print("[Done] 已截圖存於 flow_agent_after_send.png，請在 Chrome 查看 Flow Agent 生成進度。")


if __name__ == "__main__":
    main()
