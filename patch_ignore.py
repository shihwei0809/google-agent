path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Get the ignore list right at the start of parseSheet
old_start = """        function parseSheet(sheetName) {
          const worksheet = workbook.Sheets[sheetName];"""
new_start = """        function parseSheet(sheetName) {
          const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
          const ignoredConfig = cfgStr ? JSON.parse(cfgStr)['T100_IGNORE_PRODUCTS'] : 'IPAHQ';
          const ignoredList = (ignoredConfig || 'IPAHQ').split(',').map(s => s.trim().toUpperCase());

          const worksheet = workbook.Sheets[sheetName];"""
text = text.replace(old_start, new_start)

# For shipping
old_out = """              if(!docNo || !prod) continue;

              // 嚴格只從「預計出貨日期」欄位抓取"""
new_out = """              if(!docNo || !prod) continue;
              if(ignoredList.includes(String(prod).trim().toUpperCase())) continue;

              // 嚴格只從「預計出貨日期」欄位抓取"""
text = text.replace(old_out, new_out)

# For incoming
old_in = """              if(!docNo || !prod) continue;

              // 嚴格只從「預計進貨日」欄位抓取"""
new_in = """              if(!docNo || !prod) continue;
              if(ignoredList.includes(String(prod).trim().toUpperCase())) continue;

              // 嚴格只從「預計進貨日」欄位抓取"""
text = text.replace(old_in, new_in)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
