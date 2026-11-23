#!/usr/bin/env python3
"""
Generate Word manual (鴻勝產銷動態計畫系統_操作手冊.docx) using python-docx.
"""
from __future__ import annotations

import os
from pathlib import Path
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE_DIR = Path(__file__).resolve().parent
OUT_DOCX = BASE_DIR / "鴻勝產銷動態計畫系統_操作手冊.docx"


def set_cell_bg(cell, hex_color: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_east_asian_font(run, font_name="Microsoft JhengHei", size=11, bold=False, color=None):
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font_name)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_heading_tw(doc: Document, text: str, level: int = 1):
    p = doc.add_heading("", level=level)
    run = p.add_run(text)
    size = 18 if level == 1 else (14 if level == 2 else 12)
    color = (15, 23, 42) if level <= 2 else (37, 99, 235)
    set_east_asian_font(run, size=size, bold=True, color=color)
    return p


def add_para_tw(doc: Document, text: str, bold=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    set_east_asian_font(run, size=10.5, bold=bold, color=(30, 41, 59))
    return p


def add_styled_table(doc: Document, headers: list[str], rows: list[list[str]]):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = "Table Grid"
    for c_idx, h in enumerate(headers):
        cell = table.rows[0].cells[c_idx]
        set_cell_bg(cell, "1E293B")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        set_east_asian_font(r, size=10, bold=True, color=(255, 255, 255))
    for r_idx, row_vals in enumerate(rows):
        row_cells = table.rows[r_idx + 1].cells
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_vals):
            cell = row_cells[c_idx]
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            set_east_asian_font(r, size=9.5, color=(15, 23, 42))
    doc.add_paragraph()


def build():
    doc = Document()
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tr = title_p.add_run("鴻勝產銷動態計畫系統\n線上協作與公式報表整合操作手冊")
    set_east_asian_font(tr, size=20, bold=True, color=(15, 23, 42))

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sr = sub_p.add_run("適用版本：v1.0.0（三軌架構：雲端 D1 + PWA 離線版 + 單機網頁版）")
    set_east_asian_font(sr, size=10.5, color=(71, 85, 105))
    doc.add_paragraph()

    add_heading_tw(doc, "一、系統設計目標與舊版 Excel 問題根治", 1)
    add_para_tw(
        doc,
        "本系統將原有六工作表結構之《產銷計畫 Excel》轉化為多人可直接於瀏覽器即時編輯的線上協作平台，"
        "並徹底解決原檔與早期原型程式五大痛點："
    )
    add_styled_table(
        doc,
        ["原 Excel / 舊程式問題", "本系統解決方案"],
        [
            ["產銷總表出現 #REF! 與刪除列造成的斷鏈", "取消手動複製貼上，由計算引擎依品項 ID 即時演算並於匯出時動態重建跨表 SUMIF 公式"],
            ["初餾產銷「代工入庫(+)」被 -SUM(H:J) 誤減", "將代工入庫獨立為正向加法 (+ contractIn)，完全符合實際庫存邏輯"],
            ["調配產銷 ACT790 七月 SUM(K:L) 錯位 / 1PG-GB 漏公式", "統一由純 JS 計算引擎與潔淨 Excel 匯出模組處理各月結存與 BOM 展開，杜絕漏格錯欄"],
            ["臨時停車 1~2 天想微調用量卻要重拆排程", "保留所有 BOM 自動計算欄位，並提供一鍵「✍️ 覆寫本月總耗用」與「↺ 還原公式」功能"],
            ["舊原型機匯出 12,276 列冗餘日報且單機無同步", "改採 7 工作表潔淨公式報表，搭配 Cloudflare D1 樂觀鎖多人協作與歷史快照存檔"]
        ],
    )

    add_heading_tw(doc, "二、三種啟動與作業方式", 1)
    add_styled_table(
        doc,
        ["使用情境", "開啟位置 / 方式", "說明"],
        [
            ["公司團隊多人即時協作（推薦）", "https://sales-planner-pwa.pages.dev", "資料儲存於 Cloudflare D1，支援多人衝突比對、歷史快照與斷網離線補傳"],
            ["本機 / 區網伺服器模式", "執行 2_PWA_App版\\啟動PWA本機測試.bat", "啟動本機 FastAPI + SQLite（預設 Port 8005，佔用自動順延）並顯示區網 IP"],
            ["無網路單機臨時開啟", "雙擊 1_Web_網頁版\\index.html", "免後端直接開啟，可匯入/編輯/匯出 Excel，資料暫存瀏覽器本機"]
        ],
    )

    add_heading_tw(doc, "三、日常線上編修標準流程", 1)
    steps = [
        "1. 設定操作人員：進入系統後於上方工具列輸入姓名或課別，後續存檔與異動紀錄皆會自動留存署名。",
        "2. 匯入新月份 Excel（選用）：點擊「📥 匯入 Excel」，選擇最新月份產銷計畫 .xlsx 即可自動解析全廠品項與 73 條秏料公式。",
        "3. 滾動推算基準月份（選用）：於上方「📅 基準日」挑選新起始日並點「套用」，系統自動推算連續四個月份標題與天數。",
        "4. 即時修改庫存與銷售排產：切換「📊 產銷總表」或「精餾／初餾／調配」分頁，直接在黃底數字格輸入資材庫存、銷售、進貨或排產量，全廠關聯品項（如 EGUPS、IPA、GB-014→IPAIF/ACTIF）將毫秒級連動重算。",
        "5. 短期單月用量覆寫（✍️ / ↺）：對於有 BOM 自動展開的品項（藍底數字），點擊右側「✍️」即可改寫單月總耗用（例如因應短期停車微調），隨時點「↺」還原回 BOM 公式。",
        "6. 產線排程甘特圖：切至「📅 產線排程與甘特圖」檢視 1~31 日 S01/S02/S03/R01/R02 重疊警告與 NMPUPS 須避開 IPAUPS/EGUPS 提醒，點擊格位可直接用「天數 × 日產能」換算。",
        "7. 雲端快照與匯出報表：關鍵調度前後可點「📸 歷史快照」建立命名備份（刪除需密碼 8888）；定版後點擊「📤 匯出公式 Excel」下載潔淨 7 分頁含公式 .xlsx 檔案。"
    ]
    for st in steps:
        add_para_tw(doc, st)

    doc.save(str(OUT_DOCX))
    print(f"Generated Word manual: {OUT_DOCX}")


if __name__ == "__main__":
    build()
