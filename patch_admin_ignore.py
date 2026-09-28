path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\admin.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_html = """          <div>
            <label>自訂判定結果選項 (用逗號分隔，例如 PASS:合格放行, FAIL:不合格退回)</label>
            <input type="text" id="cfg_OPTIONS_JUDGE_RESULTS" placeholder="預設: PASS:合格放行, FAIL:不合格退回">
          </div>"""
new_html = """          <div>
            <label>自訂判定結果選項 (用逗號分隔，例如 PASS:合格放行, FAIL:不合格退回)</label>
            <input type="text" id="cfg_OPTIONS_JUDGE_RESULTS" placeholder="預設: PASS:合格放行, FAIL:不合格退回">
          </div>
          <div>
            <label>匯入排程時「自動省略/免送樣」的產品 (用逗號分隔，預設 IPAHQ)</label>
            <input type="text" id="cfg_T100_IGNORE_PRODUCTS" placeholder="例如: IPAHQ, PRODUCT_B">
          </div>"""
text = text.replace(old_html, new_html)

old_load = """      document.getElementById('cfg_OPTIONS_JUDGE_RESULTS').value = cfg.OPTIONS_JUDGE_RESULTS || 'PASS:合格放行, FAIL:不合格退回';"""
new_load = """      document.getElementById('cfg_OPTIONS_JUDGE_RESULTS').value = cfg.OPTIONS_JUDGE_RESULTS || 'PASS:合格放行, FAIL:不合格退回';
      document.getElementById('cfg_T100_IGNORE_PRODUCTS').value = cfg.T100_IGNORE_PRODUCTS || 'IPAHQ';"""
text = text.replace(old_load, new_load)

old_save = """        OPTIONS_JUDGE_RESULTS: document.getElementById('cfg_OPTIONS_JUDGE_RESULTS').value"""
new_save = """        OPTIONS_JUDGE_RESULTS: document.getElementById('cfg_OPTIONS_JUDGE_RESULTS').value,
        T100_IGNORE_PRODUCTS: document.getElementById('cfg_T100_IGNORE_PRODUCTS').value"""
text = text.replace(old_save, new_save)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
