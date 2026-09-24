path = r'D:\GOOGLE ANGET\勝一三合一單產生系統\main.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update load_mapping
load_map_old = r'''    def load_mapping\(self\):
        self\.mapping_dict = \{\}
        if os\.path\.exists\(self\.mapping_path\):
            try:
                map_wb = openpyxl\.load_workbook\(self\.mapping_path, data_only=True\)
                map_ws = map_wb\.active
                for row in map_ws\.iter_rows\(values_only=True\):
                    if row and len\(row\) >= 2 and row\[0\] and row\[1\]:
                        loc_key = str\(row\[0\]\)\.strip\(\)\.upper\(\)
                        loc_val = str\(row\[1\]\)\.strip\(\)
                        # .*?
                        if any\(kw in loc_key for kw in \(".*?", ".*?", "SHORT", "LOCATION", "KEY", "HEADER"\)\):
                            continue
                        self\.mapping_dict\[loc_key\] = loc_val
                map_wb\.close\(\)'''

load_map_new = r'''    def load_mapping(self):
        self.mapping_dict = {}
        self.part_mapping_dict = {}
        if os.path.exists(self.mapping_path):
            try:
                map_wb = openpyxl.load_workbook(self.mapping_path, data_only=True)
                map_ws = map_wb.active
                rows = list(map_ws.iter_rows(values_only=True))
                if rows:
                    headers = [str(h).strip() if h else "" for h in rows[0]]
                    for row in rows[1:]:
                        if row and len(row) >= 2 and row[0] and row[1]:
                            loc_key = str(row[0]).strip().upper()
                            loc_val = str(row[1]).strip()
                            if any(kw in loc_key for kw in ("廠", "地點", "代號", "SHORT", "LOCATION", "KEY", "HEADER")):
                                continue
                            self.mapping_dict[loc_key] = loc_val
                            info = {"default": str(row[2]).strip() if len(row) > 2 and row[2] else "", "origins": {}}
                            for i in range(3, len(headers)):
                                if i < len(row) and row[i] is not None:
                                    h_name = headers[i]
                                    if h_name: info["origins"][h_name] = str(row[i]).strip()
                            self.part_mapping_dict[loc_key] = info
                map_wb.close()'''
text = re.sub(load_map_old, load_map_new, text, flags=re.DOTALL)

# 2. Update Headers
headers_old = r'''        headers = \[
            \(0, ".*?"\),
            \(1, ".*?"\),
            \(2, ".*?"\),
            \(3, ".*?"\),
            \(4, ".*?"\),
            \(5, ".*?"\),
            \(6, ".*?"\),
            \(7, ".*?"\),
            \(8, ".*?"\),
            \(9, ".*?"\)
        \]'''
headers_new = r'''        headers = [
            (0, "產生"),
            (1, "項次"),
            (2, "批號 (請輸入10~11碼)"),
            (3, "槽號 (自動)"),
            (4, "品名 (貼上)"),
            (5, "地點 (如 15P5)"),
            (6, "長代號 (自動)"),
            (7, "料號 (自動)"),
            (8, "出貨日期 (必填)"),
            (9, "採購單號"),
            (10, "單列清除")
        ]'''
text = re.sub(headers_old, headers_new, text)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
