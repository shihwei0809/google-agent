path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '.bind(id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade).run();',
    '.bind(id||null, barcode||null, productName||null, tankNo||null, customer||null, quantity||null, flowType||null, dept||null, requester||null, grade||null).run();'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
