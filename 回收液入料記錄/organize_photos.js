const fs = require('fs');
const path = require('path');

function pad(n) {
  return (n < 10 ? '0' : '') + n;
}

function getWeeklyFolderName(dateInput) {
  let d;
  if (!dateInput) d = new Date();
  else if (typeof dateInput === 'string') {
    const m = dateInput.match(/(\d{4})[-_/](\d{1,2})[-_/](\d{1,2})/);
    if (m) d = new Date(parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10));
    else d = new Date(dateInput);
  } else d = new Date(dateInput);
  if (isNaN(d.getTime())) d = new Date();

  // 取得該週星期一 (以星期一為每週開始，星期日為結束)
  const day = d.getDay(); // 0 是週日, 1 是週一...
  const diffToMon = (day === 0 ? -6 : 1) - day;
  const monday = new Date(d.getFullYear(), d.getMonth(), d.getDate() + diffToMon);
  const sunday = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 6);

  // ISO 週數計算 (以週四決定所屬年與週次)
  const target = new Date(monday.getFullYear(), monday.getMonth(), monday.getDate() + 3);
  const jan4 = new Date(target.getFullYear(), 0, 4);
  const diffDays = Math.round((target - jan4) / 86400000);
  const weekNum = 1 + Math.round((diffDays - (3 - ((jan4.getDay() + 6) % 7))) / 7);
  const weekStr = pad(weekNum);

  const m1 = pad(monday.getMonth() + 1);
  const d1 = pad(monday.getDate());
  const m2 = pad(sunday.getMonth() + 1);
  const d2 = pad(sunday.getDate());

  return `${target.getFullYear()}年第${weekStr}週 (${m1}.${d1}~${m2}.${d2})`;
}

// 尋找 Google Drive 路徑
function findGoogleDriveFolder() {
  const directPath = 'G:\\我的雲端硬碟\\回收液照片歸檔';
  if (fs.existsSync(directPath)) return directPath;

  const letters = 'CDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  for (const l of letters) {
    const p = `${l}:\\我的雲端硬碟\\回收液照片歸檔`;
    if (fs.existsSync(p)) return p;
  }
  return null;
}

function main() {
  const targetDir = findGoogleDriveFolder();
  if (!targetDir) {
    console.error('❌ 找不到「我的雲端硬碟\\回收液照片歸檔」資料夾！');
    process.exit(1);
  }

  console.log(`🚀 目標資料夾：${targetDir}`);

  const items = fs.readdirSync(targetDir);
  const files = items.filter(f => {
    const full = path.join(targetDir, f);
    return fs.statSync(full).isFile() && /\.(jpg|jpeg|png)$/i.test(f);
  });

  console.log(`📦 掃描到未分類照片檔案：${files.length} 個`);

  let movedCount = 0;
  for (const file of files) {
    let targetDate = null;
    const m1 = file.match(/(\d{4})[-_/](\d{1,2})[-_/](\d{1,2})/);
    if (m1) {
      targetDate = new Date(parseInt(m1[1], 10), parseInt(m1[2], 10) - 1, parseInt(m1[3], 10));
    } else {
      const m2 = file.match(/([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2}\s+\d{4})/);
      if (m2) {
        const d2 = new Date(m2[1]);
        if (!isNaN(d2.getTime())) targetDate = d2;
      }
    }

    if (!targetDate) {
      const stat = fs.statSync(path.join(targetDir, file));
      targetDate = stat.birthtime || stat.mtime;
    }

    const folderName = getWeeklyFolderName(targetDate);
    const destDir = path.join(targetDir, folderName);

    if (!fs.existsSync(destDir)) {
      fs.mkdirSync(destDir, { recursive: true });
      console.log(`📁 建立週資料夾：${folderName}`);
    }

    const oldPath = path.join(targetDir, file);
    const newPath = path.join(destDir, file);
    fs.renameSync(oldPath, newPath);
    movedCount++;
    console.log(`  -> [${folderName}] ${file}`);
  }

  console.log('========================================');
  console.log(`✅ 整理完成！共分類移入 ${movedCount} 個照片至各週資料夾。`);
}

main();
