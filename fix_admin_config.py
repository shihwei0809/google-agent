path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_code = """        for(const k in data) {
          t.innerHTML += `<tr><td><strong>${k}</strong></td><td><input type="text" id="cfg_${k}" value="${data[k].replace(/"/g, '&quot;')}"></td></tr>`;
        }"""

new_code = """        if (data['OPTIONS_PRODUCT_GRADES_MAP'] === undefined) data['OPTIONS_PRODUCT_GRADES_MAP'] = 'EBR-P1R:電子級, IPAUPS:UPS';
        
        for(const k in data) {
          t.innerHTML += `<tr><td><strong>${k}</strong></td><td><input type="text" id="cfg_${k}" value="${data[k].replace(/"/g, '&quot;')}"></td></tr>`;
        }"""

text = text.replace(old_code, new_code)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
