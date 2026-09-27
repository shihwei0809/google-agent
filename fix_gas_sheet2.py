import re
path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\Code.gs'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r"      if \(key === 'OPTIONS_PRODUCT_GRADES_MAP'.*?return config;\s*} catch", text, re.DOTALL)
if m:
    old_text = m.group(0)
    new_text = """      if (key === 'OPTIONS_PRODUCT_GRADES_MAP' && val) {
        config.productGradesMap = val;
      }
    }

    // 支援從獨立工作表讀取品名等級對應 (讓人員更好填寫)
    const mapSheet = ss.getSheetByName('OPTIONS_PRODUCT_GRADES_MAP');
    if (mapSheet) {
      const mapData = mapSheet.getDataRange().getValues();
      const pairs = [];
      for (let i = 1; i < mapData.length; i++) {
        const p = String(mapData[i][0] || '').trim();
        const g = String(mapData[i][1] || '').trim();
        if (p && g) pairs.push(`${p}:${g}`);
      }
      if (pairs.length > 0) {
        config.productGradesMap = pairs.join(', ');
      }
    }

    return config;
  } catch"""
    text = text.replace(old_text, new_text)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print("Modified Code.gs")
else:
    print("Not found")
