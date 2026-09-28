const fs = require('fs');
const code = fs.readFileSync('C:/GOOGLE ANGET/第二類_生產管理與API串接/QC-系統客製化電子化工廠/Code.gs', 'utf8');
const regex = /getSheetByName\(['"]([^'"]+)['"]\)/g;
const names = new Set();
let m;
while ((m = regex.exec(code)) !== null) names.add(m[1]);
console.log('Sheets referenced:\n' + [...names].join('\n'));
