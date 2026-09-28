for folder in ["1_Web_網頁版", "2_PWA_App版", "admin"]:
    if folder == "admin":
        path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\1_Web_網頁版\admin.html'
        # The admin UI logic is identical for GAS, we can just apply it (assuming it has the same code structure)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
            text = text.replace("<div>\n            <label>自訂判定結果選項 (用逗號分隔，例如 PASS:合格放行, FAIL:不合格退回)</label>\n            <input type=\"text\" id=\"cfg_OPTIONS_JUDGE_RESULTS\" placeholder=\"預設: PASS:合格放行, FAIL:不合格退回\">\n          </div>", "<div>\n            <label>自訂判定結果選項 (用逗號分隔，例如 PASS:合格放行, FAIL:不合格退回)</label>\n            <input type=\"text\" id=\"cfg_OPTIONS_JUDGE_RESULTS\" placeholder=\"預設: PASS:合格放行, FAIL:不合格退回\">\n          </div>\n          <div>\n            <label>匯入排程時「自動省略/免送樣」的產品 (用逗號分隔，預設 IPAHQ)</label>\n            <input type=\"text\" id=\"cfg_T100_IGNORE_PRODUCTS\" placeholder=\"例如: IPAHQ, PRODUCT_B\">\n          </div>")
            text = text.replace("document.getElementById('cfg_OPTIONS_JUDGE_RESULTS').value = cfg.OPTIONS_JUDGE_RESULTS || 'PASS:合格放行, FAIL:不合格退回';", "document.getElementById('cfg_OPTIONS_JUDGE_RESULTS').value = cfg.OPTIONS_JUDGE_RESULTS || 'PASS:合格放行, FAIL:不合格退回';\n      document.getElementById('cfg_T100_IGNORE_PRODUCTS').value = cfg.T100_IGNORE_PRODUCTS || 'IPAHQ';")
            text = text.replace("OPTIONS_JUDGE_RESULTS: document.getElementById('cfg_OPTIONS_JUDGE_RESULTS').value", "OPTIONS_JUDGE_RESULTS: document.getElementById('cfg_OPTIONS_JUDGE_RESULTS').value,\n        T100_IGNORE_PRODUCTS: document.getElementById('cfg_T100_IGNORE_PRODUCTS').value")
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        except:
            pass
        continue

    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    old_start = """        function parseSheet(sheetName) {
          const worksheet = workbook.Sheets[sheetName];"""
    new_start = """        function parseSheet(sheetName) {
          const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
          const ignoredConfig = cfgStr ? JSON.parse(cfgStr)['T100_IGNORE_PRODUCTS'] : 'IPAHQ';
          const ignoredList = (ignoredConfig || 'IPAHQ').split(',').map(s => s.trim().toUpperCase());

          const worksheet = workbook.Sheets[sheetName];"""
    text = text.replace(old_start, new_start)

    old_out = """              if(!docNo || !prod) continue;

              // 嚴格只從「預計出貨日期」欄位抓取"""
    new_out = """              if(!docNo || !prod) continue;
              if(ignoredList.includes(String(prod).trim().toUpperCase())) continue;

              // 嚴格只從「預計出貨日期」欄位抓取"""
    text = text.replace(old_out, new_out)

    old_in = """              if(!docNo || !prod) continue;

              // 嚴格只從「預計進貨日」欄位抓取"""
    new_in = """              if(!docNo || !prod) continue;
              if(ignoredList.includes(String(prod).trim().toUpperCase())) continue;

              // 嚴格只從「預計進貨日」欄位抓取"""
    text = text.replace(old_in, new_in)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Patched {folder}")
