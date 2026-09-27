path_index = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path_index, 'r', encoding='utf-8') as f:
    text = f.read()

old_defaults = "['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR']"
new_defaults = "['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR'],\n        ['OPTIONS_PRODUCT_GRADES_MAP', 'EBR-P1R:電子級, IPAUPS:UPS']"

text = text.replace(old_defaults, new_defaults)

with open(path_index, 'w', encoding='utf-8') as f:
    f.write(text)

path_sql = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\schema.sql'
with open(path_sql, 'r', encoding='utf-8') as f:
    text2 = f.read()

old_sql = "('OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR');"
new_sql = "('OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR'),\n('OPTIONS_PRODUCT_GRADES_MAP', 'EBR-P1R:電子級, IPAUPS:UPS');"

text2 = text2.replace(old_sql, new_sql)

with open(path_sql, 'w', encoding='utf-8') as f:
    f.write(text2)
