import pandas as pd
wb = pd.ExcelFile(r'C:\GOOGLE ANGET\儲槽作業日報\崙尾\崙尾儲槽作業日報表-2026.10月.xlsm')
print(wb.sheet_names)
df = pd.read_excel(wb, sheet_name='10.1', header=None)
for r in range(min(40, df.shape[0])):
    row_vals = []
    for c in range(min(15, df.shape[1])):
        val = str(df.iloc[r, c]).strip()
        if '617' in val or 'TK' in val:
            row_vals.append(f"C{c}:{val}")
    if row_vals:
        print(f"Row {r}: " + ", ".join(row_vals))
