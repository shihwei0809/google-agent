path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\Code.gs'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Modify getSystemConfigFromSheet_ to parse productGradesMap
old_parse = """      if (key === 'OPTIONS_PRODUCTS' && val) {
        config.products = val.split(/[,，]/).map(s => s.trim()).filter(Boolean);
      }
    }"""
new_parse = """      if (key === 'OPTIONS_PRODUCTS' && val) {
        config.products = val.split(/[,，]/).map(s => s.trim()).filter(Boolean);
      }
      if (key === 'OPTIONS_PRODUCT_GRADES_MAP' && val) {
        config.productGradesMap = val;
      }
    }"""
text = text.replace(old_parse, new_parse)

# Modify initSystemConfigSheet to include the row
old_init = """      ['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR', '品名建議選單 (以逗號隔開)']
    ];"""
new_init = """      ['OPTIONS_PRODUCTS', 'IPA, IPAUPS, IPAHQ, CPNE3(T), CPNE4, CPN-P1R, EBR, EBR-P1R, NBAC, NBAC-P1R, CPN, EG, NMP, GAA, ACT, PM, PMA98, heavy-R, DPM, DPM-B1, SEP73, Anone, GBL, PG, EBRR', '品名建議選單 (以逗號隔開)'],
      ['OPTIONS_PRODUCT_GRADES_MAP', 'EBR-P1R:電子級, IPAUPS:UPS', '品名對應等級 (格式：品名:等級，多組用逗號隔開)']
    ];"""
text = text.replace(old_init, new_init)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
