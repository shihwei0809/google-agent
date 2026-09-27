import re

path3 = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path3, 'r', encoding='utf-8') as f:
    text3 = f.read()

# Extract autoSelectGrade from text3
m = re.search(r'(// 自動套用產品等級\s*function autoSelectGrade.*?})\s*</script>', text3, re.DOTALL)
if m:
    auto_fn = m.group(1)
    # Modify it to support both cfg keys
    auto_fn = auto_fn.replace("const mapStr = cfg.OPTIONS_PRODUCT_GRADES_MAP || '';", "const mapStr = cfg.OPTIONS_PRODUCT_GRADES_MAP || cfg.productGradesMap || '';")
    
# Extract getOrderSubmissionInfo from text3
m2 = re.search(r'(// 檢查某筆排程是否已在看板.*?function getOrderSubmissionInfo\(order\) {.*?return false;\s*})', text3, re.DOTALL)
if m2:
    get_fn = m2.group(1)

for folder in ['1_Web_網頁版', '2_PWA_App版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Replace getOrderSubmissionInfo
    text = re.sub(r'// 檢查某筆排程是否已在看板.*?function getOrderSubmissionInfo\(order\) {.*?return \(sameTank && sameProd\) \|\| \(sameCont && sameProd\);\s*}', get_fn, text, flags=re.DOTALL)
    
    # Inject autoSelectGrade
    if 'function autoSelectGrade' not in text:
        text = re.sub(r'(<script>\s*let allData = \[\];)', auto_fn + r'\n\1', text)
    
    # Replace onT100SelectChange
    text = text.replace(
        """    document.getElementById('productName').value = item.productName || '';\n    document.getElementById('tankNo').value = item.tankNo || '';""",
        """    document.getElementById('productName').value = item.productName || '';\n    autoSelectGrade(item.productName);\n    document.getElementById('tankNo').value = item.tankNo || '';"""
    )
    
    # Add onchange to productName
    text = text.replace(
        '<input type="text" id="productName" list="productList" placeholder="點選或輸入" required>',
        '<input type="text" id="productName" list="productList" placeholder="點選或輸入" required onchange="autoSelectGrade(this.value)">'
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

