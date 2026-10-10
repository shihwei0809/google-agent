import pandas as pd
import glob
import os
import re
from datetime import datetime

data_2026 = []

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

path = r'C:\GOOGLE ANGET\儲槽作業日報\2026'
files = glob.glob(os.path.join(path, '*.xlsm'))
for f in files:
    if '~$' in f:
        continue
    try:
        wb = pd.ExcelFile(f)
    except:
        continue
        
    for sheet in wb.sheet_names:
        m = re.match(r'^(\d+)\.(\d+)$', sheet)
        if not m:
            continue
        month = int(m.group(1))
        day = int(m.group(2))
        try:
            date_obj = datetime.strptime(f"2026-{month:02d}-{day:02d}", "%Y-%m-%d")
        except:
            continue
            
        df = pd.read_excel(wb, sheet_name=sheet, header=None)
        
        tk604a_col = -1
        tk604b_col = -1
        tk_row_header = -1
        
        for r in range(min(40, df.shape[0])):
            for c in range(df.shape[1]):
                val = str(df.iloc[r, c]).strip()
                if 'TK-604A' == val or 'TK604A' in val:
                    tk604a_col = c
                    tk_row_header = r
                elif 'TK-604B' == val or 'TK604B' in val:
                    tk604b_col = c
                    
        if tk604a_col == -1 or tk604b_col == -1:
            continue
            
        row_0800 = find_time_row(df, tk_row_header, '08:00')
        row_1600 = find_time_row(df, tk_row_header, '16:00')
        
        # Temperature is 2 rows below the time row
        temp_0800_row = row_0800 + 2 if row_0800 != -1 else -1
        temp_1600_row = row_1600 + 2 if row_1600 != -1 else -1
                
        t_604a_0800 = df.iloc[temp_0800_row, tk604a_col] if temp_0800_row != -1 else None
        t_604b_0800 = df.iloc[temp_0800_row, tk604b_col] if temp_0800_row != -1 else None
        t_604a_1600 = df.iloc[temp_1600_row, tk604a_col] if temp_1600_row != -1 else None
        t_604b_1600 = df.iloc[temp_1600_row, tk604b_col] if temp_1600_row != -1 else None
        
        record = {
            'Date': date_obj,
            'TK604A_0800_Temp': t_604a_0800,
            'TK604B_0800_Temp': t_604b_0800,
            'TK604A_1600_Temp': t_604a_1600,
            'TK604B_1600_Temp': t_604b_1600
        }
        data_2026.append(record)

df_all = pd.DataFrame(data_2026).sort_values('Date').reset_index(drop=True)

writer = pd.ExcelWriter('TK604_2026_Temperature_Report_v2.xlsx', engine='xlsxwriter')
workbook = writer.book

if not df_all.empty:
    df_all['Date_str'] = df_all['Date'].dt.strftime('%Y/%m/%d')
    sheet_name = '2026_Temperature'
    df_out = df_all[['Date_str', 'TK604A_0800_Temp', 'TK604B_0800_Temp', 'TK604A_1600_Temp', 'TK604B_1600_Temp']]
    df_out.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.sheets[sheet_name]
    
    max_row = len(df_all) + 1
    
    chart_a = workbook.add_chart({'type': 'line'})
    chart_b = workbook.add_chart({'type': 'line'})
    
    chart_a.add_series({'name': 'TK604A 08:00 (℃)', 'categories': [sheet_name, 1, 0, max_row-1, 0], 'values': [sheet_name, 1, 1, max_row-1, 1]})
    chart_a.add_series({'name': 'TK604A 16:00 (℃)', 'categories': [sheet_name, 1, 0, max_row-1, 0], 'values': [sheet_name, 1, 3, max_row-1, 3]})
    chart_a.set_title({'name': 'TK604A 溫度 (℃)'})
    chart_a.set_y_axis({'max': 45})
    worksheet.insert_chart('G2', chart_a)
    
    chart_b.add_series({'name': 'TK604B 08:00 (℃)', 'categories': [sheet_name, 1, 0, max_row-1, 0], 'values': [sheet_name, 1, 2, max_row-1, 2]})
    chart_b.add_series({'name': 'TK604B 16:00 (℃)', 'categories': [sheet_name, 1, 0, max_row-1, 0], 'values': [sheet_name, 1, 4, max_row-1, 4]})
    chart_b.set_title({'name': 'TK604B 溫度 (℃)'})
    chart_b.set_y_axis({'max': 45})
    worksheet.insert_chart('G18', chart_b)

writer.close()
print("Temperature Report v2 generated successfully.")
