import os
import re
import pandas as pd

map_path = r"d:\GOOGLE ANGET\N系列報表產生\N系料小包-地點代號對照表.xlsx"
ship_path = r"d:\GOOGLE ANGET\N系列報表產生\2026台積電出貨表 NSE1106 & NSE-1106A.xlsx"
src_dir = r"d:\GOOGLE ANGET\N系列報表產生\NSE-1106A"

ship_df = pd.read_excel(ship_path, header=1)
cols = list(ship_df.columns)
col_idx = {}
for i, c in enumerate(cols):
    c_str = str(c).strip()
    if '出貨' in c_str: col_idx['出貨'] = i
    elif '到貨' in c_str and '地點' not in c_str: col_idx['到貨'] = i
    elif '批號' in c_str: col_idx['批號'] = i
    elif '到貨地點' in c_str: col_idx['到貨地點'] = i

ship_data = {}
for _, row in ship_df.iterrows():
    batch_no = str(row.iloc[col_idx.get('批號', 2)]).strip()
    raw_loc = str(row.iloc[col_idx.get('到貨地點', 5)]).strip()
    clean_loc = raw_loc.replace('廠', '') 
    ship_data[(batch_no, clean_loc)] = True

print("Sample ship_data keys:", list(ship_data.keys())[:5])

files = [f for f in os.listdir(src_dir) if f.endswith('.xlsx') or f.endswith('.csv')]
for filename in files:
    m = re.search(r'([0-9]{4,5}[A-Z][0-9]{4,5})\s+.*?\s+([0-9A-Z]+)\.(xlsx|csv)', filename, re.IGNORECASE)
    if m:
        batch_no = m.group(1)
        loc_part = m.group(2)
        match = (batch_no, loc_part) in ship_data
        print(f"File: {filename}\nParsed: batch={batch_no}, loc={loc_part}, Found in ship_data? {match}")
    else:
        print(f"File: {filename}\nRegex failed")
