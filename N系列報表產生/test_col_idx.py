import pandas as pd
ship_path = r"d:\GOOGLE ANGET\N系列報表產生\2026台積電出貨表 NSE1106 & NSE-1106A.xlsx"
ship_df = pd.read_excel(ship_path, header=1)
cols = list(ship_df.columns)
col_idx = {}
for i, c in enumerate(cols):
    c_str = str(c).strip()
    if '出貨' in c_str: col_idx['出貨'] = i
    elif '到貨' in c_str and '地點' not in c_str: col_idx['到貨'] = i
    elif '批號' in c_str: col_idx['批號'] = i
    elif '到貨地點' in c_str: col_idx['到貨地點'] = i
print("col_idx:", col_idx)
