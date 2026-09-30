# -*- coding: utf-8 -*-
import re

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Revert default width/height back to 90/50
content = re.sub(
    r"const savedWidthRaw = localStorage\.getItem\('HS_QC_PRINT_WIDTH'\) \|\| '50';.*?const savedHeight = isLegacyTscLandscape \? '90' : savedHeightRaw;",
    "const savedWidth = localStorage.getItem('HS_QC_PRINT_WIDTH') || '90';\n    const savedHeight = localStorage.getItem('HS_QC_PRINT_HEIGHT') || '50';",
    content, flags=re.DOTALL
)

content = re.sub(
    r"const width = parseInt\(document\.getElementById\('printLabelWidth'\)\.value \|\| '50', 10\);\s*const height = parseInt\(document\.getElementById\('printLabelHeight'\)\.value \|\| '90', 10\);",
    "const width = parseInt(document.getElementById('printLabelWidth').value || '90', 10);\n    const height = parseInt(document.getElementById('printLabelHeight').value || '50', 10);",
    content, flags=re.DOTALL
)

content = re.sub(
    r"document\.getElementById\('printLabelWidth'\)\.value = '50';\s*document\.getElementById\('printLabelHeight'\)\.value = '90';",
    "document.getElementById('printLabelWidth').value = '90';\n    document.getElementById('printLabelHeight').value = '50';",
    content, flags=re.DOTALL
)

content = content.replace(
    '已恢復 TSC 直式預設規格：50mm × 90mm',
    '已恢復預設規格：90mm × 50mm'
)

# 2. Fix getPrintDimensions
new_getPrintDimensions = '''function getPrintDimensions(rotateMode = 'none') {
    const configuredWidth = parseInt(localStorage.getItem('HS_QC_PRINT_WIDTH') || '90', 10);
    const configuredHeight = parseInt(localStorage.getItem('HS_QC_PRINT_HEIGHT') || '50', 10);
    const labelWidth = (Number.isFinite(configuredWidth) && configuredWidth > 0) ? configuredWidth : 90;
    const labelHeight = (Number.isFinite(configuredHeight) && configuredHeight > 0) ? configuredHeight : 50;

    const fixOrientation = localStorage.getItem('HS_QC_PRINT_FIX') === 'true';
    const needsRotate = rotateMode === '90' || rotateMode === '-90';
    // 勾選修正方向時，若原圖是橫式(寬>高)，強迫將 @page 改為直式，並在下方自動加上旋轉
    const swapPageAxes = needsRotate || (fixOrientation && labelWidth > labelHeight);

    return {
      labelWidth,
      labelHeight,
      pageWidth: swapPageAxes ? labelHeight : labelWidth,
      pageHeight: swapPageAxes ? labelWidth : labelHeight,
      autoRotate: (fixOrientation && labelWidth > labelHeight && !needsRotate)
    };
  }'''

content = re.sub(
    r"function getPrintDimensions\(rotateMode = 'none'\) \{.*?\}\s*\}\s*// 標籤機專用連續列印輸出核心",
    new_getPrintDimensions + "\n\n  // 標籤機專用連續列印輸出核心",
    content, flags=re.DOTALL
)

# 3. Fix doPrintLabels rotation and remove tsc-portrait
new_doPrintLabels_top = '''function doPrintLabels(data, waterCount, metalCount, rotateMode = 'none') {
    const totalLabels = waterCount + metalCount;
    const { labelWidth, labelHeight, pageWidth, pageHeight, autoRotate } = getPrintDimensions(rotateMode);
    let labelPagesHtml = '';
    let currentIdx = 1;

    const isCompact = labelHeight <= 60;
    const compactClass = isCompact ? ' compact' : '';
    const rotationTransform = rotateMode === '90' 
      ? 	ransform: rotate(90deg) translateY(-100%); transform-origin: top left; 
      : rotateMode === '-90'
      ? 	ransform: rotate(-90deg) translateX(-100%); transform-origin: top left;
      : rotateMode === '180'
      ? 	ransform: rotate(180deg); transform-origin: center center;
      : autoRotate
      ? 	ransform: rotate(90deg) translateY(-100%); transform-origin: top left;
      : '';
    const orientationClass = '';'''

content = re.sub(
    r"function doPrintLabels\(data, waterCount, metalCount, rotateMode = 'none'\) \{.*?const orientationClass = isTscPortrait \? ' tsc-portrait' : '';",
    new_doPrintLabels_top,
    content, flags=re.DOTALL
)

# 4. Remove .tsc-portrait CSS
content = re.sub(
    r"/\* TSC 直式模式.*?min-height: 0;\s*\}",
    "",
    content, flags=re.DOTALL
)

# 5. Fix dynamic font size for barcode
content = content.replace(
    '<div class="barcode-num"></div>',
    '<div class="barcode-num" style=""></div>'
)

# Restore the checkbox label to original text to avoid confusion
content = content.replace(
    'TSC 直式模式（高 > 寬時自動使用直向紙張）',
    '修正 TSC 標籤機方向錯亂 (印出跨兩張請勾我)'
)

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done modifying index.html')
