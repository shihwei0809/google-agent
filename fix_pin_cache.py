path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

if "localStorage.setItem('HS_QC_ADMIN_PIN', cfg.QC_PIN)" not in text:
    text = text.replace("localStorage.setItem('HS_QC_DYNAMIC_OPTIONS', JSON.stringify(cfg));", "localStorage.setItem('HS_QC_DYNAMIC_OPTIONS', JSON.stringify(cfg));\n            if(cfg.QC_PIN) localStorage.setItem('HS_QC_ADMIN_PIN', cfg.QC_PIN);")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Added QC_PIN caching")
else:
    print("Already there")
