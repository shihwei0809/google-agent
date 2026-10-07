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

for year in ['2025', '2026']:
    path = rf'C:\GOOGLE ANGET\儲槽作業日報\{year}'
    files = glob.glob(os.path.join(path, '*.xlsm'))
    for f in files:
        print(f"Processing {f}...")
        try:
            wb = pd.ExcelFile(f)
        except Exception as e:
            print(f"Error reading {f}: {e}")
            continue
            
        for sheet in wb.sheet_names:
            if sheet in ['新增', '密碼']: # skip known non-data sheets
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
                'TK604A_0800': val_604a_0800,
                'TK604B_0800': val_604b_0800,
                'TK604A_1600': val_604a_1600,
                'TK604B_1600': val_604b_1600
            }
            if year == '2025':
                data_2025.append(record)
            else:
                data_2026.append(record)

df_2025 = pd.DataFrame(data_2025).sort_values('Date').reset_index(drop=True)
df_2026 = pd.DataFrame(data_2026).sort_values('Date').reset_index(drop=True)
df_all = pd.concat([df_2025, df_2026]).sort_values('Date').reset_index(drop=True)

df_2025.to_excel('2025_TK604_Data.xlsx', index=False)
df_2026.to_excel('2026_TK604_Data.xlsx', index=False)
df_all.to_excel('All_TK604_Data.xlsx', index=False)
print("Data saved to Excel files")

# Now create the final report with charts
writer = pd.ExcelWriter('TK604_Report.xlsx', engine='xlsxwriter')

for sheet_name, df in [('2025', df_2025), ('2026', df_2026), ('2025_2026', df_all)]:
    df['Date_str'] = df['Date'].dt.strftime('%Y/%m/%d')
    export_df = df[['Date_str', 'TK604A_0800', 'TK604B_0800', 'TK604A_1600', 'TK604B_1600']]
    export_df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    workbook = writer.book
    worksheet = writer.sheets[sheet_name]
    
    chart_a = workbook.add_chart({'type': 'line'})
    chart_b = workbook.add_chart({'type': 'line'})
    
    # Configure TK604A chart
    chart_a.add_series({
        'name': 'TK604A 08:00',
        'categories': [sheet_name, 1, 0, len(df), 0],
        'values':     [sheet_name, 1, 1, len(df), 1],
    })
    chart_a.add_series({
        'name': 'TK604A 16:00',
        'categories': [sheet_name, 1, 0, len(df), 0],
        'values':     [sheet_name, 1, 3, len(df), 3],
    })
    chart_a.set_title({'name': 'TK604A 液位(mm/%)'})
    worksheet.insert_chart('G2', chart_a)
    
    # Configure TK604B chart
    chart_b.add_series({
        'name': 'TK604B 08:00',
        'categories': [sheet_name, 1, 0, len(df), 0],
        'values':     [sheet_name, 1, 2, len(df), 2],
    })
    chart_b.add_series({
        'name': 'TK604B 16:00',
        'categories': [sheet_name, 1, 0, len(df), 0],
        'values':     [sheet_name, 1, 4, len(df), 4],
    })
    chart_b.set_title({'name': 'TK604B 液位(mm/%)'})
    worksheet.insert_chart('G18', chart_b)

writer.close()
print("Report generated successfully.")
