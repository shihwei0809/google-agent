import re
path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Inject autoSelectGrade function
auto_select_js = """
  // 自動套用產品等級
  function autoSelectGrade(prodName) {
    if(!prodName) return;
    const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
    if(!cfgStr) return;
    try {
      const cfg = JSON.parse(cfgStr);
      const mapStr = cfg.OPTIONS_PRODUCT_GRADES_MAP || '';
      if(!mapStr) return;
      const pairs = mapStr.split(',').map(s => s.trim()).filter(Boolean);
      const mapping = {};
      pairs.forEach(p => {
        const parts = p.split(':').map(s => s.trim());
        if(parts.length >= 2) mapping[parts[0]] = parts[1];
      });
      if(mapping[prodName]) {
        document.getElementById('grade').value = mapping[prodName];
      }
    } catch(e) { console.warn(e); }
  }
"""

text = re.sub(
    r'(<script>\s*let allData = \[\];)',
    auto_select_js + r'\n\1',
    text
)

# 2. Add onchange to productName
text = text.replace(
    '<input type="text" id="productName" list="productList" placeholder="點選或輸入" required>',
    '<input type="text" id="productName" list="productList" placeholder="點選或輸入" required onchange="autoSelectGrade(this.value)">'
)

# 3. Call it in onT100SelectChange
old_t100_set = """    document.getElementById('grade').value = item.grade || '工業級';
    document.getElementById('productName').value = item.productName || '';
    document.getElementById('tankNo').value = item.tankNo || '';"""

new_t100_set = """    document.getElementById('grade').value = item.grade || '工業級';
    document.getElementById('productName').value = item.productName || '';
    autoSelectGrade(item.productName);
    document.getElementById('tankNo').value = item.tankNo || '';"""

text = text.replace(old_t100_set, new_t100_set)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
