import os
import sys

try:
    from docx import Document
    from docx.shared import Pt, RGBColor
except ImportError:
    print("[錯誤] 缺少 python-docx，請執行：pip install python-docx")
    sys.exit(1)


def build_manual():
    doc = Document()
    title = doc.add_heading("資材辦公室 2D/3D 互動平面配置工具 操作手冊", level=0)
    for run in title.runs:
        run.font.color.rgb = RGBColor(0x10, 0xB9, 0x81)

    doc.add_paragraph("用途：2027 年資材辦公室空間不足改善規劃（現況與提案視覺化模擬）。")

    sections = [
        ("一、快速開啟", [
            "雙擊「點我開啟資材辦公室2D3D配置工具.bat」或直接開啟 1_Web_網頁版/index.html，無需安裝任何軟體即可在瀏覽器使用。"
        ]),
        ("二、操作方式", [
            "1. 檢視切換：上方工具列可切換「純 2D」、「2D + 3D 同屏」、「純 3D」。",
            "2. 拖拉與旋轉：在 2D 畫面點擊任一桌櫃即可拖拉移動（支援 5cm 吸附），按鍵盤 R 鍵或右側「旋轉 90°」按鈕即可轉向。",
            "3. 3D 視角操作：於 3D 畫面左鍵拖拉旋轉視角、右鍵平移、滾輪縮放，即時觀察 280cm 高櫃與走道空間感。",
            "4. 碰撞偵測：若桌櫃超出刀把形牆面、撞到結構柱或互相重疊，會自動以紅框警示。",
            "5. 方案切換與匯出：左側可一鍵切換「現況配置」、「2027 改善提案 A / B」，並可匯出高清 2D 平面圖 (.png) 貼入簡報，或匯出/匯入 JSON 保存多個版本。"
        ])
    ]
    for h, items in sections:
        doc.add_heading(h, level=1)
        for t in items:
            p = doc.add_paragraph(t)
            p.paragraph_format.space_after = Pt(4)

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "資材辦公室平面配置工具_操作手冊.docx")
    doc.save(out)
    print(f"[完成] 已產出操作手冊：{out}")


if __name__ == "__main__":
    build_manual()
