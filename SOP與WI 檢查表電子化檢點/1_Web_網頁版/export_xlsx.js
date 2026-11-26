// 真實 .xlsx 匯出引擎 (ExcelJS) — 含框線、合併儲存格、透明手寫簽名 PNG 圖片嵌入
// 若離線未載入 ExcelJS，自動降級為 .xls HTML 表格匯出
window.exportRecordToXlsx = async function (rec) {
  const tpl = rec.templateSnapshot;
  const m = rec.meta || {};
  const fileName = `${tpl.formCode}_${rec.id}_${m.date || 'export'}.xlsx`;

  if (typeof ExcelJS === 'undefined') {
    const el = document.getElementById('a4-print-area');
    const html = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel"><head><meta charset="UTF-8"><style>table{border-collapse:collapse;}td,th{border:1px solid #000;padding:4px;font-size:11pt;}</style></head><body>${el ? el.innerHTML : ''}</body></html>`;
    const blob = new Blob([html], { type: 'application/vnd.ms-excel;charset=utf-8;' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = fileName.replace('.xlsx', '.xls');
    a.click();
    return { mode: 'xls-fallback', fileName: a.download };
  }

  const wb = new ExcelJS.Workbook();
  wb.creator = 'shihwei0809 SOP/WI 電子檢點系統';
  wb.created = new Date();
  const ws = wb.addWorksheet(tpl.shortCode + ' ' + tpl.title.slice(0, 18), {
    pageSetup: { paperSize: 9, orientation: 'portrait', fitToPage: true, fitToWidth: 1, fitToHeight: 1 }
  });

  const thinBorder = {
    top: { style: 'thin' }, left: { style: 'thin' },
    bottom: { style: 'thin' }, right: { style: 'thin' }
  };

  ws.columns = [
    { width: 6 }, { width: 32 }, { width: 14 }, { width: 16 }, { width: 16 }, { width: 18 }
  ];

  // Title
  ws.mergeCells('A1:F1');
  ws.getCell('A1').value = tpl.company;
  ws.getCell('A1').font = { name: '標楷體', size: 13, bold: true };
  ws.getCell('A1').alignment = { horizontal: 'center', vertical: 'middle' };

  ws.mergeCells('A2:F2');
  ws.getCell('A2').value = tpl.title;
  ws.getCell('A2').font = { name: '標楷體', size: 15, bold: true, underline: true };
  ws.getCell('A2').alignment = { horizontal: 'center', vertical: 'middle' };

  // Plant & Date
  const plantStr = tpl.plantDisplayMode === 'text'
    ? `廠區：${m.plant || ''}`
    : (tpl.plants || []).map(p => `${m.plant === p ? '☑' : '☐'}${p}`).join('  ');
  ws.mergeCells('A3:D3');
  ws.getCell('A3').value = plantStr;
  ws.getCell('A3').font = { name: '標楷體', size: 10 };
  ws.mergeCells('E3:F3');
  ws.getCell('E3').value = `檢查日期：${m.date || ''}`;
  ws.getCell('E3').alignment = { horizontal: 'right' };
  ws.getCell('E3').font = { name: '標楷體', size: 10 };

  let rowIdx = 4;

  // Layout-specific header & body
  if (tpl.layoutType === 'single_stage') {
    ws.mergeCells(`A${rowIdx}:F${rowIdx}`);
    ws.getCell(`A${rowIdx}`).value = `儲槽編號：${m.tankNo || ''}    卸貨泵浦編號：${m.pumpNo || ''}    儲存料品名稱：${m.material || ''}`;
    ws.getCell(`A${rowIdx}`).border = thinBorder;
    rowIdx++;

    ws.mergeCells(`A${rowIdx}:F${rowIdx}`);
    ws.getCell(`A${rowIdx}`).value = `(A)最大容積：${m.volA || 0} KL － (B)目前容積：${m.volB || 0} KL ＝ (C)可存容積：${m.volC || 0} KL ｜ 可存：${m.mtAvail || 0} M/T (約${m.trucks || 0}車)，預定入槽：${m.mtPlan || 0} M/T`;
    ws.getCell(`A${rowIdx}`).border = thinBorder;
    rowIdx++;

    ws.mergeCells(`A${rowIdx}:D${rowIdx}`);
    ws.getCell(`A${rowIdx}`).value = '檢查項目';
    ws.getCell(`A${rowIdx}`).alignment = { horizontal: 'center' };
    ws.getCell(`A${rowIdx}`).font = { bold: true };
    ws.mergeCells(`E${rowIdx}:F${rowIdx}`);
    ws.getCell(`E${rowIdx}`).value = '檢查結果';
    ws.getCell(`E${rowIdx}`).alignment = { horizontal: 'center' };
    ws.getCell(`E${rowIdx}`).font = { bold: true };
    for (let c = 1; c <= 6; c++) ws.getRow(rowIdx).getCell(c).border = thinBorder;
    rowIdx++;

    const sections = {};
    tpl.items.forEach(it => { (sections[it.section] = sections[it.section] || []).push(it); });
    Object.entries(sections).forEach(([sec, list]) => {
      const startR = rowIdx;
      list.forEach(it => {
        const a = (rec.answers && rec.answers[it.id]) || {};
        ws.mergeCells(`B${rowIdx}:D${rowIdx}`);
        ws.getCell(`B${rowIdx}`).value = it.name;
        ws.mergeCells(`E${rowIdx}:F${rowIdx}`);
        let res = '';
        if (it.mode === 'num_only') res = `${a.num || ''} ${it.unit || ''}`;
        else {
          res = `${a.choice === '是' ? '☑是' : '☐是'}  ${a.choice === '否' ? '☑否' : '☐否'}${a.choice === '＼' ? ' (＼)' : ''}`;
          if (it.mode === 'yn_num' && a.num) res += ` (${a.num} ${it.unit || ''})`;
        }
        ws.getCell(`E${rowIdx}`).value = res;
        ws.getCell(`E${rowIdx}`).alignment = { horizontal: 'center' };
        for (let c = 1; c <= 6; c++) ws.getRow(rowIdx).getCell(c).border = thinBorder;
        rowIdx++;
      });
      if (rowIdx - 1 >= startR) {
        ws.mergeCells(`A${startR}:A${rowIdx - 1}`);
        ws.getCell(`A${startR}`).value = sec;
        ws.getCell(`A${startR}`).alignment = { horizontal: 'center', vertical: 'middle', wrapText: true };
        ws.getCell(`A${startR}`).border = thinBorder;
      }
    });
  } else if (tpl.layoutType === 'dual_compare') {
    const infoStr = (tpl.extraHeaderFields || []).map(f => `${f.label}：${m[f.key] || ''}`).join('   ');
    ws.mergeCells(`A${rowIdx}:F${rowIdx}`);
    ws.getCell(`A${rowIdx}`).value = infoStr + (m.opType ? `   作業別：${m.opType}` : '');
    ws.getCell(`A${rowIdx}`).border = thinBorder;
    rowIdx++;

    ws.mergeCells(`A${rowIdx}:C${rowIdx}`);
    ws.getCell(`A${rowIdx}`).value = '安檢 / 清潔度檢核項目';
    ws.getCell(`D${rowIdx}`).value = tpl.colLeftLabel || '運輸公司檢點';
    ws.mergeCells(`E${rowIdx}:F${rowIdx}`);
    ws.getCell(`E${rowIdx}`).value = tpl.colRightLabel || '現場人員確認';
    for (let c = 1; c <= 6; c++) {
      ws.getRow(rowIdx).getCell(c).border = thinBorder;
      ws.getRow(rowIdx).getCell(c).font = { bold: true };
      ws.getRow(rowIdx).getCell(c).alignment = { horizontal: 'center' };
    }
    rowIdx++;

    tpl.items.forEach(it => {
      const a = (rec.answers && rec.answers[it.id]) || {};
      ws.getCell(`A${rowIdx}`).value = it.section;
      ws.mergeCells(`B${rowIdx}:C${rowIdx}`);
      ws.getCell(`B${rowIdx}`).value = it.name;
      ws.getCell(`D${rowIdx}`).value = it.leftDisabled ? '＼' : (a.left || '');
      ws.mergeCells(`E${rowIdx}:F${rowIdx}`);
      ws.getCell(`E${rowIdx}`).value = (a.right || '') + (a.num ? ` (${a.num} ${it.unit || ''})` : '');
      ws.getCell(`D${rowIdx}`).alignment = { horizontal: 'center' };
      ws.getCell(`E${rowIdx}`).alignment = { horizontal: 'center' };
      for (let c = 1; c <= 6; c++) ws.getRow(rowIdx).getCell(c).border = thinBorder;
      rowIdx++;
    });
  } else {
    // before_after (6.3 / 6.4)
    const infoStr = (tpl.extraHeaderFields || []).map(f => `${f.label}：${m[f.key] || ''}`).join('   ');
    ws.mergeCells(`A${rowIdx}:F${rowIdx}`);
    ws.getCell(`A${rowIdx}`).value = infoStr;
    ws.getCell(`A${rowIdx}`).border = thinBorder;
    rowIdx++;

    ['設備', '檢查項目', '狀態', '接合前', '拆卸後', '備註'].forEach((h, i) => {
      const cell = ws.getRow(rowIdx).getCell(i + 1);
      cell.value = h;
      cell.font = { bold: true };
      cell.alignment = { horizontal: 'center' };
      cell.border = thinBorder;
    });
    rowIdx++;

    tpl.items.forEach(it => {
      const a = (rec.answers && rec.answers[it.id]) || {};
      ws.getCell(`A${rowIdx}`).value = 'ISO TANK';
      ws.getCell(`B${rowIdx}`).value = it.name;
      ws.getCell(`C${rowIdx}`).value = it.stateLabel || '';
      ws.getCell(`D${rowIdx}`).value = it.beforeDisabled ? '＼' : (a.before || '');
      ws.getCell(`E${rowIdx}`).value = a.after || '';
      ws.getCell(`F${rowIdx}`).value = a.note || '';
      for (let c = 1; c <= 6; c++) ws.getRow(rowIdx).getCell(c).border = thinBorder;
      rowIdx++;
    });
  }

  // Remark row
  const itemNotes = tpl.items.map(it => {
    const a = rec.answers && rec.answers[it.id];
    return a && a.note ? `【${it.name}】${a.note}` : '';
  }).filter(Boolean);
  const fullRemark = [m.remark, ...itemNotes].filter(Boolean).join('；');
  ws.getCell(`A${rowIdx}`).value = '備註';
  ws.mergeCells(`B${rowIdx}:F${rowIdx}`);
  ws.getCell(`B${rowIdx}`).value = (tpl.footerNote ? tpl.footerNote + '\n' : '') + (fullRemark || '');
  ws.getCell(`B${rowIdx}`).alignment = { wrapText: true };
  for (let c = 1; c <= 6; c++) ws.getRow(rowIdx).getCell(c).border = thinBorder;
  ws.getRow(rowIdx).height = 34;
  rowIdx++;

  // Signatures row + real PNG image embedding!
  const sigHeaderRow = rowIdx;
  const sigImgRow = rowIdx + 1;
  ws.getRow(sigImgRow).height = 56;
  const signers = tpl.signers || [];
  signers.forEach((s, idx) => {
    const col = Math.min(idx + 1, 6);
    const hdr = ws.getRow(sigHeaderRow).getCell(col);
    hdr.value = s.label;
    hdr.font = { bold: true };
    hdr.alignment = { horizontal: 'center' };
    hdr.border = thinBorder;

    const sigCell = ws.getRow(sigImgRow).getCell(col);
    sigCell.border = thinBorder;
    const sigData = rec.signatures && rec.signatures[s.key];
    if (sigData && sigData.dataUrl && sigData.dataUrl.startsWith('data:image/png;base64,')) {
      const imgId = wb.addImage({ base64: sigData.dataUrl, extension: 'png' });
      ws.addImage(imgId, {
        tl: { col: col - 1 + 0.08, row: sigImgRow - 1 + 0.08 },
        ext: { width: 92, height: 42 }
      });
      sigCell.value = sigData.signedAt ? `${sigData.name || ''} ${sigData.signedAt}` : (sigData.name || '');
      sigCell.alignment = { vertical: 'bottom', horizontal: 'center' };
      sigCell.font = { size: 8, color: { argb: 'FF555555' } };
    }
  });

  // Form code footer
  const codeRow = sigImgRow + 1;
  ws.mergeCells(`A${codeRow}:F${codeRow}`);
  ws.getCell(`A${codeRow}`).value = tpl.formCode;
  ws.getCell(`A${codeRow}`).alignment = { horizontal: 'right' };
  ws.getCell(`A${codeRow}`).font = { name: 'Consolas', size: 10, bold: true };

  const buffer = await wb.xlsx.writeBuffer();
  const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  return { mode: 'xlsx', fileName };
};
