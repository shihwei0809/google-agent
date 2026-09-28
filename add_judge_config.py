path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add to fixDatabase defaults
if 'OPTIONS_JUDGE_RESULTS' not in text:
    text = text.replace("['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR']", 
                        "['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR'],\n        ['OPTIONS_JUDGE_RESULTS', 'PASS:合格放行, FAIL:不合格退回']")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Added to index.js")
else:
    print("Already in index.js")
