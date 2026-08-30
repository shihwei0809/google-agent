
import glob, os, csv, datetime
from weather_monitor import append_to_monthly_xlsx

path = r'G:\我的雲端硬碟\GOOGLE ANGET\溫度通報\24 小時趨勢備份'
csvs = glob.glob(os.path.join(path, '*24小時趨勢備份.csv'))

# sort by name
csvs.sort()

all_rows = []
for c in csvs:
    if 'Q' in c:
        continue # skip new format
    try:
        with open(c, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if not rows: continue
            
            headers = rows[0]
            for row in rows[1:]:
                all_rows.append(row)
    except Exception as e:
        print(f'Error reading {c}: {e}')

# sort all rows by time (first col)
all_rows.sort(key=lambda x: x[0])

# group by quarter and write
for row in all_rows:
    time_str = row[0]
    try:
        dt = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
    except:
        continue
        
    year_str = dt.strftime('%Y')
    quarter = (dt.month - 1) // 3 + 1
    sheet_name = dt.strftime('%m月%d日')
    
    xlsx_file = os.path.join(path, f'{year_str}-Q{quarter}_24小時趨勢備份.xlsx')
    
    append_to_monthly_xlsx(xlsx_file, sheet_name, headers, row)

print('Consolidation complete.')

