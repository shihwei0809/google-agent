"""
自動生成《Blender_3D_AI建模與白模運鏡系統_操作手冊.docx》與嘗試轉出 PDF
"""

from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
OUT_DOCX = ROOT / "Blender_3D_AI建模與白模運鏡系統_操作手冊.docx"


def add_image_if_exists(doc: Document, filename: str, caption: str, width_in: float = 5.6):
    img_path = ROOT / filename
    if img_path.exists():
        p_cap = doc.add_paragraph()
        run_cap = p_cap.add_run(caption)
        run_cap.bold = True
        run_cap.font.size = Pt(10)
        run_cap.font.color.rgb = RGBColor(51, 65, 85)
        doc.add_picture(str(img_path), width=Inches(width_in))


def build_manual():
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Microsoft JhengHei"
    style.font.size = Pt(11)

    title = doc.add_heading("Blender 3D AI 自動建模與 FPV 白模運鏡系統 — 操作手冊", level=0)
    title.runs[0].font.color.rgb = RGBColor(15, 23, 42)

    doc.add_paragraph(
        "本專案專為無獨立顯卡筆電（如 Intel Iris Xe 內顯）打造，整合 Blender 5.3、"
        "Antigravity MCP 即時遙控、Three.js 互動式 3D 數位孿生看板，以及針對 AI 影片生成"
        "（Google Flow / Seedance / 可靈 Kling）設計的 3D 白模 (Previs) 運鏡管線。"
    )

    doc.add_heading("一、快速啟動網頁 3D 雙看板", level=1)
    for step in [
        "1. 新電腦首次使用請先執行 setup_env.ps1（自動檢查並安裝 python-docx、uv、Blender 與 MCP 外掛）。",
        "2. 雙擊專案資料夾內的「啟動3D儲位展示.bat」。",
        "3. 終端機會自動檢查可用 Port（預設 8088，被佔用自動順延），並顯示本機網址與手機區網網址。",
        "4. 瀏覽器自動開啟「3D 智慧儲位看板 (index.html)」，點擊左下角「前往 FPV 白模運鏡工作室」可切換至 fpv_studio.html。",
    ]:
        doc.add_paragraph(step)

    doc.add_heading("二、使用 Antigravity 中文遙控 Blender 即時建模", level=1)
    for step in [
        "1. 確認 C:\\Users\\<使用者>\\.gemini\\config\\mcp_config.json 已設定 blender MCP（command 指向 uvx.exe）。",
        "2. 用 Blender 開啟 warehouse_scene.blend 或 fpv_white_model.blend。",
        "3. 在 3D 視窗按鍵盤 N 鍵展開右側欄 → 切換到「MCP for Blender」分頁 → 點擊「Connect to MCP server」。",
        "4. 回到 Antigravity 對話框用中文下指令（例如新增貨架、調整燈光、重新匯出 .glb），Blender 畫面會即時同步變化。",
    ]:
        doc.add_paragraph(step)

    doc.add_heading("三、AI 影片救星：3D 白模 (Previs) FPV 運鏡工作流", level=1)
    doc.add_paragraph(
        "純文字提示詞難以控制複雜的穿越與俯衝運鏡。透過 Blender Workbench 白模引擎（免獨顯、約 20 秒內"
        "即可算完 120 格 1280×720 影片），可先生成精準的白模運鏡影片 (fpv_white_model.mp4) 與首尾白模關鍵幀："
    )
    add_image_if_exists(doc, "fpv_first_frame.png", "圖 1：Blender 白模首幀 (fpv_first_frame.png) — 高空俯衝起點")
    add_image_if_exists(doc, "fpv_last_frame.png", "圖 2：Blender 白模尾幀 (fpv_last_frame.png) — 急煞主角特寫")

    doc.add_heading("四、Google Flow (Frames to Video) 與 AI 影片實戰對接", level=1)
    for step in [
        "1. 先將白模首尾兩張圖轉換為目標美術風格（賽博龐克、奇幻武俠或兒童卡通版），維持完全一致的透視構圖。",
        "2. 打開 Google Flow (https://flow.google.com) 並切換為「影片 -> 影格 (Frames to Video)」模式。",
        "3. 免 API Key 一鍵自動上傳：雙擊「一鍵自動上傳Google_Flow.bat」（或於 fpv_studio.html 點擊「一鍵自動送進 Flow」），"
        "系統會透過本機 Chrome (Port 9222) 自動上傳首尾幀並填入 Prompt，直接使用你的 PRO / 免費點數生成。",
        "4. 若使用 Seedance 2.0 / 可靈 Kling / Runway，則改用「影片參考 (Motion Reference)」模式，同時上傳「風格首幀圖」與「fpv_white_model.mp4」。",
    ]:
        doc.add_paragraph(step)

    add_image_if_exists(doc, "cyberpunk_first_frame.png", "圖 3：賽博龐克首幀 (cyberpunk_first_frame.png)")
    add_image_if_exists(doc, "cyberpunk_last_frame.png", "圖 4：賽博龐克尾幀 (cyberpunk_last_frame.png)")
    add_image_if_exists(doc, "wuxia_first_frame.png", "圖 5：奇幻武俠首幀 (wuxia_first_frame.png)")
    add_image_if_exists(doc, "wuxia_last_frame.png", "圖 6：奇幻武俠尾幀 (wuxia_last_frame.png)")
    add_image_if_exists(doc, "kids_first_frame.png", "圖 7：兒童卡通版首幀 (kids_first_frame.png)")
    add_image_if_exists(doc, "kids_last_frame.png", "圖 8：兒童卡通版尾幀 (kids_last_frame.png)")

    doc.save(str(OUT_DOCX))
    print(f"已產出 Word 操作手冊: {OUT_DOCX}")

    try:
        from docx2pdf import convert
        out_pdf = OUT_DOCX.with_suffix(".pdf")
        convert(str(OUT_DOCX), str(out_pdf))
        print(f"已產出 PDF 操作手冊: {out_pdf}")
    except Exception as e:
        print(f"[提示] 略過 PDF 轉檔（未安裝 docx2pdf 或 Word COM 不可用）: {e}")


if __name__ == "__main__":
    build_manual()
