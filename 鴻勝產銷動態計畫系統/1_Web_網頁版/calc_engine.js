/**
 * 鴻勝產銷動態計畫系統 - 核心計算引擎 (純 JS，瀏覽器 & Node.js 共用)
 * 整合多階 BOM 展開、充填連動、回收連動、多區間日數解析、線別衝突檢查與安全庫存/容量預警。
 */
(function (root) {
  'use strict';

  function num(v, fallback) {
    if (v === null || v === undefined || v === '' || typeof v === 'boolean') {
      return fallback !== undefined ? fallback : 0;
    }
    var n = Number(v);
    return Number.isFinite(n) ? n : (fallback !== undefined ? fallback : 0);
  }

  function roundN(val, decimals) {
    var d = Math.max(0, Math.min(6, Number(decimals) || 0));
    var factor = Math.pow(10, d);
    return Math.round((Number(val) + Number.EPSILON) * factor) / factor;
  }

  function round6(val) {
    return roundN(val, 6);
  }

  /**
   * 解析生產區間字串，例如 "11~12\n18~22"、"1~31"、"17" -> 天數與日期陣列
   */
  function parsePeriodDays(periodStr, monthMeta) {
    var s = String(periodStr || '').trim();
    if (!s || s === '0') {
      return { days: [], count: 0, ranges: [], raw: '' };
    }
    var maxDay = monthMeta && monthMeta.endDay ? Number(monthMeta.endDay) : 31;
    var minDay = 1;
    var parts = s.split(/[\r\n,;、]+/).map(function (x) { return x.trim(); }).filter(Boolean);
    var daySet = new Set();
    var ranges = [];
    var hasInvalid = false;

    for (var i = 0; i < parts.length; i++) {
      var p = parts[i].replace(/[～－—]/g, '~').replace(/\s+/g, '');
      var mRange = p.match(/^(\d{1,2})~(\d{1,2})$/);
      if (mRange) {
        var a = parseInt(mRange[1], 10);
        var b = parseInt(mRange[2], 10);
        if (a < minDay || b > maxDay || a > b) {
          hasInvalid = true;
          var lo = Math.max(1, Math.min(a, b));
          var hi = Math.min(31, Math.max(a, b));
          for (var d = lo; d <= hi; d++) daySet.add(d);
          ranges.push({ start: lo, end: hi });
        } else {
          for (var d2 = a; d2 <= b; d2++) daySet.add(d2);
          ranges.push({ start: a, end: b });
        }
        continue;
      }
      var mSingle = p.match(/^(\d{1,2})$/);
      if (mSingle) {
        var sd = parseInt(mSingle[1], 10);
        if (sd >= 1 && sd <= 31) {
          daySet.add(sd);
          ranges.push({ start: sd, end: sd });
          if (sd > maxDay) hasInvalid = true;
        } else {
          hasInvalid = true;
        }
        continue;
      }
      // Handle strings like "11~31" or month label like "6月"
      if (!/^\d{1,2}月$/.test(p)) {
        hasInvalid = true;
      }
    }

    var days = Array.from(daySet).sort(function (x, y) { return x - y; });
    return {
      days: days,
      count: days.length,
      ranges: ranges,
      raw: s,
      hasInvalid: hasInvalid
    };
  }

  /**
   * 依基準日期 (YYYY-MM-DD) 推算連續 4 個月份區間資訊
   */
  function buildMonthsFromBaseDate(baseDateStr) {
    var m = String(baseDateStr || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
    var start = m ? new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3])) : new Date();
    var out = [];
    for (var i = 0; i < 4; i++) {
      var yr = start.getFullYear();
      var mo = start.getMonth() + i;
      var dFirst = new Date(yr, mo, 1);
      var dLast = new Date(dFirst.getFullYear(), dFirst.getMonth() + 1, 0);
      var realStartDay = i === 0 ? start.getDate() : 1;
      var endDay = dLast.getDate();
      var mm = String(dFirst.getMonth() + 1).padStart(2, '0');
      var sd = String(realStartDay).padStart(2, '0');
      var ed = String(endDay).padStart(2, '0');
      out.push({
        id: 'm' + (i + 1),
        label: (dFirst.getMonth() + 1) + '月',
        periodLabel: mm + '/' + sd + '~' + mm + '/' + ed,
        endDate: dFirst.getFullYear() + '-' + mm + '-' + ed,
        startDay: realStartDay,
        endDay: endDay,
        days: Math.max(1, endDay - realStartDay + 1)
      });
    }
    return out;
  }

  function calcItemOpening(item) {
    var mat = num(item.invMaterial, 0);
    var p2 = num(item.invProcess2, 0);
    var bot = num(item.tankBottom, 0);
    var autoOpen = Math.max(0, round6(mat + p2 - bot));
    if (item.openingOverride !== null && item.openingOverride !== undefined && item.openingOverride !== '') {
      return {
        opening: num(item.openingOverride, 0),
        autoOpening: autoOpen,
        isOverridden: true
      };
    }
    return {
      opening: autoOpen,
      autoOpening: autoOpen,
      isOverridden: false
    };
  }

  function recalculatePlan(plan) {
    if (!plan || !Array.isArray(plan.items)) {
      return {
        computedById: {},
        bomBreakdownByTarget: {},
        alerts: [],
        conflicts: [],
        stats: { totalItems: 0, criticalCount: 0, overCapCount: 0, belowMinCount: 0, overrideCount: 0 }
      };
    }

    var monthsMeta = (plan.meta && Array.isArray(plan.meta.months) && plan.meta.months.length === 4)
      ? plan.meta.months
      : buildMonthsFromBaseDate(plan.meta && plan.meta.baseDate ? plan.meta.baseDate : '2026-05-11');

    var items = plan.items;
    var bomRules = Array.isArray(plan.bomRules) ? plan.bomRules : [];
    var recoveryRules = Array.isArray(plan.recoveryRules) ? plan.recoveryRules : [];
    var useFixedEbrR = !!(plan.meta && plan.meta.ebrRUseFixed110);

    // Map items by id and by name (first occurrence for canonical lookup, array for duplicates)
    var itemsByName = {};
    for (var i = 0; i < items.length; i++) {
      var it = items[i];
      if (!itemsByName[it.name]) itemsByName[it.name] = it;
    }

    // Working per-item state across 6 convergence passes (handles multi-level BOM & filling feedback)
    var work = {};
    for (var idx = 0; idx < items.length; idx++) {
      var item = items[idx];
      var op = calcItemOpening(item);
      work[item.id] = {
        item: item,
        opening: op.opening,
        autoOpening: op.autoOpening,
        isOpeningOverridden: op.isOverridden,
        months: [0, 1, 2, 3].map(function () {
          return {
            startStock: 0,
            sales: 0,
            contractIn: 0,
            directUsage: 0,
            bomUsage: 0,
            effectiveUsage: 0,
            isUsageOverridden: false,
            effectiveProdQty: 0,
            childRollupProd: 0,
            purchase: 0,
            autoOtherIn: 0,
            effectiveOtherIn: 0,
            isOtherInOverridden: false,
            adjBalance: 0,
            endStock: 0,
            capPct: null,
            alerts: [],
            scheduleDays: [],
            scheduleDayCount: 0
          };
        })
      };
    }

    var bomBreakdownByTarget = {};
    var recoveryBreakdownByTarget = {};

    for (var pass = 0; pass < 6; pass++) {
      // 1) Aggregate effective production by product name & calculate BOM consumption
      var prodByName = {};
      for (var pIdx = 0; pIdx < items.length; pIdx++) {
        var pItem = items[pIdx];
        var pw = work[pItem.id];
        if (!prodByName[pItem.name]) prodByName[pItem.name] = [0, 0, 0, 0];

        for (var m = 0; m < 4; m++) {
          var pm = (pItem.months && pItem.months[m]) || {};
          var parsedSched = parsePeriodDays(pm.periodStr, monthsMeta[m]);
          pw.months[m].scheduleDays = parsedSched.days;
          pw.months[m].scheduleDayCount = parsedSched.count;
          pw.months[m].scheduleInvalid = parsedSched.hasInvalid;

          var s = num(pm.sales, 0);
          var ci = num(pm.contractIn, 0);
          var effProd = num(pm.prodQty, 0);
          if (pm.prodFormulaMode === 'sales_plus_usage') {
            // Note: Uses effectiveUsage from previous pass; converges by pass 2-3
            effProd = round6(s + pw.months[m].effectiveUsage);
          } else if (pm.prodFormulaMode === 'daily_rate' && num(pm.dailyRate, 0) > 0 && parsedSched.count > 0) {
            effProd = round6(parsedSched.count * num(pm.dailyRate, 0));
          }
          pw.months[m].sales = s;
          pw.months[m].contractIn = ci;
          pw.months[m].effectiveProdQty = effProd;
          prodByName[pItem.name][m] = round6(prodByName[pItem.name][m] + effProd);
        }
      }

      // 2) Compute BOM demand per target item name & month
      var bomSumByTarget = {};
      bomBreakdownByTarget = {};
      for (var bIdx = 0; bIdx < bomRules.length; bIdx++) {
        var rule = bomRules[bIdx];
        if (rule.active === false) continue;
        var pQtys = prodByName[rule.product] || [0, 0, 0, 0];
        var yRate = num(rule.yieldRate, 0);
        var ratio = num(rule.ratio, 0);
        var dec = num(rule.roundingDecimals, 0);

        // Optional Excel fidelity for 初餾產銷!R41 EBR(R) (=EBR95*1.1) vs 秏料 R47
        if (useFixedEbrR && rule.product === 'EBR95' && rule.rawMaterial === 'EBR(R)') {
          yRate = 1.1;
          ratio = 1.0;
          dec = 1;
        }

        if (!bomSumByTarget[rule.rawMaterial]) bomSumByTarget[rule.rawMaterial] = [0, 0, 0, 0];
        if (!bomBreakdownByTarget[rule.rawMaterial]) bomBreakdownByTarget[rule.rawMaterial] = [];

        var ruleMonths = [];
        for (var bm = 0; bm < 4; bm++) {
          var qtyUsed = roundN(pQtys[bm] * yRate * ratio, dec);
          bomSumByTarget[rule.rawMaterial][bm] = round6(bomSumByTarget[rule.rawMaterial][bm] + qtyUsed);
          ruleMonths.push(qtyUsed);
        }
        bomBreakdownByTarget[rule.rawMaterial].push({
          ruleId: rule.id,
          product: rule.product,
          yieldRate: yRate,
          ratio: ratio,
          roundingDecimals: dec,
          months: ruleMonths
        });
      }

      // 3) Update effectiveUsage for every item
      var usageByName = {};
      var directUsageByName = {};
      for (var uIdx = 0; uIdx < items.length; uIdx++) {
        var uItem = items[uIdx];
        var uw = work[uItem.id];
        if (!usageByName[uItem.name]) usageByName[uItem.name] = [0, 0, 0, 0];
        if (!directUsageByName[uItem.name]) directUsageByName[uItem.name] = [0, 0, 0, 0];
        for (var um = 0; um < 4; um++) {
          var umRaw = (uItem.months && uItem.months[um]) || {};
          var dUse = num(umRaw.directUsage, 0);
          var bUse = (bomSumByTarget[uItem.name] && bomSumByTarget[uItem.name][um]) || 0;
          var hasOv = umRaw.usageOverride !== null && umRaw.usageOverride !== undefined && umRaw.usageOverride !== '';
          var effU = hasOv ? num(umRaw.usageOverride, 0) : round6(dUse + bUse);

          uw.months[um].directUsage = dUse;
          uw.months[um].bomUsage = bUse;
          uw.months[um].isUsageOverridden = hasOv;
          uw.months[um].effectiveUsage = effU;

          usageByName[uItem.name][um] = round6(usageByName[uItem.name][um] + effU);
          directUsageByName[uItem.name][um] = round6(directUsageByName[uItem.name][um] + dUse);
        }
      }

      // 4) Recovery rules (e.g. IPAUPS directUsage * 95% + 2IPA -> IPA otherIn; CPNE4(含浸) usage -> 1CPN otherIn)
      var recoverySumByTarget = {};
      recoveryBreakdownByTarget = {};
      for (var rIdx = 0; rIdx < recoveryRules.length; rIdx++) {
        var rRule = recoveryRules[rIdx];
        if (rRule.active === false) continue;
        if (!recoverySumByTarget[rRule.targetRaw]) recoverySumByTarget[rRule.targetRaw] = [0, 0, 0, 0];
        if (!recoveryBreakdownByTarget[rRule.targetRaw]) recoveryBreakdownByTarget[rRule.targetRaw] = [];

        var srcArr = [0, 0, 0, 0];
        if (rRule.sourceField === 'prodQty') {
          srcArr = prodByName[rRule.sourceItem] || [0, 0, 0, 0];
        } else if (rRule.sourceField === 'directUsage') {
          srcArr = directUsageByName[rRule.sourceItem] || [0, 0, 0, 0];
        } else {
          srcArr = usageByName[rRule.sourceItem] || [0, 0, 0, 0];
        }

        var rMonths = [];
        for (var rm = 0; rm < 4; rm++) {
          var recVal = roundN(srcArr[rm] * num(rRule.factor, 1), num(rRule.roundingDecimals, 0));
          recoverySumByTarget[rRule.targetRaw][rm] = round6(recoverySumByTarget[rRule.targetRaw][rm] + recVal);
          rMonths.push(recVal);
        }
        recoveryBreakdownByTarget[rRule.targetRaw].push({
          ruleId: rRule.id,
          sourceItem: rRule.sourceItem,
          factor: rRule.factor,
          note: rRule.note,
          months: rMonths
        });
      }

      // 5) Child-to-parent production rollups (e.g. EGUPS(勝一S07)->EGUPS, ACTUPS(外購)->ACTUPS, LG->IPAUPS M1)
      var rollupByParent = {};
      for (var cIdx = 0; cIdx < items.length; cIdx++) {
        var cItem = items[cIdx];
        if (!cItem.rollupTo) continue;
        var cw = work[cItem.id];
        if (!rollupByParent[cItem.rollupTo]) rollupByParent[cItem.rollupTo] = [0, 0, 0, 0];
        for (var cm = 0; cm < 4; cm++) {
          var allow = Array.isArray(cItem.rollupMonths) ? !!cItem.rollupMonths[cm] : true;
          if (allow) {
            rollupByParent[cItem.rollupTo][cm] = round6(rollupByParent[cItem.rollupTo][cm] + cw.months[cm].effectiveProdQty);
          }
        }
      }

      // 6) Calculate Ending Stock sequentially M1 -> M4
      for (var fIdx = 0; fIdx < items.length; fIdx++) {
        var fItem = items[fIdx];
        var fw = work[fItem.id];
        var runningStart = fw.opening;
        var childArr = rollupByParent[fItem.name] || [0, 0, 0, 0];
        var recArr = recoverySumByTarget[fItem.name] || [0, 0, 0, 0];

        for (var fm = 0; fm < 4; fm++) {
          var fmRaw = (fItem.months && fItem.months[fm]) || {};
          var cell = fw.months[fm];
          cell.startStock = runningStart;
          cell.childRollupProd = childArr[fm];
          cell.purchase = num(fmRaw.purchase, 0);
          cell.autoOtherIn = recArr[fm];

          var hasOtherOv = fmRaw.otherInOverride !== null && fmRaw.otherInOverride !== undefined && fmRaw.otherInOverride !== '';
          cell.isOtherInOverridden = hasOtherOv;
          cell.effectiveOtherIn = hasOtherOv ? num(fmRaw.otherInOverride, 0) : round6(num(fmRaw.otherIn, 0) + cell.autoOtherIn);
          cell.adjBalance = num(fmRaw.adjBalance, 0);

          // Note: For Filling items whose mode is sales_plus_usage, keep effectiveProdQty = sales + effectiveUsage on last pass
          if (fmRaw.prodFormulaMode === 'sales_plus_usage') {
            cell.effectiveProdQty = round6(cell.sales + cell.effectiveUsage);
          }

          var endVal = round6(
            cell.startStock -
            cell.sales +
            cell.contractIn -
            cell.effectiveUsage +
            cell.effectiveProdQty +
            cell.childRollupProd +
            cell.purchase +
            cell.effectiveOtherIn +
            cell.adjBalance
          );
          cell.endStock = endVal;
          runningStart = endVal;
        }
      }
    }

    // 7) Evaluate alerts & line schedule conflicts (post-convergence)
    var alerts = [];
    var scheduleEntriesByLineMonth = {}; // line|mIdx -> array of entries
    var overrideCount = 0;
    var criticalCount = 0;
    var overCapCount = 0;
    var belowMinCount = 0;

    for (var aIdx = 0; aIdx < items.length; aIdx++) {
      var aItem = items[aIdx];
      var aw = work[aItem.id];
      if (aw.isOpeningOverridden) overrideCount++;

      // Skip rolled-up child-only rows or inactive placeholder rows without stock tracking
      var isNonStockChild = (aItem.sourceSheet === '精餾產銷' && (
        aItem.name === 'IPAUPS(崙尾區日本料)' ||
        aItem.name === 'IPAUPS(崙尾區LG)' ||
        aItem.name === 'IPAUPS(預備行)' ||
        (aItem.rollupTo && num(aItem.capacity, 0) === 0 && num(aItem.invMaterial, 0) === 0)
      ));

      for (var am = 0; am < 4; am++) {
        var mCell = aw.months[am];
        var mRaw = (aItem.months && aItem.months[am]) || {};
        if (mCell.isUsageOverridden || mCell.isOtherInOverridden || num(mCell.adjBalance, 0) !== 0) {
          overrideCount++;
        }

        if (aItem.capacity > 0) {
          mCell.capPct = roundN((mCell.endStock / aItem.capacity) * 100, 1);
        }

        mCell.alerts = [];
        if (!isNonStockChild) {
          if (mCell.endStock < -0.001) {
            mCell.alerts.push('critical');
            criticalCount++;
            alerts.push({
              severity: 'critical',
              itemId: aItem.id,
              itemName: aItem.name,
              process: aItem.process,
              monthIdx: am,
              monthLabel: monthsMeta[am].label,
              value: mCell.endStock,
              message: aItem.name + ' 在 ' + monthsMeta[am].label + ' 預估結存 ' + roundN(mCell.endStock, 2) + ' MT (< 0 缺料)'
            });
          } else if (aItem.capacity > 0 && mCell.endStock > aItem.capacity + 0.001) {
            mCell.alerts.push('over_capacity');
            overCapCount++;
            alerts.push({
              severity: 'over_capacity',
              itemId: aItem.id,
              itemName: aItem.name,
              process: aItem.process,
              monthIdx: am,
              monthLabel: monthsMeta[am].label,
              value: mCell.endStock,
              limit: aItem.capacity,
              message: aItem.name + ' 在 ' + monthsMeta[am].label + ' 結存 ' + roundN(mCell.endStock, 2) + ' MT 超過儲槽上限 ' + aItem.capacity + ' MT'
            });
          }

          if (aItem.safetyMin !== null && aItem.safetyMin !== undefined && mCell.endStock < aItem.safetyMin - 0.001) {
            mCell.alerts.push('below_min');
            belowMinCount++;
            alerts.push({
              severity: 'below_min',
              itemId: aItem.id,
              itemName: aItem.name,
              process: aItem.process,
              monthIdx: am,
              monthLabel: monthsMeta[am].label,
              value: mCell.endStock,
              limit: aItem.safetyMin,
              message: aItem.name + ' 在 ' + monthsMeta[am].label + ' 結存 ' + roundN(mCell.endStock, 2) + ' MT 低於安全庫存 ' + aItem.safetyMin + ' MT'
            });
          }
        }

        // Collect schedule entries for Gantt & conflict detection
        var lineStr = String(mRaw.line || '').trim();
        if (lineStr && mCell.effectiveProdQty > 0) {
          var lineList = lineStr.split('+').map(function (x) { return x.trim(); }).filter(Boolean);
          for (var lIdx = 0; lIdx < lineList.length; lIdx++) {
            var singleLine = lineList[lIdx];
            var key = singleLine + '|' + am;
            if (!scheduleEntriesByLineMonth[key]) scheduleEntriesByLineMonth[key] = [];
            scheduleEntriesByLineMonth[key].push({
              itemId: aItem.id,
              itemName: aItem.name,
              process: aItem.process,
              line: singleLine,
              monthIdx: am,
              monthLabel: monthsMeta[am].label,
              periodStr: mRaw.periodStr || '',
              days: mCell.scheduleDays,
              prodQty: mCell.effectiveProdQty
            });
          }
        }
      }
    }

    // Check same-line day overlap only for continuous distillation towers (S01/S02/S03/R01/R02)
    var exclusiveTowers = { S01: true, S02: true, S03: true, R01: true, R02: true };
    var conflicts = [];
    Object.keys(scheduleEntriesByLineMonth).forEach(function (key) {
      var lineName = key.split('|')[0];
      if (!exclusiveTowers[lineName]) return;
      var entries = scheduleEntriesByLineMonth[key];
      for (var i1 = 0; i1 < entries.length; i1++) {
        for (var i2 = i1 + 1; i2 < entries.length; i2++) {
          var e1 = entries[i1];
          var e2 = entries[i2];
          var set1 = new Set(e1.days);
          var overlap = e2.days.filter(function (d) { return set1.has(d); });
          if (overlap.length > 0) {
            var isNmpRule = (
              (e1.itemName === 'NMPUPS' && (e2.itemName === 'IPAUPS' || e2.itemName === 'EGUPS')) ||
              (e2.itemName === 'NMPUPS' && (e1.itemName === 'IPAUPS' || e1.itemName === 'EGUPS'))
            );
            conflicts.push({
              type: isNmpRule ? 'nmp_avoidance' : 'line_overlap',
              line: e1.line,
              monthIdx: e1.monthIdx,
              monthLabel: e1.monthLabel,
              items: [e1.itemName, e2.itemName],
              overlapDays: overlap,
              message: e1.line + ' 在 ' + e1.monthLabel + ' 的 ' + overlap.join(',') + ' 日同時排產「' + e1.itemName + '」與「' + e2.itemName + '」' + (isNmpRule ? '（違反 NMPUPS 須避開 IPAUPS/EGUPS 規範）' : '')
            });
          }
        }
      }
    });

    // Cross-month NMPUPS vs IPAUPS/EGUPS adjacency warning per factory rule
    for (var cmIdx = 0; cmIdx < 4; cmIdx++) {
      ['S01', 'S02', 'S03'].forEach(function (ln) {
        var ents = scheduleEntriesByLineMonth[ln + '|' + cmIdx] || [];
        var hasNmp = ents.find(function (x) { return x.itemName === 'NMPUPS'; });
        var hasTarget = ents.filter(function (x) { return x.itemName === 'IPAUPS' || x.itemName === 'EGUPS'; });
        if (hasNmp && hasTarget.length > 0) {
          hasTarget.forEach(function (t) {
            conflicts.push({
              type: 'nmp_sequence_notice',
              line: ln,
              monthIdx: cmIdx,
              monthLabel: monthsMeta[cmIdx].label,
              items: [hasNmp.itemName, t.itemName],
              overlapDays: [],
              message: ln + ' 在 ' + monthsMeta[cmIdx].label + ' 同月排有 NMPUPS 與 ' + t.itemName + '，請確認切換清洗避讓順序'
            });
          });
        }
      });
    }

    return {
      monthsMeta: monthsMeta,
      computedById: work,
      bomBreakdownByTarget: bomBreakdownByTarget,
      recoveryBreakdownByTarget: recoveryBreakdownByTarget,
      scheduleEntriesByLineMonth: scheduleEntriesByLineMonth,
      alerts: alerts,
      conflicts: conflicts,
      stats: {
        totalItems: items.length,
        criticalCount: criticalCount,
        overCapCount: overCapCount,
        belowMinCount: belowMinCount,
        overrideCount: overrideCount,
        conflictCount: conflicts.length
      }
    };
  }

  var api = {
    num: num,
    roundN: roundN,
    round6: round6,
    parsePeriodDays: parsePeriodDays,
    buildMonthsFromBaseDate: buildMonthsFromBaseDate,
    calcItemOpening: calcItemOpening,
    recalculatePlan: recalculatePlan
  };

  root.SalesPlannerEngine = api;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
  }
})(typeof window !== 'undefined' ? window : globalThis);
