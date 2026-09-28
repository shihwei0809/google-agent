path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()
if 'QC_PIN' in text:
    print("QC_PIN STILL FOUND!")
else:
    print("REMOVED!")
