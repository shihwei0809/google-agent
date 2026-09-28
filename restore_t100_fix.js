const fs = require('fs');

['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版'].forEach(dir => {
  const p = 'C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/' + dir + '/index.html';
  let html = fs.readFileSync(p, 'utf8');
  
  const searchStr = `let filteredOrders = t100Orders.filter(o => 
      (o.date === selectedDate) && 
      (o.flowType === currentDeptTab || 
       (currentDeptTab === '液體' && o.flowType === '特殊液體') || 
       (currentDeptTab === '粉體' && o.flowType === '特殊粉體'))
    );`;
    
  const replaceStr = `let filteredOrders = t100Orders.filter(o => 
      (o.date === selectedDate) && 
      (o.flowType === currentDeptTab || 
       (currentDeptTab === '液體' && o.flowType === '特殊液體') || 
       (currentDeptTab === '粉體' && o.flowType === '特殊粉體'))
    );

    // 把尚未判定的退回單據 (pending 且 round > 1 或 status == failed) 加入到選項中
    const pendingFails = cData.filter(c => (c.status === 'failed' || (c.status === 'pending' && parseInt(c.round || 1) > 1)) && c.dept === currentDeptTab);
    if (pendingFails.length > 0) {
      filteredOrders.push({
         isResampleGroup: true
      });
      pendingFails.forEach(f => {
         let icon = '🔄[已自動重送待驗]';
         if (f.status === 'failed' && f.qcResult === 'FAIL') icon = '⛔[被退件需重送]';
         if (f.status === 'failed' && f.qcResult === '需特採') icon = '⚠️[不符內控需特採]';
         filteredOrders.push({
            ...f,
            isResampleItem: true,
            displayTitle: \`\${icon} \${f.barcode} - \${f.productName} (\${f.tankNo || f.customer || '-'}) (第\${f.round}次)\`
         });
      });
    }`;
    
  // Check if it's there
  if (html.includes(searchStr)) {
      html = html.replace(searchStr, replaceStr);
      fs.writeFileSync(p, html, 'utf8');
      console.log('Replaced in ' + dir);
  } else {
      console.log('Could not find search string in ' + dir);
  }
});
