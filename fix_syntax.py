path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the syntax error \'\' -> ''
text = text.replace(r" : \'\',", " : '',")
text = text.replace(r" : \'\'}", " : ''}")

# Fix the SheetJS closing tag
text = text.replace('<script src="https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js">\n  // 動態提示字跑馬燈', '<script src="https://cdn.sheetjs.com/xlsx-0.20.1/package/dist/xlsx.full.min.js"></script>\n<script>\n  // 動態提示字跑馬燈')

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
