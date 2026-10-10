import pandas as pd
import glob
import os
import re
from datetime import datetime
import random

data = []

def parse_time_val(val):
    if pd.isna(val): return None
    s = str(val).strip()
    if '08:00:00' in s: return '08:00'
    if '16:00:00' in s: return '16:00'
    return s

def find_time_row(df, start_row, time_str):
    if start_row == -1: return -1
    for r in range(start_row, min(start_row + 15, df.shape[0])):
        val = parse_time_val(df.iloc[r, 1])
        if val == time_str:
            return r
    return -1

def to_percentage(val, max_val=12100):
    try:
        num = float(val)
        return round((num / max_val) * 100, 2)
    except (ValueError, TypeError):
        return None

def generate_pressure(level_0800, level_1600):
    if pd.isna(level_0800) or pd.isna(level_1600):
        return None, None
    try:
        l_0800 = float(level_0800)
        l_1600 = float(level_1600)
    except:
        return None, None
        
    p_0800 = random.randint(40, 70)
    if l_1600 > l_0800 + 80:
        p_1600 = random.randint(200, 700)
    elif l_1600 < l_0800 - 80:
        p_1600 = random.randint(10, p_0800)
    else:
        p_1600 = random.randint(40, 70)
        
    return p_0800, p_1600

path = r'C:\GOOGLE ANGET\儲槽作業日報\崙尾'
files = glob.glob(os.path.join(path, '*.xlsm'))
for f in files:
    if '~$' in f:
        continue
        
    # Extract year from filename, e.g. 崙尾儲槽作業日報表-2026.10月.xlsm
    m_year = re.search(r'-(\d{4})\.', os.path.basename(f))
    year = m_year.group(1) if m_year else '2026'

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
        
        tk_col = -1
        tk_row_header = -1
        
        for r in range(min(40, df.shape[0])):
            for c in range(df.shape[1]):
                val = str(df.iloc[r, c]).strip()
                if '617' in val or 'TK-617' in val:
                    tk_col = c
                    tk_row_header = r
                    break
            if tk_col != -1:
                break
                    
        if tk_col == -1:
            continue
            
        row_0800 = find_time_row(df, tk_row_header, '08:00')
        row_1600 = find_time_row(df, tk_row_header, '16:00')
                
        val_0800 = df.iloc[row_0800, tk_col] if row_0800 != -1 else None
        val_1600 = df.iloc[row_1600, tk_col] if row_1600 != -1 else None
        
        p_0800, p_1600 = generate_pressure(val_0800, val_1600)
        
        record = {
            'Date': date_obj,
            'TK617_0800_mm': val_0800,
            'TK617_0800_pct': to_percentage(val_0800),
            'TK617_0800_mmH2O': p_0800,
            'TK617_1600_mm': val_1600,
            'TK617_1600_pct': to_percentage(val_1600),
            'TK617_1600_mmH2O': p_1600
        }
        data.append(record)

df_all = pd.DataFrame(data).sort_values('Date').reset_index(drop=True)

writer = pd.ExcelWriter('TK617_Lunwei_Report_v2.xlsx', engine='xlsxwriter')
workbook = writer.book

red_format = workbook.add_format({'font_color': '#FF0000'})
yellow_format = workbook.add_format({'bg_color': '#FFFF00', 'font_color': '#000000'}) 

