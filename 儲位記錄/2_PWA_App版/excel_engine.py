"""
Excel (.xlsm) 讀取與無損回寫引擎
- 讀取：使用 openpyxl (read_only + data_only) 快速解析總表與表單選單
- 寫入：採用 Surgical XML/ZIP 寫入，完整保留 VBA 巨集、圖表、資料驗證、分區儲位表公式與格式
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import openpyxl
from lxml import etree

SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"

COL_INDEX = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8}

DEFAULT_WAREHOUSES: dict[str, dict[str, str]] = {
    "lunwei": {
        "id": "lunwei",
        "name": "崙尾倉儲",
        "icon": "🏭",
        "filename": "崙尾倉儲儲位表.xlsm",
        "master_sheet": "崙尾倉儲儲位表_總表202208",
        "form_sheet": "表單",
        "form_layout": "name_first",
    },
    "hongsheng": {
        "id": "hongsheng",
        "name": "鴻勝倉庫",
        "icon": "🏢",
        "filename": "鴻勝儲位表.xlsm",
        "master_sheet": "倉庫總表",
        "form_sheet": "單位表單",
        "form_layout": "code_first",
    },
}
WAREHOUSES = DEFAULT_WAREHOUSES


class ExcelLockedError(Exception):
    """目標 Excel 檔案正被其他程式（例如 Microsoft Excel）開啟鎖定。"""


class ExcelEngine:
    """讀寫各倉庫 .xlsm 儲位表的核心引擎（支援動態新增倉庫）。"""

    def __init__(self, base_dir: str | Path, registry_path: str | Path | None = None):
        self.base_dir = Path(base_dir)
        self.backup_dir = self.base_dir / "backups"
        self.registry_path = Path(registry_path) if registry_path else (Path(__file__).resolve().parent / "data" / "warehouses.json")
        self._lock = threading.Lock()

    def get_warehouses(self) -> dict[str, dict[str, str]]:
        if self.registry_path.exists():
            try:
                items = json.loads(self.registry_path.read_text(encoding="utf-8"))
                if isinstance(items, list) and items:
                    return {w["id"]: w for w in items if w.get("id")}
                if isinstance(items, dict) and items:
                    return items
            except Exception:
                pass
        return dict(DEFAULT_WAREHOUSES)

    def save_warehouses(self, warehouses_map: dict[str, dict[str, str]]) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(list(warehouses_map.values()), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get_file_path(self, wh_id: str) -> Path:
        whs = self.get_warehouses()
        if wh_id not in whs:
            raise ValueError(f"未知倉庫代碼: {wh_id}")
        return self.base_dir / whs[wh_id]["filename"]

    def list_warehouses(self) -> list[dict[str, Any]]:
        result = []
        for wh_id, cfg in self.get_warehouses().items():
            fpath = self.base_dir / cfg["filename"]
            result.append(
                {
                    "id": wh_id,
                    "name": cfg["name"],
                    "icon": cfg.get("icon", "🏬"),
                    "filename": cfg["filename"],
                    "master_sheet": cfg.get("master_sheet", ""),
                    "form_sheet": cfg.get("form_sheet", ""),
                    "form_layout": cfg.get("form_layout", "name_first"),
                    "exists": fpath.exists(),
                    "mtime": (
                        datetime.fromtimestamp(fpath.stat().st_mtime).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                        if fpath.exists()
                        else None
                    ),
                }
            )
        return result

    def read_warehouse_data(self, wh_id: str) -> dict[str, Any]:
        """讀取指定倉庫的所有儲位、區域、品名/品號/包材選單與現有批號。"""
        whs = self.get_warehouses()
        if wh_id not in whs:
            raise ValueError(f"未知倉庫代碼: {wh_id}")
        cfg = whs[wh_id]
        fpath = self.get_file_path(wh_id)
        if not fpath.exists():
            raise FileNotFoundError(f"找不到檔案: {fpath}")

        wb = openpyxl.load_workbook(fpath, data_only=True, read_only=True)
        try:
            ws = wb[cfg["master_sheet"]]
            locations: list[dict[str, Any]] = []
            zones_seen: list[str] = []
            zones_set: set[str] = set()
            batches_set: set[str] = set()
            products_from_master: dict[str, dict[str, Any]] = {}
            packages_set: set[str] = set()

            current_zone = "未分類"
            for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                if row_idx < 3:
                    continue
                col_a = row[0] if len(row) > 0 else None
                col_b = row[1] if len(row) > 1 else None
                if col_a is not None and str(col_a).strip():
                    current_zone = str(col_a).strip()
                if col_b is None or not str(col_b).strip():
                    continue

                loc_code = str(col_b).strip()
                item_no = (
                    str(row[2]).strip()
                    if len(row) > 2 and row[2] is not None
                    else ""
                )
                item_name = (
                    str(row[3]).strip()
                    if len(row) > 3 and row[3] is not None
                    else ""
                )
                lot_no = (
                    str(row[4]).strip()
                    if len(row) > 4 and row[4] is not None
                    else ""
                )
                pkg = (
                    str(row[5]).strip()
                    if len(row) > 5 and row[5] is not None
                    else ""
                )
                qty_raw = row[6] if len(row) > 6 else None
                qty: float | int = 0
                if isinstance(qty_raw, (int, float)):
                    qty = int(qty_raw) if float(qty_raw).is_integer() else float(qty_raw)
                elif qty_raw is not None and str(qty_raw).strip():
                    try:
                        val = float(str(qty_raw).strip())
                        qty = int(val) if val.is_integer() else val
                    except ValueError:
                        qty = 0
                note = (
                    str(row[7]).strip()
                    if len(row) > 7 and row[7] is not None
                    else ""
                )

                if current_zone not in zones_set:
                    zones_set.add(current_zone)
                    zones_seen.append(current_zone)

                if lot_no:
                    batches_set.add(lot_no)
                if item_name:
                    if item_name not in products_from_master:
                        products_from_master[item_name] = {"item_no": item_no, "pkg_counts": {}}
                    elif not products_from_master[item_name]["item_no"] and item_no:
                        products_from_master[item_name]["item_no"] = item_no
                    if pkg:
                        counts = products_from_master[item_name]["pkg_counts"]
                        counts[pkg] = counts.get(pkg, 0) + 1
                if pkg:
                    packages_set.add(pkg)

                locations.append(
                    {
                        "row": row_idx,
                        "zone": current_zone,
                        "location": loc_code,
                        "item_no": item_no,
                        "item_name": item_name,
                        "lot_no": lot_no,
                        "package": pkg,
                        "qty": qty,
                        "note": note,
                        "occupied": bool(item_name or lot_no or qty > 0),
                    }
                )

            catalog, form_packages = self._read_form_sheet(
                wb, cfg["form_sheet"], wh_id, cfg.get("form_layout", "name_first" if wh_id == "lunwei" else "code_first")
            )
            for p_name, p_info in products_from_master.items():
                top_pkg = ""
                if p_info["pkg_counts"]:
                    top_pkg = max(p_info["pkg_counts"].items(), key=lambda kv: kv[1])[0]
                if p_name not in catalog:
                    catalog[p_name] = {"item_no": p_info["item_no"], "package": top_pkg}
                else:
                    if not catalog[p_name]["item_no"] and p_info["item_no"]:
                        catalog[p_name]["item_no"] = p_info["item_no"]
                    if top_pkg:
                        catalog[p_name]["package"] = top_pkg

            all_packages = list(dict.fromkeys(form_packages + sorted(packages_set)))

            return {
                "warehouse": {"id": wh_id, "name": cfg["name"], "filename": cfg["filename"]},
                "zones": zones_seen,
                "locations": locations,
                "catalog": [
                    {"item_name": k, "item_no": v["item_no"], "package": v["package"]}
                    for k, v in catalog.items()
                ],
                "packages": all_packages,
                "existing_lots": sorted(batches_set),
                "summary": {
                    "total_locations": len(locations),
                    "occupied_locations": sum(1 for loc in locations if loc["occupied"]),
                    "empty_locations": sum(1 for loc in locations if not loc["occupied"]),
                    "total_qty": sum(loc["qty"] for loc in locations),
                },
                "dashboard": self.compute_dashboard_stats(wh_id, locations),
            }
        finally:
            wb.close()

    def compute_dashboard_stats(
        self, wh_id: str, locations: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """計算總表即時統計：僅顯示架上有貨的品名、各區空儲位，以及依備註動態抓取異常/HOLD品。"""
        qty_by_item: dict[str, float] = {}
        pallets_by_item: dict[str, int] = {}
        abnormal_by_key: dict[str, float] = {}
        abnormal_keywords = ("HOLD", "異常", "不良", "後助", "侯住")

        for loc in locations:
            name = (loc.get("item_name") or "").strip()
            note = (loc.get("note") or "").strip()
            q = float(loc.get("qty") or 0)
            if name and (q > 0 or loc.get("occupied")):
                qty_by_item[name] = qty_by_item.get(name, 0) + q
                pallets_by_item[name] = pallets_by_item.get(name, 0) + 1

            note_upper = note.upper()
            name_upper = name.upper()
            is_abnormal = any(kw in note_upper or kw in name_upper for kw in abnormal_keywords)
            if is_abnormal and (q > 0 or name):
                ab_label = f"{name or '(未填品名)'}"
                if note and not any(kw in name_upper for kw in abnormal_keywords):
                    ab_label = f"{ab_label} ({note})"
                abnormal_by_key[ab_label] = abnormal_by_key.get(ab_label, 0) + q

        def fmt(v: float) -> int | float:
            return int(v) if float(v).is_integer() else round(v, 3)

        # 只顯示架上實際有數量的品名（依桶數由大到小排序）
        product_totals = [
            {
                "item_name": k,
                "total_qty": fmt(v),
                "pallets": pallets_by_item.get(k, 0),
            }
            for k, v in sorted(qty_by_item.items(), key=lambda kv: (-kv[1], kv[0]))
            if v > 0
        ]

        abnormal_totals = [
            {"item_name": k, "total_qty": fmt(v)}
            for k, v in sorted(abnormal_by_key.items(), key=lambda kv: (-kv[1], kv[0]))
            if v > 0
        ]

        if wh_id == "lunwei":
            # 1~4 區 1~4 層空儲位統計
            zone_empty = []
            total_empty_1_4 = 0
            for z_idx, z_label in [(1, "第一區空儲位\n1~4層"), (2, "第二區空儲位\n1~4層"), (3, "第三區空儲位\n1~4層"), (4, "第四區空儲位\n1~4層")]:
                target_zones = {f"{z_idx}區{layer}層" for layer in (1, 2, 3, 4)}
                z_locs = [l for l in locations if l.get("zone") in target_zones]
                empty_cnt = sum(1 for l in z_locs if not l.get("occupied"))
                total_empty_1_4 += empty_cnt
                zone_empty.append({
                    "label": f"{z_label}({len(z_locs)})",
                    "empty_count": empty_cnt,
                    "total_count": len(z_locs),
                })

            return {
                "product_totals": product_totals,
                "zone_empty": zone_empty,
                "total_empty_summary_label": "崙尾倉貨架板數",
                "total_empty_summary_count": total_empty_1_4,
                "abnormal_totals": abnormal_totals,
            }
        else:
            zone_map: dict[str, dict[str, int]] = {}
            for l in locations:
                z = l.get("zone") or "未分類"
                if z not in zone_map:
                    zone_map[z] = {"total": 0, "empty": 0}
                zone_map[z]["total"] += 1
                if not l.get("occupied"):
                    zone_map[z]["empty"] += 1
            zone_empty = [
                {"label": f"{z} ({c['total']})", "empty_count": c["empty"], "total_count": c["total"]}
                for z, c in zone_map.items()
            ]
            total_empty = sum(c["empty"] for c in zone_map.values())
            return {
                "product_totals": product_totals,
                "zone_empty": zone_empty,
                "total_empty_summary_label": "鴻勝倉空儲位合計",
                "total_empty_summary_count": total_empty,
                "abnormal_totals": abnormal_totals,
            }

    def _read_form_sheet(
        self, wb: openpyxl.Workbook, form_sheet_name: str, wh_id: str, form_layout: str = "name_first"
    ) -> tuple[dict[str, dict[str, str]], list[str]]:
        """解析 表單 / 單位表單 取得品名->(品號, 預設包材)對照與包材清單。"""
        catalog: dict[str, dict[str, str]] = {}
        packages: list[str] = []
        if not form_sheet_name or form_sheet_name not in wb.sheetnames:
            return catalog, packages
        ws = wb[form_sheet_name]
        for row_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if row_idx == 1:
                continue
            if form_layout == "name_first":
                # A=品名, B=品號, C=包材
                name = str(row[0]).strip() if len(row) > 0 and row[0] else ""
                code = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                pkg = str(row[2]).strip() if len(row) > 2 and row[2] else ""
            else:
                # A=品號, B=品名, C=包材
                code = str(row[0]).strip() if len(row) > 0 and row[0] else ""
                name = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                pkg = str(row[2]).strip() if len(row) > 2 and row[2] else ""
            if name and name not in catalog:
                catalog[name] = {"item_no": code, "package": pkg if code else ""}
            if pkg and pkg not in packages:
                packages.append(pkg)
        return catalog, packages

    def update_location_row(
        self,
        wh_id: str,
        row_idx: int,
        item_no: str,
        item_name: str,
        lot_no: str,
        package: str,
        qty: int | float | None,
        note: str,
    ) -> None:
        """
        以 Surgical XML/ZIP 方式精準回寫 .xlsm 總表該列儲存格，
        保留所有巨集、圖表、資料驗證、分區儲位表與公式。
        """
        cfg = self.get_warehouses()[wh_id]
        fpath = self.get_file_path(wh_id)
        if not fpath.exists():
            raise FileNotFoundError(f"找不到檔案: {fpath}")

        with self._lock:
            self._ensure_daily_backup(fpath)
            tmp_path = fpath.with_suffix(".xlsm.tmp")

            try:
                with zipfile.ZipFile(fpath, "r") as zin:
                    sheet_entry = self._resolve_sheet_zip_path(zin, cfg["master_sheet"])
                    sheet_bytes = zin.read(sheet_entry)
                    wb_bytes = zin.read("xl/workbook.xml")

                    updated_sheet = self._patch_sheet_xml(
                        sheet_bytes,
                        row_idx=row_idx,
                        values={
                            "C": item_no,
                            "D": item_name,
                            "E": lot_no,
                            "F": package,
                            "G": qty,
                            "H": note,
                        },
                    )
                    updated_wb = self._enable_full_calc_on_load(wb_bytes)

                    with zipfile.ZipFile(
                        tmp_path, "w", compression=zipfile.ZIP_DEFLATED
                    ) as zout:
                        for item in zin.infolist():
                            if item.filename == sheet_entry:
                                zout.writestr(item, updated_sheet)
                            elif item.filename == "xl/workbook.xml":
                                zout.writestr(item, updated_wb)
                            else:
                                zout.writestr(item, zin.read(item.filename))

                os.replace(tmp_path, fpath)
            except PermissionError as exc:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except OSError:
                        pass
                raise ExcelLockedError(
                    f"檔案 {fpath.name} 正被 Excel 或其他程式開啟中，請先關閉檔案後再試！"
                ) from exc
            except Exception:
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except OSError:
                        pass
                raise

    def _ensure_daily_backup(self, fpath: Path) -> None:
        """每日首次寫入前自動建立備份，避免誤寫。"""
        today = datetime.now().strftime("%Y%m%d")
        day_dir = self.backup_dir / today
        day_dir.mkdir(parents=True, exist_ok=True)
        bak_path = day_dir / fpath.name
        if not bak_path.exists():
            shutil.copy2(fpath, bak_path)

    def _resolve_sheet_zip_path(
        self, zf: zipfile.ZipFile, sheet_name: str
    ) -> str:
        wb_root = etree.fromstring(zf.read("xl/workbook.xml"))
        rels_root = etree.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            r.attrib["Id"]: r.attrib["Target"]
            for r in rels_root
            if "Id" in r.attrib and "Target" in r.attrib
        }
        for sh in wb_root.findall(f".//{{{SPREADSHEET_NS}}}sheet"):
            if sh.attrib.get("name") == sheet_name:
                rid = sh.attrib.get(f"{{{REL_NS}}}id")
                target = rel_map[rid].lstrip("/")
                if not target.startswith("xl/"):
                    target = f"xl/{target}"
                return target
        raise KeyError(f"在工作簿中找不到工作表: {sheet_name}")

    def _enable_full_calc_on_load(self, wb_bytes: bytes) -> bytes:
        root = etree.fromstring(wb_bytes)
        calc_pr = root.find(f"{{{SPREADSHEET_NS}}}calcPr")
        if calc_pr is None:
            calc_pr = etree.SubElement(root, f"{{{SPREADSHEET_NS}}}calcPr")
        calc_pr.set("fullCalcOnLoad", "1")
        return etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", standalone=True
        )

    def _patch_sheet_xml(
        self, sheet_bytes: bytes, row_idx: int, values: dict[str, Any]
    ) -> bytes:
        root = etree.fromstring(sheet_bytes)
        sheet_data = root.find(f"{{{SPREADSHEET_NS}}}sheetData")
        if sheet_data is None:
            raise ValueError("工作表缺少 sheetData 節點")

        row_str = str(row_idx)
        target_row = None
        for r in sheet_data.findall(f"{{{SPREADSHEET_NS}}}row"):
            if r.attrib.get("r") == row_str:
                target_row = r
                break

        if target_row is None:
            raise ValueError(f"找不到第 {row_idx} 列")

        existing_cells = {
            c.attrib.get("r"): c
            for c in target_row.findall(f"{{{SPREADSHEET_NS}}}c")
        }

        for col_letter, val in values.items():
            ref = f"{col_letter}{row_idx}"
            cell = existing_cells.get(ref)
            if cell is None:
                cell = self._insert_cell_sorted(target_row, ref, col_letter)

            formula_el = cell.find(f"{{{SPREADSHEET_NS}}}f")
            if col_letter == "C" and formula_el is not None:
                # C 欄有 VLOOKUP 公式，保留公式並清除舊快取，讓 Excel 開啟時自動重算
                for child in list(cell):
                    if child is not formula_el:
                        cell.remove(child)
                if "t" in cell.attrib:
                    del cell.attrib["t"]
                continue

            # 清除舊值與舊屬性
            for child in list(cell):
                cell.remove(child)
            if "t" in cell.attrib:
                del cell.attrib["t"]

            if val is None or val == "":
                continue
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                v_el = etree.SubElement(cell, f"{{{SPREADSHEET_NS}}}v")
                v_el.text = str(val)
            else:
                cell.set("t", "inlineStr")
                is_el = etree.SubElement(cell, f"{{{SPREADSHEET_NS}}}is")
                t_el = etree.SubElement(is_el, f"{{{SPREADSHEET_NS}}}t")
                text_val = str(val)
                if text_val != text_val.strip():
                    t_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
                t_el.text = text_val

        return etree.tostring(
            root, xml_declaration=True, encoding="UTF-8", standalone=True
        )

    @staticmethod
    def _insert_cell_sorted(
        row_el: etree._Element, ref: str, col_letter: str
    ) -> etree._Element:
        target_col = COL_INDEX.get(col_letter, ExcelEngine._col_to_num(col_letter))
        new_cell = etree.Element(f"{{{SPREADSHEET_NS}}}c", r=ref)
        for idx, child in enumerate(list(row_el)):
            c_ref = child.attrib.get("r", "")
            m = re.match(r"([A-Z]+)", c_ref)
            if m and ExcelEngine._col_to_num(m.group(1)) > target_col:
                row_el.insert(idx, new_cell)
                return new_cell
        row_el.append(new_cell)
        return new_cell

    @staticmethod
    def _col_to_num(col: str) -> int:
        num = 0
        for ch in col:
            num = num * 26 + (ord(ch) - ord("A") + 1)
        return num

    def export_storage_only_xlsm(self, wh_id: str, out_path: Path) -> Path:
        """產生只包含「儲位總表、表單及各區儲位分頁」的精簡版 .xlsm 供下載（不影響原始主檔）。"""
        fpath = self.get_file_path(wh_id)
        if not fpath.exists():
            raise FileNotFoundError(f"找不到檔案: {fpath}")

        def should_keep(name: str) -> bool:
            whs = self.get_warehouses()
            cfg = whs.get(wh_id, {})
            if wh_id == "lunwei":
                return (
                    name in ("崙尾倉儲儲位表_總表202208", "表單")
                    or "儲位" in name
                )
            if wh_id == "hongsheng":
                return name in ("倉庫總表", "單位表單", "位置圖", "暫存區") or (
                    "區" in name and ("儲位" in name or "走道" in name or "走到" in name)
                )
            return name in (cfg.get("master_sheet"), cfg.get("form_sheet"), "位置圖", "暫存區") or "儲位" in name

        with zipfile.ZipFile(fpath, "r") as zin:
            wb_root = etree.fromstring(zin.read("xl/workbook.xml"))
            rels_root = etree.fromstring(zin.read("xl/_rels/workbook.xml.rels"))
            ct_root = etree.fromstring(zin.read("[Content_Types].xml"))

            rel_by_id = {
                r.attrib["Id"]: r
                for r in rels_root
                if "Id" in r.attrib
            }

            sheets_el = wb_root.find(f"{{{SPREADSHEET_NS}}}sheets")
            removed_targets: set[str] = set()
            removed_sheet_names: set[str] = set()
            old_to_new_idx: dict[str, str] = {}
            new_idx = 0

            for old_idx, sh in enumerate(list(sheets_el)):
                s_name = sh.attrib.get("name", "")
                if not should_keep(s_name):
                    removed_sheet_names.add(s_name)
                    rid = sh.attrib.get(f"{{{REL_NS}}}id")
                    rel_el = rel_by_id.get(rid)
                    if rel_el is not None:
                        target = rel_el.attrib.get("Target", "").lstrip("/")
                        full_target = target if target.startswith("xl/") else f"xl/{target}"
                        removed_targets.add(full_target)
                        rels_root.remove(rel_el)
                    sheets_el.remove(sh)
                else:
                    old_to_new_idx[str(old_idx)] = str(new_idx)
                    new_idx += 1

            # 移除指向已刪除工作表的 definedNames，並重新對應 localSheetId
            def_names = wb_root.find(f"{{{SPREADSHEET_NS}}}definedNames")
            if def_names is not None:
                for dn in list(def_names):
                    txt = dn.text or ""
                    lsid = dn.attrib.get("localSheetId")
                    if any(sn in txt for sn in removed_sheet_names):
                        def_names.remove(dn)
                    elif lsid is not None:
                        if lsid in old_to_new_idx:
                            dn.set("localSheetId", old_to_new_idx[lsid])
                        else:
                            def_names.remove(dn)

            # 重設 activeTab="0" 與 firstSheet="0"
            book_views = wb_root.find(f"{{{SPREADSHEET_NS}}}bookViews")
            if book_views is not None:
                for bv in book_views:
                    bv.set("activeTab", "0")
                    bv.set("firstSheet", "0")

            # 開啟自動重算
            calc_pr = wb_root.find(f"{{{SPREADSHEET_NS}}}calcPr")
            if calc_pr is not None:
                calc_pr.set("fullCalcOnLoad", "1")

            # 從 [Content_Types].xml 移除被刪分頁的 Override 與 calcChain
            for ov in list(ct_root):
                pn = ov.attrib.get("PartName", "").lstrip("/")
                if pn in removed_targets or pn == "xl/calcChain.xml":
                    ct_root.remove(ov)

            new_wb = etree.tostring(wb_root, xml_declaration=True, encoding="UTF-8", standalone=True)
            new_rels = etree.tostring(rels_root, xml_declaration=True, encoding="UTF-8", standalone=True)
            new_ct = etree.tostring(ct_root, xml_declaration=True, encoding="UTF-8", standalone=True)

            with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if item.filename in removed_targets or item.filename == "xl/calcChain.xml":
                        continue
                    if item.filename == "xl/workbook.xml":
                        zout.writestr(item, new_wb)
                    elif item.filename == "xl/_rels/workbook.xml.rels":
                        zout.writestr(item, new_rels)
                    elif item.filename == "[Content_Types].xml":
                        zout.writestr(item, new_ct)
                    else:
                        zout.writestr(item, zin.read(item.filename))
        return out_path
