path = r'D:\GOOGLE ANGET\三合一單網頁架機伺服器\server.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'def load_location_mapping\(\):.*?return mapping', text, re.DOTALL)
if m:
    with open('server_old.txt', 'w', encoding='utf-8') as f:
        f.write(m.group(0))
    print('FOUND')
else:
    print('NOT FOUND')
