import glob, os, re, json
import pandas as pd

def extract_all():
    base_path = r'C:\GOOGLE ANGET\儲槽作業日報'
    output_data = {}

    # 1. 彰濱一廠與其他槽
    files_main = glob.glob(os.path.join(base_path, '2026', '*.xlsm'))
    for f in files_main:
        if '~$' in f: continue
        m_year = re.search(r'(\d{4})\.(\d{1,2})', os.path.basename(f))
        if not m_year: continue
        year = int(m_year.group(1))
        try:
            xl = pd.ExcelFile(f)
        except Exception:
            continue
        for sheet in xl.sheet_names:
            m_s = re.match(r'^(\d{1,2})\.(\d{1,2})$', sheet.strip())
            if not m_s: continue
            month, day = int(m_s.group(1)), int(m_s.group(2))
            date_key = f'{year}-{month:02d}-{day:02d}'
            if date_key not in output_data: output_data[date_key] = {}
            try:
                df = pd.read_excel(xl, sheet_name=sheet, header=None)
                tanks_map = {
                    'TK604A': 'TK604A', 'TK604B': 'TK604B', 
                    'TK696': 'TK696', 'TK697': 'TK697', 'TK693': 'TK693',
                    'TK652': 'TK652', 'TK611': 'TK611', 'TK613': 'TK613'
                }
                for r in range(min(40, df.shape[0])):
                    for c in range(df.shape[1]):
                        val_norm = str(df.iloc[r, c]).strip().upper().replace('-', '').replace(' ', '')
                        for t_key in tanks_map:
                            if val_norm == t_key:
                                for sr in range(r+1, min(r+8, df.shape[0])):
                                    if '重量' in str(df.iloc[sr, 2]) or 'kg' in str(df.iloc[sr, 2]).lower():
                                        try:
                                            kg = float(df.iloc[sr, c])
                                            output_data[date_key][t_key] = round(kg / 1000, 2)
                                            break
                                        except: pass
            except Exception: pass

    # 2. 崙尾二廠 TK617, TK618
    files_lunwei = glob.glob(os.path.join(base_path, '崙尾', '*.xlsm'))
    for f in files_lunwei:
        if '~$' in f: continue
        m_year = re.search(r'(\d{4})\.(\d{1,2})', os.path.basename(f))
        year = int(m_year.group(1)) if m_year else 2026
        try:
            xl = pd.ExcelFile(f)
        except Exception:
            continue
        for sheet in xl.sheet_names:
            m_s = re.match(r'^(\d{1,2})\.(\d{1,2})$', sheet.strip())
            if not m_s: continue
            month, day = int(m_s.group(1)), int(m_s.group(2))
            date_key = f'{year}-{month:02d}-{day:02d}'
            if date_key not in output_data: output_data[date_key] = {}
            try:
                df = pd.read_excel(xl, sheet_name=sheet, header=None)
                for r in range(min(30, df.shape[0])):
                    for c in range(df.shape[1]):
                        val_norm = str(df.iloc[r, c]).strip().upper().replace('-', '').replace(' ', '')
                        if val_norm in ['TK617', 'TK618']:
                            for sr in range(r+1, min(r+8, df.shape[0])):
                                if '重量' in str(df.iloc[sr, 2]) or 'kg' in str(df.iloc[sr, 2]).lower() or sr == r+3:
                                    try:
                                        kg = float(df.iloc[sr, c])
                                        if kg > 0:
                                            output_data[date_key][val_norm] = round(kg / 1000, 2)
                                            break
                                    except: pass
            except Exception: pass

    # 一廠共用池合計
    for d, tanks in output_data.items():
        p1_tanks = ['TK604A', 'TK604B', 'TK696', 'TK697', 'TK693']
        p1_total = sum(tanks.get(tk, 0) for tk in p1_tanks)
        if p1_total > 0:
            tanks['plant1'] = round(p1_total, 2)

    out_file = r'c:\GOOGLE ANGET\IPA 專用動態生產排程與進耗存整合系統\2_PWA_App版\public\tank_daily_0800.json'
    with open(out_file, 'w', encoding='utf-8') as fp:
        json.dump(output_data, fp, ensure_ascii=False, indent=2)
    print(f'Done! Saved {len(output_data)} dates to {out_file}')

if __name__ == '__main__':
    extract_all()
