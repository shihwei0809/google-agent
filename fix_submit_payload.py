path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

import re

# Fix submitSample
text = re.sub(
    r'const \{ id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade \} = payload;',
    r'const data = payload.payload || payload;\n      const { id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade } = data;',
    text
)

# Fix other places if they need it (like saveOrders?)
# saveOrders uses payload.orders, which is fine since frontend sends {action: 'saveOrders', orders: orders}

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
