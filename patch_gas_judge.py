path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\Code.gs'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Modify getSystemConfigFromSheet_ to parse judge results
new_parse = """      if (key === 'OPTIONS_PRODUCT_GRADES_MAP' && val) {
        config.productGradesMap = val;
      }
      if (key === 'OPTIONS_JUDGE_RESULTS' && val) {
        config.judgeResults = val;
      }"""
text = text.replace("""      if (key === 'OPTIONS_PRODUCT_GRADES_MAP' && val) {
        config.productGradesMap = val;
      }""", new_parse)

# Modify initSystemConfigSheet
new_init = """      ['OPTIONS_PRODUCT_GRADES_MAP', 'EBR-P1R:電子級, IPAUPS:UPS', '品名對應等級 (格式：品名:等級，多組用逗號隔開)'],
      ['OPTIONS_JUDGE_RESULTS', 'PASS:合格放行, FAIL:不合格退回', '判定結果選項 (格式：值:顯示名稱，多組用逗號隔開)']
    ];"""
text = text.replace("""      ['OPTIONS_PRODUCT_GRADES_MAP', 'EBR-P1R:電子級, IPAUPS:UPS', '品名對應等級 (格式：品名:等級，多組用逗號隔開)']
    ];""", new_init)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
