#!/usr/bin/env python3
r"""
Deterministic extractor converting G:\我的雲端硬碟\產銷排程與原料需求\source_plan.xlsx
into 2_PWA_App版/public/seed_data.js (and mirrored tracks).
Preserves Excel opening overrides, child rollups, recovery rules, and BOM precision.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
import openpyxl

SOURCE_XLSX = r"G:\我的雲端硬碟\產銷排程與原料需求\source_plan.xlsx"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATHS = [
    os.path.join(BASE_DIR, "1_Web_網頁版", "seed_data.js"),
    os.path.join(BASE_DIR, "2_PWA_App版", "public", "seed_data.js"),
    os.path.join(BASE_DIR, "3_Cloudflare_D1版", "public", "seed_data.js"),
]


def fnum(val, default=0.0):
    if val is None or isinstance(val, bool):
        return default
    if isinstance(val, (int, float)):
        return round(float(val), 6)
    try:
        return round(float(str(val).strip()), 6)
    except Exception:
        return default


def fstr(val):
    if val is None:
        return ""
    s = str(val).strip()
    if s in ("0", "0.0"):
        return ""
    return s


def fmt_date(val):
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d")
    s = str(val or "").strip()
    return s[:10] if len(s) >= 10 else s


def is_formula(val):
    return isinstance(val, str) and val.startswith("=")


def parse_sheet_items():
    wb_v = openpyxl.load_workbook(SOURCE_XLSX, data_only=True)
    wb_f = openpyxl.load_workbook(SOURCE_XLSX, data_only=False)

    # 1) BOM rules from 秏料
    ws_bom_v = wb_v["秏料"]
    ws_bom_f = wb_f["秏料"]
    bom_rules = []
    seen_bom = set()
    for r in range(3, ws_bom_v.max_row + 1):
        prod = fstr(ws_bom_v.cell(r, 1).value)
        raw = fstr(ws_bom_v.cell(r, 2).value)
        if not prod or not raw:
            continue
        if fstr(ws_bom_v.cell(r, 4).value) == "%":
            continue
        y_val = fnum(ws_bom_v.cell(r, 3).value, None)
        ratio_val = fnum(ws_bom_v.cell(r, 4).value, None)
        if y_val is None or ratio_val is None:
            continue
        # Detect decimal precision from col 6/8/10/12 formula (ROUND(...,3) vs ROUND(...,0))
        dec = 0
        for fc in (6, 8, 10, 12):
            fml = str(ws_bom_f.cell(r, fc).value or "")
            if ",3)" in fml:
                dec = 3
                break
        key = (prod, raw)
        if key in seen_bom:
            continue
        seen_bom.add(key)
        bom_rules.append({
            "id": f"bom_{len(bom_rules)+1}",
            "product": prod,
            "rawMaterial": raw,
            "yieldRate": y_val,
            "ratio": ratio_val,
            "roundingDecimals": dec,
            "active": True,
            "sourceRow": r,
            "note": ""
        })

    items = []

    def build_item(
        ws_v, ws_f, r, kind, process, section, cols_cfg,
        override_name=None, rollup_to=None, rollup_months=None,
        adj_balance=None, adj_notes=None, expected_ending=None,
        show_in_summary=None
    ):
        name = override_name or fstr(ws_v.cell(r, 1).value)
        if not name:
            return None
        tanks = fstr(ws_v.cell(r, 2).value)
        capacity = fnum(ws_v.cell(r, 3).value, 0.0)
        inv_mat = fnum(ws_v.cell(r, 4).value, 0.0)
        inv_p2 = fnum(ws_v.cell(r, 5).value, 0.0)
        tank_bottom = fnum(ws_v.cell(r, 6).value, 0.0)
        g_val = fnum(ws_v.cell(r, 7).value, 0.0)
        g_fml = ws_f.cell(r, 7).value
        calc_open = max(0.0, round(inv_mat + inv_p2 - tank_bottom, 6))
        opening_override = None
        if not is_formula(g_fml) and abs(g_val - calc_open) > 1e-4:
            opening_override = g_val
        elif is_formula(g_fml) and abs(g_val - calc_open) > 1e-4:
            # e.g., =IF(+E13-F13<=0,0,+E13-F13) missing D, still expose cleanly
            opening_override = g_val

        safety_max = fnum(ws_v.cell(r, cols_cfg["safetyMax"]).value, None) if cols_cfg.get("safetyMax") else None
        safety_min = fnum(ws_v.cell(r, cols_cfg["safetyMin"]).value, None) if cols_cfg.get("safetyMin") else None
        if safety_max == 0:
            safety_max = None
        if safety_min == 0:
            safety_min = None

        months = []
        for mi in range(4):
            m_cfg = cols_cfg["months"][mi]
            sales = fnum(ws_v.cell(r, m_cfg["sales"]).value, 0.0) if m_cfg.get("sales") else 0.0
            contract_in = fnum(ws_v.cell(r, m_cfg["contractIn"]).value, 0.0) if m_cfg.get("contractIn") else 0.0

            # Usage handling: Distinguish SUMIF BOM vs manual directUsage
            direct_usage = 0.0
            raw_consume_val = 0.0
            u_col = m_cfg.get("usage")
            if u_col:
                u_fml = ws_f.cell(r, u_col).value
                u_val = fnum(ws_v.cell(r, u_col).value, 0.0)
                if not is_formula(u_fml) or ("秏料" not in str(u_fml)):
                    direct_usage = u_val

            rc_col = m_cfg.get("rawConsume")
            if rc_col:
                rc_fml = ws_f.cell(r, rc_col).value
                rc_val = fnum(ws_v.cell(r, rc_col).value, 0.0)
                raw_consume_val = rc_val

            purchase = fnum(ws_v.cell(r, m_cfg["purchase"]).value, 0.0) if m_cfg.get("purchase") else 0.0
            other_in = 0.0
            if m_cfg.get("otherIn"):
                oi_fml = ws_f.cell(r, m_cfg["otherIn"]).value
                oi_val = fnum(ws_v.cell(r, m_cfg["otherIn"]).value, 0.0)
                if not is_formula(oi_fml):
                    other_in = oi_val

            line = fstr(ws_v.cell(r, m_cfg["line"]).value) if m_cfg.get("line") else ""
            period_str = fstr(ws_v.cell(r, m_cfg["period"]).value) if m_cfg.get("period") else ""
            prod_qty = fnum(ws_v.cell(r, m_cfg["prodQty"]).value, 0.0) if m_cfg.get("prodQty") else 0.0
            prod_fml = ws_f.cell(r, m_cfg["prodQty"]).value if m_cfg.get("prodQty") else None
            prod_mode = "sales_plus_usage" if (kind == "filling" and is_formula(prod_fml) and "+" in str(prod_fml)) else "manual"
            if kind == "filling" and prod_mode == "sales_plus_usage":
                # Keep prod_qty as computed baseline too
                pass

            end_col = m_cfg.get("endStock")
            excel_end = fnum(ws_v.cell(r, end_col).value, None) if end_col else None

            months.append({
                "sales": sales,
                "contractIn": contract_in,
                "directUsage": direct_usage,
                "usageOverride": None,
                "purchase": purchase,
                "otherIn": other_in,
                "otherInOverride": None,
                "adjBalance": (adj_balance[mi] if adj_balance else 0.0),
                "adjNote": (adj_notes[mi] if adj_notes else ""),
                "line": line,
                "periodStr": period_str,
                "prodQty": prod_qty,
                "prodFormulaMode": prod_mode,
                "dailyRate": None,
                "_excelEndStock": excel_end,
            })

        non_zero = (
            inv_mat != 0 or inv_p2 != 0 or g_val != 0 or
            any(m["sales"] != 0 or m["contractIn"] != 0 or m["directUsage"] != 0 or m["purchase"] != 0 or m["otherIn"] != 0 or m["prodQty"] != 0 for m in months)
        )
        return {
            "id": f"{kind}_{process}_{len(items)+1}_{name}",
            "name": name,
            "kind": kind,
            "process": process,
            "section": section,
            "sourceSheet": ws_v.title,
            "sourceRow": r,
            "tanks": tanks,
            "capacity": capacity,
            "invMaterial": inv_mat,
            "invProcess2": inv_p2,
            "tankBottom": tank_bottom,
            "openingOverride": opening_override,
            "safetyMax": safety_max,
            "safetyMin": safety_min,
            "rollupTo": rollup_to,
            "rollupMonths": rollup_months or ([True, True, True, True] if rollup_to else [False, False, False, False]),
            "showInSummary": show_in_summary if show_in_summary is not None else non_zero,
            "months": months,
        }

    # --- Standard Month Column Configs ---
    rect_prod_cfg = {
        "safetyMax": 33, "safetyMin": 34,
        "months": [
            {"sales": 8, "usage": 9, "line": 16, "period": 17, "prodQty": 18, "endStock": 28},
            {"sales": 10, "usage": 11, "line": 19, "period": 20, "prodQty": 21, "endStock": 29},
            {"sales": 12, "usage": 13, "line": 22, "period": 23, "prodQty": 24, "endStock": 30},
            {"sales": 14, "usage": 15, "line": 25, "period": 26, "prodQty": 27, "endStock": 31},
        ]
    }
    rect_raw_cfg = {
        "safetyMax": 33, "safetyMin": 34,
        "months": [
            {"sales": 8, "usage": 9, "rawConsume": 16, "purchase": 20, "otherIn": 24, "endStock": 28},
            {"sales": 10, "usage": 11, "rawConsume": 17, "purchase": 21, "otherIn": 25, "endStock": 29},
            {"sales": 12, "usage": 13, "rawConsume": 18, "purchase": 22, "otherIn": 26, "endStock": 30},
            {"sales": 14, "usage": 15, "rawConsume": 19, "purchase": 23, "otherIn": 27, "endStock": 31},
        ]
    }
    prim_prod_cfg = {
        "safetyMax": 38, "safetyMin": None,
        "months": [
            {"sales": 8, "contractIn": 9, "usage": 10, "line": 20, "period": 21, "prodQty": 22, "endStock": 32},
            {"sales": 11, "contractIn": 12, "usage": 13, "line": 23, "period": 24, "prodQty": 25, "endStock": 33},
            {"sales": 14, "contractIn": 15, "usage": 16, "line": 26, "period": 27, "prodQty": 28, "endStock": 34},
            {"sales": 17, "contractIn": 18, "usage": 19, "line": 29, "period": 30, "prodQty": 31, "endStock": 35},
        ]
    }
    prim_raw_cfg = {
        "safetyMax": 38, "safetyMin": None,
        "months": [
            {"sales": 8, "contractIn": 9, "usage": 10, "rawConsume": 20, "purchase": 24, "otherIn": 28, "endStock": 32},
            {"sales": 11, "contractIn": 12, "usage": 13, "rawConsume": 21, "purchase": 25, "otherIn": 29, "endStock": 33},
            {"sales": 14, "contractIn": 15, "usage": 16, "rawConsume": 22, "purchase": 26, "otherIn": 30, "endStock": 34},
            {"sales": 17, "contractIn": 18, "usage": 19, "rawConsume": 23, "purchase": 27, "otherIn": 31, "endStock": 35},
        ]
    }
    blend_prod_cfg = {
        "safetyMax": 34, "safetyMin": 35,
        "months": [
            {"sales": 8, "usage": 9, "line": 16, "period": 17, "prodQty": 18, "endStock": 28},
            {"sales": 10, "usage": 11, "line": 19, "period": 20, "prodQty": 21, "endStock": 29},
            {"sales": 12, "usage": 13, "line": 22, "period": 23, "prodQty": 24, "endStock": 30},
            {"sales": 14, "usage": 15, "line": 25, "period": 26, "prodQty": 27, "endStock": 31},
        ]
    }
    blend_raw_cfg = {
        "safetyMax": 34, "safetyMin": 35,
        "months": [
            {"sales": 8, "usage": 9, "rawConsume": 16, "purchase": 20, "otherIn": 24, "endStock": 28},
            {"sales": 10, "usage": 11, "rawConsume": 17, "purchase": 21, "otherIn": 25, "endStock": 29},
            {"sales": 12, "usage": 13, "rawConsume": 18, "purchase": 22, "otherIn": 26, "endStock": 30},
            {"sales": 14, "usage": 15, "rawConsume": 19, "purchase": 23, "otherIn": 27, "endStock": 31},
        ]
    }

    # --- Sheet 1: 精餾產銷 ---
    ws_rv, ws_rf = wb_v["精餾產銷"], wb_f["精餾產銷"]
    rect_child_parent = {
        7: ("IPAUPS(預備行)", None, [False, False, False, False]),
        8: ("IPAUPS(崙尾區日本料)", None, [False, False, False, False]),
        9: ("IPAUPS(崙尾區LG)", "IPAUPS", [True, False, False, False]),  # May Excel R5 sums R5:R9!
        12: ("EGUPS(勝一S07)", "EGUPS", [True, True, True, True]),         # Excel R11 sums R11:R12
        18: ("ACTUPS(外購)", "ACTUPS", [True, True, True, True]),          # Excel R17 sums R17:R18
        20: ("NMPUPS(外購)", "NMPUPS", [True, True, True, True]),          # Excel R19 sums R19:R20
        27: ("2DPM-1(委外加工)", "2DPM-1", [True, True, True, True]),      # Excel R26 sums R26:R27
        30: ("NMP-3(外購)", "NMP-3", [True, True, True, True]),            # Excel R29 sums R29:R30
    }
    for r in range(5, 35):
        name = fstr(ws_rv.cell(r, 1).value)
        if not name:
            continue
        ov_name, r_to, r_mo = rect_child_parent.get(r, (None, None, None))
        adj_b = None
        adj_n = None
        if r == 5:  # IPAUPS has manual +80 in May formula
            adj_b = [80.0, 0.0, 0.0, 0.0]
            adj_n = ["原Excel 5月庫存公式含手動調整 (+80)", "", "", ""]
        elif r == 24:  # CPNE3-R has manual deduction in Jun/Jul/Aug formula
            adj_b = [0.0, -429.0, -184.5, -330.0]
            adj_n = ["", "原Excel 6月公式扣減 (-U22*1.1 = -429)", "原Excel 7月公式扣減 (-X22*1.23 = -184.5)", "原Excel 8月公式扣減 (-AA22*1.1 = -330)"]
        item = build_item(
            ws_rv, ws_rf, r, "product", "精餾", "精餾成品", rect_prod_cfg,
            override_name=ov_name, rollup_to=r_to, rollup_months=r_mo,
            adj_balance=adj_b, adj_notes=adj_n
        )
        if item:
            if r == 7:  # duplicate blank IPAUPS placeholder row
                item["showInSummary"] = False
            items.append(item)

    # Filling items rows 44..51
    for r in range(44, 52):
        item = build_item(ws_rv, ws_rf, r, "filling", "精餾", "充填成品", rect_prod_cfg)
        if item:
            items.append(item)

    # Rectification Raw rows 61..81
    for r in range(61, 82):
        name = fstr(ws_rv.cell(r, 1).value)
        if not name:
            continue
        item = build_item(ws_rv, ws_rf, r, "raw", "精餾", "精餾原料", rect_raw_cfg)
        if item:
            # 1CPN & IPA otherIn formulas will be handled by recoveryRules dynamically!
            items.append(item)

    # --- Sheet 2: 初餾產銷 ---
    ws_pv, ws_pf = wb_v["初餾產銷"], wb_f["初餾產銷"]
    for r in range(5, 16):
        item = build_item(ws_pv, ws_pf, r, "product", "初餾", "初餾成品", prim_prod_cfg)
        if item:
            items.append(item)

    for r in range(36, 46):
        item = build_item(ws_pv, ws_pf, r, "raw", "初餾", "初餾原料", prim_raw_cfg)
        if item:
            items.append(item)

    # --- Sheet 3: 調配產銷 ---
    ws_bv, ws_bf = wb_v["調配產銷"], wb_f["調配產銷"]
    for r in range(6, 16):
        item = build_item(ws_bv, ws_bf, r, "product", "調配", "調配成品", blend_prod_cfg)
        if item:
            if r == 11:
                # Fix documentation note for ACT790 July where source_plan had SUM(K11:L11) typo instead of SUM(L11:M11)
                item["sourceBugNote"] = "已修正原Excel 7月期末公式錯位 SUM(K11:L11)->正確應扣7月銷售34"
            items.append(item)

    for r in range(37, 49):
        name = fstr(ws_bv.cell(r, 1).value)
        if not name or name == "EGUPS":
            # EGUPS is already in items from 精餾產銷 (linked cross-process!)
            continue
        item = build_item(ws_bv, ws_bf, r, "raw", "調配", "調配原料", blend_raw_cfg)
        if item:
            if name == "1PG-GB":
                item["sourceBugNote"] = "已修正原Excel 6~7月漏植 SUMIF(秏料) 扣減 1 MT 的公式缺失"
            items.append(item)

    # Check if ACT790 July in source_plan had typo so BOM EBR(R) rule also matches 初餾 R41
    # In 初餾 R41 EBR(R), Excel uses Y8*1.1 (38.5) while BOM R47 uses 1/0.9006782 (39)
    # Record recoveryRules + normalize BOM rules cleanly
    recovery_rules = [
        {
            "id": "rec_ipa",
            "targetRaw": "IPA",
            "sourceItem": "IPAUPS",
            "sourceField": "directUsage",
            "factor": 0.95,
            "roundingDecimals": 0,
            "active": True,
            "note": "IPAUPS 耗用 95% 回收至 IPA 原料 + 2IPA 產量"
        },
        {
            "id": "rec_2ipa",
            "targetRaw": "IPA",
            "sourceItem": "2IPA",
            "sourceField": "prodQty",
            "factor": 1.0,
            "roundingDecimals": 0,
            "active": True,
            "note": "2IPA 精餾回收產量併入 IPA 其他入庫"
        },
        {
            "id": "rec_1cpn",
            "targetRaw": "1CPN",
            "sourceItem": "CPNE4(含浸)",
            "sourceField": "totalUsage",
            "factor": 1.0,
            "roundingDecimals": 3,
            "active": True,
            "note": "CPNE4(含浸) 耗用轉入 1CPN 其他入庫"
        }
    ]

    base_dt = ws_rv.cell(3, 7).value
    base_date_str = fmt_date(base_dt) if base_dt else "2026-05-11"
    months_meta = [
        {"id": "m1", "label": "5月", "periodLabel": fstr(ws_rv.cell(3, 8).value) or "05/11~05/31", "endDate": "2026-05-31", "startDay": 11, "endDay": 31, "days": 21},
        {"id": "m2", "label": "6月", "periodLabel": "06/01~06/30", "endDate": fmt_date(ws_rv.cell(3, 10).value) or "2026-06-30", "startDay": 1, "endDay": 30, "days": 30},
        {"id": "m3", "label": "7月", "periodLabel": "07/01~07/31", "endDate": fmt_date(ws_rv.cell(3, 12).value) or "2026-07-31", "startDay": 1, "endDay": 31, "days": 31},
        {"id": "m4", "label": "8月", "periodLabel": "08/01~08/31", "endDate": fmt_date(ws_rv.cell(3, 14).value) or "2026-08-31", "startDay": 1, "endDay": 31, "days": 31},
    ]

    notes = []
    for r in range(100, 106):
        txt = fstr(ws_rv.cell(r, 7).value)
        if txt:
            notes.append(txt)

    plan = {
        "schemaVersion": "1.0.0",
        "meta": {
            "title": "2026年5月~8月 鴻勝產銷動態計畫",
            "baseDate": base_date_str,
            "sourceFile": "source_plan.xlsx (20260511產銷計畫)",
            "months": months_meta,
            "notes": notes,
            "ebrRUseFixed110": True,  # Match 初餾產銷!R41 =EBR95*1.1 (38.5) by default while showing BOM 秏料 R47 option
        },
        "lines": [
            {"id": "S01", "process": "精餾", "name": "S01 (精餾一線)", "conflictsWith": []},
            {"id": "S02", "process": "精餾", "name": "S02 (精餾二線)", "conflictsWith": []},
            {"id": "S03", "process": "精餾", "name": "S03 (精餾三線)", "conflictsWith": []},
            {"id": "S01+S02", "process": "精餾", "name": "S01+S02 (雙線併用)", "conflictsWith": []},
            {"id": "S02+S01", "process": "精餾", "name": "S02+S01 (雙線併用)", "conflictsWith": []},
            {"id": "S07", "process": "精餾", "name": "勝一 S07", "conflictsWith": []},
            {"id": "充填", "process": "精餾", "name": "充填線", "conflictsWith": []},
            {"id": "外購", "process": "精餾", "name": "外購/進貨", "conflictsWith": []},
            {"id": "委外加工", "process": "精餾", "name": "委外加工", "conflictsWith": []},
            {"id": "R01", "process": "初餾", "name": "R01 (初餾一線)", "conflictsWith": []},
            {"id": "R02", "process": "初餾", "name": "R02 (初餾二線)", "conflictsWith": []},
            {"id": "參配", "process": "調配", "name": "參配調配線", "conflictsWith": []},
        ],
        "items": items,
        "bomRules": bom_rules,
        "recoveryRules": recovery_rules,
    }
    return plan


def main():
    plan = parse_sheet_items()
    js_content = (
        "// Auto-generated from G:\\我的雲端硬碟\\產銷排程與原料需求\\source_plan.xlsx\n"
        "(function (root) {\n"
        "  root.DEFAULT_SALES_PLAN = " + json.dumps(plan, ensure_ascii=False, indent=2) + ";\n"
        "  if (typeof module !== 'undefined' && module.exports) {\n"
        "    module.exports = root.DEFAULT_SALES_PLAN;\n"
        "  }\n"
        "})(typeof window !== 'undefined' ? window : globalThis);\n"
    )
    for out_p in OUT_PATHS:
        os.makedirs(os.path.dirname(out_p), exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(js_content)
        print(f"Wrote {out_p} ({len(plan['items'])} items, {len(plan['bomRules'])} BOM rules)")


if __name__ == "__main__":
    main()
