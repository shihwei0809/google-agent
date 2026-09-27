path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Update the INSERT INTO
old_destruct = 'const { id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade } = data;'
new_destruct = 'const { id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, remark } = data;'

old_insert = 'await env.DB.prepare("INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, status, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, \'待檢驗\', datetime(\'now\', \'localtime\'))")'
new_insert = 'await env.DB.prepare("INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, remark, status, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, \'待檢驗\', datetime(\'now\', \'localtime\'))")'

old_bind = '.bind(id||null, barcode||null, productName||null, tankNo||null, customer||null, quantity||null, flowType||null, dept||null, requester||null, grade||null).run();'
new_bind = '.bind(id||null, barcode||null, productName||null, tankNo||null, customer||null, quantity||null, flowType||null, dept||null, requester||null, grade||null, remark||null).run();'

text = text.replace(old_destruct, new_destruct).replace(old_insert, new_insert).replace(old_bind, new_bind)

# Wait, if QC_Samples doesn't have `remark` column yet, the INSERT will fail!
# So I should automatically ALTER TABLE if it fails, or just execute it directly!
# Actually, I can just execute the ALTER TABLE in `createSample` if it throws, or do it during an initialization.
# Or better: when I push the code, I will use `wrangler d1 execute` to ALTER TABLE manually? But I don't have auth token working right now.
# I can just put `await env.DB.prepare("ALTER TABLE QC_Samples ADD COLUMN remark TEXT").run().catch(e=>console.log(e));` right before the insert!

text = text.replace(new_insert, 'await env.DB.prepare("ALTER TABLE QC_Samples ADD COLUMN remark TEXT").run().catch(e=>{});\n      ' + new_insert)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
