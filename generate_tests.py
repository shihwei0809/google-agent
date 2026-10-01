import os

test_dir = r'd:\GOOGLE ANGET\tsc_tests'
os.makedirs(test_dir, exist_ok=True)

base_css = '''
body { margin: 0; padding: 0; font-family: "Microsoft JhengHei", sans-serif; }
.label-border {
  border: 1.5px solid #000;
  padding: 1.5mm;
  box-sizing: border-box;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.label-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 0.5mm; }
.corp-title { font-size: 8px; font-weight: bold; }
.badge-cat { background: #1f2937; color: white; padding: 1mm 2mm; font-size: 11px; font-weight: bold; border-radius: 4px; }
.barcode-banner { border-top: 1px dashed #ccc; border-bottom: 1px dashed #ccc; margin: 0.5mm 0; padding: 0.5mm; text-align: center; }
.barcode-num { font-weight: 900; font-family: monospace; font-size: 10.5px; line-height: 1.25; letter-spacing: 0; }
.content-wrapper { display: flex; gap: 1.5mm; align-items: stretch; height: 100%; overflow: hidden; }
.info-table { width: 55%; margin: 0; font-size: 9.5px; border-collapse: collapse; }
.info-table td { padding: 0.5mm 0; vertical-align: top; }
.f-name { width: 9mm; color: #666; }
.f-val { font-weight: bold; }
.tag-grade { background: #f3f4f6; border: 1px solid #d1d5db; padding: 0 2px; border-radius: 2px; font-size: 8px; font-weight: normal; }
.tag-tank { background: #e0e7ff; color: #3730a3; border: 1px solid #c7d2fe; padding: 0 3px; border-radius: 3px; font-size: 8.5px; }
.lab-record-box { width: 45%; margin: 0; padding: 1mm; font-size: 9.5px; border: 1px dashed #999; border-radius: 4px; display: flex; flex-direction: column; justify-content: space-evenly; }
.uline { display: inline-block; border-bottom: 1px solid #000; width: 10mm; }
'''

html_content = '''
<div class="label-border" id="label-content">
  <div class="label-header">
    <div class="corp-title">鴻勝化學品管檢驗中心 (QC LAB)</div>
    <div class="badge-cat water">💧【水分 & GC】檢驗</div>
  </div>
  <div class="barcode-banner">
    <div class="barcode-num">ESPM411-20260927008, ESPM411-20260927009,<br>ESPM411-20260930007, ESPM411-20260930008</div>
  </div>
  <div class="content-wrapper">
    <table class="info-table">
      <tr><td class="f-name">品名</td><td class="f-val">EBR-P1R <span class="tag-grade">回收液</span></td></tr>
      <tr><td class="f-name">儲位</td><td class="f-val"><span class="tag-tank">TKC03</span></td></tr>
      <tr><td class="f-name">車牌</td><td class="f-val">KEC-2153 (櫃:2597)</td></tr>
      <tr><td class="f-name">數量</td><td class="f-val">進料 / 8000 KG</td></tr>
    </table>
    <div class="lab-record-box">
      <div>🧪 實驗室記錄：</div>
      <div>• 水分：<span class="uline"></span> ppm</div>
      <div>• GC：<span class="uline"></span> %</div>
      <div style="font-size:8px;">簽章：<span class="uline" style="width:5mm;"></span> 日期：<span class="uline" style="width:5mm;"></span></div>
    </div>
  </div>
</div>
'''

