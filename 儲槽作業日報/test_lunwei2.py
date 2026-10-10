import pandas as pd
wb = pd.ExcelFile(r'C:\GOOGLE ANGET\儲槽作業日報\崙尾\崙尾儲槽作業日報表-2026.10月.xlsm')
df = pd.read_excel(wb, sheet_name='10.1', header=None)
for r in range(min(40, df.shape[0])):
    print(f"Row {r}: B='{df.iloc[r, 1]}', C='{df.iloc[r, 2]}', TK617='{df.iloc[r, 14]}'")
