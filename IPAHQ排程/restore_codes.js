const fs = require('fs');
const xlsx = require('./node_modules/xlsx');

const filePath = 'C:/GOOGLE ANGET/IPAHQ排程/地點代號對照表.xlsx';

// Original codes from the previous 2-col Excel (backup data)
const knownCodes = {
  "15P5":  "E1550155A",
  "15P6":  "E1550156A",
  "18P3B": "EF180183B",
  "12P7":  "E00700001",
  "12P1":  "E01200001",
  "12P2":  "E01200002",
  "12P8":  "E01200008",
  "14P6":  "E01400006",
  "15P2":  "E01500002",
  "15P3":  "E01500003",
  "15P4":  "E01500004",
  "15P7":  "E01500007",
  "15BP5A":"E15B0005A",
  "18P1":  "EF180181A",
  "18P2":  "EF180182A",
  "18P3":  "EF180183A",
  "18P5":  "EF180185A",
  "18P6":  "EF180186A",
  "18P7":  "EF180187A",
  "18P8":  "EF180188A",
  "AP7P1": "EAP700001",
  "AP7P2": "EAP700002",
  "AP8":   "EAP800001",
  "20P1":  "EF200001A",
  "22P1":  "EF220001A",
  "14P5":  "E01400005",
  "14P1":  "E01400001",
  "A6A0":  "EA6A0001",
  "B30":   "EB300005A",
  "14P4":  "E01400004",
};

const wb = xlsx.readFile(filePath);
const sheet = wb.Sheets[wb.SheetNames[0]];
const data = xlsx.utils.sheet_to_json(sheet, { header: 1 });

const newData = [data[0]]; // keep header as-is

for (let i = 1; i < data.length; i++) {
  const row = data[i];
  if (!row || !row[0]) continue;
  const short = String(row[0]).trim().toUpperCase();
  const fullName = String(row[1] || '').trim();
  // Restore code from known backup if cell is empty
  const existingCode = String(row[2] || '').trim();
  const code = existingCode || knownCodes[short] || '';
  newData.push([String(row[0]).trim(), fullName, code]);
}

const newWs = xlsx.utils.aoa_to_sheet(newData);
const newWb = xlsx.utils.book_new();
xlsx.utils.book_append_sheet(newWb, newWs, '對照表');
xlsx.writeFile(newWb, filePath);

// Verify
const v = xlsx.readFile(filePath);
const vs = v.Sheets[v.SheetNames[0]];
const vd = xlsx.utils.sheet_to_json(vs, {header:1});
console.log('Restored! Sample:');
vd.slice(0, 5).forEach(r => console.log(JSON.stringify(r)));
