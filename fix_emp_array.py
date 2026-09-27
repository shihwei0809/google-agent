path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_fetch = """      fetch(`${GAS_API_URL}?action=getEmployees`)
        .then(res => res.json())
        .then(res => {
          if (res && res.success && res.data) {
            localStorage.setItem('HS_QC_EMP_MAP', JSON.stringify(res.data));
          }
        })
        .catch(err => console.warn("API 取得員工名單失敗", err));"""

new_fetch = """      fetch(`${GAS_API_URL}?action=getEmployees`)
        .then(res => res.json())
        .then(res => {
          if (res && res.success && res.data) {
            let empDict = {};
            if (Array.isArray(res.data)) {
              res.data.forEach(r => { if (r.emp_id) empDict[r.emp_id] = r.name; });
            } else {
              empDict = res.data;
            }
            localStorage.setItem('HS_QC_EMP_MAP', JSON.stringify(empDict));
          }
        })
        .catch(err => console.warn("API 取得員工名單失敗", err));"""

text = text.replace(old_fetch, new_fetch)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
