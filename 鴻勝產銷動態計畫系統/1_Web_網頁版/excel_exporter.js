/**
 * 鴻勝產銷動態計畫系統 - 優化版公式 Excel (.xlsx) 匯出器 (基於 ExcelJS)
 * 輸出 7 個乾淨工作表：產銷總表 / 精餾產銷 / 初餾產銷 / 調配產銷 / 秏料 / 產線排程明細 / 異常與預警摘要
 * 全面修復舊版 #REF!、SUM(K:L) 錯位、初餾代工入庫正負號錯誤與龐大空白列問題。
 */
(function (root) {
  'use strict';

  var HEADER_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1E293B' } };
  var SUBHDR_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF334155' } };
  var SECTION_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFE2E8F0' } };
  var INPUT_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFFFBEB' } };
  var AUTO_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF0F9FF' } };
  var ALERT_RED_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFEE2E2' } };
  var ALERT_ORG_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFFEDD5' } };
  var ALERT_YEL_FILL = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFFEF3C7' } };
  var THIN_BORDER = {
    top: { style: 'thin', color: { argb: 'FFCBD5E1' } },
    left: { style: 'thin', color: { argb: 'FFCBD5E1' } },
    bottom: { style: 'thin', color: { argb: 'FFCBD5E1' } },
    right: { style: 'thin', color: { argb: 'FFCBD5E1' } }
  };
  var FONT_HDR = { name: 'Microsoft JhengHei', size: 10, bold: true, color: { argb: 'FFFFFFFF' } };
  var FONT_BODY = { name: 'Microsoft JhengHei', size: 10, color: { argb: 'FF0F172A' } };
  var FONT_BOLD = { name: 'Microsoft JhengHei', size: 10, bold: true, color: { argb: 'FF0F172A' } };
  var FONT_RED = { name: 'Microsoft JhengHei', size: 10, bold: true, color: { argb: 'FFB91C1C' } };

  function styleHeaderRow(row) {
    row.height = 24;
    row.eachCell(function (cell) {
      cell.fill = HEADER_FILL;
      cell.font = FONT_HDR;
      cell.alignment = { vertical: 'middle', horizontal: 'center', wrapText: true };
      cell.border = THIN_BORDER;
    });
  }

  function styleDataRow(row, numCols, alertByCol) {
    row.height = 20;
    for (var c = 1; c <= numCols; c++) {
      var cell = row.getCell(c);
      cell.font = FONT_BODY;
      cell.border = THIN_BORDER;
      if (typeof cell.value === 'number' || (cell.value && typeof cell.value === 'object' && cell.value.formula)) {
        cell.alignment = { vertical: 'middle', horizontal: 'right' };
        cell.numFmt = '#,##0.##';
      } else {
        cell.alignment = { vertical: 'middle', horizontal: c <= 2 ? 'left' : 'center', wrapText: true };
      }
      if (alertByCol && alertByCol[c]) {
        if (alertByCol[c] === 'critical') {
          cell.fill = ALERT_RED_FILL;
          cell.font = FONT_RED;
        } else if (alertByCol[c] === 'over_capacity') {
          cell.fill = ALERT_ORG_FILL;
        } else if (alertByCol[c] === 'below_min') {
          cell.fill = ALERT_YEL_FILL;
        }
      }
    }
  }

  function colLetter(n) {
    var s = '';
    while (n > 0) {
      var m = (n - 1) % 26;
      s = String.fromCharCode(65 + m) + s;
      n = Math.floor((n - 1) / 26);
    }
    return s;
  }

  async function buildExcelBuffer(plan, calcResult, ExcelJSLib) {
    var EJ = ExcelJSLib || root.ExcelJS;
    if (!EJ) throw new Error('未載入 ExcelJS (exceljs.min.js)');

    var wb = new EJ.Workbook();
    wb.creator = '鴻勝產銷動態計畫系統';
    wb.created = new Date();
    wb.calcProperties = { fullCalcOnLoad: true };

    var months = calcResult.monthsMeta;
    var items = plan.items || [];
    var cMap = calcResult.computedById || {};

    // Maps item.id -> { sheetName, prodCols: [colLetter M1..M4], endCols: [colLetter M1..M4], row }
    var refLocByItemId = {};
    var prodLocByName = {};

    // Create sheets in logical order (place 產銷總表 first, populate 秏料 & process sheets, then link 產銷總表)
    var wsSummary = wb.addWorksheet('產銷總表', { views: [{ state: 'frozen', xSplit: 2, ySplit: 3 }] });
    var wsRect = wb.addWorksheet('精餾產銷', { views: [{ state: 'frozen', xSplit: 2, ySplit: 4 }] });
    var wsPrim = wb.addWorksheet('初餾產銷', { views: [{ state: 'frozen', xSplit: 2, ySplit: 4 }] });
    var wsBlend = wb.addWorksheet('調配產銷', { views: [{ state: 'frozen', xSplit: 2, ySplit: 4 }] });
    var wsBom = wb.addWorksheet('秏料', { views: [{ state: 'frozen', xSplit: 2, ySplit: 2 }] });
    var wsSched = wb.addWorksheet('產線排程明細', { views: [{ state: 'frozen', xSplit: 2, ySplit: 2 }] });
    var wsAlert = wb.addWorksheet('異常與預警摘要', { views: [{ state: 'frozen', xSplit: 1, ySplit: 2 }] });

    // ------------------------------------------------------------------
    // STEP 1: Build process sheets FIRST so row numbers are known, then build 秏料 & 產銷總表 formulas!
    // Actually we need 秏料 rows & prodLocByName! Wait:
    // In Excel: 秏料 sums production by product name from 精餾產銷/初餾產銷/調配產銷,
    // OR simpler & circular-ref-free: populate process sheets' production cells at exact rows,
    // record prodLocByName, build 秏料 summing exact sheet ranges, AND process sheets SUMIF(秏料!...)!
    // Wait: let's pre-assign row layout cleanly for 精餾產銷, 初餾產銷, 調配產銷!
    // ------------------------------------------------------------------
    var rectProducts = items.filter(function (x) { return x.process === '精餾' && (x.kind === 'product' || x.kind === 'filling'); });
    var rectRaws = items.filter(function (x) { return x.process === '精餾' && x.kind === 'raw'; });
    var primProducts = items.filter(function (x) { return x.process === '初餾' && x.kind === 'product'; });
    var primRaws = items.filter(function (x) { return x.process === '初餾' && x.kind === 'raw'; });
    var blendProducts = items.filter(function (x) { return x.process === '調配' && x.kind === 'product'; });
    var blendRaws = items.filter(function (x) { return x.process === '調配' && x.kind === 'raw'; });

    function setupProcessHeader(ws, title, hasContractIn) {
      ws.getCell('A1').value = title + '（基準日：' + (plan.meta.baseDate || '') + '）';
      ws.getCell('A1').font = { name: 'Microsoft JhengHei', size: 13, bold: true, color: { argb: 'FF0F172A' } };
      ws.getCell('A2').value = '單位：MT｜黃底=可編輯欄位、藍底=自動連動公式、紅/橘=庫存預警';
      ws.getCell('A2').font = { name: 'Microsoft JhengHei', size: 9, italic: true, color: { argb: 'FF475569' } };

      // Unified 35-col clean layout (no shifting columns!):
      // 1 品名 | 2 儲槽位置 | 3 儲槽容量 | 4 資材 | 5 製2 | 6 桶底 | 7 期初可用
      // Per Month m (4 cols for supply/demand? Even cleaner unified 6 cols per month:
      // 銷售(-), 代工/進貨(+), 其他入庫/調整(+), 直接耗用(-), 耗用合計(-), 生產/入庫(+)? Wait:
      // Let's make 1 row schema for Finished Product & 1 clean subheader for Raw Materials!
      // Layout:
      // Col 1: 品名, Col 2: 存放位置, Col 3: 容量(MT), Col 4: 資材, Col 5: 製2, Col 6: 桶底, Col 7: 期初庫存
      // M1..M4 (7 cols each -> cols 8..35):
      //   +0 銷售(-), +1 入庫/進貨/代工(+), +2 其他入庫/調整(+), +3 耗用(-)[BOM+直接或覆寫], +4 生產線別, +5 排程區間, +6 生產量(+)
      // Cols 36..39: 月末結存 M1..M4
      // Col 40: 安全最低, Col 41: 安全最高, Col 42: 備註/修正說明
      var topHdr = [
        '品名', '存放位置', '容量(MT)', '資材', '製2', '桶底', '期初可用'
      ];
      for (var mi = 0; mi < 4; mi++) {
        var ml = months[mi].label + ' (' + months[mi].periodLabel + ')';
        topHdr.push(ml, ml, ml, ml, ml, ml, ml);
      }
      topHdr.push('月末結存', '月末結存', '月末結存', '月末結存', '安全最低', '安全最高', '備註 / 調整說明');
      ws.getRow(3).values = topHdr;
      styleHeaderRow(ws.getRow(3));

      var subHdr = ['品名', '儲槽群', 'MT', '在庫', '製2', '不可抽', '=MAX(0,D+E-F)'];
      for (var mi2 = 0; mi2 < 4; mi2++) {
        subHdr.push(
          '銷售(-)',
          hasContractIn ? '代工/進貨(+)' : '進貨/併入(+)',
          '其他/調整(+/-)',
          '總耗用(-)',
          '線別',
          '排程區間',
          '自產量(+)'
        );
      }
      subHdr.push(months[0].label, months[1].label, months[2].label, months[3].label, '最低(MT)', '最高(MT)', '規則與覆寫紀錄');
      ws.getRow(4).values = subHdr;
      ws.getRow(4).height = 22;
      ws.getRow(4).eachCell(function (cell) {
        cell.fill = SUBHDR_FILL;
        cell.font = FONT_HDR;
        cell.alignment = { vertical: 'middle', horizontal: 'center' };
        cell.border = THIN_BORDER;
      });

      // Merge topHdr month headers cleanly
      [8, 15, 22, 29].forEach(function (cStart) {
        ws.mergeCells(3, cStart, 3, cStart + 6);
      });
      ws.mergeCells(3, 36, 3, 39);
    }

    var bomEndRow = 2 + (plan.bomRules ? plan.bomRules.length : 0);

    function writeItemRow(ws, rowIdx, item, sheetName, isProductBlock) {
      var w = cMap[item.id];
      var row = ws.getRow(rowIdx);
      row.getCell(1).value = item.name;
      row.getCell(2).value = item.tanks || '';
      row.getCell(3).value = item.capacity || 0;
      row.getCell(4).value = item.invMaterial || 0;
      row.getCell(5).value = item.invProcess2 || 0;
      row.getCell(6).value = item.tankBottom || 0;

      if (w.isOpeningOverridden) {
        row.getCell(7).value = w.opening;
      } else {
        row.getCell(7).value = { formula: 'MAX(0,D' + rowIdx + '+E' + rowIdx + '-F' + rowIdx + ')', result: w.opening };
      }

      var prodCols = [];
      var endCols = [];
      var alertCols = {};
      var rowNotes = [];
      if (item.sourceBugNote) rowNotes.push(item.sourceBugNote);
      if (w.isOpeningOverridden) rowNotes.push('期初手動固定 ' + w.opening);

      for (var mi = 0; mi < 4; mi++) {
        var cBase = 8 + mi * 7;
        var mRaw = (item.months && item.months[mi]) || {};
        var mCell = w.months[mi];
        var sCol = colLetter(cBase);       // Sales (-)
        var inCol = colLetter(cBase + 1);  // Purchase or ContractIn (+)
        var othCol = colLetter(cBase + 2); // OtherIn / AdjBalance (+/-)
        var uCol = colLetter(cBase + 3);   // Effective Usage (-)
        var lCol = colLetter(cBase + 4);   // Line
        var pStrCol = colLetter(cBase + 5);// PeriodStr
        var prdCol = colLetter(cBase + 6); // ProdQty (+)
        prodCols.push(prdCol);

        row.getCell(cBase).value = mCell.sales || 0;
        // In (+) column combines purchase + contractIn + childRollupProd
        var combinedIn = Math.round(((mCell.purchase || 0) + (mCell.contractIn || 0) + (mCell.childRollupProd || 0)) * 1000000) / 1000000;
        row.getCell(cBase + 1).value = combinedIn;
        // Other / Adj column
        var combinedOther = Math.round(((mCell.effectiveOtherIn || 0) + (mCell.adjBalance || 0)) * 1000000) / 1000000;
        row.getCell(cBase + 2).value = combinedOther;

        // Usage cell: if usageOverride OR directUsage only, write number/formula; else SUMIF BOM + directUsage!
        var bomSumColLetter = colLetter(6 + mi * 2); // 秏料! F, H, J, L
        if (mCell.isUsageOverridden || mCell.directUsage > 0 && mCell.bomUsage === 0) {
          row.getCell(cBase + 3).value = mCell.effectiveUsage;
          if (mCell.isUsageOverridden) rowNotes.push(months[mi].label + '覆寫耗用=' + mCell.effectiveUsage);
        } else if (mCell.bomUsage > 0 || !isProductBlock) {
          var bomRange = '秏料!$B$3:$B$' + Math.max(3, bomEndRow);
          var amtRange = '秏料!$' + bomSumColLetter + '$3:$' + bomSumColLetter + '$' + Math.max(3, bomEndRow);
          var fmlUsage = 'SUMIF(' + bomRange + ',$A' + rowIdx + ',' + amtRange + ')' + (mCell.directUsage ? ('+' + mCell.directUsage) : '');
          row.getCell(cBase + 3).value = { formula: fmlUsage, result: mCell.effectiveUsage };
        } else {
          row.getCell(cBase + 3).value = mCell.effectiveUsage || 0;
        }

        row.getCell(cBase + 4).value = mRaw.line || (mCell.effectiveProdQty > 0 && item.kind === 'filling' ? '充填' : '');
        row.getCell(cBase + 5).value = mRaw.periodStr || '';

        if (mRaw.prodFormulaMode === 'sales_plus_usage') {
          row.getCell(cBase + 6).value = {
            formula: sCol + rowIdx + '+' + uCol + rowIdx,
            result: mCell.effectiveProdQty
          };
        } else {
          row.getCell(cBase + 6).value = mCell.effectiveProdQty || 0;
        }

        if (mCell.adjNote) rowNotes.push(mCell.adjNote);

        // Ending stock cols 36..39
        var eColIdx = 36 + mi;
        var eColLet = colLetter(eColIdx);
        endCols.push(eColLet);
        var prevRef = mi === 0 ? ('G' + rowIdx) : (colLetter(36 + mi - 1) + rowIdx);
        row.getCell(eColIdx).value = {
          formula: prevRef + '-' + sCol + rowIdx + '+' + inCol + rowIdx + '+' + othCol + rowIdx + '-' + uCol + rowIdx + '+' + prdCol + rowIdx,
          result: mCell.endStock
        };
        if (mCell.alerts && mCell.alerts.length) {
          alertCols[eColIdx] = mCell.alerts[0];
        }
      }

      row.getCell(40).value = item.safetyMin !== null ? item.safetyMin : '';
      row.getCell(41).value = item.safetyMax !== null ? item.safetyMax : '';
      row.getCell(42).value = rowNotes.join('；');

      styleDataRow(row, 42, alertCols);
      refLocByItemId[item.id] = { sheetName: sheetName, row: rowIdx, prodCols: prodCols, endCols: endCols };
      if (!prodLocByName[item.name]) prodLocByName[item.name] = [];
      prodLocByName[item.name].push({ sheetName: sheetName, row: rowIdx, prodCols: prodCols });
    }

    function populateProcessSheet(ws, title, prodList, rawList, sheetName, hasContractIn) {
      setupProcessHeader(ws, title, hasContractIn);
      var r = 5;
      prodList.forEach(function (it) {
        writeItemRow(ws, r, it, sheetName, true);
        r++;
      });
      r += 1;
      ws.getRow(r).getCell(1).value = '【專屬原料與半成品消耗區】';
      ws.getRow(r).getCell(1).font = FONT_BOLD;
      ws.getRow(r).fill = SECTION_FILL;
      r++;
      rawList.forEach(function (it) {
        writeItemRow(ws, r, it, sheetName, false);
        r++;
      });
      // Clean column widths
      ws.getColumn(1).width = 24;
      ws.getColumn(2).width = 22;
      ws.getColumn(42).width = 34;
    }

    populateProcessSheet(wsRect, '產銷計劃表（精餾／充填）', rectProducts, rectRaws, '精餾產銷', false);
    populateProcessSheet(wsPrim, '產銷計劃表（初餾）', primProducts, primRaws, '初餾產銷', true);
    populateProcessSheet(wsBlend, '產銷計劃表（調配）', blendProducts, blendRaws, '調配產銷', false);

    // ------------------------------------------------------------------
    // STEP 2: Populate 秏料 (BOM) linking cleanly to exact sheet rows!
    // ------------------------------------------------------------------
    wsBom.getCell('A1').value = '秏料標準與多階 BOM 展開明細';
    wsBom.getCell('A1').font = { name: 'Microsoft JhengHei', size: 12, bold: true };
    wsBom.getRow(2).values = [
      '上階產品', '消耗原料/半成品', '收率', '占比',
      months[0].label + '產量', months[0].label + '用量',
      months[1].label + '產量', months[1].label + '用量',
      months[2].label + '產量', months[2].label + '用量',
      months[3].label + '產量', months[3].label + '用量',
      '小數位數', '狀態'
    ];
    styleHeaderRow(wsBom.getRow(2));

    var br = 3;
    (plan.bomRules || []).forEach(function (rule) {
      var row = wsBom.getRow(br);
      row.getCell(1).value = rule.product;
      row.getCell(2).value = rule.rawMaterial;
      var yR = rule.yieldRate;
      var rat = rule.ratio;
      var dec = rule.roundingDecimals || 0;
      if (plan.meta && plan.meta.ebrRUseFixed110 && rule.product === 'EBR95' && rule.rawMaterial === 'EBR(R)') {
        yR = 1.1;
        rat = 1;
        dec = 1;
      }
      row.getCell(3).value = yR;
      row.getCell(4).value = rat;

      var locs = prodLocByName[rule.product] || [];
      for (var mi = 0; mi < 4; mi++) {
        var pCol = 5 + mi * 2;
        var uCol = 6 + mi * 2;
        var pLet = colLetter(pCol);
        var valProd = 0;
        var terms = [];
        locs.forEach(function (loc) {
          terms.push("'" + loc.sheetName + "'!" + loc.prodCols[mi] + loc.row);
        });
        items.forEach(function (it) {
          if (it.name === rule.product && cMap[it.id]) {
            valProd += cMap[it.id].months[mi].effectiveProdQty;
          }
        });
        if (terms.length > 0 && rule.active !== false) {
          row.getCell(pCol).value = { formula: terms.join('+'), result: valProd };
        } else {
          row.getCell(pCol).value = rule.active !== false ? valProd : 0;
        }
        var expUse = rule.active !== false
          ? root.SalesPlannerEngine.roundN(valProd * yR * rat, dec)
          : 0;
        row.getCell(uCol).value = rule.active !== false
          ? { formula: 'ROUND(C' + br + '*D' + br + '*' + pLet + br + ',' + dec + ')', result: expUse }
          : 0;
      }
      row.getCell(13).value = dec;
      row.getCell(14).value = rule.active !== false ? '啟用' : '停用';
      styleDataRow(row, 14, null);
      br++;
    });
    wsBom.getColumn(1).width = 20;
    wsBom.getColumn(2).width = 24;

    // ------------------------------------------------------------------
    // STEP 3: Populate 產銷總表 with clean live formulas pointing to sheets!
    // ------------------------------------------------------------------
    wsSummary.getCell('A1').value = (plan.meta.title || '鴻勝產銷動態計畫總表') + '（跨頁公式自動彙總版）';
    wsSummary.getCell('A1').font = { name: 'Microsoft JhengHei', size: 13, bold: true };
    wsSummary.getCell('A2').value = '基準日：' + (plan.meta.baseDate || '') + '｜點選各工作表可檢視專屬原料明細';
    wsSummary.getRow(3).values = [
      '製程分類', '品名', '儲槽/庫位', '容量(MT)', '期初可用',
      months[0].label + '自產', months[0].label + '結存',
      months[1].label + '自產', months[1].label + '結存',
      months[2].label + '自產', months[2].label + '結存',
      months[3].label + '自產', months[3].label + '結存',
      '安全最低', '預警狀態'
    ];
    styleHeaderRow(wsSummary.getRow(3));
    var sr = 4;
    items.filter(function (it) { return it.kind !== 'raw'; }).forEach(function (it) {
      var loc = refLocByItemId[it.id];
      var w = cMap[it.id];
      if (!loc || !w) return;
      var row = wsSummary.getRow(sr);
      row.getCell(1).value = it.section;
      row.getCell(2).value = { formula: "'" + loc.sheetName + "'!A" + loc.row, result: it.name };
      row.getCell(3).value = it.tanks || '';
      row.getCell(4).value = it.capacity || 0;
      row.getCell(5).value = { formula: "'" + loc.sheetName + "'!G" + loc.row, result: w.opening };
      var alertCols = {};
      var rowAlMsgs = [];
      for (var mi = 0; mi < 4; mi++) {
        var cPrd = 6 + mi * 2;
        var cEnd = 7 + mi * 2;
        row.getCell(cPrd).value = { formula: "'" + loc.sheetName + "'!" + loc.prodCols[mi] + loc.row, result: w.months[mi].effectiveProdQty };
        row.getCell(cEnd).value = { formula: "'" + loc.sheetName + "'!" + loc.endCols[mi] + loc.row, result: w.months[mi].endStock };
        if (w.months[mi].alerts && w.months[mi].alerts.length) {
          alertCols[cEnd] = w.months[mi].alerts[0];
          rowAlMsgs.push(months[mi].label + ':' + w.months[mi].alerts.join('/'));
        }
      }
      row.getCell(14).value = it.safetyMin !== null ? it.safetyMin : '';
      row.getCell(15).value = rowAlMsgs.length ? rowAlMsgs.join('；') : '正常';
      styleDataRow(row, 15, alertCols);
      sr++;
    });
    wsSummary.getColumn(1).width = 14;
    wsSummary.getColumn(2).width = 24;
    wsSummary.getColumn(3).width = 20;
    wsSummary.getColumn(15).width = 28;

    // ------------------------------------------------------------------
    // STEP 4: 產線排程明細 (Clean Schedule Table instead of 12k dummy rows)
    // ------------------------------------------------------------------
    wsSched.getCell('A1').value = '各月份產線排程與天數負荷明細';
    wsSched.getRow(2).values = ['月份', '生產線別', '製程', '產品品名', '排程區間', '排產天數', '排產數量(MT)', '日均產量(MT/日)'];
    styleHeaderRow(wsSched.getRow(2));
    var schRow = 3;
    for (var sm = 0; sm < 4; sm++) {
      items.forEach(function (it) {
        var w = cMap[it.id];
        var mr = (it.months && it.months[sm]) || {};
        var mc = w.months[sm];
        if (!mc || mc.effectiveProdQty <= 0) return;
        var row = wsSched.getRow(schRow);
        row.getCell(1).value = months[sm].label;
        row.getCell(2).value = mr.line || (it.kind === 'filling' ? '充填' : '未指定');
        row.getCell(3).value = it.process;
        row.getCell(4).value = it.name;
        row.getCell(5).value = mr.periodStr || '-';
        row.getCell(6).value = mc.scheduleDayCount || 0;
        row.getCell(7).value = mc.effectiveProdQty;
        row.getCell(8).value = mc.scheduleDayCount > 0
          ? { formula: 'ROUND(G' + schRow + '/F' + schRow + ',2)', result: Math.round((mc.effectiveProdQty / mc.scheduleDayCount) * 100) / 100 }
          : '-';
        styleDataRow(row, 8, null);
        schRow++;
      });
    }
    wsSched.getColumn(4).width = 24;
    wsSched.getColumn(5).width = 22;

    // ------------------------------------------------------------------
    // STEP 5: 異常與預警摘要
    // ------------------------------------------------------------------
    wsAlert.getCell('A1').value = '庫存預警與排程衝突檢查報告';
    wsAlert.getRow(2).values = ['類型', '等級', '製程/線別', '品項', '月份', '預估/衝突內容'];
    styleHeaderRow(wsAlert.getRow(2));
    var alRow = 3;
    (calcResult.alerts || []).forEach(function (al) {
      var row = wsAlert.getRow(alRow);
      row.getCell(1).value = '庫存預警';
      row.getCell(2).value = al.severity === 'critical' ? '嚴重缺料 (<0)' : (al.severity === 'over_capacity' ? '超容量 (>Cap)' : '低於安全庫存');
      row.getCell(3).value = al.process;
      row.getCell(4).value = al.itemName;
      row.getCell(5).value = al.monthLabel;
      row.getCell(6).value = al.message;
      styleDataRow(row, 6, { 2: al.severity });
      alRow++;
    });
    (calcResult.conflicts || []).forEach(function (cf) {
      var row = wsAlert.getRow(alRow);
      row.getCell(1).value = '排程衝突';
      row.getCell(2).value = cf.type === 'nmp_avoidance' ? 'NMP避讓違規' : (cf.type === 'line_overlap' ? '同線重疊' : '順序提醒');
      row.getCell(3).value = cf.line;
      row.getCell(4).value = (cf.items || []).join(' vs ');
      row.getCell(5).value = cf.monthLabel;
      row.getCell(6).value = cf.message;
      styleDataRow(row, 6, { 2: cf.type === 'nmp_sequence_notice' ? 'below_min' : 'over_capacity' });
      alRow++;
    });
    wsAlert.getColumn(4).width = 24;
    wsAlert.getColumn(6).width = 56;

    return await wb.xlsx.writeBuffer();
  }

  var api = { buildExcelBuffer: buildExcelBuffer };
  root.SalesExcelExporter = api;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof window !== 'undefined' ? window : globalThis);
