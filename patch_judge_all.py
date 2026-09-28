import re

injection = """
    // 3. 判定結果選單
    const judgeResStr = cfg.OPTIONS_JUDGE_RESULTS || cfg.judgeResults;
    if(judgeResStr) {
      const selRes = document.getElementById('modalResult');
      if(selRes) {
        const opts = judgeResStr.split(',').map(s => s.trim()).filter(Boolean);
        selRes.innerHTML = opts.map(o => {
          const parts = o.split(':');
          const val = parts[0].trim();
          const label = parts[1] ? `${val} (${parts[1].trim()})` : val;
          return `<option value="${val}">${label}</option>`;
        }).join('');
      }
    }
"""

for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Only for 1 and 2 (already did 3 but will update it to support cfg.judgeResults)
    if folder == '3_Cloudflare_D1版':
        text = re.sub(r'// 3\. 判定結果選單.*?}\s*}', injection.strip(), text, flags=re.DOTALL)
    else:
        if '// 3. 判定結果選單' not in text:
            text = text.replace("    // 1. 動向下拉選單", injection + "\n    // 1. 動向下拉選單")
            
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Patched {folder}")
