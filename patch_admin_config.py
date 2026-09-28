path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = """        if (data['OPTIONS_PRODUCT_GRADES_MAP'] === undefined) data['OPTIONS_PRODUCT_GRADES_MAP'] = 'EBR-P1R:電子級, IPAUPS:UPS';"""
new_logic = """        if (data['OPTIONS_PRODUCT_GRADES_MAP'] === undefined) data['OPTIONS_PRODUCT_GRADES_MAP'] = 'EBR-P1R:電子級, IPAUPS:UPS';
        if (data['OPTIONS_JUDGE_RESULTS'] === undefined) data['OPTIONS_JUDGE_RESULTS'] = 'PASS:合格放行, FAIL:不合格退回';
        if (data['T100_IGNORE_PRODUCTS'] === undefined) data['T100_IGNORE_PRODUCTS'] = 'IPAHQ';"""

text = text.replace(old_logic, new_logic)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
