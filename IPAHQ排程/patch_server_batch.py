import re

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/server.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

old_str = "const batchNo = order.product || '';"
new_str = "const batchNo = order.batch || '';"

if old_str in js:
    js = js.replace(old_str, new_str)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print("Fixed batchNo assignment in server.js")
else:
    print("Could not find exact string. Checking alternative...")
    # Just in case there are spaces
    js = re.sub(r'const batchNo\s*=\s*order\.product\s*\|\|\s*\'\';', new_str, js)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(js)
    print("Fixed batchNo via regex")
