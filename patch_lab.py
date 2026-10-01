import re

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 水分 & GC 實驗室記錄替換
c = re.sub(
    r'<div class="lab-row"><span>• 水分：</span><span class="fill-line">________ ppm</span></div>\s*<div class="lab-row"><span>• GC：</span><span class="fill-line">________ %</span></div>\s*<div class="lab-row sign-row"><span>簽章：____</span><span>日期：______</span></div>',
    r'<div class="lab-row" style="display:block;">• 水分：<span class="uline" style="width:12mm; display:inline-block; border-bottom:1px solid #000; margin:0 1mm;"></span> ppm</div>\n                  <div class="lab-row" style="display:block;">• GC：<span class="uline" style="width:15mm; display:inline-block; border-bottom:1px solid #000; margin:0 1mm;"></span> %</div>\n                  <div class="lab-row sign-row" style="display:block; margin-top:1mm;">簽章：<span class="uline sign-line" style="width:7mm; display:inline-block; border-bottom:1px solid #000; margin:0 1mm;"></span> 日期：<span class="uline sign-line" style="width:7mm; display:inline-block; border-bottom:1px solid #000; margin:0 1mm;"></span></div>',
    c
)

# Metal ICP-MS 實驗室記錄替換
c = re.sub(
    r'<div class="lab-row"><span>• 案號：</span><span class="fill-line">____________</span></div>\s*<div class="lab-row type-row"><span>\</span></div>\s*<div class="lab-row sign-row"><span>簽章：____</span><span>日期：______</span></div>',
    r'<div class="lab-row" style="display:block;">• 案號：<span class="uline" style="width:15mm; display:inline-block; border-bottom:1px solid #000; margin:0 1mm;"></span></div>\n                  <div class="lab-row type-row" style="display:block; margin: 1mm 0;"></div>\n                  <div class="lab-row sign-row" style="display:block; margin-top:1mm;">簽章：<span class="uline sign-line" style="width:7mm; display:inline-block; border-bottom:1px solid #000; margin:0 1mm;"></span> 日期：<span class="uline sign-line" style="width:7mm; display:inline-block; border-bottom:1px solid #000; margin:0 1mm;"></span></div>',
    c
)

# 順便把 compact 模式下的字體稍微改小一點，避免「時間」被腰斬
c = re.sub(
    r'\.label-page\.compact \.info-table \{[\s\S]*?\}',
    r'.label-page.compact .info-table {\n            width: 53%;\n            margin: 0;\n            font-size: 8.5px;\n          }',
    c
)
c = re.sub(
    r'\.label-page\.compact \.info-table td \{[\s\S]*?\}',
    r'.label-page.compact .info-table td {\n            padding: 0.3mm 0;\n          }',
    c
)
c = re.sub(
    r'\.label-page\.compact \.lab-record-box \{[\s\S]*?\}',
    r'.label-page.compact .lab-record-box {\n            width: 47%;\n            margin: 0;\n            padding: 1mm;\n            font-size: 8.5px;\n            display: flex;\n            flex-direction: column;\n            justify-content: space-evenly;\n          }',
    c
)

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'w', encoding='utf-8') as f:
    f.write(c)

