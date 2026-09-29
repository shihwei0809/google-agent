path = r'D:\GOOGLE ANGET\QC-系統客製化電子化工廠\2_PWA_App版\index.html'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add Checkbox to Modal
if 'id="printFixOrientation"' not in text:
    target_modal = r'(<span style="font-weight:bold; color:#334155;">📐 貼紙規格.*?</div>\s*</div>)'
    replacement_modal = r'\1\n      <div style="background:#fef2f2; padding:8px 12px; border-radius:8px; margin-bottom:12px; display:flex; align-items:center; font-size:0.85rem; border: 1px solid #fecaca; color: #991b1b; font-weight:bold;">\n        <label style="cursor:pointer; display:flex; align-items:center; gap:6px;"><input type="checkbox" id="printFixOrientation" style="width:16px;height:16px;"> ☑ 修正 TSC 標籤機方向錯亂 (印出跨兩張請勾我)</label>\n      </div>'
    text = re.sub(target_modal, replacement_modal, text, flags=re.DOTALL)

# 2. Add loading/saving state
if 'HS_QC_PRINT_FIX' not in text:
    text = text.replace(
        "const savedHeight = localStorage.getItem('HS_QC_PRINT_HEIGHT') || '100';",
        "const savedHeight = localStorage.getItem('HS_QC_PRINT_HEIGHT') || '100';\n    const savedFix = localStorage.getItem('HS_QC_PRINT_FIX') === 'true';"
    )
    text = text.replace(
        "document.getElementById('printLabelHeight').value = savedHeight;",
        "document.getElementById('printLabelHeight').value = savedHeight;\n    if(document.getElementById('printFixOrientation')) document.getElementById('printFixOrientation').checked = savedFix;"
    )
    
    # Save state
    save_logic = r"localStorage\.setItem\('HS_QC_PRINT_HEIGHT', height\);"
    save_logic_new = r"localStorage.setItem('HS_QC_PRINT_HEIGHT', height);\n    if(document.getElementById('printFixOrientation')) localStorage.setItem('HS_QC_PRINT_FIX', document.getElementById('printFixOrientation').checked);"
    text = re.sub(save_logic, save_logic_new, text)
    
    # Reset state
    text = text.replace(
        "localStorage.removeItem('HS_QC_PRINT_HEIGHT');",
        "localStorage.removeItem('HS_QC_PRINT_HEIGHT');\n    localStorage.removeItem('HS_QC_PRINT_FIX');\n    if(document.getElementById('printFixOrientation')) document.getElementById('printFixOrientation').checked = false;"
    )

# 3. Update doPrintLabels
if 'const fixOrientation =' not in text:
    text = text.replace(
        "const labelHeight = parseInt(localStorage.getItem('HS_QC_PRINT_HEIGHT') || '100', 10);",
        "const labelHeight = parseInt(localStorage.getItem('HS_QC_PRINT_HEIGHT') || '100', 10);\n    const fixOrientation = localStorage.getItem('HS_QC_PRINT_FIX') === 'true';\n    const finalWidth = fixOrientation ? labelHeight : labelWidth;\n    const finalHeight = fixOrientation ? labelWidth : labelHeight;"
    )

# 4. Modify label wrapper in JS template strings
text = text.replace(
    '<div class="label-page">',
    '<div class="page-wrapper">\n          <div class="label-page">'
)

text = re.sub(
    r'(<div class="label-footer">.*?</div>\s*</div>\s*)</div>',
    r'\1</div>\n        </div>',
    text,
    flags=re.DOTALL
)

# 5. Modify Print CSS
css_old = r'''          @page \{
            size: \$\{labelWidth\}mm \$\{labelHeight\}mm;
            margin: 0;
          \}
          \* \{ box-sizing: border-box; \}
          html, body \{
            width: \$\{labelWidth\}mm;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft JhengHei", sans-serif;
            background: #fff;
            color: #000;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          \}
          \.label-page \{
            width: \$\{labelWidth\}mm;
            height: \$\{labelHeight\}mm;
            max-width: \$\{labelWidth\}mm;
            max-height: \$\{labelHeight\}mm;
            padding: 3mm 3\.5mm;
            page-break-after: always;
            page-break-inside: avoid;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
          \}
          \.label-page:last-child \{
            page-break-after: auto;
          \}'''

css_new = r'''          @page {
            size: ${finalWidth}mm ${finalHeight}mm;
            margin: 0;
          }
          * { box-sizing: border-box; }
          html, body {
            width: ${finalWidth}mm;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft JhengHei", sans-serif;
            background: #fff;
            color: #000;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .page-wrapper {
            width: ${finalWidth}mm;
            height: ${finalHeight}mm;
            display: flex;
            justify-content: center;
            align-items: center;
            page-break-after: always;
            page-break-inside: avoid;
            overflow: hidden;
          }
          .page-wrapper:last-child {
            page-break-after: auto;
          }
          .label-page {
            width: ${labelWidth}mm;
            height: ${labelHeight}mm;
            padding: 3mm 3.5mm;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            ${fixOrientation ? 'transform: rotate(-90deg); transform-origin: center;' : ''}
          }'''

text = re.sub(css_old, css_new, text, flags=re.DOTALL)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
print("QC PWA Index Patched!")
