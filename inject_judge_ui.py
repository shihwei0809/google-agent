path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

injection = """
    // 3. 判定結果選單
    if(cfg.OPTIONS_JUDGE_RESULTS) {
      const selRes = document.getElementById('modalResult');
      if(selRes) {
        const cur = selRes.value;
        const opts = cfg.OPTIONS_JUDGE_RESULTS.split(',').map(s => s.trim()).filter(Boolean);
        selRes.innerHTML = opts.map(o => {
          const parts = o.split(':');
          const val = parts[0].trim();
          const label = parts[1] ? `${val} (${parts[1].trim()})` : val;
          return `<option value="${val}">${label}</option>`;
        }).join('');
      }
    }
"""

if '// 3. 判定結果選單' not in text:
    text = text.replace("    // 1. 動向下拉選單", injection + "\n    // 1. 動向下拉選單")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Injected into index.html")
else:
    print("Already exists")
