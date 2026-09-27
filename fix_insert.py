path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

bad = 'const stmt = env.DB.prepare("INSERT INTO T100_Orders (doc_no, flowType, productName, tankNo, container, quantity, customer, grade, targetDate") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?));'
good = 'const stmt = env.DB.prepare("INSERT INTO T100_Orders (doc_no, flowType, productName, tankNo, container, quantity, customer, grade, targetDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");'

text = text.replace(bad, good)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
