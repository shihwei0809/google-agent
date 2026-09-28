path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("action: 'completeSample',\n          id: id,\n          result: result,\n          note: note,\n          pin: pin", "action: 'completeSample',\n          id: id,\n          result: result,\n          note: note,\n          pin: pin,\n          approver: approver")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
