path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\Code.gs'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add to getConfig
old_get = """    if(k === 'OPTIONS_JUDGE_RESULTS') config['OPTIONS_JUDGE_RESULTS'] = String(v);"""
new_get = """    if(k === 'OPTIONS_JUDGE_RESULTS') config['OPTIONS_JUDGE_RESULTS'] = String(v);
    if(k === 'T100_IGNORE_PRODUCTS') config['T100_IGNORE_PRODUCTS'] = String(v);"""
text = text.replace(old_get, new_get)

# Add to updateConfig
old_upd = """    if(row[0] === 'OPTIONS_JUDGE_RESULTS' && payload.OPTIONS_JUDGE_RESULTS) sheet.getRange(i+1, 2).setValue(payload.OPTIONS_JUDGE_RESULTS);"""
new_upd = """    if(row[0] === 'OPTIONS_JUDGE_RESULTS' && payload.OPTIONS_JUDGE_RESULTS) sheet.getRange(i+1, 2).setValue(payload.OPTIONS_JUDGE_RESULTS);
    if(row[0] === 'T100_IGNORE_PRODUCTS' && payload.T100_IGNORE_PRODUCTS !== undefined) sheet.getRange(i+1, 2).setValue(payload.T100_IGNORE_PRODUCTS);"""
text = text.replace(old_upd, new_upd)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
