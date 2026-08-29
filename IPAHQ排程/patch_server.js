const fs = require('fs');
let serverJs = fs.readFileSync('C:/GOOGLE ANGET/IPAHQ排程/server.js', 'utf8');

const additionalCode = `
// TSMC 3-in-1 API
app.get('/api/orders/:id/tsmc-3in1', (req, res) => {
  try {
    const orderId = req.params.id;
    const db = getDB();
    const order = db.orders.find(o => o.id === orderId);
    if (!order) return res.status(404).json({ success: false, message: '找不到訂單' });
    
    const { execFile } = require('child_process');
    const path = require('path');
    
    const destB64 = Buffer.from(order.destination || '').toString('base64');
    const pyScript = path.join(__dirname, 'generate_3in1.py');
    const batchNo = order.product || ''; 
    execFile('python', [pyScript, batchNo, destB64, order.fill_hand || '', order.driver || '', order.plate || '', order.id || ''], (err, stdout, stderr) => {
      if (err) {
         console.error(err);
         return res.status(500).json({ success: false, message: '生成失敗' });
      }
      const outFile = stdout.trim();
      if (fs.existsSync(outFile)) {
         res.download(outFile);
      } else {
         res.status(500).json({ success: false, message: '找不到生成的檔案' });
      }
    });
  } catch(e) {
    res.status(500).json({ success: false, message: e.message });
  }
});

// Location Mapping API
const LOCATION_MAPPING_FILE = path.join(__dirname, '地點代號對照表.xlsx');
app.get('/api/location-mappings', (req, res) => {
  try {
    if (!fs.existsSync(LOCATION_MAPPING_FILE)) {
      return res.json({ success: true, data: [] });
    }
    const wb = xlsx.readFile(LOCATION_MAPPING_FILE);
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const data = xlsx.utils.sheet_to_json(sheet, { header: ['shortName', 'longCode'], range: 1 });
    res.json({ success: true, data });
  } catch (err) {
    res.status(500).json({ success: false, message: '讀取失敗: ' + err.message });
  }
});

app.post('/api/location-mappings', (req, res) => {
  try {
    const { mappings, operator, role } = req.body;
    const wb = xlsx.utils.book_new();
    const wsData = [['短地點', '長代號']];
    mappings.forEach(m => {
      if (m.shortName && m.longCode) {
        wsData.push([m.shortName, m.longCode]);
      }
    });
    const ws = xlsx.utils.aoa_to_sheet(wsData);
    xlsx.utils.book_append_sheet(wb, ws, '對照表');
    xlsx.writeFile(wb, LOCATION_MAPPING_FILE);
    
    const db = getDB();
    addLog(db, operator || '未知', role || 'admin', '更新地點對照表', \`更新了 \${mappings.length} 筆資料\`);
    saveDB(db);
    res.json({ success: true, message: '地點對照表更新成功' });
  } catch (err) {
    res.status(500).json({ success: false, message: '儲存失敗: ' + err.message });
  }
});
`;

if (!serverJs.includes('/api/location-mappings')) {
    serverJs = serverJs.replace('app.listen(', additionalCode + '\n\napp.listen(');
    fs.writeFileSync('C:/GOOGLE ANGET/IPAHQ排程/server.js', serverJs, 'utf8');
}
console.log('patched server.js');