tests = [
    {
        "name": "Test_1_純橫向_90x50.html",
        "desc": "方案1：純橫式 90x50 (不旋轉)",
        "css": "@media print { @page { size: 90mm 50mm; margin: 0; } } .label-page { width: 90mm; height: 50mm; box-sizing: border-box; overflow: hidden; background: white; }",
        "body": f'<div class="label-page">{html_content}</div>',
        "script": ""
    },
    {
        "name": "Test_2_直式翻轉_50x90.html",
        "desc": "方案2：直式紙張 50x90 + CSS 旋轉 90 度",
        "css": "@media print { @page { size: 50mm 90mm; margin: 0; } } .label-page { width: 50mm; height: 90mm; box-sizing: border-box; position: relative; overflow: hidden; background: white; } .rotatable { width: 90mm; height: 50mm; transform: rotate(90deg) translateY(-100%); transform-origin: top left; }",
        "body": f'<div class="label-page"><div class="rotatable">{html_content}</div></div>',
        "script": ""
    },
    {
        "name": "Test_3_無視窗限制_交給驅動.html",
        "desc": "方案3：不設定 @page 尺寸，完全交由印表機驅動 (USER) 決定",
        "css": "@media print { @page { margin: 0; } } .label-page { width: 90mm; height: 50mm; box-sizing: border-box; overflow: hidden; background: white; }",
        "body": f'<div class="label-page">{html_content}</div>',
        "script": ""
    },
    {
        "name": "Test_4_100x60_稍微縮放.html",
        "desc": "方案4：加大畫布至 100x60 以防邊界被裁",
        "css": "@media print { @page { size: 100mm 60mm; margin: 0; } } .label-page { width: 90mm; height: 50mm; margin: 5mm; box-sizing: border-box; overflow: hidden; background: white; }",
        "body": f'<div class="label-page">{html_content}</div>',
        "script": ""
    },
    {
        "name": "Test_5_純橫式_90x50_旋轉90.html",
        "desc": "方案5：純橫式 90x50 (旋轉 90 度)",
        "css": "@media print { @page { size: 90mm 50mm; margin: 0; } } .label-page { width: 90mm; height: 50mm; box-sizing: border-box; overflow: hidden; background: white; } .rotatable { width: 90mm; height: 50mm; transform: rotate(90deg) translateY(-100%); transform-origin: top left; }",
        "body": f'<div class="label-page"><div class="rotatable">{html_content}</div></div>',
        "script": ""
    },
    {
        "name": "Test_6_純橫式_90x50_旋轉180.html",
        "desc": "方案6：純橫式 90x50 (旋轉 180 度/顛倒)",
        "css": "@media print { @page { size: 90mm 50mm; margin: 0; } } .label-page { width: 90mm; height: 50mm; box-sizing: border-box; overflow: hidden; background: white; } .rotatable { width: 90mm; height: 50mm; transform: rotate(180deg); transform-origin: center center; }",
        "body": f'<div class="label-page"><div class="rotatable">{html_content}</div></div>',
        "script": ""
    },
    {
        "name": "Test_7_純橫式_90x50_旋轉270.html",
        "desc": "方案7：純橫式 90x50 (旋轉 270 度/-90 度)",
        "css": "@media print { @page { size: 90mm 50mm; margin: 0; } } .label-page { width: 90mm; height: 50mm; box-sizing: border-box; overflow: hidden; background: white; } .rotatable { width: 90mm; height: 50mm; transform: rotate(-90deg) translateX(-100%); transform-origin: top left; }",
        "body": f'<div class="label-page"><div class="rotatable">{html_content}</div></div>',
        "script": ""
    },
    {
        "name": "Test_8_純圖片轉印模式.html",
        "desc": "方案8：圖片轉印模式 (終極大絕招)",
        "css": "@media print { @page { size: 90mm 50mm; margin: 0; } .no-print, .label-page { display: none !important; } #print-img { display: block !important; width: 90mm; height: 50mm; } } .label-page { width: 90mm; height: 50mm; box-sizing: border-box; background: white; position: relative; }",
        "body": f'<div class="label-page" id="capture-source">{html_content}</div><img id="print-img" style="display:none;" />',
        "script": '''<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script>
function printAsImage() {
  const btn = document.querySelector('.print-btn');
  btn.innerText = '正在轉換圖片...';
  btn.disabled = true;
  html2canvas(document.getElementById('capture-source'), { scale: 3, useCORS: true }).then(canvas => {
    document.getElementById('print-img').src = canvas.toDataURL('image/png');
    btn.innerText = '🖨️ 點我列印圖片測試';
    btn.disabled = false;
    setTimeout(() => window.print(), 500);
  });
}
</script>'''
    }
]

index_links = ""

for t in tests:
    print_action = "printAsImage()" if t["name"] == "Test_8_純圖片轉印模式.html" else "window.print()"
    
    full_html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8">
<title>{t["desc"]}</title>
<style>
{base_css}
{t["css"]}
.print-btn {{ display: block; margin: 20px; padding: 15px 30px; font-size: 20px; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; }}
@media print {{ .no-print {{ display: none !important; }} }}
</style>
</head>
<body style="background: #f3f4f6;">
<div class="no-print" style="text-align: center; padding: 20px;">
  <h2>{t["desc"]}</h2>
  <button class="print-btn" onclick="{print_action}">🖨️ 點我列印測試</button>
  <p>💡 列印時請選擇目的地：<b>TSC TDP-345</b>，紙張：<b>USER</b>，邊界：<b>無</b></p>
</div>
<div style="display:flex; justify-content:center;">
{t["body"]}
</div>
{t["script"]}
</body>
</html>'''
    with open(os.path.join(test_dir, t["name"]), "w", encoding="utf-8") as f:
        f.write(full_html)
    
    index_links += f'<li style="margin-bottom:15px;"><a href="{t["name"]}" target="_blank" style="font-size: 20px; text-decoration: none; color: #2563eb;">👉 {t["desc"]}</a></li>\n'

index_html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="UTF-8"><title>TSC 標籤列印終極測試包</title></head>
<body style="font-family: 'Microsoft JhengHei'; padding: 40px; background: #f8fafc;">
  <h1>🖨️ TSC 標籤列印終極測試包 (含 8 種排版與轉印法)</h1>
  <p>這 8 個測試擋涵蓋了所有可能的方向與尺寸設定，包含最後一個純圖片輸出大絕招。</p>
  <p style="color: red; font-weight: bold;">⚠️ 測試前請確認：1.紙張選 USER  2.邊界選「無」</p>
  <ul>
    {index_links}
  </ul>
</body>
</html>'''

with open(os.path.join(test_dir, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_html)

print("8個測試檔產生完成！")