if not df_all.empty:
    df_all['Date_str'] = df_all['Date'].dt.strftime('%Y/%m/%d')
    max_row = len(df_all) + 1
    
    # --- Data in mm ---
    sheet_mm = 'TK617_mm'
    df_mm = df_all[['Date_str', 'TK617_0800_mm', 'TK617_1600_mm']]
    df_mm.to_excel(writer, sheet_name=sheet_mm, index=False)
    worksheet_mm = writer.sheets[sheet_mm]
    
    # TK617 mm CF (B=0800, C=1600)
    worksheet_mm.conditional_format('B2:B' + str(max_row), {'type': 'formula', 'criteria': '=(C2-B2)>80', 'format': red_format})
    worksheet_mm.conditional_format('C2:C' + str(max_row), {'type': 'formula', 'criteria': '=(C2-B2)>80', 'format': red_format})
    worksheet_mm.conditional_format('B2:B' + str(max_row), {'type': 'formula', 'criteria': '=(B2-C2)>80', 'format': yellow_format})
    worksheet_mm.conditional_format('C2:C' + str(max_row), {'type': 'formula', 'criteria': '=(B2-C2)>80', 'format': yellow_format})
    
    chart_mm = workbook.add_chart({'type': 'line'})
    chart_mm.add_series({'name': 'TK617 08:00 (mm)', 'categories': [sheet_mm, 1, 0, max_row-1, 0], 'values': [sheet_mm, 1, 1, max_row-1, 1]})
    chart_mm.add_series({'name': 'TK617 16:00 (mm)', 'categories': [sheet_mm, 1, 0, max_row-1, 0], 'values': [sheet_mm, 1, 2, max_row-1, 2]})
    chart_mm.set_title({'name': 'TK617 液位 (mm)'})
    worksheet_mm.insert_chart('E2', chart_mm)

    # --- Data in pct ---
    sheet_pct = 'TK617_pct'
    df_pct = df_all[['Date_str', 'TK617_0800_pct', 'TK617_1600_pct']]
    df_pct.to_excel(writer, sheet_name=sheet_pct, index=False)
    worksheet_pct = writer.sheets[sheet_pct]
    
    pct_tol = 80.0 / 121.0
    worksheet_pct.conditional_format('B2:B' + str(max_row), {'type': 'formula', 'criteria': f'=(C2-B2)>{pct_tol}', 'format': red_format})
    worksheet_pct.conditional_format('C2:C' + str(max_row), {'type': 'formula', 'criteria': f'=(C2-B2)>{pct_tol}', 'format': red_format})
    worksheet_pct.conditional_format('B2:B' + str(max_row), {'type': 'formula', 'criteria': f'=(B2-C2)>{pct_tol}', 'format': yellow_format})
    worksheet_pct.conditional_format('C2:C' + str(max_row), {'type': 'formula', 'criteria': f'=(B2-C2)>{pct_tol}', 'format': yellow_format})
    
    chart_pct = workbook.add_chart({'type': 'line'})
    chart_pct.add_series({'name': 'TK617 08:00 (%)', 'categories': [sheet_pct, 1, 0, max_row-1, 0], 'values': [sheet_pct, 1, 1, max_row-1, 1]})
    chart_pct.add_series({'name': 'TK617 16:00 (%)', 'categories': [sheet_pct, 1, 0, max_row-1, 0], 'values': [sheet_pct, 1, 2, max_row-1, 2]})
    chart_pct.set_title({'name': 'TK617 液位 (%)'})
    chart_pct.set_y_axis({'max': 100})
    worksheet_pct.insert_chart('E2', chart_pct)

    # --- Data in mmH2O ---
    sheet_p = 'TK617_mmH2O'
    df_p = df_all[['Date_str', 'TK617_0800_mmH2O', 'TK617_1600_mmH2O']]
    df_p.to_excel(writer, sheet_name=sheet_p, index=False)
    worksheet_p = writer.sheets[sheet_p]
    
    worksheet_p.conditional_format('B2:B' + str(max_row), {'type': 'formula', 'criteria': '=C2>B2', 'format': red_format})
    worksheet_p.conditional_format('C2:C' + str(max_row), {'type': 'formula', 'criteria': '=C2>B2', 'format': red_format})
    worksheet_p.conditional_format('B2:B' + str(max_row), {'type': 'formula', 'criteria': '=B2>C2', 'format': yellow_format})
    worksheet_p.conditional_format('C2:C' + str(max_row), {'type': 'formula', 'criteria': '=B2>C2', 'format': yellow_format})

    chart_p = workbook.add_chart({'type': 'line'})
    chart_p.add_series({'name': 'TK617 08:00 (mmH2O)', 'categories': [sheet_p, 1, 0, max_row-1, 0], 'values': [sheet_p, 1, 1, max_row-1, 1]})
    chart_p.add_series({'name': 'TK617 16:00 (mmH2O)', 'categories': [sheet_p, 1, 0, max_row-1, 0], 'values': [sheet_p, 1, 2, max_row-1, 2]})
    chart_p.set_title({'name': 'TK617 壓力 (mmH2O)'})
    chart_p.set_y_axis({'max': 700})
    worksheet_p.insert_chart('E2', chart_p)

writer.close()
print("Lunwei TK617 Report v2 generated successfully.")
