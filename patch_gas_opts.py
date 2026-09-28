for folder in ["1_Web_網頁版", "2_PWA_App版"]:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()

        old_fn = """  function applyDynamicDropdownOptions(cfg) {
    if (cfg && cfg.OPTIONS_JUDGE_RESULTS) {
      const select = document.getElementById('modalResult');
      if (select) {
        select.innerHTML = '';
        const opts = cfg.OPTIONS_JUDGE_RESULTS.split(',').map(s => s.trim()).filter(Boolean);
        opts.forEach(o => {
          const parts = o.split(':');
          const val = parts[0];
          const text = parts.length > 1 ? parts[1] : val;
          const option = document.createElement('option');
          option.value = val;
          option.innerText = `${val} (${text})`;
          select.appendChild(option);
        });
      }
    }
  }"""
        new_fn = """  function applyDynamicDropdownOptions(cfg) {
    if (cfg && cfg.OPTIONS_JUDGE_RESULTS) {
      const select = document.getElementById('modalResult');
      if (select) {
        select.innerHTML = '';
        const opts = cfg.OPTIONS_JUDGE_RESULTS.split(',').map(s => s.trim()).filter(Boolean);
        opts.forEach(o => {
          const parts = o.split(':');
          const val = parts[0];
          const text = parts.length > 1 ? parts[1] : val;
          const option = document.createElement('option');
          option.value = val;
          option.innerText = `${val} (${text})`;
          select.appendChild(option);
        });
      }
    }
    if (cfg && cfg.OPTIONS_PRODUCTS) {
      const dl = document.getElementById('productList');
      if (dl) {
        dl.innerHTML = '';
        const opts = cfg.OPTIONS_PRODUCTS.split(',').map(s => s.trim()).filter(Boolean);
        opts.forEach(p => {
          const option = document.createElement('option');
          option.value = p;
          dl.appendChild(option);
        });
      }
    }
  }"""
        text = text.replace(old_fn, new_fn)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception as e:
        print(e)
