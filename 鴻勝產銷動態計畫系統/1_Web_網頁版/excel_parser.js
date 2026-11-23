/**
 * 鴻勝產銷動態計畫系統 - 瀏覽器端 Excel (.xlsx) 匯入解析器 (基於 SheetJS)
 * 可直接上傳任何月份的「產銷計畫.xlsx」，自動動態辨識 精餾產銷 / 初餾產銷 / 調配產銷 / 秏料 結構，
 * 支援動態增減列與公式/手寫覆寫區分。
 */
(function (root) {
  'use strict';

  function getCell(ws, row1, col1, XLSXLib) {
    var addr = XLSXLib.utils.encode_cell({ r: row1 - 1, c: col1 - 1 });
    return ws ? ws[addr] : null;
  }

  function fnum(cell, fallback) {
    if (!cell || cell.v === null || cell.v === undefined || typeof cell.v === 'boolean') {
      return fallback !== undefined ? fallback : 0;
    }
    var n = Number(cell.v);
    if (!Number.isFinite(n)) return fallback !== undefined ? fallback : 0;
    return Math.round(n * 1000000) / 1000000;
  }

  function fstr(cell) {
    if (!cell || cell.v === null || cell.v === undefined) return '';
    var s = String(cell.v).trim();
    return (s === '0' || s === '0.0') ? '' : s;
  }

  function isFormula(cell) {
    return !!(cell && typeof cell.f === 'string' && cell.f.trim().length > 0);
  }

  function fmtDateCell(cell) {
    if (!cell || cell.v === null || cell.v === undefined) return '';
    var v = cell.v;
    if (v instanceof Date && !isNaN(v.getTime())) {
      var y = v.getFullYear();
      var m = String(v.getMonth() + 1).padStart(2, '0');
      var d = String(v.getDate()).padStart(2, '0');
      return y + '-' + m + '-' + d;
    }
    if (typeof v === 'number' && v > 20000 && v < 80000) {
      // Excel serial date fallback
      var utcDays = Math.floor(v - 25569);
      var dt = new Date(utcDays * 86400 * 1000);
      return dt.toISOString().slice(0, 10);
    }
    var s = String(v).trim();
    return s.length >= 10 ? s.slice(0, 10) : s;
  }

  function getMaxRowCol(ws, XLSXLib) {
    var ref = ws && ws['!ref'];
    if (!ref) return { maxRow: 140, maxCol: 42 };
    var range = XLSXLib.utils.decode_range(ref);
    return { maxRow: range.e.r + 1, maxCol: range.e.c + 1 };
  }

  function findRowByColText(ws, col1, keywords, startRow, maxRow, XLSXLib) {
    for (var r = startRow; r <= maxRow; r++) {
      var val = fstr(getCell(ws, r, col1, XLSXLib));
      if (!val) continue;
      for (var i = 0; i < keywords.length; i++) {
        if (val.indexOf(keywords[i]) !== -1) return r;
      }
    }
    return -1;
  }

  function parseWorkbookToPlan(arrayBuffer, fileName, XLSXLib) {
    var X = XLSXLib || root.XLSX;
    if (!X) throw new Error('未載入 SheetJS (xlsx.full.min.js)');

    var wb = X.read(arrayBuffer, { type: 'array', cellFormula: true, cellDates: true, cellNF: true });
    var required = ['精餾產銷', '初餾產銷', '調配產銷', '秏料'];
    for (var i = 0; i < required.length; i++) {
      if (!wb.Sheets[required[i]]) {
        throw new Error('找不到必要工作表：「' + required[i] + '」（目前工作表：' + wb.SheetNames.join(', ') + '）');
      }
    }

    // 1) Parse BOM rules from 秏料
    var wsBom = wb.Sheets['秏料'];
    var bomBounds = getMaxRowCol(wsBom, X);
    var bomRules = [];
    var seenBom = {};
    for (var br = 3; br <= bomBounds.maxRow; br++) {
      var bProd = fstr(getCell(wsBom, br, 1, X));
      var bRaw = fstr(getCell(wsBom, br, 2, X));
      if (!bProd || !bRaw || bProd === '小計') continue;
      if (fstr(getCell(wsBom, br, 4, X)) === '%') continue;

      var yCell = getCell(wsBom, br, 3, X);
      var rCell = getCell(wsBom, br, 4, X);
      var yVal = fnum(yCell, null);
      var rVal = fnum(rCell, null);
      if (yVal === null || rVal === null || (!yCell && !rCell)) continue;

      var dec = 0;
      [6, 8, 10, 12].forEach(function (fc) {
        var cObj = getCell(wsBom, br, fc, X);
        if (cObj && cObj.f && String(cObj.f).indexOf(',3)') !== -1) dec = 3;
      });
      var key = bProd + '||' + bRaw;
      if (seenBom[key]) continue;
      seenBom[key] = true;
      bomRules.push({
        id: 'bom_' + (bomRules.length + 1),
        product: bProd,
        rawMaterial: bRaw,
        yieldRate: yVal,
        ratio: rVal,
        roundingDecimals: dec,
        active: true,
        sourceRow: br,
        note: ''
      });
    }

    var items = [];
    function buildItem(ws, sheetName, r, kind, process, section, colsCfg, opts) {
      opts = opts || {};
      var name = opts.overrideName || fstr(getCell(ws, r, 1, X));
      if (!name) return null;

      var tanks = fstr(getCell(ws, r, 2, X));
      var capacity = fnum(getCell(ws, r, 3, X), 0);
      var invMat = fnum(getCell(ws, r, 4, X), 0);
      var invP2 = fnum(getCell(ws, r, 5, X), 0);
      var tankBottom = fnum(getCell(ws, r, 6, X), 0);
      var gCell = getCell(ws, r, 7, X);
      var gVal = fnum(gCell, 0);
      var calcOpen = Math.max(0, Math.round((invMat + invP2 - tankBottom) * 1000000) / 1000000);
      var openingOverride = null;
      if (Math.abs(gVal - calcOpen) > 0.0001) {
        openingOverride = gVal;
      }

      var safetyMax = colsCfg.safetyMax ? fnum(getCell(ws, r, colsCfg.safetyMax, X), null) : null;
      var safetyMin = colsCfg.safetyMin ? fnum(getCell(ws, r, colsCfg.safetyMin, X), null) : null;
      if (safetyMax === 0) safetyMax = null;
      if (safetyMin === 0) safetyMin = null;

      var months = [];
      for (var mi = 0; mi < 4; mi++) {
        var mc = colsCfg.months[mi];
        var sales = mc.sales ? fnum(getCell(ws, r, mc.sales, X), 0) : 0;
        var contractIn = mc.contractIn ? fnum(getCell(ws, r, mc.contractIn, X), 0) : 0;

        var directUsage = 0;
        if (mc.usage) {
          var uCell = getCell(ws, r, mc.usage, X);
          var uVal = fnum(uCell, 0);
          var uFml = (uCell && uCell.f) ? String(uCell.f) : '';
          if (!isFormula(uCell) || uFml.indexOf('秏料') === -1) {
            directUsage = uVal;
          }
        }

        var purchase = mc.purchase ? fnum(getCell(ws, r, mc.purchase, X), 0) : 0;
        var otherIn = 0;
        if (mc.otherIn) {
          var oiCell = getCell(ws, r, mc.otherIn, X);
          if (!isFormula(oiCell)) {
            otherIn = fnum(oiCell, 0);
          }
        }

        var line = mc.line ? fstr(getCell(ws, r, mc.line, X)) : '';
        var periodStr = mc.period ? fstr(getCell(ws, r, mc.period, X)) : '';
        var pCell = mc.prodQty ? getCell(ws, r, mc.prodQty, X) : null;
        var prodQty = fnum(pCell, 0);
        var prodMode = (kind === 'filling' && isFormula(pCell) && String(pCell.f).indexOf('+') !== -1)
          ? 'sales_plus_usage' : 'manual';
        var excelEnd = mc.endStock ? fnum(getCell(ws, r, mc.endStock, X), null) : null;
        if (getCell(ws, r, mc.endStock, X) == null) excelEnd = null;

        months.push({
          sales: sales,
          contractIn: contractIn,
          directUsage: directUsage,
          usageOverride: null,
          purchase: purchase,
          otherIn: otherIn,
          otherInOverride: null,
          adjBalance: opts.adjBalance ? opts.adjBalance[mi] : 0,
          adjNote: opts.adjNotes ? opts.adjNotes[mi] : '',
          line: line,
          periodStr: periodStr,
          prodQty: prodQty,
          prodFormulaMode: prodMode,
          dailyRate: null,
          _excelEndStock: excelEnd
        });
      }

      var hasActivity = (
        invMat !== 0 || invP2 !== 0 || gVal !== 0 ||
        months.some(function (m) {
          return m.sales !== 0 || m.contractIn !== 0 || m.directUsage !== 0 || m.purchase !== 0 || m.otherIn !== 0 || m.prodQty !== 0;
        })
      );

      return {
        id: kind + '_' + process + '_' + (items.length + 1) + '_' + name,
        name: name,
        kind: kind,
        process: process,
        section: section,
        sourceSheet: sheetName,
        sourceRow: r,
        tanks: tanks,
        capacity: capacity,
        invMaterial: invMat,
        invProcess2: invP2,
        tankBottom: tankBottom,
        openingOverride: openingOverride,
        safetyMax: safetyMax,
        safetyMin: safetyMin,
        rollupTo: opts.rollupTo || null,
        rollupMonths: opts.rollupMonths || (opts.rollupTo ? [true, true, true, true] : [false, false, false, false]),
        showInSummary: opts.showInSummary !== undefined ? opts.showInSummary : hasActivity,
        months: months,
        sourceBugNote: opts.sourceBugNote || ''
      };
    }

    var rectProdCfg = {
      safetyMax: 33, safetyMin: 34,
      months: [
        { sales: 8, usage: 9, line: 16, period: 17, prodQty: 18, endStock: 28 },
        { sales: 10, usage: 11, line: 19, period: 20, prodQty: 21, endStock: 29 },
        { sales: 12, usage: 13, line: 22, period: 23, prodQty: 24, endStock: 30 },
        { sales: 14, usage: 15, line: 25, period: 26, prodQty: 27, endStock: 31 }
      ]
    };
    var rectRawCfg = {
      safetyMax: 33, safetyMin: 34,
      months: [
        { sales: 8, usage: 9, rawConsume: 16, purchase: 20, otherIn: 24, endStock: 28 },
        { sales: 10, usage: 11, rawConsume: 17, purchase: 21, otherIn: 25, endStock: 29 },
        { sales: 12, usage: 13, rawConsume: 18, purchase: 22, otherIn: 26, endStock: 30 },
        { sales: 14, usage: 15, rawConsume: 19, purchase: 23, otherIn: 27, endStock: 31 }
      ]
    };
    var primProdCfg = {
      safetyMax: 38, safetyMin: null,
      months: [
        { sales: 8, contractIn: 9, usage: 10, line: 20, period: 21, prodQty: 22, endStock: 32 },
        { sales: 11, contractIn: 12, usage: 13, line: 23, period: 24, prodQty: 25, endStock: 33 },
        { sales: 14, contractIn: 15, usage: 16, line: 26, period: 27, prodQty: 28, endStock: 34 },
        { sales: 17, contractIn: 18, usage: 19, line: 29, period: 30, prodQty: 31, endStock: 35 }
      ]
    };
    var primRawCfg = {
      safetyMax: 38, safetyMin: null,
      months: [
        { sales: 8, contractIn: 9, usage: 10, rawConsume: 20, purchase: 24, otherIn: 28, endStock: 32 },
        { sales: 11, contractIn: 12, usage: 13, rawConsume: 21, purchase: 25, otherIn: 29, endStock: 33 },
        { sales: 14, contractIn: 15, usage: 16, rawConsume: 22, purchase: 26, otherIn: 30, endStock: 34 },
        { sales: 17, contractIn: 18, usage: 19, rawConsume: 23, purchase: 27, otherIn: 31, endStock: 35 }
      ]
    };
    var blendProdCfg = {
      safetyMax: 34, safetyMin: 35,
      months: [
        { sales: 8, usage: 9, line: 16, period: 17, prodQty: 18, endStock: 28 },
        { sales: 10, usage: 11, line: 19, period: 20, prodQty: 21, endStock: 29 },
        { sales: 12, usage: 13, line: 22, period: 23, prodQty: 24, endStock: 30 },
        { sales: 14, usage: 15, line: 25, period: 26, prodQty: 27, endStock: 31 }
      ]
    };
    var blendRawCfg = {
      safetyMax: 34, safetyMin: 35,
      months: [
        { sales: 8, usage: 9, rawConsume: 16, purchase: 20, otherIn: 24, endStock: 28 },
        { sales: 10, usage: 11, rawConsume: 17, purchase: 21, otherIn: 25, endStock: 29 },
        { sales: 12, usage: 13, rawConsume: 18, purchase: 22, otherIn: 26, endStock: 30 },
        { sales: 14, usage: 15, rawConsume: 19, purchase: 23, otherIn: 27, endStock: 31 }
      ]
    };

    // --- 1. 精餾產銷 dynamic row scan ---
    var wsRect = wb.Sheets['精餾產銷'];
    var rBounds = getMaxRowCol(wsRect, X);
    var rectRawHeaderRow = findRowByColText(wsRect, 1, ['原料品名'], 45, rBounds.maxRow, X);
    if (rectRawHeaderRow < 0) rectRawHeaderRow = 59;
    var rectFillStart = findRowByColText(wsRect, 1, ['IPAIF'], 30, rectRawHeaderRow, X);
    if (rectFillStart < 0) rectFillStart = 44;
    var rectFooterRow = findRowByColText(wsRect, 1, ['備', '註'], rectRawHeaderRow + 2, rBounds.maxRow, X);
    if (rectFooterRow < 0) rectFooterRow = 95;

    var prevMainProduct = '';
    for (var rr = 5; rr < rectFillStart; rr++) {
      var nm = fstr(getCell(wsRect, rr, 1, X));
      if (!nm) continue;
      var opts = {};
      if (nm === '外購' || nm === '委外加工') {
        opts.overrideName = prevMainProduct + '(' + nm + ')';
        opts.rollupTo = prevMainProduct;
        opts.rollupMonths = [true, true, true, true];
      } else if (nm === 'EGUPS(勝一S07)') {
        opts.rollupTo = 'EGUPS';
        opts.rollupMonths = [true, true, true, true];
        prevMainProduct = nm;
      } else if (nm === 'IPAUPS(崙尾區LG)') {
        // Check if parent IPAUPS M1 ending formula includes R5:R9
        var m1Fml = (getCell(wsRect, 5, 28, X) && getCell(wsRect, 5, 28, X).f) || '';
        opts.rollupTo = 'IPAUPS';
        opts.rollupMonths = [m1Fml.indexOf('R9') !== -1 || m1Fml.indexOf(':R9') !== -1, false, false, false];
        prevMainProduct = nm;
      } else if (nm === 'IPAUPS' && prevMainProduct) {
        // Blank placeholder duplicate row for IPAUPS (row 7 in template)
        opts.overrideName = 'IPAUPS(預備行)';
        opts.showInSummary = false;
      } else {
        prevMainProduct = nm;
      }

      if (nm === 'IPAUPS' && !opts.overrideName) {
        // Detect trailing constant like +80 inside May formula =G5-SUM(H5:I5)+SUM(R5:R9)+80
        var f28 = (getCell(wsRect, rr, 28, X) && getCell(wsRect, rr, 28, X).f) || '';
        var tailM = f28.match(/\+\s*(\d+(?:\.\d+)?)\s*$/);
        if (tailM) {
          opts.adjBalance = [Number(tailM[1]), 0, 0, 0];
          opts.adjNotes = ['原Excel 5月庫存公式含手動調整 (+' + tailM[1] + ')', '', '', ''];
        }
      }
      if (nm === 'CPNE3-R') {
        // Detect -U22*秏料!C23 style deductions in Jun/Jul/Aug
        var adjB = [0, 0, 0, 0];
        var adjN = ['', '', '', ''];
        [29, 30, 31].forEach(function (ec, idxOffset) {
          var fc = (getCell(wsRect, rr, ec, X) && getCell(wsRect, rr, ec, X).f) || '';
          if (fc.indexOf('秏料!') !== -1) {
            var mi = idxOffset + 1;
            // Recompute residual against standard formula
            var endV = fnum(getCell(wsRect, rr, ec, X), null);
            var prevV = fnum(getCell(wsRect, rr, ec - 1, X), 0);
            var mColProd = rectProdCfg.months[mi].prodQty;
            var mColSales = rectProdCfg.months[mi].sales;
            var mColUse = rectProdCfg.months[mi].usage;
            var pVal = fnum(getCell(wsRect, rr, mColProd, X), 0);
            var sVal = fnum(getCell(wsRect, rr, mColSales, X), 0);
            var uVal = fnum(getCell(wsRect, rr, mColUse, X), 0);
            if (endV !== null) {
              var diff = Math.round((endV - (prevV - sVal - uVal + pVal)) * 1000) / 1000;
              if (Math.abs(diff) > 0.001) {
                adjB[mi] = diff;
                adjN[mi] = '原Excel公式扣減 (' + diff + ')';
              }
            }
          }
        });
        if (adjB.some(function (x) { return x !== 0; })) {
          opts.adjBalance = adjB;
          opts.adjNotes = adjN;
        }
      }

      var rectIt = buildItem(wsRect, '精餾產銷', rr, 'product', '精餾', '精餾成品', rectProdCfg, opts);
      if (rectIt) items.push(rectIt);
    }

    for (var rf = rectFillStart; rf < rectRawHeaderRow; rf++) {
      var fillIt = buildItem(wsRect, '精餾產銷', rf, 'filling', '精餾', '充填成品', rectProdCfg);
      if (fillIt) items.push(fillIt);
    }

    for (var rraw = rectRawHeaderRow + 2; rraw < rectFooterRow; rraw++) {
      var rawIt = buildItem(wsRect, '精餾產銷', rraw, 'raw', '精餾', '精餾原料', rectRawCfg);
      if (rawIt) items.push(rawIt);
    }

    // --- 2. 初餾產銷 ---
    var wsPrim = wb.Sheets['初餾產銷'];
    var pBounds = getMaxRowCol(wsPrim, X);
    var primRawHeader = findRowByColText(wsPrim, 1, ['原料品名'], 15, pBounds.maxRow, X);
    if (primRawHeader < 0) primRawHeader = 34;
    var primFooter = findRowByColText(wsPrim, 1, ['備', '註'], primRawHeader + 2, pBounds.maxRow, X);
    if (primFooter < 0) primFooter = 70;

    for (var pr = 5; pr < primRawHeader; pr++) {
      var primP = buildItem(wsPrim, '初餾產銷', pr, 'product', '初餾', '初餾成品', primProdCfg);
      if (primP) items.push(primP);
    }
    for (var praw = primRawHeader + 2; praw < primFooter; praw++) {
      var primR = buildItem(wsPrim, '初餾產銷', praw, 'raw', '初餾', '初餾原料', primRawCfg);
      if (primR) items.push(primR);
    }

    // --- 3. 調配產銷 ---
    var wsBlend = wb.Sheets['調配產銷'];
    var bBounds = getMaxRowCol(wsBlend, X);
    var blendRawHeader = findRowByColText(wsBlend, 1, ['原料品名'], 15, bBounds.maxRow, X);
    if (blendRawHeader < 0) blendRawHeader = 35;
    var blendFooter = findRowByColText(wsBlend, 1, ['備', '註'], blendRawHeader + 2, bBounds.maxRow, X);
    if (blendFooter < 0) blendFooter = 75;

    for (var blr = 6; blr < blendRawHeader; blr++) {
      var blNm = fstr(getCell(wsBlend, blr, 1, X));
      var blOpts = (blNm === 'ACT790')
        ? { sourceBugNote: '系統自動以本月銷售計算結存 (修正舊表7月 SUM(K:L) 錯位)' } : {};
      var blP = buildItem(wsBlend, '調配產銷', blr, 'product', '調配', '調配成品', blendProdCfg, blOpts);
      if (blP) items.push(blP);
    }
    for (var blraw = blendRawHeader + 2; blraw < blendFooter; blraw++) {
      var rawName = fstr(getCell(wsBlend, blraw, 1, X));
      if (!rawName || rawName === 'EGUPS') continue; // Linked directly to 精餾 EGUPS
      var blOpts2 = (rawName === '1PG-GB')
        ? { sourceBugNote: '系統以 BOM 公式自動扣減本月耗用 (修正舊表6~7月漏植 SUMIF)' } : {};
      var blR = buildItem(wsBlend, '調配產銷', blraw, 'raw', '調配', '調配原料', blendRawCfg, blOpts2);
      if (blR) items.push(blR);
    }

    var baseDateStr = fmtDateCell(getCell(wsRect, 3, 7, X)) || new Date().toISOString().slice(0, 10);
    var buildMonths = root.SalesPlannerEngine && root.SalesPlannerEngine.buildMonthsFromBaseDate;
    var monthsMeta = buildMonths ? buildMonths(baseDateStr) : [
      { id: 'm1', label: '5月', periodLabel: fstr(getCell(wsRect, 3, 8, X)) || baseDateStr, endDate: baseDateStr, startDay: 11, endDay: 31, days: 21 },
      { id: 'm2', label: '6月', periodLabel: '06/01~06/30', endDate: fmtDateCell(getCell(wsRect, 3, 10, X)), startDay: 1, endDay: 30, days: 30 },
      { id: 'm3', label: '7月', periodLabel: '07/01~07/31', endDate: fmtDateCell(getCell(wsRect, 3, 12, X)), startDay: 1, endDay: 31, days: 31 },
      { id: 'm4', label: '8月', periodLabel: '08/01~08/31', endDate: fmtDateCell(getCell(wsRect, 3, 14, X)), startDay: 1, endDay: 31, days: 31 }
    ];

    var notes = [];
    for (var nr = rectFooterRow; nr <= Math.min(rBounds.maxRow, rectFooterRow + 8); nr++) {
      var ntxt = fstr(getCell(wsRect, nr, 7, X));
      if (ntxt) notes.push(ntxt);
    }

    return {
      schemaVersion: '1.0.0',
      meta: {
        title: (fileName ? fileName.replace(/\.xlsx?$/i, '') : '匯入產銷計畫') + ' (' + baseDateStr + ')',
        baseDate: baseDateStr,
        sourceFile: fileName || 'uploaded.xlsx',
        months: monthsMeta,
        notes: notes.length ? notes : [
          '*NMPUPS生產排程後必須避開EGUPS及IPAUPS。',
          '*儲槽須重新檢討儲放的利用率，每次產銷須檢討儲槽的存放率，提高儲槽的利用。'
        ],
        ebrRUseFixed110: true
      },
      lines: (root.DEFAULT_SALES_PLAN && root.DEFAULT_SALES_PLAN.lines) || [
        { id: 'S01', process: '精餾', name: 'S01 (精餾一線)' },
        { id: 'S02', process: '精餾', name: 'S02 (精餾二線)' },
        { id: 'S03', process: '精餾', name: 'S03 (精餾三線)' },
        { id: 'S01+S02', process: '精餾', name: 'S01+S02 (雙線併用)' },
        { id: 'S02+S01', process: '精餾', name: 'S02+S01 (雙線併用)' },
        { id: 'S07', process: '精餾', name: '勝一 S07' },
        { id: '充填', process: '精餾', name: '充填線' },
        { id: '外購', process: '精餾', name: '外購/進貨' },
        { id: '委外加工', process: '精餾', name: '委外加工' },
        { id: 'R01', process: '初餾', name: 'R01 (初餾一線)' },
        { id: 'R02', process: '初餾', name: 'R02 (初餾二線)' },
        { id: '參配', process: '調配', name: '參配調配線' }
      ],
      items: items,
      bomRules: bomRules,
      recoveryRules: (root.DEFAULT_SALES_PLAN && root.DEFAULT_SALES_PLAN.recoveryRules) || [
        { id: 'rec_ipa', targetRaw: 'IPA', sourceItem: 'IPAUPS', sourceField: 'directUsage', factor: 0.95, roundingDecimals: 0, active: true, note: 'IPAUPS 耗用 95% 回收至 IPA 原料' },
        { id: 'rec_2ipa', targetRaw: 'IPA', sourceItem: '2IPA', sourceField: 'prodQty', factor: 1.0, roundingDecimals: 0, active: true, note: '2IPA 精餾回收產量併入 IPA 其他入庫' },
        { id: 'rec_1cpn', targetRaw: '1CPN', sourceItem: 'CPNE4(含浸)', sourceField: 'totalUsage', factor: 1.0, roundingDecimals: 3, active: true, note: 'CPNE4(含浸) 耗用轉入 1CPN 其他入庫' }
      ]
    };
  }

  var api = { parseWorkbookToPlan: parseWorkbookToPlan };
  root.SalesExcelParser = api;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof window !== 'undefined' ? window : globalThis);
