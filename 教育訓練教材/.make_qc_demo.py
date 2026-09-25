from datetime import date
from pathlib import Path
import re
import shutil
from openpyxl import Workbook

source = Path(r"C:\GOOGLE ANGET\QC-系統客製化電子化工廠")
demo = source / ".video_demo"
demo.mkdir(exist_ok=True)
shutil.copy2(source / "2_PWA_App版" / "index.html", demo / "index.html")
html = (demo / "index.html").read_text(encoding="utf-8-sig")
api_line = "let GAS_API_URL = localStorage.getItem('HS_QC_GAS_API_URL') || DEFAULT_GAS_API_URL;"
assert api_line in html
html = html.replace(api_line, "let GAS_API_URL = ''; // isolated local demo: cloud disabled", 1)
html, fallback_count = re.subn(
    r'allData = \[\s*\{ id: "sample-1".*?\n        \];',
    "allData = [];",
    html,
    count=1,
    flags=re.S,
)
assert fallback_count == 1, "offline fallback sample records not found"
html, count = re.subn(
    r"  let t100Orders = \[.*?\n  \];\n\n  let t100FilterMode",
    "  let t100Orders = [];\n\n  let t100FilterMode",
    html,
    count=1,
    flags=re.S,
)
assert count == 1
send_guard = "if (localTeamsConfig.enableRealSend) {"
assert send_guard in html
html = html.replace(send_guard, "if (false && localTeamsConfig.enableRealSend) {", 1)
import_button = "onclick=\"document.getElementById('excelFileInput').click()\""
assert import_button in html
html = html.replace(import_button, 'onclick="loadDemoExcel()"', 1)
html = html.replace(
    'document.getElementById(\'envBadge\').innerText = "💻 獨立 PWA 運作模式";',
    'document.getElementById(\'envBadge\').innerText = "🧪 示範模式（合成資料）";',
    1,
)
hook = '''
  async function loadDemoExcel() {
    const button = document.querySelector('.btn-t100-upload');
    const oldText = button ? button.innerText : '';
    if (button) { button.disabled = true; button.innerText = '讀取示範排程中...'; }
    try {
      const response = await fetch('/QC_排程匯入示範_合成資料.xlsx', { cache: 'no-store' });
      if (!response.ok) throw new Error('示範檔讀取失敗');
      const file = new File([await response.arrayBuffer()], 'QC_排程匯入示範_合成資料.xlsx', { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      handleExcelUpload({ target: { files: [file] } });
    } catch (error) { alert('匯入示範排程失敗：' + error.message); }
    finally { if (button) { button.disabled = false; button.innerText = oldText; } }
  }
'''
insert_at = html.rfind('</script>')
assert insert_at >= 0
html = html[:insert_at] + hook + html[insert_at:]
(demo / "index.html").write_text(html, encoding="utf-8")

wb = Workbook()
ws = wb.active
ws.title = "明天進出貨排程報表(槽車)"
today = date(2026, 9, 25).isoformat()
ws.append(["出貨通知單", "預計出貨日期", "預計出貨時間", "品名", "儲位名稱", "規格", "交易對象簡稱", "車牌號碼", "換算數量", "注意事項"])
ws.append(["DEMO-OUT-20260925-01", today, "09:30", "DEMO-IPA", "TK-DEMO-01", "示範規格", "示範客戶", "DEMO-TRUCK-01", 1000, "訓練示範資料"])
ws.append([])
ws.append(["入庫單", "預計進貨日", "預計進貨時間", "品名", "槽別", "規格", "供應商簡稱", "出貨廠別(廠商)", "車牌號碼", "櫃號", "預計進貨數量(KG)", "備註"])
ws.append(["DEMO-IN-20260925-01", today, "14:00", "DEMO-IPA", "TK-DEMO-02", "示範規格", "示範供應商", "示範廠別", "DEMO-TRUCK-02", "DEMO-BOX-02", 800, "訓練示範資料"])
wb.save(demo / "QC_排程匯入示範_合成資料.xlsx")
print(demo)
