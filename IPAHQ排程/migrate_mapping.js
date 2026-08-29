const fs = require('fs');
const xlsx = require('./node_modules/xlsx');

const filePath = 'C:/GOOGLE ANGET/IPAHQ排程/地點代號對照表.xlsx';
const wb = xlsx.readFile(filePath);
const sheet = wb.Sheets[wb.SheetNames[0]];
const data = xlsx.utils.sheet_to_json(sheet, { header: 1 });

// Build new 3-col data
// Data may be:
// - Already 3-col: [shortName, fullName, code]  (header: 送達地簡稱, 送達地全名, 送達地點代號)
// - Already 3-col but with wrong header: [送達地簡稱, 全名, 點代號]
// - Legacy 2-col: [shortName, code]

const newData = [];
const header = data[0] || [];
const is3col = header.length >= 3;
const is2col = header.length === 2;

// Add proper header
newData.push(['送達地簡稱', '送達地全名', '送達地點代號']);

for (let i = 1; i < data.length; i++) {
  const row = data[i];
  if (!row || !row[0]) continue;
  const short = String(row[0] || '').trim();
  if (!short) continue;

  if (is3col) {
    // Was 3-col, but col C may have been lost in previous migration
    // Check: if col[2] has value, it's code. If col[1] has value and col[2] is empty, might be legacy
    const fullName = String(row[1] || '').trim();
    const codeOrEmpty = String(row[2] || '').trim();
    // If no col[2] but col[1] looks like a barcode (all caps, 9 chars), treat col[1] as code
    const col1LooksLikeCode = fullName && /^[A-Z0-9]{5,12}$/.test(fullName.replace(/\s/g, ''));
    if (col1LooksLikeCode && !codeOrEmpty) {
      newData.push([short, '', fullName]);
    } else {
      newData.push([short, fullName, codeOrEmpty]);
    }
  } else if (is2col) {
    const code = String(row[1] || '').trim();
    newData.push([short, '', code]);
  } else {
    newData.push([short, '', '']);
  }
}

const newWs = xlsx.utils.aoa_to_sheet(newData);
const newWb = xlsx.utils.book_new();
xlsx.utils.book_append_sheet(newWb, newWs, '對照表');
xlsx.writeFile(newWb, filePath);

// Verify
const vWb = xlsx.readFile(filePath);
const vSheet = vWb.Sheets[vWb.SheetNames[0]];
const vData = xlsx.utils.sheet_to_json(vSheet, {header: 1});
console.log('Header:', vData[0]);
console.log('Row 1:', vData[1]);
console.log('Total rows:', vData.length - 1);
