import pandas as pd

shipping_file = r"d:\GOOGLE ANGET\N系列報表產生\2026台積電出貨表 NSE1106 & NSE-1106A.xlsx"
mapping_file = r"d:\GOOGLE ANGET\N系列報表產生\N系料小包-地點代號對照表.xlsx"

map_df = pd.read_excel(mapping_file)
print("Mapping Columns:", map_df.columns.tolist())
print(map_df.head(5))

ship_df = pd.read_excel(shipping_file, header=1) # Row 2
print("Shipping Columns:", ship_df.columns.tolist())
print(ship_df.head(5))
