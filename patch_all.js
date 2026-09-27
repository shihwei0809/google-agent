const fs = require('fs');

const autoFnTemplate = `
  // 自動套用產品等級
  function autoSelectGrade(prodName) {
    if(!prodName) return;
    const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
    if(!cfgStr) return;
    try {
      const cfg = JSON.parse(cfgStr);
      const mapStr = cfg.OPTIONS_PRODUCT_GRADES_MAP || cfg.productGradesMap || '';
      if(!mapStr) return;
      const pairs = mapStr.split(',').map(s => s.trim()).filter(Boolean);
      const mapping = {};
      pairs.forEach(p => {
        const parts = p.split(':').map(s => s.trim());
        if(parts.length >= 2) mapping[parts[0]] = parts[1];
      });
      if(mapping[prodName]) {
        const gradeSelect = document.getElementById('grade');
        if (gradeSelect) gradeSelect.value = mapping[prodName];
      }
    } catch(e) { console.warn(e); }
  }
`;

function patchHtml(path) {
    if (!fs.existsSync(path)) return;
    let html = fs.readFileSync(path, 'utf8');
    
    // Inject function if missing
    if (!html.includes('function autoSelectGrade')) {
        html = html.replace('let allData = [];', autoFnTemplate + '\n  let allData = [];');
    }
    
    // Inject onchange if missing
    if (html.includes('id="productName" list="productList" placeholder="點選或輸入" required>')) {
        html = html.replace(
            '<input type="text" id="productName" list="productList" placeholder="點選或輸入" required>',
            '<input type="text" id="productName" list="productList" placeholder="點選或輸入" required onchange="autoSelectGrade(this.value)">'
        );
    }
    
    // Update onT100SelectChange if missing
    if (!html.includes('autoSelectGrade(item.productName);')) {
        html = html.replace(
            "document.getElementById('productName').value = item.productName || '';\n    document.getElementById('tankNo').value = item.tankNo || '';",
            "document.getElementById('productName').value = item.productName || '';\n    autoSelectGrade(item.productName);\n    document.getElementById('tankNo').value = item.tankNo || '';"
        );
    }
    
    // Apply getOrderSubmissionInfo fix
    const fixedMatch = `// 2. 槽號 + 品名 + 客戶/車號/櫃號比對 (針對無單號或預先充填送樣)
    const matchDetails = allData.find(s => {
      const sameProd = order.productName && s.productName && (String(s.productName).trim().toLowerCase() === String(order.productName).trim().toLowerCase());
      if (!sameProd) return false;

      let tankMatch = false;
      let contMatch = false;
      let hasTankData = order.tankNo && s.tankNo;
      let hasContData = order.container && s.customer;

      if (hasTankData) {
        tankMatch = String(s.tankNo).trim().toLowerCase() === String(order.tankNo).trim().toLowerCase();
      }
      if (hasContData) {
        contMatch = String(s.customer).trim().toLowerCase().includes(String(order.container).trim().toLowerCase()) ||
                    String(order.container).trim().toLowerCase().includes(String(s.customer).trim().toLowerCase());
      }

      if (hasTankData && hasContData) return tankMatch && contMatch;
      if (hasTankData) return tankMatch;
      if (hasContData) return contMatch;
      return false;
    });`;

    const oldMatchRegex = /\/\/ 2\. 槽號 \+ 品名 \+ 客戶\/車號\/櫃號比對 \(針對無單號或預先充填送樣\)\s*const matchDetails = allData\.find\(s => {[\s\S]*?return \(sameTank && sameProd\) \|\| \(sameCont && sameProd\);\s*}\);/g;
    
    html = html.replace(oldMatchRegex, fixedMatch);

    fs.writeFileSync(path, html);
    console.log("Patched", path);
}

const folders = ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版'];
folders.forEach(f => {
    patchHtml(`C:\\GOOGLE ANGET\\第二類_生產管理與API串接\\QC-系統客製化電子化工廠\\${f}\\index.html`);
});
