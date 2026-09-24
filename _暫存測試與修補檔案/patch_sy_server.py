path = r'D:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

new_load = r'''def load_location_mapping():
    mapping = {
        "15P5": "E1550155A",
        "15P6": "E1550156A",
        "18P3B": "EF180183B",
        "12P7": "E00700001"
    }
    part_mapping = {}
    if os.path.exists(MAPPING_PATH):
        try:
            wb = openpyxl.load_workbook(MAPPING_PATH, data_only=True)
            ws = wb.active
            rows = list(ws.iter_rows(values_only=True))
            if rows:
                headers = [str(h).strip() if h else "" for h in rows[0]]
                for row in rows[1:]:
                    if row and len(row) >= 2 and row[0] and row[1]:
                        k = str(row[0]).strip().upper()
                        v = str(row[1]).strip()
                        if any(kw in k for kw in ("地點", "代號", "SHORT", "LOCATION", "KEY", "簡稱")):
                            continue
                        mapping[k] = v
                        info = {"default": str(row[2]).strip() if len(row) > 2 and row[2] else "", "origins": {}}
                        for i in range(3, len(headers)):
                            if i < len(row) and row[i] is not None:
                                h_name = headers[i]
                                if h_name: info["origins"][h_name] = str(row[i]).strip()
                        part_mapping[k] = info
            wb.close()
        except Exception as e:
            print(f"警告: 讀取地點代號失敗: {e}")
    return {"basic": mapping, "parts": part_mapping}'''

text = re.sub(r'def load_location_mapping\(\):.*?return mapping', new_load, text, flags=re.DOTALL)

# Fix API /api/mapping
text = text.replace(
    'mapping = load_location_mapping()\n    return JSONResponse({"status": "success", "count": len(mapping), "data": mapping})',
    'mapping_data = load_location_mapping()\n    return JSONResponse({"status": "success", "count": len(mapping_data["basic"]), "data": mapping_data["basic"], "parts": mapping_data["parts"]})'
)

# Fix generate_all_zip
text = text.replace(
    'mapping = load_location_mapping()',
    'mapping_data = load_location_mapping()\n        mapping = mapping_data["basic"]\n        part_mapping = mapping_data["parts"]'
)

# Fix generation writing
old_write = r'''                    ws\['C5'\] = tank_with_prefix
                    ws\['C7'\] = batch_with_prefix
                    ws\['C11'\] = loc_code

                    mat_no = str\(ws\['C3'\]\.value or "4L12C53161"\)\.strip\(\)'''

new_write = r'''                    ws['C5'] = tank_with_prefix
                    ws['C7'] = batch_with_prefix
                    ws['C11'] = loc_code

                    # Update C3 part no dynamically based on product
                    prod = item.get("prod", "").strip().upper()
                    info = part_mapping.get(loc, {})
                    part_no = ""
                    for key, val in info.get("origins", {}).items():
                        if prod and key.upper() in prod:
                            part_no = val
                            break
                    if not part_no: part_no = info.get("default", "")
                    if not part_no:
                        part_no = str(ws['C3'].value or "L12C53161").strip().lstrip("4")
                    ws['C3'] = "4" + part_no
                    mat_no = "4" + part_no'''

text = re.sub(old_write, new_write, text)

# Fix close block indentation
text = text.replace(
    '                    src_wb.close()',
    '                        src_wb.close()'
)
text = text.replace(
    '                except Exception as ex:\n                    print(f"[Lorry Error] {ex}")',
    '                    except Exception as ex:\n                        print(f"[Lorry Error] {ex}")'
)

text = text.replace(
    '                            src_wb_l.close()\n                        except Exception as e:\n                            print(f"[COA Lorry Extraction Error] {e}")',
    '                                src_wb_l.close()\n                            except Exception as e:\n                                print(f"[COA Lorry Extraction Error] {e}")'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
