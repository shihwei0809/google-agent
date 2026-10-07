import pandas as pd
import glob
import os
import re
from datetime import datetime

data_2025 = []
data_2026 = []

def parse_time_val(val):
    if pd.isna(val): return None
    s = str(val).strip()
    if '08:00:00' in s: return '08:00'
    if '16:00:00' in s: return '16:00'
    return s

def to_percentage(val, max_val=9100):
    try:
        num = float(val)
        return round((num / max_val) * 100, 2)
    except (ValueError, TypeError):
        return None

for year in ['2025', '2026']:
    path = rf'C:\GOOGLE ANGET\儲槽作業日報\{year}'
    files = glob.glob(os.path.join(path, '*.xlsm'))
    for f in files:
        if '~$' in f:
            continue
        try:
            wb = pd.ExcelFile(f)
        except Exception as e:
            continue
            
        for sheet in wb.sheet_names:
            if sheet in ['新增', '密碼']:
                continue
            
            m = re.match(r'^(\d+)\.(\d+)$', sheet)
            if not m:
                continue
            
            month = int(m.group(1))
            day = int(m.group(2))
            
            try:
                date_str = f"{year}-{month:02d}-{day:02d}"
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
                
            df = pd.read_excel(wb, sheet_name=sheet, header=None)
            
            tk604a_col = -1
            tk604b_col = -1
            
            for r in range(min(10, df.shape[0])):
                for c in range(df.shape[1]):
                    val = str(df.iloc[r, c]).strip()
                    if 'TK-604A' in val:
                        tk604a_col = c
                    elif 'TK-604B' in val:
                        tk604b_col = c
                        
            if tk604a_col == -1 or tk604b_col == -1:
                continue
                
            row_0800 = -1
            row_1600 = -1
            for r in range(min(30, df.shape[0])):
                val = parse_time_val(df.iloc[r, 1])
                if val == '08:00':
                    row_0800 = r
                elif val == '16:00':
                    row_1600 = r
                    
            val_604a_0800 = df.iloc[row_0800, tk604a_col] if row_0800 != -1 else None
            val_604b_0800 = df.iloc[row_0800, tk604b_col] if row_0800 != -1 else None
            val_604a_1600 = df.iloc[row_1600, tk604a_col] if row_1600 != -1 else None
            val_604b_1600 = df.iloc[row_1600, tk604b_col] if row_1600 != -1 else None
            
            record = {
                'Date': date_obj,
                'TK604A_0800_mm': val_604a_0800,
                'TK604A_0800_%': to_percentage(val_604a_0800),
                'TK604B_0800_mm': val_604b_0800,
                'TK604B_0800_%': to_percentage(val_604b_0800),
                'TK604A_1600_mm': val_604a_1600,
                'TK604A_1600_%': to_percentage(val_604a_1600),
                'TK604B_1600_mm': val_604b_1600,
                'TK604B_1600_%': to_percentage(val_604b_1600)
            }
            if year == '2025':
                data_2025.append(record)
            else:
                data_2026.append(record)

df_2025 = pd.DataFrame(data_2025).sort_values('Date').reset_index(drop=True)
df_2026 = pd.DataFrame(data_2026).sort_values('Date').reset_index(drop=True)
df_all = pd.concat([df_2025, df_2026]).sort_values('Date').reset_index(drop=True)

# Create the final report with charts
writer = pd.ExcelWriter('TK604_Report_v2.xlsx', engine='xlsxwriter')

datasets = [
    ('2025', df_2025),
    ('2026', df_2026),
    ('2025_2026', df_all)
]

for base_sheet_name, df in datasets:
    if df.empty: continue
    
    df['Date_str'] = df['Date'].dt.strftime('%Y/%m/%d')
    
    # --- Data in mm ---
    sheet_mm = base_sheet_name + '_mm'
    df_mm = df[['Date_str', 'TK604A_0800_mm', 'TK604B_0800_mm', 'TK604A_1600_mm', 'TK604B_1600_mm']]
    df_mm.to_excel(writer, sheet_name=sheet_mm, index=False)
    
    workbook = writer.book
    worksheet_mm = writer.sheets[sheet_mm]
    
    chart_a_mm = workbook.add_chart({'type': 'line'})
    chart_b_mm = workbook.add_chart({'type': 'line'})
    
    chart_a_mm.add_series({
        'name': 'TK604A 08:00 (mm)',
        'categories': [sheet_mm, 1, 0, len(df), 0],
        'values':     [sheet_mm, 1, 1, len(df), 1],
    })
    chart_a_mm.add_series({
        'name': 'TK604A 16:00 (mm)',
        'categories': [sheet_mm, 1, 0, len(df), 0],
        'values':     [sheet_mm, 1, 3, len(df), 3],
    })
    chart_a_mm.set_title({'name': 'TK604A 液位 (mm)'})
    worksheet_mm.insert_chart('G2', chart_a_mm)
    
    chart_b_mm.add_series({
        'name': 'TK604B 08:00 (mm)',
        'categories': [sheet_mm, 1, 0, len(df), 0],
        'values':     [sheet_mm, 1, 2, len(df), 2],
    })
    chart_b_mm.add_series({
        'name': 'TK604B 16:00 (mm)',
        'categories': [sheet_mm, 1, 0, len(df), 0],
        'values':     [sheet_mm, 1, 4, len(df), 4],
    })
    chart_b_mm.set_title({'name': 'TK604B 液位 (mm)'})
    worksheet_mm.insert_chart('G18', chart_b_mm)

    # --- Data in % ---
    sheet_pct = base_sheet_name + '_pct'
    df_pct = df[['Date_str', 'TK604A_0800_%', 'TK604B_0800_%', 'TK604A_1600_%', 'TK604B_1600_%']]
    df_pct.to_excel(writer, sheet_name=sheet_pct, index=False)
    
    worksheet_pct = writer.sheets[sheet_pct]
    
    chart_a_pct = workbook.add_chart({'type': 'line'})
    chart_b_pct = workbook.add_chart({'type': 'line'})
    
    chart_a_pct.add_series({
        'name': 'TK604A 08:00 (%)',
        'categories': [sheet_pct, 1, 0, len(df), 0],
        'values':     [sheet_pct, 1, 1, len(df), 1],
    })
    chart_a_pct.add_series({
        'name': 'TK604A 16:00 (%)',
        'categories': [sheet_pct, 1, 0, len(df), 0],
        'values':     [sheet_pct, 1, 3, len(df), 3],
    })
    chart_a_pct.set_title({'name': 'TK604A 液位 (%)'})
    chart_a_pct.set_y_axis({'max': 100})
    worksheet_pct.insert_chart('G2', chart_a_pct)
    
    chart_b_pct.add_series({
        'name': 'TK604B 08:00 (%)',
        'categories': [sheet_pct, 1, 0, len(df), 0],
        'values':     [sheet_pct, 1, 2, len(df), 2],
    })
    chart_b_pct.add_series({
        'name': 'TK604B 16:00 (%)',
        'categories': [sheet_pct, 1, 0, len(df), 0],
        'values':     [sheet_pct, 1, 4, len(df), 4],
    })
    chart_b_pct.set_title({'name': 'TK604B 液位 (%)'})
    chart_b_pct.set_y_axis({'max': 100})
    worksheet_pct.insert_chart('G18', chart_b_pct)

writer.close()
print("v2 Report generated successfully.")
