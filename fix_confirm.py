path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

bad_str = 'if (confirm(發現此車次 () 共有  筆排程單號：\\n\\n\\n是否要自動合併成同一張檢驗單？)) {'
good_str = 'if (confirm(發現此車次 (\) 共有 \ 筆排程單號：\\n\\\n\\n是否要自動合併成同一張檢驗單？)) {'

text = text.replace(bad_str, good_str)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
