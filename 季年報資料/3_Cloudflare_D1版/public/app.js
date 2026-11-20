/**
 * 鴻勝資材部｜季年報智慧分析系統核心邏輯 (app.js)
 * 支援：1_Web_網頁版 (純前端) / 2_PWA_App版 (本機 SQLite) / 3_Cloudflare_D1版 (雲端 D1)
 */
(function () {
  'use strict';

  const STORAGE_KEYS = {
    METRICS: 'hs_report_metrics_v1',
    MGMT: 'hs_report_mgmt_v1',
    PROJECTS: 'hs_report_projects_v1',
    GEMINI_KEY: 'hs_report_gemini_key',
    THRESHOLD: 'hs_report_alert_threshold',
  };

  const GEMINI_MODELS = [
    'gemini-3.8-flash',
    'gemini-3.7-flash',
    'gemini-3.6-flash',
    'gemini-2.5-flash',
    'gemini-1.5-flash',
  ];

  const WH_ITEMS = [
    '原料進貨',
    '客供包材進貨',
    '自用包材進貨',
    '成品入庫',
    '調撥',
    '換標或理貨作業',
    '出貨',
  ];
  const WH_COLORS = ['#38bdf8', '#818cf8', '#a78bfa', '#34d399', '#fbbf24', '#f472b6', '#fb7185'];

  // Configure pdf.js worker
  if (window.pdfjsLib) {
    pdfjsLib.GlobalWorkerOptions.workerSrc =
      'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
  }

  let state = {
    apiOnline: false,
    apiMode: 'LOCAL_BROWSER',
    metrics: [],
    management: [],
    projects: [],
    parsedPreview: [],
    mgmtPreview: [],
    projPreview: [],
    projViewMode: 'active',
    alertThreshold: Number(localStorage.getItem(STORAGE_KEYS.THRESHOLD) || 15),
    charts: { inbound: null, outbound: null, warehouse: null, warehouseTrend: null },
    deferredPrompt: null,
  };

  let syncMgr = null;

  function getProjectYearGroup(p) {
    const eta = String(p?.eta || '').trim();
    const yr = eta.match(/(20\d{2})/);
    if (yr) return yr[1];
    if (/全年|持續/.test(eta)) return 'ONGOING';
    return 'UNSCHEDULED';
  }

  function formatProjectYearGroupLabel(g) {
    if (/^20\d{2}$/.test(g)) return `📅 ${g} 年度`;
    if (g === 'ONGOING') return '🔁 全年持續 / 常態目標';
    return '⏳ 待排程 / 暫緩';
  }

  function sortYearGroups(groups) {
    return [...groups].sort((a, b) => {
      const aYr = /^20\d{2}$/.test(a);
      const bYr = /^20\d{2}$/.test(b);
      if (aYr && bYr) return Number(b) - Number(a);
      if (aYr) return -1;
      if (bYr) return 1;
      if (a === 'ONGOING' && b !== 'ONGOING') return -1;
      if (b === 'ONGOING' && a !== 'ONGOING') return 1;
      return a.localeCompare(b);
    });
  }

  function getProjectsForReportYear(targetYear, includeWarehouseFilter = false) {
    const whKw = /倉|板|儲|包材|堆高機|庫房|報廢|危險品|理貨|換標/;
    const baseList = includeWarehouseFilter
      ? (() => {
          const whOnly = state.projects.filter((p) => whKw.test(`${p.title} ${p.desc} ${p.effect}`));
          return whOnly.length ? whOnly : state.projects;
        })()
      : state.projects;

    const yrStr = String(targetYear || '').trim();
    const yrNum = Number(yrStr);

    let filtered = baseList.filter((p) => {
      const g = getProjectYearGroup(p);
      if (p.status === '已完成') {
        return yrStr ? g === yrStr : false;
      }
      if (/^20\d{2}$/.test(g) && yrNum) {
        return Number(g) <= yrNum;
      }
      return true;
    });

    if (!filtered.length) {
      const activeOnly = baseList.filter((p) => p.status !== '已完成');
      filtered = activeOnly.length ? activeOnly : baseList;
    }

    return [...filtered].sort((a, b) => {
      const aDone = a.status === '已完成' ? 1 : 0;
      const bDone = b.status === '已完成' ? 1 : 0;
      return aDone - bDone;
    });
  }

  // ==================== 工具函式 ====================
  function showToast(msg, type = 'info') {
    const box = document.getElementById('toastBox');
    if (!box) return;
    const colors = {
      success: 'bg-emerald-600 border-emerald-400',
      error: 'bg-rose-600 border-rose-400',
      warning: 'bg-amber-600 border-amber-400',
      info: 'bg-sky-600 border-sky-400',
    };
    const el = document.createElement('div');
    el.className = `${colors[type] || colors.info} border text-white text-sm font-semibold px-4 py-2.5 rounded-xl shadow-xl transition`;
    el.textContent = msg;
    box.appendChild(el);
    setTimeout(() => {
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 300);
    }, 3200);
  }

  function fmtNum(v, decimals = 0) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    return Number(v).toLocaleString('zh-TW', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  function fmtDiff(curr, prev, unit = '', decimals = 0) {
    if (curr == null || prev == null || prev === 0) {
      return { text: '無對照基期', pct: null, delta: null, cls: 'text-slate-400', isAlert: false };
    }
    const delta = curr - prev;
    const pct = (delta / Math.abs(prev)) * 100;
    const sign = delta >= 0 ? '+' : '';
    const isAlert = Math.abs(pct) >= state.alertThreshold;
    const cls = isAlert
      ? 'text-rose-400 font-extrabold'
      : delta >= 0
      ? 'text-emerald-400 font-bold'
      : 'text-amber-300 font-bold';
    return {
      text: `${sign}${fmtNum(delta, decimals)}${unit} (${sign}${pct.toFixed(2)}%)`,
      pct,
      delta,
      cls,
      isAlert,
    };
  }

  function getTodayStr() {
    const d = new Date();
    return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`;
  }

  // ==================== 資料初始化與後端同步 ====================
  function loadSeedData() {
    const seed = window.SEED_DATA || { official_metrics: [], bi_metrics: [], management: [], projects: [] };
    const combined = [...(seed.official_metrics || []), ...(seed.bi_metrics || [])];
    return {
      metrics: combined,
      management: JSON.parse(JSON.stringify(seed.management || [])),
      projects: JSON.parse(JSON.stringify(seed.projects || [])),
    };
  }

  function mergeMissingSeedOfficial() {
    const officialSeed = window.SEED_DATA?.official_metrics || [];
    const existingKeys = new Set(state.metrics.map((m) => `${m.ym}|${m.category}|${m.source}`));
    const added = [];
    for (const r of officialSeed) {
      const k = `${r.ym}|${r.category}|${r.source}`;
      if (!existingKeys.has(k)) {
        const clone = JSON.parse(JSON.stringify(r));
        state.metrics.push(clone);
        existingKeys.add(k);
        added.push(clone);
      }
    }
    if (added.length > 0) saveLocalState();
    return added;
  }

  function loadLocalState() {
    const seed = loadSeedData();
    try {
      const m = JSON.parse(localStorage.getItem(STORAGE_KEYS.METRICS) || 'null');
      const g = JSON.parse(localStorage.getItem(STORAGE_KEYS.MGMT) || 'null');
      const p = JSON.parse(localStorage.getItem(STORAGE_KEYS.PROJECTS) || 'null');
      state.metrics = Array.isArray(m) && m.length ? m : seed.metrics;
      state.management = Array.isArray(g) && g.length ? g : seed.management;
      state.projects = Array.isArray(p) && p.length ? p : seed.projects;
    } catch {
      state.metrics = seed.metrics;
      state.management = seed.management;
      state.projects = seed.projects;
    }
    mergeMissingSeedOfficial();
  }

  function saveLocalState() {
    localStorage.setItem(STORAGE_KEYS.METRICS, JSON.stringify(state.metrics));
    localStorage.setItem(STORAGE_KEYS.MGMT, JSON.stringify(state.management));
    localStorage.setItem(STORAGE_KEYS.PROJECTS, JSON.stringify(state.projects));
  }

  async function detectApiAndSync(manual = false) {
    const badge = document.getElementById('modeBadge');
    try {
      const res = await fetch('/api/health', { cache: 'no-store' });
      if (res.ok) {
        const info = await res.json();
        state.apiOnline = true;
        state.apiMode = info.mode || 'SERVER_API';
        if (badge) badge.textContent = info.mode === 'CLOUDFLARE_D1' ? '☁️ Cloudflare D1 雲端版' : '🖥️ PWA 本機 SQLite 版';
        await pullAllFromServer();
        if (manual) showToast('已從資料庫同步最新數據', 'success');
        return;
      }
    } catch {
      // Static / offline mode
    }
    state.apiOnline = false;
    state.apiMode = 'LOCAL_BROWSER';
    if (badge) badge.textContent = '🌐 單機網頁版 (LocalStorage)';
    if (manual) showToast('目前為單機瀏覽器模式，已載入本機最新資料', 'info');
  }

  async function pullAllFromServer() {
    try {
      const [mRes, gRes, pRes] = await Promise.all([
        fetch('/api/metrics'),
        fetch('/api/management'),
        fetch('/api/projects'),
      ]);
      if (mRes.ok) {
        const d = await mRes.json();
        if (Array.isArray(d.data) && d.data.length > 0) {
          state.metrics = d.data;
          const newlyAdded = mergeMissingSeedOfficial();
          if (newlyAdded.length > 0) {
            await pushMetricsBatch(newlyAdded, 'SEED_PATCH_2026Q1_WH');
          }
        } else {
          // Seed server if empty
          await pushMetricsBatch(state.metrics, 'INITIAL_SEED');
        }
      }
      if (gRes.ok) {
        const d = await gRes.json();
        if (Array.isArray(d.data) && d.data.length > 0) {
          state.management = d.data;
        } else if (state.management.length > 0) {
          await apiPost('/api/management', { records: state.management }, '初始化日常管理基準');
        }
      }
      if (pRes.ok) {
        const d = await pRes.json();
        if (Array.isArray(d.data) && d.data.length > 0) {
          state.projects = d.data;
        } else if (state.projects.length > 0) {
          await apiPost('/api/projects', { records: state.projects }, '初始化重要工作進度基準');
        }
      }
      saveLocalState();
      populateYearSelector();
      renderAll();
    } catch (e) {
      console.warn('Pull from server skipped:', e);
    }
  }

  async function apiPost(url, payload, title) {
    if (!state.apiOnline) return { offline: true, localOnly: true };
    if (syncMgr) {
      return await syncMgr.request(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        title,
      });
    }
    const r = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return await r.json();
  }

  async function pushMetricsBatch(records, filename = 'MANUAL') {
    if (!state.apiOnline) return;
    await apiPost('/api/metrics', { records, filename }, `寫入 ${records.length} 筆月度指標`);
  }

  // ==================== 資料口徑整合與查詢 ====================
  function getScopedMetrics() {
    const scope = document.getElementById('selScope')?.value || 'merged';
    const map = new Map(); // key: ym|category
    const priority = { OFFICIAL_PPT: 1, BI_EXCEL: 2, BI_PDF: 3, MANUAL: 4 };

    for (const r of state.metrics) {
      if (scope === 'official' && r.source !== 'OFFICIAL_PPT' && r.source !== 'MANUAL') continue;
      if (scope === 'bi' && r.source !== 'BI_EXCEL' && r.source !== 'BI_PDF' && r.source !== 'MANUAL') continue;

      const key = `${r.ym}|${r.category}`;
      if (!map.has(key)) {
        map.set(key, { ...r });
      } else {
        const prev = map.get(key);
        if (scope === 'merged') {
          // For 2022-2025, prefer OFFICIAL_PPT for headline KPIs, but attach BI breakdown if available!
          const isHist = r.ym <= '2025-09';
          if (isHist) {
            if (r.source === 'OFFICIAL_PPT') {
              map.set(key, { ...r, bi_breakdown: prev.breakdown || prev.bi_breakdown });
            } else if (prev.source === 'OFFICIAL_PPT') {
              prev.bi_breakdown = r.breakdown;
            } else if ((priority[r.source] || 0) >= (priority[prev.source] || 0)) {
              map.set(key, { ...r });
            }
          } else {
            if ((priority[r.source] || 0) >= (priority[prev.source] || 0)) {
              map.set(key, { ...r });
            }
          }
        } else {
          if ((priority[r.source] || 0) >= (priority[prev.source] || 0)) {
            map.set(key, { ...r });
          }
        }
      }
    }
    return map;
  }

  function getPeriodMonths(type, year, sub) {
    const y = Number(year);
    const s = Number(sub);
    if (type === 'month') {
      return [`${y}-${String(s).padStart(2, '0')}`];
    }
    if (type === 'quarter') {
      const start = (s - 1) * 3 + 1;
      return [start, start + 1, start + 2].map((m) => `${y}-${String(m).padStart(2, '0')}`);
    }
    if (type === 'half') {
      const start = s === 1 ? 1 : 7;
      return Array.from({ length: 6 }, (_, i) => `${y}-${String(start + i).padStart(2, '0')}`);
    }
    return Array.from({ length: 12 }, (_, i) => `${y}-${String(i + 1).padStart(2, '0')}`);
  }

  function getComparePeriod(type, year, sub, compareMode) {
    const y = Number(year);
    const s = Number(sub);
    if (compareMode === 'yoy' || type === 'year') {
      return { year: y - 1, sub: s, label: formatPeriodLabel(type, y - 1, s) };
    }
    // Previous period (MoM / QoQ / HoH)
    if (type === 'month') {
      return s === 1
        ? { year: y - 1, sub: 12, label: formatPeriodLabel(type, y - 1, 12) }
        : { year: y, sub: s - 1, label: formatPeriodLabel(type, y, s - 1) };
    }
    if (type === 'quarter') {
      return s === 1
        ? { year: y - 1, sub: 4, label: formatPeriodLabel(type, y - 1, 4) }
        : { year: y, sub: s - 1, label: formatPeriodLabel(type, y, s - 1) };
    }
    if (type === 'half') {
      return s === 1
        ? { year: y - 1, sub: 2, label: formatPeriodLabel(type, y - 1, 2) }
        : { year: y, sub: 1, label: formatPeriodLabel(type, y, 1) };
    }
    return { year: y - 1, sub: 1, label: `${y - 1}年` };
  }

  function formatPeriodLabel(type, year, sub) {
    if (type === 'month') return `${year}年${sub}月`;
    if (type === 'quarter') return `${year}年Q${sub}`;
    if (type === 'half') return `${year}年H${sub}`;
    return `${year}年全年`;
  }

  function aggregateMonths(scopedMap, months) {
    const sum = {
      inMt: 0, inTrips: 0, inCount: 0,
      outMt: 0, outTrips: 0, outCount: 0,
      whPallets: 0, whCount: 0,
      whDailyAvgList: [],
      inProducts: {}, inPartners: {},
      outProducts: {}, outPartners: {},
      whBreakdown: {
        原料進貨: 0,
        客供包材進貨: 0,
        自用包材進貨: 0,
        成品入庫: 0,
        調撥: 0,
        換標或理貨作業: 0,
        出貨: 0,
      },
    };

    for (const ym of months) {
      const iRec = scopedMap.get(`${ym}|inbound`);
      if (iRec) {
        if (iRec.mt != null) { sum.inMt += Number(iRec.mt); sum.inCount++; }
        if (iRec.trips != null) sum.inTrips += Number(iRec.trips);
        const bd = iRec.bi_breakdown || iRec.breakdown || {};
        (bd.top_products || []).forEach(([k, v]) => (sum.inProducts[k] = (sum.inProducts[k] || 0) + v));
        (bd.top_partners || []).forEach(([k, v]) => (sum.inPartners[k] = (sum.inPartners[k] || 0) + v));
      }
      const oRec = scopedMap.get(`${ym}|outbound`);
      if (oRec) {
        if (oRec.mt != null) { sum.outMt += Number(oRec.mt); sum.outCount++; }
        if (oRec.trips != null) sum.outTrips += Number(oRec.trips);
        const bd = oRec.bi_breakdown || oRec.breakdown || {};
        (bd.top_products || []).forEach(([k, v]) => (sum.outProducts[k] = (sum.outProducts[k] || 0) + v));
        (bd.top_partners || []).forEach(([k, v]) => (sum.outPartners[k] = (sum.outPartners[k] || 0) + v));
      }
      const wRec = scopedMap.get(`${ym}|warehouse`);
      if (wRec && wRec.pallets != null) {
        sum.whPallets += Number(wRec.pallets);
        sum.whCount++;
        const bd = wRec.breakdown || {};
        WH_ITEMS.forEach((k) => {
          if (bd[k]) sum.whBreakdown[k] += Number(bd[k]);
        });
        if (bd['平均工作日棧板數'] != null && bd['平均工作日棧板數'] !== '') {
          sum.whDailyAvgList.push(Number(bd['平均工作日棧板數']));
        }
      }
    }
    return sum;
  }

  // ==================== 畫面渲染 ====================
  function populateYearSelector() {
    const years = Array.from(new Set(state.metrics.map((m) => m.ym.slice(0, 4)))).sort().reverse();
    if (!years.length) years.push('2026', '2025', '2024');
    const sel = document.getElementById('selYear');
    const prev = sel.value;
    const html = years.map((y) => `<option value="${y}">${y} 年</option>`).join('');
    sel.innerHTML = html;
    sel.value = prev && years.includes(prev) ? prev : years.includes('2025') ? '2025' : years[0];

    const whYr = document.getElementById('whQuickYear');
    if (whYr) {
      whYr.innerHTML = html;
      whYr.value = sel.value;
    }
    populateSubPeriodSelector();
  }

  function populateSubPeriodSelector() {
    const type = document.getElementById('selPeriodType').value;
    const sel = document.getElementById('selSubPeriod');
    const wrap = document.getElementById('subPeriodWrap');
    const whType = document.getElementById('whQuickPeriodType');
    const whSub = document.getElementById('whQuickSub');
    if (whType) whType.value = type;

    const prev = sel.value;
    if (type === 'year') {
      wrap.classList.add('opacity-40', 'pointer-events-none');
      sel.innerHTML = `<option value="1">全年度 (1~12月)</option>`;
      if (whSub) {
        whSub.innerHTML = sel.innerHTML;
        whSub.value = '1';
        whSub.disabled = true;
      }
      return;
    }
    wrap.classList.remove('opacity-40', 'pointer-events-none');
    if (whSub) whSub.disabled = false;

    if (type === 'quarter') {
      sel.innerHTML = [1, 2, 3, 4].map((q) => `<option value="${q}">Q${q} (${(q - 1) * 3 + 1}~${q * 3}月)</option>`).join('');
      sel.value = ['1', '2', '3', '4'].includes(prev) ? prev : '3';
    } else if (type === 'half') {
      sel.innerHTML = `<option value="1">H1 上半年 (1~6月)</option><option value="2">H2 下半年 (7~12月)</option>`;
      sel.value = ['1', '2'].includes(prev) ? prev : '1';
    } else {
      sel.innerHTML = Array.from({ length: 12 }, (_, i) => `<option value="${i + 1}">${i + 1} 月</option>`).join('');
      sel.value = prev && Number(prev) >= 1 && Number(prev) <= 12 ? prev : '9';
    }
    if (whSub) {
      whSub.innerHTML = sel.innerHTML;
      whSub.value = sel.value;
    }
  }

  window.syncWarehouseFilter = function (part, val) {
    if (part === 'type') {
      document.getElementById('selPeriodType').value = val;
      populateSubPeriodSelector();
    } else if (part === 'year') {
      document.getElementById('selYear').value = val;
    } else if (part === 'sub') {
      document.getElementById('selSubPeriod').value = val;
    }
    renderAll();
  };

  function renderAll() {
    const scoped = getScopedMetrics();
    const type = document.getElementById('selPeriodType').value;
    const year = document.getElementById('selYear').value;
    const sub = document.getElementById('selSubPeriod').value;
    const cmpMode = document.getElementById('selCompareMode').value;

    const whType = document.getElementById('whQuickPeriodType');
    const whYr = document.getElementById('whQuickYear');
    const whSub = document.getElementById('whQuickSub');
    if (whType) whType.value = type;
    if (whYr) whYr.value = year;
    if (whSub) whSub.value = sub;

    const currMonths = getPeriodMonths(type, year, sub);
    const cmp = getComparePeriod(type, year, sub, cmpMode);
    const prevMonths = getPeriodMonths(type, cmp.year, cmp.sub);
    const currLabel = formatPeriodLabel(type, year, sub);

    const currAgg = aggregateMonths(scoped, currMonths);
    const prevAgg = aggregateMonths(scoped, prevMonths);

    const printHdr = document.getElementById('printDashHeader');
    if (printHdr) {
      printHdr.textContent = `鴻勝資材部｜${currLabel} 原料大車進出貨戰情報表（對照：${cmp.label} ｜ 製表日期：${getTodayStr()}）`;
    }

    renderKpiCards(currAgg, prevAgg, currLabel, cmp.label);
    renderCharts(scoped, currMonths, prevMonths, currLabel, cmp.label);
    renderWarehouseView(scoped, currMonths, prevMonths, currAgg, prevAgg, currLabel, cmp.label, year, cmp.year);
    renderDrilldown(currAgg);
    renderMonthlyTable(scoped, currMonths, prevMonths);
    renderPptReport(scoped, currMonths, prevMonths, currAgg, prevAgg, currLabel, cmp.label, year, cmp.year);
    renderAnomalyAlerts(scoped);
    renderManagementList();
    renderProjectsTable();
    renderAdminTable();
  }

  function renderKpiCards(curr, prev, currLabel, prevLabel) {
    const inAvgLoad = curr.inTrips ? (curr.inMt / curr.inTrips).toFixed(1) : '—';
    const outAvgLoad = curr.outTrips ? (curr.outMt / curr.outTrips).toFixed(1) : '—';

    const cards = [
      {
        title: '原料進貨重量 (MT)',
        icon: '📦',
        val: curr.inCount ? curr.inMt : null,
        prevVal: prev.inCount ? prev.inMt : null,
        unit: ' MT',
        dec: 0,
        subNote: `平均單車載重：${inAvgLoad} MT/車`,
        accent: 'from-sky-500/20 to-blue-600/10 border-sky-500/30',
      },
      {
        title: '進貨大車車次',
        icon: '🚛',
        val: curr.inCount ? curr.inTrips : null,
        prevVal: prev.inCount ? prev.inTrips : null,
        unit: ' 車次',
        dec: 0,
        subNote: '採購進貨・廢液回收・調撥進貨',
        accent: 'from-cyan-500/20 to-sky-600/10 border-cyan-500/30',
      },
      {
        title: '成品出貨重量 (MT)',
        icon: '🚢',
        val: curr.outCount ? curr.outMt : null,
        prevVal: prev.outCount ? prev.outMt : null,
        unit: ' MT',
        dec: 0,
        subNote: `平均單車載重：${outAvgLoad} MT/車`,
        accent: 'from-emerald-500/20 to-teal-600/10 border-emerald-500/30',
      },
      {
        title: '出貨大車車次',
        icon: '🚚',
        val: curr.outCount ? curr.outTrips : null,
        prevVal: prev.outCount ? prev.outTrips : null,
        unit: ' 車次',
        dec: 0,
        subNote: '業務出貨・調撥出貨',
        accent: 'from-teal-500/20 to-emerald-600/10 border-teal-500/30',
      },
    ];

    const grid = document.getElementById('kpiGrid');
    grid.innerHTML = cards
      .map((c) => {
        const diff = fmtDiff(c.val, c.prevVal, c.unit, c.dec);
        const alertRing = diff.isAlert ? 'ring-2 ring-rose-500/80' : '';
        return `
        <div class="glass rounded-2xl p-4 bg-gradient-to-br ${c.accent} ${alertRing} flex flex-col justify-between">
          <div class="flex items-center justify-between text-xs text-slate-300">
            <span class="font-bold">${c.icon} ${c.title}</span>
            ${diff.isAlert ? '<span class="px-1.5 py-0.5 rounded bg-rose-600 text-white text-[10px] font-bold">⚠️ 波動預警</span>' : ''}
          </div>
          <div class="my-2">
            <div class="text-2xl font-black text-white">${c.val != null ? fmtNum(c.val, c.dec) : '尚無資料'}</div>
            <div class="text-[11px] text-slate-400 mt-0.5">對照 ${prevLabel}：${c.prevVal != null ? fmtNum(c.prevVal, c.dec) + c.unit : '無資料'}</div>
            <div class="text-[10px] text-sky-300/80 mt-0.5">${c.subNote}</div>
          </div>
          <div class="text-xs ${diff.cls} pt-1.5 border-t border-slate-700/60">${diff.text}</div>
        </div>`;
      })
      .join('');
  }

  function renderCharts(scoped, currMonths, prevMonths, currLabel, prevLabel) {
    document.getElementById('inboundPeriodTag').textContent = `${currLabel} vs ${prevLabel}`;
    document.getElementById('outboundPeriodTag').textContent = `${currLabel} vs ${prevLabel}`;

    const labels = currMonths.map((ym) => `${Number(ym.slice(5))}月`);
    const getSeries = (months, cat, field) =>
      months.map((ym) => {
        const r = scoped.get(`${ym}|${cat}`);
        return r && r[field] != null ? Number(r[field]) : 0;
      });

    // Inbound Chart
    if (state.charts.inbound) state.charts.inbound.destroy();
    state.charts.inbound = new Chart(document.getElementById('chartInbound'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: `${prevLabel} (MT)`, data: getSeries(prevMonths, 'inbound', 'mt'), backgroundColor: 'rgba(148,163,184,0.45)', borderRadius: 6, yAxisID: 'y' },
          { label: `${currLabel} (MT)`, data: getSeries(currMonths, 'inbound', 'mt'), backgroundColor: 'rgba(56,189,248,0.85)', borderRadius: 6, yAxisID: 'y' },
          { label: `${currLabel} 車次`, data: getSeries(currMonths, 'inbound', 'trips'), type: 'line', borderColor: '#facc15', backgroundColor: '#facc15', tension: 0.3, yAxisID: 'y1' },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 11 } } } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
          y: { position: 'left', ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
          y1: { position: 'right', ticks: { color: '#facc15' }, grid: { drawOnChartArea: false } },
        },
      },
    });

    // Outbound Chart
    if (state.charts.outbound) state.charts.outbound.destroy();
    state.charts.outbound = new Chart(document.getElementById('chartOutbound'), {
      type: 'bar',
      data: {
        labels,
        datasets: [
          { label: `${prevLabel} (MT)`, data: getSeries(prevMonths, 'outbound', 'mt'), backgroundColor: 'rgba(148,163,184,0.45)', borderRadius: 6, yAxisID: 'y' },
          { label: `${currLabel} (MT)`, data: getSeries(currMonths, 'outbound', 'mt'), backgroundColor: 'rgba(52,211,153,0.85)', borderRadius: 6, yAxisID: 'y' },
          { label: `${currLabel} 車次`, data: getSeries(currMonths, 'outbound', 'trips'), type: 'line', borderColor: '#fb923c', backgroundColor: '#fb923c', tension: 0.3, yAxisID: 'y1' },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 11 } } } },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
          y: { position: 'left', ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
          y1: { position: 'right', ticks: { color: '#fb923c' }, grid: { drawOnChartArea: false } },
        },
      },
    });
  }

  function renderWarehouseView(scoped, currMonths, prevMonths, currAgg, prevAgg, currLabel, prevLabel, year, prevYear) {
    const labelEl = document.getElementById('whActivePeriodLabel');
    if (labelEl) labelEl.textContent = `${currLabel} vs ${prevLabel}`;
    const tag1 = document.getElementById('whPeriodTag');
    const tag2 = document.getElementById('whTrendTag');
    if (tag1) tag1.textContent = `${currLabel} 7項作業結構`;
    if (tag2) tag2.textContent = `${currLabel} vs ${prevLabel}`;

    const labels = currMonths.map((ym) => `${Number(ym.slice(5))}月`);
    const getSeries = (months, field) =>
      months.map((ym) => {
        const r = scoped.get(`${ym}|warehouse`);
        return r && r[field] != null ? Number(r[field]) : 0;
      });

    // 4 Warehouse KPI Cards
    const dailyList = currAgg.whDailyAvgList || [];
    const avgDaily = dailyList.length ? Math.round(dailyList.reduce((a, b) => a + b, 0) / dailyList.length) : null;
    const top3Sum =
      (currAgg.whBreakdown['客供包材進貨'] || 0) +
      (currAgg.whBreakdown['自用包材進貨'] || 0) +
      (currAgg.whBreakdown['成品入庫'] || 0) +
      (currAgg.whBreakdown['出貨'] || 0);
    const top3Pct = currAgg.whPallets > 0 && top3Sum > 0 ? ((top3Sum / currAgg.whPallets) * 100).toFixed(1) : null;

    let peakMonth = '—';
    let peakVal = null;
    currMonths.forEach((ym) => {
      const val = scoped.get(`${ym}|warehouse`)?.pallets;
      if (val != null && (peakVal === null || Number(val) > peakVal)) {
        peakVal = Number(val);
        peakMonth = `${Number(ym.slice(5))}月`;
      }
    });

    const whDiff = fmtDiff(currAgg.whCount ? currAgg.whPallets : null, prevAgg.whCount ? prevAgg.whPallets : null, ' 板', 0);
    const whGrid = document.getElementById('whKpiGrid');
    if (whGrid) {
      const whCards = [
        {
          title: '倉庫總作業棧板數',
          icon: '🏭',
          valText: currAgg.whCount ? fmtNum(currAgg.whPallets, 0) : '尚無資料',
          sub: `對照 ${prevLabel}：${prevAgg.whCount ? fmtNum(prevAgg.whPallets, 0) + ' 板' : '無資料'}`,
          foot: whDiff.text,
          footCls: whDiff.cls,
          alert: whDiff.isAlert,
          accent: 'from-amber-500/20 to-orange-600/10 border-amber-500/30',
        },
        {
          title: '平均每工作日作業板數',
          icon: '📅',
          valText: avgDaily != null ? `${fmtNum(avgDaily, 0)} 板/日` : '尚無明細',
          sub: dailyList.length ? `各月範圍：${Math.min(...dailyList)} ~ ${Math.max(...dailyList)} 板/日` : '上傳明細可自動計算',
          foot: dailyList.length ? `共統計 ${dailyList.length} 個月工作日` : '需包含日均板數欄位',
          footCls: 'text-sky-300 font-semibold',
          alert: false,
          accent: 'from-sky-500/20 to-indigo-600/10 border-sky-500/30',
        },
        {
          title: '三大主力作業集中度',
          icon: '📦',
          valText: top3Pct != null ? `${top3Pct}%` : '尚無明細',
          sub: '包材進貨 + 成品入庫 + 出貨',
          foot: top3Sum > 0 ? `合計 ${fmtNum(top3Sum, 0)} 板` : '未含 7 項明細拆解',
          footCls: 'text-emerald-300 font-semibold',
          alert: false,
          accent: 'from-emerald-500/20 to-teal-600/10 border-emerald-500/30',
        },
        {
          title: '區間作業尖峰月份',
          icon: '🔥',
          valText: peakVal != null ? `${peakMonth} (${fmtNum(peakVal, 0)} 板)` : '尚無資料',
          sub: `${currLabel} 單月最高負荷`,
          foot: currAgg.whCount ? `區間月均：${fmtNum(Math.round(currAgg.whPallets / currAgg.whCount), 0)} 板/月` : '無資料',
          footCls: 'text-amber-300 font-semibold',
          alert: false,
          accent: 'from-rose-500/15 to-amber-600/10 border-rose-500/30',
        },
      ];
      whGrid.innerHTML = whCards
        .map(
          (c) => `<div class="glass rounded-2xl p-4 bg-gradient-to-br ${c.accent} ${c.alert ? 'ring-2 ring-rose-500/80' : ''} flex flex-col justify-between">
          <div class="flex items-center justify-between text-xs text-slate-300">
            <span class="font-bold">${c.icon} ${c.title}</span>
            ${c.alert ? '<span class="px-1.5 py-0.5 rounded bg-rose-600 text-white text-[10px] font-bold">⚠️ 波動預警</span>' : ''}
          </div>
          <div class="my-2">
            <div class="text-2xl font-black text-white">${c.valText}</div>
            <div class="text-[11px] text-slate-400 mt-0.5">${c.sub}</div>
          </div>
          <div class="text-xs ${c.footCls} pt-1.5 border-t border-slate-700/60">${c.foot}</div>
        </div>`
        )
        .join('');
    }

    // Chart 1: 7-item Stacked Bar
    const whCanvas = document.getElementById('chartWarehouse');
    if (whCanvas) {
      if (state.charts.warehouse) state.charts.warehouse.destroy();
      const hasBreakdown = currMonths.some((ym) => {
        const r = scoped.get(`${ym}|warehouse`);
        return r && r.breakdown && WH_ITEMS.some((k) => Number(r.breakdown[k] || 0) > 0);
      });
      const whDatasets = hasBreakdown
        ? WH_ITEMS.map((name, idx) => ({
            label: name,
            data: currMonths.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.breakdown?.[name] || 0)),
            backgroundColor: WH_COLORS[idx],
            stack: 'wh',
          }))
        : [
            { label: `${prevLabel} 棧板數`, data: getSeries(prevMonths, 'pallets'), backgroundColor: 'rgba(148,163,184,0.45)', borderRadius: 6 },
            { label: `${currLabel} 棧板數`, data: getSeries(currMonths, 'pallets'), backgroundColor: 'rgba(251,191,36,0.85)', borderRadius: 6 },
          ];
      state.charts.warehouse = new Chart(whCanvas, {
        type: 'bar',
        data: { labels, datasets: whDatasets },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 11 } } } },
          scales: {
            x: { stacked: hasBreakdown, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
            y: { stacked: hasBreakdown, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
          },
        },
      });
    }

    // Chart 2: YoY Total Pallets + Daily Avg Line
    const trendCanvas = document.getElementById('chartWarehouseTrend');
    if (trendCanvas) {
      if (state.charts.warehouseTrend) state.charts.warehouseTrend.destroy();
      const dailySeries = currMonths.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.breakdown?.['平均工作日棧板數'] || 0));
      state.charts.warehouseTrend = new Chart(trendCanvas, {
        type: 'bar',
        data: {
          labels,
          datasets: [
            { label: `${prevLabel} 總棧板數`, data: getSeries(prevMonths, 'pallets'), backgroundColor: 'rgba(148,163,184,0.45)', borderRadius: 6, yAxisID: 'y' },
            { label: `${currLabel} 總棧板數`, data: getSeries(currMonths, 'pallets'), backgroundColor: 'rgba(251,191,36,0.85)', borderRadius: 6, yAxisID: 'y' },
            { label: '平均工作日作業板數', data: dailySeries, type: 'line', borderColor: '#38bdf8', backgroundColor: '#38bdf8', tension: 0.3, yAxisID: 'y1' },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { labels: { color: '#cbd5e1', font: { size: 11 } } } },
          scales: {
            x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
            y: { position: 'left', ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148,163,184,0.1)' } },
            y1: { position: 'right', ticks: { color: '#38bdf8' }, grid: { drawOnChartArea: false } },
          },
        },
      });
    }

    // Detail Table matching user's PPT screenshot
    const wrap = document.getElementById('whDetailTableWrap');
    if (wrap) {
      const mHeads = currMonths.map((ym) => `<th class="py-2.5 px-3 text-right">${Number(ym.slice(5))}月</th>`).join('');
      const itemRows = WH_ITEMS.map((item) => {
        const vals = currMonths.map((ym) => {
          const v = scoped.get(`${ym}|warehouse`)?.breakdown?.[item];
          return v != null && Number(v) !== 0 ? Number(v) : null;
        });
        const rowSum = vals.reduce((a, b) => a + (b || 0), 0);
        const share = currAgg.whPallets > 0 && rowSum > 0 ? `${((rowSum / currAgg.whPallets) * 100).toFixed(1)}%` : '—';
        return `<tr class="hover:bg-slate-800/40">
          <td class="py-2 px-3 font-bold text-slate-200">${item}</td>
          ${vals.map((v) => `<td class="py-2 px-3 text-right font-mono">${v != null ? fmtNum(v, 0) : '—'}</td>`).join('')}
          <td class="py-2 px-3 text-right font-mono font-bold text-white">${rowSum > 0 ? fmtNum(rowSum, 0) : '—'}</td>
          <td class="py-2 px-3 text-right font-mono text-xs text-slate-400">${share}</td>
        </tr>`;
      }).join('');

      const prevRowCells = prevMonths.map((ym) => {
        const v = scoped.get(`${ym}|warehouse`)?.pallets;
        return `<td class="py-2 px-3 text-right font-mono">${v != null ? fmtNum(v, 0) : '—'}</td>`;
      }).join('');
      const currRowCells = currMonths.map((ym) => {
        const v = scoped.get(`${ym}|warehouse`)?.pallets;
        return `<td class="py-2 px-3 text-right font-mono">${v != null ? fmtNum(v, 0) : '—'}</td>`;
      }).join('');
      const dailyCells = currMonths.map((ym) => {
        const v = scoped.get(`${ym}|warehouse`)?.breakdown?.['平均工作日棧板數'];
        return `<td class="py-2 px-3 text-right font-mono">${v != null && Number(v) > 0 ? fmtNum(v, 0) : '—'}</td>`;
      }).join('');

      const summaryNote =
        currAgg.whCount && prevAgg.whCount
          ? (() => {
              const d = currAgg.whPallets - prevAgg.whPallets;
              const pct = ((d / Math.abs(prevAgg.whPallets)) * 100).toFixed(2);
              const word = d >= 0 ? '增加' : '減少';
              return `說明：${currLabel}作業量 ${fmtNum(currAgg.whPallets, 0)} 板，較${prevLabel}作業量 ${fmtNum(prevAgg.whPallets, 0)} 板${word} ${fmtNum(Math.abs(d), 0)} 板 (${d >= 0 ? '+' : ''}${pct}%)。`;
            })()
          : currAgg.whCount
          ? `說明：${currLabel}作業量 ${fmtNum(currAgg.whPallets, 0)} 板（尚無 ${prevLabel} 基期可對照）。`
          : `說明：${currLabel} 尚無倉庫棧板統計資料，可至「📤 上傳解析」匯入或手動補登。`;

      wrap.innerHTML = `
        <table class="w-full text-sm text-left border-collapse">
          <thead>
            <tr class="border-b border-slate-700 text-amber-300 text-xs bg-slate-900/70">
              <th class="py-2.5 px-3">作業項目(棧板數) \\ 月份</th>
              ${mHeads}
              <th class="py-2.5 px-3 text-right">區間合計</th>
              <th class="py-2.5 px-3 text-right">佔比</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800">
            ${itemRows}
            <tr class="bg-slate-800/60 font-bold text-slate-300">
              <td class="py-2.5 px-3">${prevLabel} (棧板數)</td>
              ${prevRowCells}
              <td class="py-2.5 px-3 text-right font-mono">${prevAgg.whCount ? fmtNum(prevAgg.whPallets, 0) : '—'}</td>
              <td class="py-2.5 px-3 text-right text-xs text-slate-400">基期</td>
            </tr>
            <tr class="bg-sky-500/15 font-extrabold text-sky-300">
              <td class="py-2.5 px-3">${currLabel} (棧板數)</td>
              ${currRowCells}
              <td class="py-2.5 px-3 text-right font-mono">${currAgg.whCount ? fmtNum(currAgg.whPallets, 0) : '—'}</td>
              <td class="py-2.5 px-3 text-right font-mono text-xs ${whDiff.cls}">${whDiff.pct != null ? (whDiff.pct >= 0 ? '+' : '') + whDiff.pct.toFixed(2) + '%' : '—'}</td>
            </tr>
            <tr class="bg-slate-900/50 text-slate-300">
              <td class="py-2 px-3 font-semibold">平均每工作日作業棧板數</td>
              ${dailyCells}
              <td class="py-2 px-3 text-right font-mono font-bold text-white">${avgDaily != null ? fmtNum(avgDaily, 0) : '—'}</td>
              <td class="py-2 px-3 text-right text-xs text-slate-400">日均</td>
            </tr>
          </tbody>
        </table>
        <div class="mt-3 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-sm font-bold text-amber-200">${summaryNote}</div>
      `;
    }
  }

  function renderDrilldown(agg) {
    const box = document.getElementById('drilldownBox');
    const topInProd = Object.entries(agg.inProducts).sort((a, b) => b[1] - a[1]).slice(0, 5);
    const topOutCust = Object.entries(agg.outPartners).sort((a, b) => b[1] - a[1]).slice(0, 5);

    if (!topInProd.length && !topOutCust.length) {
      box.innerHTML = `<div class="text-slate-400 text-xs bg-slate-900/60 p-4 rounded-xl border border-slate-800">
        目前選定期間僅有彙總數據。切至 <strong>2025 / 2026</strong> 或於「上傳解析」拖入 BI 原始明細檔，即可自動展開品名與客戶佔比鑽取！
      </div>`;
      return;
    }

    const renderList = (title, items, colorCls) =>
      items.length
        ? `<div>
            <div class="text-xs font-bold ${colorCls} mb-1.5">${title}</div>
            <div class="space-y-1.5">
              ${items
                .map(([k, v]) => {
                  const maxV = items[0][1] || 1;
                  const pct = Math.min(100, Math.round((v / maxV) * 100));
                  return `<div>
                    <div class="flex justify-between text-xs"><span class="truncate max-w-[160px]" title="${k}">${k}</span><span class="font-mono text-slate-300">${fmtNum(v, 1)} MT</span></div>
                    <div class="h-1.5 bg-slate-800 rounded-full overflow-hidden mt-0.5"><div class="h-full bg-sky-500 rounded-full" style="width:${pct}%"></div></div>
                  </div>`;
                })
                .join('')}
            </div>
          </div>`
        : '';

    box.innerHTML =
      renderList('📦 進貨 Top 5 品名 (BI 明細)', topInProd, 'text-sky-300') +
      renderList('🚚 出貨 Top 5 客戶 (BI 明細)', topOutCust, 'text-emerald-300');
  }

  function renderMonthlyTable(scoped, currMonths, prevMonths) {
    const tbody = document.getElementById('monthlyTableBody');
    tbody.innerHTML = currMonths
      .map((ym, idx) => {
        const pym = prevMonths[idx];
        const iC = scoped.get(`${ym}|inbound`);
        const iP = pym ? scoped.get(`${pym}|inbound`) : null;
        const oC = scoped.get(`${ym}|outbound`);
        const oP = pym ? scoped.get(`${pym}|outbound`) : null;

        const iDiff = fmtDiff(iC?.mt, iP?.mt, ' MT', 0);
        const oDiff = fmtDiff(oC?.mt, oP?.mt, ' MT', 0);
        const srcTag = iC?.source || oC?.source || '—';

        return `<tr class="hover:bg-slate-800/50 transition">
          <td class="py-2.5 px-3 font-bold text-white">${ym}</td>
          <td class="py-2.5 px-3 text-right font-mono">${fmtNum(iC?.mt, 0)}</td>
          <td class="py-2.5 px-3 text-right text-xs ${iDiff.cls}">${iDiff.text}</td>
          <td class="py-2.5 px-3 text-right font-mono">${fmtNum(iC?.trips, 0)}</td>
          <td class="py-2.5 px-3 text-right font-mono">${fmtNum(oC?.mt, 0)}</td>
          <td class="py-2.5 px-3 text-right text-xs ${oDiff.cls}">${oDiff.text}</td>
          <td class="py-2.5 px-3 text-right font-mono">${fmtNum(oC?.trips, 0)}</td>
          <td class="py-2.5 px-3 text-center"><span class="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">${srcTag}</span></td>
        </tr>`;
      })
      .join('');
  }

  // ==================== 雙 PPT 文案與高階簡報圖卡 ====================
  function renderPptReport(scoped, currMonths, prevMonths, currAgg, prevAgg, currLabel, prevLabel, year, prevYear) {
    const phrase = (val, prevVal, unit) => {
      if (!val) return '尚無資料';
      if (!prevVal) return `${fmtNum(val, 0)}${unit}（無對照基期資料）`;
      const d = val - prevVal;
      const pct = ((d / Math.abs(prevVal)) * 100).toFixed(2);
      const word = d >= 0 ? '增加' : '減少';
      return `${fmtNum(val, 0)}，較${prevLabel}的 ${fmtNum(prevVal, 0)} ${word} ${fmtNum(Math.abs(d), 0)}${unit} (${d >= 0 ? '+' : ''}${pct}%)`;
    };

    const mgmtLines = state.management
      .slice(0, 5)
      .map((m, i) => `${i + 1}. [${m.period} ${m.type}] ${m.content}`)
      .join('\n');

    // PPT①：原料大車進出貨文案（不含倉庫棧板）
    const bulkTxt = [
      `鴻勝資材部 ${currLabel} 原料大車進出貨報告摘要（製表日期：${getTodayStr()}）`,
      `==================================================`,
      `一、${currLabel} 進貨工作狀況（採購進貨、廢液回收、調撥進貨）`,
      `1. 進貨重量：${phrase(currAgg.inMt, prevAgg.inMt, 'MT')}。`,
      `2. 進貨車次：${phrase(currAgg.inTrips, prevAgg.inTrips, '車次')}。`,
      ``,
      `二、${currLabel} 出貨工作狀況（業務出貨、調撥出貨）`,
      `1. 出貨重量：${phrase(currAgg.outMt, prevAgg.outMt, 'MT')}。`,
      `2. 出貨車次：${phrase(currAgg.outTrips, prevAgg.outTrips, '車次')}。`,
      ``,
      `三、日常管理重點`,
      mgmtLines || '（尚無日常管理紀錄）',
    ].join('\n');

    // PPT②：倉庫棧板作業文案
    const dailyList = currAgg.whDailyAvgList || [];
    const avgDaily = dailyList.length ? Math.round(dailyList.reduce((a, b) => a + b, 0) / dailyList.length) : null;
    const pkgSum =
      (currAgg.whBreakdown['客供包材進貨'] || 0) +
      (currAgg.whBreakdown['自用包材進貨'] || 0);
    const top3Pct =
      currAgg.whPallets > 0
        ? (((pkgSum + (currAgg.whBreakdown['成品入庫'] || 0) + (currAgg.whBreakdown['出貨'] || 0)) / currAgg.whPallets) * 100).toFixed(1)
        : null;

    const whTxt = [
      `鴻勝資材部 ${currLabel} 倉庫作業統計報告摘要（製表日期：${getTodayStr()}）`,
      `==================================================`,
      `一、${currLabel} 倉庫作業總量`,
      `說明：${currLabel}作業量 ${currAgg.whCount ? fmtNum(currAgg.whPallets, 0) : '—'} 板，較${prevLabel}作業量 ${prevAgg.whCount ? fmtNum(prevAgg.whPallets, 0) : '—'} 板${
        currAgg.whCount && prevAgg.whCount
          ? `${currAgg.whPallets - prevAgg.whPallets >= 0 ? '增加' : '減少'} ${fmtNum(Math.abs(currAgg.whPallets - prevAgg.whPallets), 0)} 板 (${currAgg.whPallets - prevAgg.whPallets >= 0 ? '+' : ''}${(((currAgg.whPallets - prevAgg.whPallets) / Math.abs(prevAgg.whPallets)) * 100).toFixed(2)}%)`
          : '（無對照基期）'
      }。`,
      `二、作業結構分佈（棧板數）`,
      `• 原料進貨：${fmtNum(currAgg.whBreakdown['原料進貨'], 0)} 板 ｜ 客供包材進貨：${fmtNum(currAgg.whBreakdown['客供包材進貨'], 0)} 板 ｜ 自用包材進貨：${fmtNum(currAgg.whBreakdown['自用包材進貨'], 0)} 板`,
      `• 成品入庫：${fmtNum(currAgg.whBreakdown['成品入庫'], 0)} 板 ｜ 調撥：${fmtNum(currAgg.whBreakdown['調撥'], 0)} 板 ｜ 換標或理貨作業：${fmtNum(currAgg.whBreakdown['換標或理貨作業'], 0)} 板 ｜ 出貨：${fmtNum(currAgg.whBreakdown['出貨'], 0)} 板`,
      `• 平均每工作日作業棧板數：${avgDaily != null ? fmtNum(avgDaily, 0) + ' 板/日' : '—'}${top3Pct ? `（包材進貨、成品入庫與出貨三大作業合計佔 ${top3Pct}%）` : ''}`,
    ].join('\n');

    const elBulkTxt = document.getElementById('pptSummaryBulk');
    const elWhTxt = document.getElementById('pptSummaryWarehouse');
    if (elBulkTxt) elBulkTxt.value = bulkTxt;
    if (elWhTxt) elWhTxt.value = whTxt;

    const theme = document.getElementById('selExportTheme')?.value || 'exec';
    const judgeText = (curr, prev) => {
      if (!curr || !prev) return { text: '基期未齊全', cls: '' };
      const pct = ((curr - prev) / Math.abs(prev)) * 100;
      if (pct >= state.alertThreshold) return { text: '顯著成長 (高負荷)', cls: 'row-highlight' };
      if (pct > 0) return { text: '穩健成長', cls: 'row-pos' };
      if (pct <= -state.alertThreshold) return { text: '明顯縮減 (需關注)', cls: 'row-neg' };
      return { text: '微幅調整', cls: 'row-blue' };
    };

    const inAvgPerTrip = currAgg.inTrips ? (currAgg.inMt / currAgg.inTrips).toFixed(1) : '—';
    const outAvgPerTrip = currAgg.outTrips ? (currAgg.outMt / currAgg.outTrips).toFixed(1) : '—';
    const topInProd = Object.entries(currAgg.inProducts).sort((a, b) => b[1] - a[1])[0];
    const topOutCust = Object.entries(currAgg.outPartners).sort((a, b) => b[1] - a[1])[0];

    const bulkRows = [
      { label: '• 進貨工作量 (MT)', cat: 'inbound', field: 'mt', unit: 'MT', currTot: currAgg.inMt, prevTot: prevAgg.inMt },
      { label: '• 進貨運輸車次 (車次)', cat: 'inbound', field: 'trips', unit: '車次', currTot: currAgg.inTrips, prevTot: prevAgg.inTrips },
      { label: '• 出貨工作量 (MT)', cat: 'outbound', field: 'mt', unit: 'MT', currTot: currAgg.outMt, prevTot: prevAgg.outMt },
      { label: '• 出貨運輸車次 (車次)', cat: 'outbound', field: 'trips', unit: '車次', currTot: currAgg.outTrips, prevTot: prevAgg.outTrips },
    ];

    // ---- Card 1: Bulk Inbound / Outbound ----
    const bulkContainer = document.getElementById('pptCardBulk');
    if (bulkContainer) {
      bulkContainer.className = theme === 'dark' ? 'dark-slide space-y-5' : 'exec-slide space-y-5';
      if (theme === 'exec') {
        const mHeads = currMonths.map((ym) => `<th>${Number(ym.slice(5))}月</th>`).join('');
        const tbodyHtml = bulkRows
          .map((r, idx) => {
            const vals = currMonths.map((ym) => fmtNum(scoped.get(`${ym}|${r.cat}`)?.[r.field], 0));
            const diff = fmtDiff(r.currTot || null, r.prevTot || null, '', 0);
            const judge = judgeText(r.currTot, r.prevTot);
            const diffColor = diff.delta == null ? '#64748b' : diff.delta >= 0 ? '#047857' : '#dc2626';
            return `<tr class="${idx % 2 === 1 ? 'row-alt' : ''}">
              <td class="item-col">${r.label}</td>
              ${vals.map((v) => `<td>${v}</td>`).join('')}
              <td style="background:#eff6ff;color:#1e3a8a;font-weight:800;">${fmtNum(r.currTot, 0)}</td>
              <td style="color:#475569;">${r.prevTot ? fmtNum(r.prevTot, 0) : '—'}</td>
              <td style="color:${diffColor};font-weight:800;">${diff.text}</td>
              <td class="${judge.cls}" style="font-weight:800;">${judge.text}</td>
            </tr>`;
          })
          .join('');

        bulkContainer.innerHTML = `
          <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #1e293b;padding-bottom:10px;">
            <div>
              <div style="font-size:23px;font-weight:900;color:#0f172a;">PPT①｜鴻勝資材部 ${currLabel} 原料大車進出貨績效總覽</div>
              <div style="font-size:12px;color:#64748b;margin-top:2px;">對照基準：${currLabel} vs ${prevLabel} ｜ 製表日期：${getTodayStr()}</div>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <div style="width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,#0284c7,#2563eb);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:18px;">◆</div>
              <div style="font-size:19px;font-weight:900;color:#0f172a;letter-spacing:2px;">鴻勝資材部</div>
            </div>
          </div>
          <table class="exec-table">
            <thead>
              <tr><th style="width:210px;">項目 ＼ 月份</th>${mHeads}<th>${currLabel} 累計</th><th>${prevLabel} 基準</th><th>差異增減 (%)</th><th>綜合判定</th></tr>
            </thead>
            <tbody>${tbodyHtml}</tbody>
          </table>
          <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding-top:4px;">
            <div class="exec-callout exec-callout-blue">
              <div style="font-weight:800;color:#1d4ed8;font-size:14px;margin-bottom:6px;text-align:center;">✔ 進貨量能與車次摘要</div>
              <ul style="font-size:12.5px;color:#334155;line-height:1.65;margin:0;padding-left:16px;">
                <li>本期進貨 <strong>${fmtNum(currAgg.inMt, 0)} MT</strong>，${fmtDiff(currAgg.inMt, prevAgg.inMt, ' MT').text}。</li>
                <li>累計進廠 <strong>${fmtNum(currAgg.inTrips, 0)} 車次</strong>，平均單車載重 <strong>${inAvgPerTrip} MT/車</strong>。</li>
                ${topInProd ? `<li>主力進貨品項：<strong>${topInProd[0]}</strong> (${fmtNum(topInProd[1], 0)} MT)。</li>` : ''}
              </ul>
            </div>
            <div class="exec-callout exec-callout-amber">
              <div style="font-weight:800;color:#b45309;font-size:14px;margin-bottom:6px;text-align:center;">🚀 出貨表現與運輸效率</div>
              <ul style="font-size:12.5px;color:#334155;line-height:1.65;margin:0;padding-left:16px;">
                <li>本期出貨 <strong>${fmtNum(currAgg.outMt, 0)} MT</strong>，${fmtDiff(currAgg.outMt, prevAgg.outMt, ' MT').text}。</li>
                <li>累計出貨 <strong>${fmtNum(currAgg.outTrips, 0)} 車次</strong>，平均單車載重 <strong>${outAvgPerTrip} MT/車</strong>。</li>
                ${topOutCust ? `<li>主力出貨客戶：<strong>${topOutCust[0].slice(0, 12)}</strong> (${fmtNum(topOutCust[1], 0)} MT)。</li>` : ''}
              </ul>
            </div>
            <div class="exec-callout exec-callout-green">
              <div style="font-weight:800;color:#15803d;font-size:14px;margin-bottom:6px;text-align:center;">🎯 日常管理與專案追蹤</div>
              <ul style="font-size:12.5px;color:#334155;line-height:1.65;margin:0;padding-left:16px;">
                <li>大車進出廠合計 <strong>${fmtNum(currAgg.inTrips + currAgg.outTrips, 0)} 車次</strong>，總吞吐量 <strong>${fmtNum(currAgg.inMt + currAgg.outMt, 0)} MT</strong>。</li>
                <li>日常管理已建檔 <strong>${state.management.length} 筆</strong>（品質・工安・客戶稽核）。</li>
                <li>重點專案：進行中 ${state.projects.filter((p) => p.status === '進行中').length} 項、已完成 ${state.projects.filter((p) => p.status === '已完成').length} 項。</li>
              </ul>
            </div>
          </div>`;
      } else {
        const kpiHtml = bulkRows
          .map((r, i) => {
            const diff = fmtDiff(r.currTot || null, r.prevTot || null, ' ' + r.unit, 0);
            const borders = ['#0ea5e9', '#06b6d4', '#10b981', '#14b8a6'];
            return `<div style="background:rgba(30,41,59,0.85);border:1px solid ${borders[i]}66;border-radius:14px;padding:14px;">
              <div style="font-size:12px;color:#94a3b8;font-weight:700;">${r.label.replace('• ', '')}</div>
              <div style="font-size:24px;font-weight:900;color:#fff;margin:6px 0;">${fmtNum(r.currTot, 0)}</div>
              <div style="font-size:11px;color:#94a3b8;">對照 ${prevLabel}：${r.prevTot ? fmtNum(r.prevTot, 0) : '—'}</div>
              <div style="font-size:12px;margin-top:6px;padding-top:6px;border-top:1px solid #334155;font-weight:700;color:${diff.delta >= 0 ? '#34d399' : '#fbbf24'};">${diff.text}</div>
            </div>`;
          })
          .join('');
        const mHeads = currMonths.map((ym) => `<th style="padding:8px 10px;text-align:center;color:#94a3b8;font-size:12px;">${Number(ym.slice(5))}月</th>`).join('');
        const rowsHtml = bulkRows
          .map((r) => {
            const vals = currMonths.map((ym) => `<td style="padding:8px 10px;text-align:center;font-family:monospace;color:#e2e8f0;">${fmtNum(scoped.get(`${ym}|${r.cat}`)?.[r.field], 0)}</td>`).join('');
            const diff = fmtDiff(r.currTot || null, r.prevTot || null, '', 0);
            return `<tr style="border-bottom:1px solid #1e293b;">
              <td style="padding:8px 10px;font-weight:700;color:#fff;">${r.label.replace('• ', '')}</td>
              ${vals}
              <td style="padding:8px 10px;text-align:center;font-weight:800;color:#38bdf8;">${fmtNum(r.currTot, 0)}</td>
              <td style="padding:8px 10px;text-align:center;font-weight:700;color:${diff.delta >= 0 ? '#34d399' : '#fb7185'};">${diff.text}</td>
            </tr>`;
          })
          .join('');
        bulkContainer.innerHTML = `
          <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #334155;padding-bottom:12px;">
            <div>
              <div style="font-size:21px;font-weight:900;color:#fff;">🚛 PPT①｜鴻勝資材部 ${currLabel} 原料大車進出貨戰情總覽</div>
              <div style="font-size:12px;color:#94a3b8;margin-top:2px;">比較基準：${currLabel} vs ${prevLabel} ｜ 製表日期：${getTodayStr()}</div>
            </div>
            <span style="background:rgba(14,165,233,0.2);color:#38bdf8;border:1px solid rgba(56,189,248,0.4);padding:4px 12px;border-radius:999px;font-size:12px;font-weight:700;">BULK LOGISTICS</span>
          </div>
          <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;">${kpiHtml}</div>
          <div style="background:rgba(15,23,42,0.75);border:1px solid #334155;border-radius:14px;padding:12px;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <thead><tr style="border-bottom:1px solid #334155;"><th style="text-align:left;padding:8px 10px;color:#94a3b8;">項目</th>${mHeads}<th style="padding:8px 10px;color:#38bdf8;">累計</th><th style="padding:8px 10px;color:#94a3b8;">差異增減</th></tr></thead>
              <tbody>${rowsHtml}</tbody>
            </table>
          </div>`;
      }
    }

    // ---- Card 2: Warehouse Pallets ----
    const whContainer = document.getElementById('pptCardWarehouse');
    if (whContainer) {
      whContainer.className = theme === 'dark' ? 'dark-slide space-y-5' : 'exec-slide space-y-5';
      const whDiff = fmtDiff(currAgg.whCount ? currAgg.whPallets : null, prevAgg.whCount ? prevAgg.whPallets : null, ' 板', 0);

      if (theme === 'exec') {
        const mHeads = currMonths.map((ym) => `<th>${Number(ym.slice(5))}月</th>`).join('');
        const whItemRows = WH_ITEMS.map((item, idx) => {
          const vals = currMonths.map((ym) => {
            const v = scoped.get(`${ym}|warehouse`)?.breakdown?.[item];
            return v != null && Number(v) !== 0 ? fmtNum(v, 0) : '';
          });
          const tot = currAgg.whBreakdown[item] || 0;
          const share = currAgg.whPallets > 0 && tot > 0 ? `${((tot / currAgg.whPallets) * 100).toFixed(1)}%` : '—';
          return `<tr class="${idx % 2 === 1 ? 'row-alt' : ''}">
            <td class="item-col">• ${item}</td>
            ${vals.map((v) => `<td>${v || '—'}</td>`).join('')}
            <td style="background:#eff6ff;color:#1e3a8a;font-weight:800;">${tot > 0 ? fmtNum(tot, 0) : '—'}</td>
            <td style="color:#475569;">${share}</td>
          </tr>`;
        }).join('');

        const prevRowCells = prevMonths.map((ym) => `<td>${fmtNum(scoped.get(`${ym}|warehouse`)?.pallets, 0)}</td>`).join('');
        const currRowCells = currMonths.map((ym) => `<td>${fmtNum(scoped.get(`${ym}|warehouse`)?.pallets, 0)}</td>`).join('');
        const dailyRowCells = currMonths.map((ym) => {
          const v = scoped.get(`${ym}|warehouse`)?.breakdown?.['平均工作日棧板數'];
          return `<td>${v != null && Number(v) > 0 ? fmtNum(v, 0) : '—'}</td>`;
        }).join('');

        whContainer.innerHTML = `
          <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:2px solid #1e293b;padding-bottom:10px;">
            <div>
              <div style="font-size:23px;font-weight:900;color:#0f172a;">PPT②｜鴻勝資材部 ${currLabel} 倉庫作業統計報告（棧板數）</div>
              <div style="font-size:12px;color:#64748b;margin-top:2px;">對照基準：${currLabel} vs ${prevLabel} ｜ 製表日期：${getTodayStr()}</div>
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
              <div style="width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,#f59e0b,#ea580c);display:flex;align-items:center;justify-content:center;color:#fff;font-weight:900;font-size:18px;">◆</div>
              <div style="font-size:19px;font-weight:900;color:#0f172a;letter-spacing:2px;">鴻勝資材部</div>
            </div>
          </div>

          <table class="exec-table">
            <thead>
              <tr><th style="width:220px;">作業項目 (棧板數) ＼ 月份</th>${mHeads}<th>區間合計</th><th>佔比 / 說明</th></tr>
            </thead>
            <tbody>
              ${whItemRows}
              <tr class="row-pos"><td class="item-col">${prevLabel} (棧板數)</td>${prevRowCells}<td>${prevAgg.whCount ? fmtNum(prevAgg.whPallets, 0) : '—'}</td><td>對照基期</td></tr>
              <tr class="row-blue"><td class="item-col">${currLabel} (棧板數)</td>${currRowCells}<td>${currAgg.whCount ? fmtNum(currAgg.whPallets, 0) : '—'}</td><td>${whDiff.text}</td></tr>
              <tr class="row-highlight"><td class="item-col">平均每工作日作業棧板數</td>${dailyRowCells}<td>${avgDaily != null ? fmtNum(avgDaily, 0) : '—'}</td><td>工作日均量</td></tr>
            </tbody>
          </table>

          <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;padding-top:4px;">
            <div class="exec-callout exec-callout-blue">
              <div style="font-weight:800;color:#1d4ed8;font-size:14px;margin-bottom:6px;text-align:center;">✔ 作業總量與基期差異</div>
              <ul style="font-size:12.5px;color:#334155;line-height:1.65;margin:0;padding-left:16px;">
                <li>本期倉庫作業總量 <strong>${currAgg.whCount ? fmtNum(currAgg.whPallets, 0) : '—'} 板</strong>。</li>
                <li>對照 ${prevLabel}（${prevAgg.whCount ? fmtNum(prevAgg.whPallets, 0) : '—'} 板）：<strong>${whDiff.text}</strong>。</li>
                <li>平均每工作日作業 <strong>${avgDaily != null ? fmtNum(avgDaily, 0) + ' 板/日' : '—'}</strong>。</li>
              </ul>
            </div>
            <div class="exec-callout exec-callout-amber">
              <div style="font-weight:800;color:#b45309;font-size:14px;margin-bottom:6px;text-align:center;">📦 主力作業結構分析</div>
              <ul style="font-size:12.5px;color:#334155;line-height:1.65;margin:0;padding-left:16px;">
                <li>包材進貨（客供+自用）：<strong>${fmtNum(pkgSum, 0)} 板</strong>。</li>
                <li>成品入庫：<strong>${fmtNum(currAgg.whBreakdown['成品入庫'], 0)} 板</strong> ｜ 出貨：<strong>${fmtNum(currAgg.whBreakdown['出貨'], 0)} 板</strong>。</li>
                <li>三大主力作業佔總負荷 <strong>${top3Pct ? top3Pct + '%' : '—'}</strong>。</li>
              </ul>
            </div>
            <div class="exec-callout exec-callout-green">
              <div style="font-weight:800;color:#15803d;font-size:14px;margin-bottom:6px;text-align:center;">🎯 儲位與調撥管理建言</div>
              <ul style="font-size:12.5px;color:#334155;line-height:1.65;margin:0;padding-left:16px;">
                <li>調撥作業 <strong>${fmtNum(currAgg.whBreakdown['調撥'], 0)} 板</strong>，換標/理貨 <strong>${fmtNum(currAgg.whBreakdown['換標或理貨作業'], 0)} 板</strong>。</li>
                <li>工作量主要集中在包材進貨、成品入庫與出貨三項作業。</li>
                <li>建議持續追蹤危倉擴充與小包材儲位週轉率。</li>
              </ul>
            </div>
          </div>`;
      } else {
        const mHeads = currMonths.map((ym) => `<th style="padding:8px 10px;text-align:center;color:#94a3b8;font-size:12px;">${Number(ym.slice(5))}月</th>`).join('');
        const itemRowsHtml = WH_ITEMS.map((item) => {
          const vals = currMonths.map((ym) => `<td style="padding:7px 10px;text-align:center;font-family:monospace;color:#e2e8f0;">${fmtNum(scoped.get(`${ym}|warehouse`)?.breakdown?.[item] || null, 0)}</td>`).join('');
          return `<tr style="border-bottom:1px solid #1e293b;">
            <td style="padding:7px 10px;font-weight:700;color:#fff;">${item}</td>${vals}
            <td style="padding:7px 10px;text-align:center;font-weight:800;color:#fbbf24;">${currAgg.whBreakdown[item] ? fmtNum(currAgg.whBreakdown[item], 0) : '—'}</td>
          </tr>`;
        }).join('');
        whContainer.innerHTML = `
          <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #334155;padding-bottom:12px;">
            <div>
              <div style="font-size:21px;font-weight:900;color:#fff;">🏭 PPT②｜鴻勝資材部 ${currLabel} 倉庫作業戰情統計</div>
              <div style="font-size:12px;color:#94a3b8;margin-top:2px;">總作業量：${fmtNum(currAgg.whPallets, 0)} 板（${whDiff.text}）｜ 日均：${avgDaily != null ? fmtNum(avgDaily, 0) + ' 板/日' : '—'}</div>
            </div>
            <span style="background:rgba(245,158,11,0.2);color:#fbbf24;border:1px solid rgba(245,158,11,0.4);padding:4px 12px;border-radius:999px;font-size:12px;font-weight:700;">WAREHOUSE OPS</span>
          </div>
          <div style="background:rgba(15,23,42,0.75);border:1px solid #334155;border-radius:14px;padding:12px;">
            <table style="width:100%;border-collapse:collapse;font-size:13px;">
              <thead><tr style="border-bottom:1px solid #334155;"><th style="text-align:left;padding:8px 10px;color:#94a3b8;">作業項目(棧板數)</th>${mHeads}<th style="padding:8px 10px;color:#fbbf24;">區間合計</th></tr></thead>
              <tbody>${itemRowsHtml}</tbody>
            </table>
          </div>`;
      }
    }
  }

  window.copyPptText = async function (kind = 'bulk') {
    const id = kind === 'warehouse' ? 'pptSummaryWarehouse' : 'pptSummaryBulk';
    const txt = document.getElementById(id)?.value || '';
    await navigator.clipboard.writeText(txt);
    showToast(`已複製${kind === 'warehouse' ? '倉庫作業' : '原料進出貨'} PPT 摘要文案！`, 'success');
  };

  window.exportPptCardPng = async function (kind = 'bulk') {
    const elId = kind === 'warehouse' ? 'pptCardWarehouse' : 'pptCardBulk';
    const el = document.getElementById(elId);
    if (!el) return;
    const theme = document.getElementById('selExportTheme')?.value || 'exec';
    const type = document.getElementById('selPeriodType').value;
    const year = document.getElementById('selYear').value;
    const sub = document.getElementById('selSubPeriod').value;
    const currLabel = formatPeriodLabel(type, year, sub);

    showToast(`正在渲染 2x 高解析${kind === 'warehouse' ? '倉庫' : '原料進出貨'}簡報圖卡...`, 'info');
    const canvas = await html2canvas(el, {
      scale: 2,
      backgroundColor: theme === 'dark' ? '#0b1120' : '#ffffff',
      useCORS: true,
    });
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download =
      kind === 'warehouse'
        ? `鴻勝資材部_${currLabel}_倉庫作業統計圖卡_${theme}.png`
        : `鴻勝資材部_${currLabel}_原料進出貨圖卡_${theme}.png`;
    a.click();
    showToast('高解析 PNG 圖卡下載完成！', 'success');
  };

  window.exportDashboardPng = async function () {
    showToast('正在擷取首頁深色戰情儀表板 (2x 高解析)...', 'info');
    const prevTab = document.querySelector('.tab-btn.active')?.dataset.tab || 'report';
    switchTab('dashboard');
    await new Promise((r) => setTimeout(r, 350));
    const dash = document.getElementById('tab-dashboard');
    const canvas = await html2canvas(dash, { scale: 2, backgroundColor: '#0b1120', useCORS: true });
    const a = document.createElement('a');
    a.href = canvas.toDataURL('image/png');
    a.download = `鴻勝資材部_首頁戰情總覽_${Date.now()}.png`;
    a.click();
    switchTab(prevTab);
    showToast('首頁戰情總覽高解析 PNG 已下載！', 'success');
  };

  window.printCurrentReport = function (mode = 'dark') {
    const clones = [];
    const hiddenCanvases = [];

    document.querySelectorAll('main canvas').forEach((cv) => {
      if (cv.offsetParent === null || cv.width === 0 || cv.height === 0) return;
      try {
        const img = document.createElement('img');
        img.src = cv.toDataURL('image/png', 1.0);
        img.className = 'print-canvas-clone w-full h-full object-contain';
        cv.parentNode.insertBefore(img, cv);
        cv.style.display = 'none';
        clones.push(img);
        hiddenCanvases.push(cv);
      } catch {
        // Ignore tainted canvas if any
      }
    });

    if (mode === 'light') document.body.classList.add('print-light');
    else document.body.classList.remove('print-light');

    let cleaned = false;
    let fallbackTimer = null;
    const cleanup = () => {
      if (cleaned) return;
      cleaned = true;
      if (fallbackTimer) clearTimeout(fallbackTimer);
      clones.forEach((img) => img.remove());
      hiddenCanvases.forEach((cv) => (cv.style.display = ''));
      document.body.classList.remove('print-light');
      window.removeEventListener('afterprint', cleanup);
    };

    window.addEventListener('afterprint', cleanup);
    fallbackTimer = setTimeout(cleanup, 60000);
    setTimeout(() => window.print(), 80);
  };

  window.exportDashboardEditablePptx = async function (mode = 'bulk') {
    if (typeof PptxGenJS === 'undefined') {
      showToast('PptxGenJS 模組尚未載入，請確認網路連線後重試', 'error');
      return;
    }
    const isWh = mode === 'warehouse';
    showToast(`正在產生 1:1 ${isWh ? '倉庫戰情原貌' : '首頁戰情原貌'} 可編輯 PPT (.pptx)...`, 'info');

    const scoped = getScopedMetrics();
    const type = document.getElementById('selPeriodType').value;
    const year = document.getElementById('selYear').value;
    const sub = document.getElementById('selSubPeriod').value;
    const cmpMode = document.getElementById('selCompareMode').value;

    const currMonths = getPeriodMonths(type, year, sub);
    const cmp = getComparePeriod(type, year, sub, cmpMode);
    const prevMonths = getPeriodMonths(type, cmp.year, cmp.sub);
    const currLabel = formatPeriodLabel(type, year, sub);
    const prevLabel = cmp.label;

    const currAgg = aggregateMonths(scoped, currMonths);
    const prevAgg = aggregateMonths(scoped, prevMonths);

    const pptx = new PptxGenJS();
    pptx.layout = 'LAYOUT_WIDE';
    pptx.author = '鴻勝資材部';
    pptx.title = isWh ? `鴻勝資材部 ${currLabel} 倉庫戰情原貌報告` : `鴻勝資材部 ${currLabel} 首頁戰情原貌報告`;

    const FONT = 'Microsoft JhengHei';
    const BG = '0B1120';
    const CARD = '1E293B';
    const CARD_DARK = '0F172A';
    const MUTED = '94A3B8';

    const safeArr = (arr) => (arr && arr.length ? arr.map((v) => (Number.isFinite(Number(v)) ? Number(v) : 0)) : [0]);
    const chartLabels = currMonths.length ? currMonths.map((ym) => `${Number(ym.slice(5))}月`) : ['—'];

    const addDarkHeader = (slide, titleText, pageNum) => {
      slide.background = { color: BG };
      slide.addText(titleText, {
        x: 0.45, y: 0.22, w: 8.85, h: 0.46,
        fontFace: FONT, fontSize: 19, bold: true, color: 'FFFFFF',
      });
      slide.addShape(pptx.ShapeType.roundRect, {
        x: 9.45, y: 0.25, w: 3.43, h: 0.36, rectRadius: 0.18,
        fill: { color: CARD }, line: { color: isWh ? 'F59E0B' : '38BDF8', width: 1 },
      });
      slide.addText(`對照 ${prevLabel} ｜ ${getTodayStr()} ｜ P.${pageNum}`, {
        x: 9.45, y: 0.25, w: 3.43, h: 0.36,
        fontFace: FONT, fontSize: 9.5, bold: true, color: isWh ? 'FBBF24' : '38BDF8', align: 'center', valign: 'middle',
      });
      slide.addShape(pptx.ShapeType.line, {
        x: 0.45, y: 0.76, w: 12.43, h: 0,
        line: { color: '334155', width: 1 },
      });
    };

    const addDarkKpiCard = (slide, x, y, w, h, borderCol, title, valStr, subStr, footStr, footCol) => {
      slide.addShape(pptx.ShapeType.roundRect, {
        x, y, w, h, rectRadius: 0.08,
        fill: { color: CARD }, line: { color: borderCol, width: 1.2 },
      });
      slide.addText(title, {
        x: x + 0.14, y: y + 0.1, w: w - 0.28, h: 0.24,
        fontFace: FONT, fontSize: 10, bold: true, color: 'CBD5E1',
      });
      slide.addText(valStr, {
        x: x + 0.14, y: y + 0.38, w: w - 0.28, h: 0.42,
        fontFace: FONT, fontSize: 22, bold: true, color: 'FFFFFF',
      });
      slide.addText(subStr, {
        x: x + 0.14, y: y + 0.84, w: w - 0.28, h: 0.24,
        fontFace: FONT, fontSize: 9, color: MUTED,
      });
      slide.addShape(pptx.ShapeType.line, {
        x: x + 0.14, y: y + h - 0.38, w: w - 0.28, h: 0,
        line: { color: '334155', width: 0.75 },
      });
      slide.addText(footStr, {
        x: x + 0.14, y: y + h - 0.34, w: w - 0.28, h: 0.26,
        fontFace: FONT, fontSize: 10, bold: true, color: footCol,
      });
    };

    const addDarkComboChart = (slide, x, y, w, h, title, titleCol, labels, b1Name, b1Vals, b1Col, b2Name, b2Vals, b2Col, lName, lVals, lCol) => {
      slide.addShape(pptx.ShapeType.roundRect, {
        x, y, w, h, rectRadius: 0.08,
        fill: { color: CARD }, line: { color: '334155', width: 1 },
      });
      slide.addText(title, {
        x: x + 0.18, y: y + 0.12, w: w - 0.36, h: 0.3,
        fontFace: FONT, fontSize: 12.5, bold: true, color: titleCol,
      });
      const comboTypes = [
        {
          type: pptx.ChartType.bar,
          data: [
            { name: b1Name, labels, values: safeArr(b1Vals) },
            { name: b2Name, labels, values: safeArr(b2Vals) },
          ],
          options: {
            barDir: 'col',
            barGrouping: 'clustered',
            chartColors: [b1Col, b2Col],
          },
        },
        {
          type: pptx.ChartType.line,
          data: [{ name: lName, labels, values: safeArr(lVals) }],
          options: {
            secondaryValAxis: true,
            secondaryCatAxis: true,
            chartColors: [lCol],
            lineSmooth: true,
            lineSize: 2.5,
            lineDataSymbol: 'circle',
            lineDataSymbolSize: 6,
          },
        },
      ];
      slide.addChart(comboTypes, {
        x: x + 0.12, y: y + 0.45, w: w - 0.24, h: h - 0.56,
        plotArea: { fill: { color: CARD_DARK } },
        showLegend: true,
        legendPos: 't',
        legendColor: 'CBD5E1',
        legendFontSize: 9,
        catAxes: [
          { catAxisLabelColor: 'CBD5E1', catAxisLabelFontSize: 9.5 },
          { catAxisHidden: true },
        ],
        valAxes: [
          { valAxisLabelColor: '94A3B8', valAxisLabelFontSize: 9, valGridLine: { color: '334155', width: 0.5 } },
          { valAxisLabelColor: lCol, valAxisLabelFontSize: 9, valGridLine: { style: 'none' } },
        ],
      });
    };

    const diffPptCol = (diff) => (diff.isAlert ? 'FB7185' : diff.delta == null ? '94A3B8' : diff.delta >= 0 ? '34D399' : 'FBBF24');

    if (!isWh) {
      // ==================== 首頁 1:1 戰情原貌可編輯 PPT ====================
      const s1 = pptx.addSlide();
      addDarkHeader(s1, `📊 鴻勝資材部｜${currLabel} 原料大車進出貨戰情總覽`, 1);

      const inAvgLoad = currAgg.inTrips ? (currAgg.inMt / currAgg.inTrips).toFixed(1) : '—';
      const outAvgLoad = currAgg.outTrips ? (currAgg.outMt / currAgg.outTrips).toFixed(1) : '—';
      const dInMt = fmtDiff(currAgg.inCount ? currAgg.inMt : null, prevAgg.inCount ? prevAgg.inMt : null, ' MT', 0);
      const dInTr = fmtDiff(currAgg.inCount ? currAgg.inTrips : null, prevAgg.inCount ? prevAgg.inTrips : null, ' 車次', 0);
      const dOutMt = fmtDiff(currAgg.outCount ? currAgg.outMt : null, prevAgg.outCount ? prevAgg.outMt : null, ' MT', 0);
      const dOutTr = fmtDiff(currAgg.outCount ? currAgg.outTrips : null, prevAgg.outCount ? prevAgg.outTrips : null, ' 車次', 0);

      const kpis = [
        { border: '0EA5E9', title: '📦 原料進貨重量 (MT)', val: currAgg.inCount ? fmtNum(currAgg.inMt, 0) : '尚無資料', sub: `對照 ${prevLabel}：${prevAgg.inCount ? fmtNum(prevAgg.inMt, 0) + ' MT' : '無'} ｜ ${inAvgLoad} MT/車`, foot: dInMt.text, fCol: diffPptCol(dInMt) },
        { border: '06B6D4', title: '🚛 進貨大車車次', val: currAgg.inCount ? fmtNum(currAgg.inTrips, 0) : '尚無資料', sub: `對照 ${prevLabel}：${prevAgg.inCount ? fmtNum(prevAgg.inTrips, 0) + ' 車次' : '無'}`, foot: dInTr.text, fCol: diffPptCol(dInTr) },
        { border: '10B981', title: '🚢 成品出貨重量 (MT)', val: currAgg.outCount ? fmtNum(currAgg.outMt, 0) : '尚無資料', sub: `對照 ${prevLabel}：${prevAgg.outCount ? fmtNum(prevAgg.outMt, 0) + ' MT' : '無'} ｜ ${outAvgLoad} MT/車`, foot: dOutMt.text, fCol: diffPptCol(dOutMt) },
        { border: '14B8A6', title: '🚚 出貨大車車次', val: currAgg.outCount ? fmtNum(currAgg.outTrips, 0) : '尚無資料', sub: `對照 ${prevLabel}：${prevAgg.outCount ? fmtNum(prevAgg.outTrips, 0) + ' 車次' : '無'}`, foot: dOutTr.text, fCol: diffPptCol(dOutTr) },
      ];
      kpis.forEach((k, i) => addDarkKpiCard(s1, 0.45 + i * 3.15, 0.9, 2.98, 1.56, k.border, k.title, k.val, k.sub, k.foot, k.fCol));

      const getVals = (months, cat, field) => months.map((ym) => Number(scoped.get(`${ym}|${cat}`)?.[field] || 0));
      addDarkComboChart(
        s1, 0.45, 2.64, 6.1, 4.5,
        '📦 進貨工作量對照 (柱狀 MT + 曲線 車次)', '38BDF8',
        chartLabels,
        `${prevLabel} (MT)`, getVals(prevMonths, 'inbound', 'mt'), '64748B',
        `${currLabel} (MT)`, getVals(currMonths, 'inbound', 'mt'), '38BDF8',
        `${currLabel} 車次`, getVals(currMonths, 'inbound', 'trips'), 'FACC15'
      );
      addDarkComboChart(
        s1, 6.78, 2.64, 6.1, 4.5,
        '🚚 出貨工作量對照 (柱狀 MT + 曲線 車次)', '34D399',
        chartLabels,
        `${prevLabel} (MT)`, getVals(prevMonths, 'outbound', 'mt'), '64748B',
        `${currLabel} (MT)`, getVals(currMonths, 'outbound', 'mt'), '34D399',
        `${currLabel} 車次`, getVals(currMonths, 'outbound', 'trips'), 'FB923C'
      );

      // Slide 2: Top 5 水平條圖 + 完整月度明細與差異表
      const s2 = pptx.addSlide();
      addDarkHeader(s2, `🔍 鴻勝資材部｜${currLabel} BI 品名/客戶鑽取與月度差異明細`, 2);

      const topInProd = Object.entries(currAgg.inProducts).sort((a, b) => b[1] - a[1]).slice(0, 5);
      const topOutCust = Object.entries(currAgg.outPartners).sort((a, b) => b[1] - a[1]).slice(0, 5);

      const addTop5Card = (x, title, titleCol, items, barCol) => {
        s2.addShape(pptx.ShapeType.roundRect, {
          x, y: 0.9, w: 6.1, h: 2.82, rectRadius: 0.08,
          fill: { color: CARD }, line: { color: '334155', width: 1 },
        });
        s2.addText(title, {
          x: x + 0.16, y: 0.98, w: 5.78, h: 0.28,
          fontFace: FONT, fontSize: 12, bold: true, color: titleCol,
        });
        if (!items.length) {
          s2.addText('目前選定期間無 BI 原始明細（切至 2025/2026 或上傳 BI 明細檔即可自動展開）', {
            x: x + 0.25, y: 1.7, w: 5.6, h: 1.0,
            fontFace: FONT, fontSize: 10.5, color: MUTED, align: 'center', valign: 'middle',
          });
          return;
        }
        const rev = [...items].reverse();
        s2.addChart(
          pptx.ChartType.bar,
          [{ name: '重量 (MT)', labels: rev.map(([k]) => String(k).slice(0, 14)), values: rev.map(([, v]) => Math.round(v * 10) / 10) }],
          {
            x: x + 0.12, y: 1.3, w: 5.86, h: 2.32,
            barDir: 'bar', plotArea: { fill: { color: CARD_DARK } },
            chartColors: [barCol], showLegend: false, showValue: true,
            dataLabelColor: 'FFFFFF', dataLabelFontSize: 8.5,
            catAxisLabelColor: 'CBD5E1', catAxisLabelFontSize: 8.5,
            valAxisLabelColor: '94A3B8', valAxisLabelFontSize: 8,
            valGridLine: { color: '334155', width: 0.5 },
          }
        );
      };

      addTop5Card(0.45, '📦 進貨 Top 5 品名 (BI 明細 MT)', '38BDF8', topInProd, '38BDF8');
      addTop5Card(6.78, '🚚 出貨 Top 5 客戶 (BI 明細 MT)', '34D399', topOutCust, '34D399');

      // Monthly detail table
      s2.addShape(pptx.ShapeType.roundRect, {
        x: 0.45, y: 3.88, w: 12.43, h: 3.35, rectRadius: 0.08,
        fill: { color: CARD }, line: { color: '334155', width: 1 },
      });
      s2.addText('📅 區間月度數據明細與差異表', {
        x: 0.62, y: 3.96, w: 10.0, h: 0.28,
        fontFace: FONT, fontSize: 12, bold: true, color: 'FFFFFF',
      });

      const isMany = currMonths.length > 6;
      const mTableRows = [
        ['月份', '進貨 (MT)', '進貨差異', '進貨車次', '出貨 (MT)', '出貨差異', '出貨車次', '來源口徑'].map((h, i) => ({
          text: h,
          options: { fill: { color: CARD_DARK }, color: '94A3B8', bold: true, align: i === 0 || i === 7 ? 'center' : 'right' },
        })),
        ...currMonths.map((ym, idx) => {
          const pym = prevMonths[idx];
          const iC = scoped.get(`${ym}|inbound`);
          const iP = pym ? scoped.get(`${pym}|inbound`) : null;
          const oC = scoped.get(`${ym}|outbound`);
          const oP = pym ? scoped.get(`${pym}|outbound`) : null;
          const iDiff = fmtDiff(iC?.mt, iP?.mt, ' MT', 0);
          const oDiff = fmtDiff(oC?.mt, oP?.mt, ' MT', 0);
          const rowBg = idx % 2 === 1 ? '162032' : CARD;
          return [
            { text: ym, options: { fill: { color: rowBg }, color: 'FFFFFF', bold: true, align: 'center' } },
            { text: fmtNum(iC?.mt, 0), options: { fill: { color: rowBg }, color: 'E2E8F0', align: 'right' } },
            { text: iDiff.text, options: { fill: { color: rowBg }, color: diffPptCol(iDiff), bold: true, align: 'right' } },
            { text: fmtNum(iC?.trips, 0), options: { fill: { color: rowBg }, color: 'E2E8F0', align: 'right' } },
            { text: fmtNum(oC?.mt, 0), options: { fill: { color: rowBg }, color: 'E2E8F0', align: 'right' } },
            { text: oDiff.text, options: { fill: { color: rowBg }, color: diffPptCol(oDiff), bold: true, align: 'right' } },
            { text: fmtNum(oC?.trips, 0), options: { fill: { color: rowBg }, color: 'E2E8F0', align: 'right' } },
            { text: iC?.source || oC?.source || '—', options: { fill: { color: rowBg }, color: '94A3B8', align: 'center' } },
          ];
        }),
      ];
      s2.addTable(mTableRows, {
        x: 0.6, y: 4.3, w: 12.13,
        colW: [1.1, 1.25, 2.35, 1.1, 1.25, 2.35, 1.1, 1.63],
        fontFace: FONT, fontSize: isMany ? 8 : 10, rowH: isMany ? 0.21 : 0.38, valign: 'middle',
        border: { pt: 0.5, color: '334155' },
      });
    } else {
      // ==================== 倉庫專頁 1:1 戰情原貌可編輯 PPT ====================
      const s1 = pptx.addSlide();
      addDarkHeader(s1, `🏭 鴻勝資材部｜${currLabel} 倉庫作業戰情總覽`, 1);

      const dailyList = currAgg.whDailyAvgList || [];
      const avgDaily = dailyList.length ? Math.round(dailyList.reduce((a, b) => a + b, 0) / dailyList.length) : null;
      const top3Sum =
        (currAgg.whBreakdown['客供包材進貨'] || 0) +
        (currAgg.whBreakdown['自用包材進貨'] || 0) +
        (currAgg.whBreakdown['成品入庫'] || 0) +
        (currAgg.whBreakdown['出貨'] || 0);
      const top3Pct = currAgg.whPallets > 0 && top3Sum > 0 ? ((top3Sum / currAgg.whPallets) * 100).toFixed(1) : null;

      let peakMonth = '—';
      let peakVal = null;
      currMonths.forEach((ym) => {
        const val = scoped.get(`${ym}|warehouse`)?.pallets;
        if (val != null && (peakVal === null || Number(val) > peakVal)) {
          peakVal = Number(val);
          peakMonth = `${Number(ym.slice(5))}月`;
        }
      });

      const whDiff = fmtDiff(currAgg.whCount ? currAgg.whPallets : null, prevAgg.whCount ? prevAgg.whPallets : null, ' 板', 0);
      const whKpis = [
        { border: 'F59E0B', title: '🏭 倉庫總作業棧板數', val: currAgg.whCount ? fmtNum(currAgg.whPallets, 0) : '尚無資料', sub: `對照 ${prevLabel}：${prevAgg.whCount ? fmtNum(prevAgg.whPallets, 0) + ' 板' : '無'}`, foot: whDiff.text, fCol: diffPptCol(whDiff) },
        { border: '0EA5E9', title: '📅 平均每工作日作業板數', val: avgDaily != null ? `${fmtNum(avgDaily, 0)} 板/日` : '尚無明細', sub: dailyList.length ? `各月範圍：${Math.min(...dailyList)} ~ ${Math.max(...dailyList)} 板/日` : '需含日均板數', foot: dailyList.length ? `統計 ${dailyList.length} 個月` : '—', fCol: '38BDF8' },
        { border: '10B981', title: '📦 三大主力作業集中度', val: top3Pct != null ? `${top3Pct}%` : '尚無明細', sub: '包材進貨 + 成品入庫 + 出貨', foot: top3Sum > 0 ? `合計 ${fmtNum(top3Sum, 0)} 板` : '—', fCol: '34D399' },
        { border: 'FB7185', title: '🔥 區間作業尖峰月份', val: peakVal != null ? `${peakMonth} (${fmtNum(peakVal, 0)})` : '尚無資料', sub: `${currLabel} 單月最高負荷`, foot: currAgg.whCount ? `月均：${fmtNum(Math.round(currAgg.whPallets / currAgg.whCount), 0)} 板/月` : '—', fCol: 'FBBF24' },
      ];
      whKpis.forEach((k, i) => addDarkKpiCard(s1, 0.45 + i * 3.15, 0.9, 2.98, 1.56, k.border, k.title, k.val, k.sub, k.foot, k.fCol));

      // Left Chart: 7-item stacked bar
      s1.addShape(pptx.ShapeType.roundRect, {
        x: 0.45, y: 2.64, w: 6.1, h: 4.5, rectRadius: 0.08,
        fill: { color: CARD }, line: { color: '334155', width: 1 },
      });
      s1.addText('📊 倉庫 7 項作業結構堆疊圖 (棧板數)', {
        x: 0.63, y: 2.76, w: 5.7, h: 0.3, fontFace: FONT, fontSize: 12.5, bold: true, color: 'FBBF24',
      });
      const hasBd = currMonths.some((ym) => WH_ITEMS.some((k) => Number(scoped.get(`${ym}|warehouse`)?.breakdown?.[k] || 0) > 0));
      const stackedData = hasBd
        ? WH_ITEMS.map((item) => ({
            name: item,
            labels: chartLabels,
            values: safeArr(currMonths.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.breakdown?.[item] || 0))),
          }))
        : [
            { name: `${prevLabel} 棧板數`, labels: chartLabels, values: safeArr(prevMonths.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.pallets || 0))) },
            { name: `${currLabel} 棧板數`, labels: chartLabels, values: safeArr(currMonths.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.pallets || 0))) },
          ];
      s1.addChart(pptx.ChartType.bar, stackedData, {
        x: 0.57, y: 3.1, w: 5.86, h: 3.92,
        barDir: 'col',
        barGrouping: hasBd ? 'stacked' : 'clustered',
        plotArea: { fill: { color: CARD_DARK } },
        chartColors: hasBd ? ['38BDF8', '818CF8', 'A78BFA', '34D399', 'FBBF24', 'F472B6', 'FB7185'] : ['64748B', 'F59E0B'],
        showLegend: true, legendPos: 't', legendColor: 'CBD5E1', legendFontSize: 8.5,
        catAxisLabelColor: 'CBD5E1', catAxisLabelFontSize: 9.5,
        valAxisLabelColor: '94A3B8', valAxisLabelFontSize: 9,
        valGridLine: { color: '334155', width: 0.5 },
      });

      // Right Chart: YoY Pallets + Daily Avg Curve
      addDarkComboChart(
        s1, 6.78, 2.64, 6.1, 4.5,
        '📈 同期總棧板對照 & 日均作業板數曲線', '38BDF8',
        chartLabels,
        `${prevLabel} 總板數`, prevMonths.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.pallets || 0)), '64748B',
        `${currLabel} 總板數`, currMonths.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.pallets || 0)), 'F59E0B',
        '平均工作日板數', currMonths.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.breakdown?.['平均工作日棧板數'] || 0)), '38BDF8'
      );

      // Slide 2: Warehouse 7-item dark detail table
      const s2 = pptx.addSlide();
      addDarkHeader(s2, `📋 鴻勝資材部｜${currLabel} 倉庫 7 項作業明細統計表`, 2);
      const showCols =
        currMonths.length <= 6
          ? currMonths.map((ym) => ({ label: `${Number(ym.slice(5))}月`, months: [ym] }))
          : [
              { label: 'Q1', months: currMonths.slice(0, 3) },
              { label: 'Q2', months: currMonths.slice(3, 6) },
              { label: 'Q3', months: currMonths.slice(6, 9) },
              { label: 'Q4', months: currMonths.slice(9, 12) },
            ];
      const prevCols =
        prevMonths.length <= 6
          ? prevMonths.map((ym) => ({ label: `${Number(ym.slice(5))}月`, months: [ym] }))
          : [
              { label: 'Q1', months: prevMonths.slice(0, 3) },
              { label: 'Q2', months: prevMonths.slice(3, 6) },
              { label: 'Q3', months: prevMonths.slice(6, 9) },
              { label: 'Q4', months: prevMonths.slice(9, 12) },
            ];

      s2.addShape(pptx.ShapeType.roundRect, {
        x: 0.45, y: 0.9, w: 12.43, h: 5.2, rectRadius: 0.08,
        fill: { color: CARD }, line: { color: '334155', width: 1 },
      });

      const whRows = [
        [
          { text: '作業項目 (棧板數) ＼ 月份', options: { fill: { color: CARD_DARK }, color: 'FBBF24', bold: true, align: 'left' } },
          ...showCols.map((c) => ({ text: c.label, options: { fill: { color: CARD_DARK }, color: 'FBBF24', bold: true, align: 'right' } })),
          { text: '區間合計', options: { fill: { color: CARD_DARK }, color: 'FBBF24', bold: true, align: 'right' } },
          { text: '佔比 / 說明', options: { fill: { color: CARD_DARK }, color: 'FBBF24', bold: true, align: 'right' } },
        ],
        ...WH_ITEMS.map((item, idx) => {
          const rowBg = idx % 2 === 1 ? '162032' : CARD;
          let tot = 0;
          const cells = showCols.map((c) => {
            const v = c.months.reduce((a, ym) => a + (Number(scoped.get(`${ym}|warehouse`)?.breakdown?.[item]) || 0), 0);
            tot += v;
            return { text: v > 0 ? fmtNum(v, 0) : '—', options: { fill: { color: rowBg }, color: 'E2E8F0', align: 'right' } };
          });
          const share = currAgg.whPallets > 0 && tot > 0 ? `${((tot / currAgg.whPallets) * 100).toFixed(1)}%` : '—';
          return [
            { text: item, options: { fill: { color: rowBg }, color: 'FFFFFF', bold: true, align: 'left' } },
            ...cells,
            { text: tot > 0 ? fmtNum(tot, 0) : '—', options: { fill: { color: rowBg }, color: 'FFFFFF', bold: true, align: 'right' } },
            { text: share, options: { fill: { color: rowBg }, color: MUTED, align: 'right' } },
          ];
        }),
        [
          { text: `${prevLabel} (棧板數)`, options: { fill: { color: '1E293B' }, color: 'CBD5E1', bold: true, align: 'left' } },
          ...prevCols.map((c) => {
            const v = c.months.reduce((a, ym) => a + (Number(scoped.get(`${ym}|warehouse`)?.pallets) || 0), 0);
            return { text: v > 0 ? fmtNum(v, 0) : '—', options: { fill: { color: '1E293B' }, color: 'CBD5E1', bold: true, align: 'right' } };
          }),
          { text: prevAgg.whCount ? fmtNum(prevAgg.whPallets, 0) : '—', options: { fill: { color: '1E293B' }, color: 'CBD5E1', bold: true, align: 'right' } },
          { text: '對照基期', options: { fill: { color: '1E293B' }, color: MUTED, align: 'right' } },
        ],
        [
          { text: `${currLabel} (棧板數)`, options: { fill: { color: '0C4A6E' }, color: '7DD3FC', bold: true, align: 'left' } },
          ...showCols.map((c) => {
            const v = c.months.reduce((a, ym) => a + (Number(scoped.get(`${ym}|warehouse`)?.pallets) || 0), 0);
            return { text: v > 0 ? fmtNum(v, 0) : '—', options: { fill: { color: '0C4A6E' }, color: '7DD3FC', bold: true, align: 'right' } };
          }),
          { text: currAgg.whCount ? fmtNum(currAgg.whPallets, 0) : '—', options: { fill: { color: '0C4A6E' }, color: 'FFFFFF', bold: true, align: 'right' } },
          { text: whDiff.text, options: { fill: { color: '0C4A6E' }, color: diffPptCol(whDiff), bold: true, align: 'right' } },
        ],
        [
          { text: '平均每工作日作業棧板數', options: { fill: { color: CARD_DARK }, color: 'FCD34D', bold: true, align: 'left' } },
          ...showCols.map((c) => {
            const ds = c.months
              .map((ym) => scoped.get(`${ym}|warehouse`)?.breakdown?.['平均工作日棧板數'])
              .filter((x) => x != null && Number(x) > 0)
              .map(Number);
            const avg = ds.length ? Math.round(ds.reduce((a, b) => a + b, 0) / ds.length) : 0;
            return { text: avg > 0 ? fmtNum(avg, 0) : '—', options: { fill: { color: CARD_DARK }, color: 'FCD34D', bold: true, align: 'right' } };
          }),
          { text: avgDaily != null ? fmtNum(avgDaily, 0) : '—', options: { fill: { color: CARD_DARK }, color: 'FFFFFF', bold: true, align: 'right' } },
          { text: '日均板數', options: { fill: { color: CARD_DARK }, color: MUTED, align: 'right' } },
        ],
      ];

      s2.addTable(whRows, {
        x: 0.62, y: 1.06, w: 12.1,
        fontFace: FONT, fontSize: 10.5, rowH: 0.42, valign: 'middle',
        border: { pt: 0.5, color: '334155' },
      });

      s2.addShape(pptx.ShapeType.roundRect, {
        x: 0.45, y: 6.26, w: 12.43, h: 0.9, rectRadius: 0.08,
        fill: { color: '451A03' }, line: { color: 'F59E0B', width: 1 },
      });
      const whSummary =
        currAgg.whCount && prevAgg.whCount
          ? `說明：${currLabel}作業量 ${fmtNum(currAgg.whPallets, 0)} 板，較${prevLabel}作業量 ${fmtNum(prevAgg.whPallets, 0)} 板${currAgg.whPallets - prevAgg.whPallets >= 0 ? '增加' : '減少'} ${fmtNum(Math.abs(currAgg.whPallets - prevAgg.whPallets), 0)} 板 (${currAgg.whPallets - prevAgg.whPallets >= 0 ? '+' : ''}${(((currAgg.whPallets - prevAgg.whPallets) / Math.abs(prevAgg.whPallets)) * 100).toFixed(2)}%)。`
          : `說明：${currLabel}作業量 ${fmtNum(currAgg.whPallets, 0)} 板。`;
      s2.addText(whSummary, {
        x: 0.65, y: 6.32, w: 12.0, h: 0.78,
        fontFace: FONT, fontSize: 12.5, bold: true, color: 'FDE68A', valign: 'middle',
      });
    }

    const outName = isWh
      ? `鴻勝資材部_${currLabel}_倉庫戰情原貌可編輯_${getTodayStr().replace(/\//g, '')}.pptx`
      : `鴻勝資材部_${currLabel}_首頁戰情原貌可編輯_${getTodayStr().replace(/\//g, '')}.pptx`;
    await pptx.writeFile({ fileName: outName });
    showToast(`已下載 1:1 戰情原貌可編輯 PPT：${outName}`, 'success');
  };

  window.exportEditablePptx = async function (mode = 'bulk') {
    if (typeof PptxGenJS === 'undefined') {
      showToast('PptxGenJS 模組尚未載入，請確認網路連線後重試', 'error');
      return;
    }
    const isWh = mode === 'warehouse';
    showToast(`正在產生 100% 可編輯 ${isWh ? 'PPT② 倉庫作業' : 'PPT① 原料進出貨'} (.pptx)...`, 'info');

    const scoped = getScopedMetrics();
    const type = document.getElementById('selPeriodType').value;
    const year = document.getElementById('selYear').value;
    const sub = document.getElementById('selSubPeriod').value;
    const cmpMode = document.getElementById('selCompareMode').value;

    const currMonths = getPeriodMonths(type, year, sub);
    const cmp = getComparePeriod(type, year, sub, cmpMode);
    const prevMonths = getPeriodMonths(type, cmp.year, cmp.sub);
    const currLabel = formatPeriodLabel(type, year, sub);
    const prevLabel = cmp.label;

    const currAgg = aggregateMonths(scoped, currMonths);
    const prevAgg = aggregateMonths(scoped, prevMonths);

    const pptx = new PptxGenJS();
    pptx.layout = 'LAYOUT_WIDE';
    pptx.author = '鴻勝資材部';
    pptx.title = isWh ? `鴻勝資材部 ${currLabel} 倉庫作業統計報告` : `鴻勝資材部 ${currLabel} 原料進出貨績效報告`;

    const FONT = 'Microsoft JhengHei';
    const NAVY = '1B3668';
    const DARK = '0F172A';
    const SLATE = '475569';
    const ACCENT_HEX = isWh ? 'D97706' : '0284C7';

    const showCols =
      currMonths.length <= 6
        ? currMonths.map((ym) => ({ label: `${Number(ym.slice(5))}月`, months: [ym] }))
        : [
            { label: 'Q1', months: currMonths.slice(0, 3) },
            { label: 'Q2', months: currMonths.slice(3, 6) },
            { label: 'Q3', months: currMonths.slice(6, 9) },
            { label: 'Q4', months: currMonths.slice(9, 12) },
          ];
    const prevShowCols =
      prevMonths.length <= 6
        ? prevMonths.map((ym) => ({ label: `${Number(ym.slice(5))}月`, months: [ym] }))
        : [
            { label: 'Q1', months: prevMonths.slice(0, 3) },
            { label: 'Q2', months: prevMonths.slice(3, 6) },
            { label: 'Q3', months: prevMonths.slice(6, 9) },
            { label: 'Q4', months: prevMonths.slice(9, 12) },
          ];

    const addHeader = (slide, titleText, pageNum) => {
      slide.background = { color: 'FFFFFF' };
      slide.addText(titleText, {
        x: 0.45, y: 0.28, w: 9.8, h: 0.55,
        fontFace: FONT, fontSize: 21, bold: true, color: DARK,
      });
      slide.addShape(pptx.ShapeType.roundRect, {
        x: 10.65, y: 0.32, w: 0.36, h: 0.36, rectRadius: 0.15,
        fill: { color: ACCENT_HEX }, line: { color: ACCENT_HEX },
      });
      slide.addText('◆', {
        x: 10.65, y: 0.31, w: 0.36, h: 0.36,
        fontFace: FONT, fontSize: 14, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle',
      });
      slide.addText('鴻勝資材部', {
        x: 11.08, y: 0.28, w: 1.85, h: 0.45,
        fontFace: FONT, fontSize: 17, bold: true, color: DARK, valign: 'middle',
      });
      slide.addShape(pptx.ShapeType.line, {
        x: 0.45, y: 0.88, w: 12.43, h: 0,
        line: { color: '1E293B', width: 1.5 },
      });
      if (pageNum) {
        slide.addText(`製表日期：${getTodayStr()} ｜ 第 ${pageNum} 頁`, {
          x: 9.5, y: 7.12, w: 3.4, h: 0.28,
          fontFace: FONT, fontSize: 9, color: '94A3B8', align: 'right',
        });
      }
    };

    const addCallouts = (slide, callouts, yPos = 4.65, hPos = 2.25) => {
      callouts.forEach((c, i) => {
        const cx = 0.45 + i * 4.21;
        slide.addShape(pptx.ShapeType.roundRect, {
          x: cx, y: yPos, w: 4.0, h: hPos, rectRadius: 0.12,
          fill: { color: c.fill }, line: { color: c.border, width: 1.5 },
        });
        slide.addText(c.title, {
          x: cx + 0.15, y: yPos + 0.1, w: 3.7, h: 0.36,
          fontFace: FONT, fontSize: 13, bold: true, color: c.titleColor, align: 'center',
        });
        slide.addText(
          c.bullets.map((b) => ({ text: b, options: { bullet: true, breakLine: true } })),
          {
            x: cx + 0.18, y: yPos + 0.48, w: 3.64, h: hPos - 0.56,
            fontFace: FONT, fontSize: 10.5, color: '334155', valign: 'top', lineSpacingMultiple: 1.32,
          }
        );
      });
    };

    // ---------- Slide 1: 獨立封面頁 ----------
    const s1 = pptx.addSlide();
    s1.background = { color: 'FFFFFF' };
    s1.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: 0.45, h: 7.5, fill: { color: NAVY } });
    s1.addShape(pptx.ShapeType.rect, { x: 0.45, y: 0, w: 0.12, h: 7.5, fill: { color: ACCENT_HEX } });
    s1.addText('鴻勝資材部', {
      x: 1.2, y: 1.65, w: 10, h: 0.6,
      fontFace: FONT, fontSize: 24, bold: true, color: ACCENT_HEX,
    });
    s1.addText(isWh ? `${currLabel} 倉庫作業統計報告（棧板數）` : `${currLabel} 原料大車進出貨績效報告`, {
      x: 1.2, y: 2.35, w: 11, h: 1.1,
      fontFace: FONT, fontSize: 36, bold: true, color: DARK,
    });
    s1.addShape(pptx.ShapeType.line, {
      x: 1.2, y: 3.6, w: 4.5, h: 0,
      line: { color: 'EA580C', width: 3 },
    });
    s1.addText(
      `比較基準：${currLabel} vs ${prevLabel}\n製表日期：${getTodayStr()}\n資料範疇：${isWh ? '倉庫 7 大作業項目棧板數與日均作業量' : '採購/廢液/調撥進貨 與 業務/調撥出貨 (MT・車次)'}\n（本簡報所有表格、圖表與文字皆為 PowerPoint 原生可編輯物件）`,
      {
        x: 1.2, y: 4.0, w: 10.5, h: 1.8,
        fontFace: FONT, fontSize: 15, color: SLATE, lineSpacingMultiple: 1.45,
      }
    );

    if (!isWh) {
      // ==================== PPT①：原料大車進出貨簡報 ====================
      const s2 = pptx.addSlide();
      addHeader(s2, `一、${currLabel} 原料大車進出貨績效總覽（vs ${prevLabel}）`, 2);

      const bulkMetricRows = [
        { label: '• 進貨工作量 (MT)', cat: 'inbound', field: 'mt', currTot: currAgg.inMt, prevTot: prevAgg.inMt },
        { label: '• 進貨運輸車次 (車次)', cat: 'inbound', field: 'trips', currTot: currAgg.inTrips, prevTot: prevAgg.inTrips },
        { label: '• 出貨工作量 (MT)', cat: 'outbound', field: 'mt', currTot: currAgg.outMt, prevTot: prevAgg.outMt },
        { label: '• 出貨運輸車次 (車次)', cat: 'outbound', field: 'trips', currTot: currAgg.outTrips, prevTot: prevAgg.outTrips },
      ];

      const headerRow = [
        { text: '項目 ＼ 期別', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
        ...showCols.map((c) => ({ text: c.label, options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } })),
        { text: `${currLabel} 累計`, options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
        { text: `${prevLabel} 基準`, options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
        { text: '差異增減 (%)', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
        { text: '綜合判定', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
      ];

      const bodyRows = bulkMetricRows.map((r, idx) => {
        const bg = idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF';
        const colCells = showCols.map((c) => {
          const sumV = c.months.reduce((acc, ym) => acc + (Number(scoped.get(`${ym}|${r.cat}`)?.[r.field]) || 0), 0);
          return { text: sumV ? fmtNum(sumV, 0) : '—', options: { fill: { color: bg }, color: DARK, align: 'center' } };
        });
        const diff = fmtDiff(r.currTot || null, r.prevTot || null, '', 0);
        const diffColor = diff.delta == null ? '64748B' : diff.delta >= 0 ? '047857' : 'DC2626';

        let judgeText = '基期未齊全';
        let judgeBg = bg;
        let judgeColor = '64748B';
        if (r.currTot && r.prevTot) {
          const pct = ((r.currTot - r.prevTot) / Math.abs(r.prevTot)) * 100;
          if (pct >= state.alertThreshold) { judgeText = '顯著成長 (高負荷)'; judgeBg = 'FEF3C7'; judgeColor = '92400E'; }
          else if (pct > 0) { judgeText = '穩健成長'; judgeBg = 'ECFDF5'; judgeColor = '047857'; }
          else if (pct <= -state.alertThreshold) { judgeText = '明顯縮減 (需關注)'; judgeBg = 'FEF2F2'; judgeColor = 'DC2626'; }
          else { judgeText = '微幅調整'; judgeBg = 'EFF6FF'; judgeColor = '1D4ED8'; }
        }
        return [
          { text: r.label, options: { fill: { color: bg }, color: DARK, bold: true, align: 'left' } },
          ...colCells,
          { text: r.currTot ? fmtNum(r.currTot, 0) : '—', options: { fill: { color: 'EFF6FF' }, color: NAVY, bold: true, align: 'center' } },
          { text: r.prevTot ? fmtNum(r.prevTot, 0) : '—', options: { fill: { color: bg }, color: SLATE, align: 'center' } },
          { text: diff.text, options: { fill: { color: bg }, color: diffColor, bold: true, align: 'center' } },
          { text: judgeText, options: { fill: { color: judgeBg }, color: judgeColor, bold: true, align: 'center' } },
        ];
      });

      s2.addTable([headerRow, ...bodyRows], {
        x: 0.45, y: 1.15, w: 12.43,
        fontFace: FONT, fontSize: 12, rowH: 0.58, valign: 'middle',
        border: { pt: 0.75, color: 'E2E8F0' },
      });

      const inAvgPerTrip = currAgg.inTrips ? (currAgg.inMt / currAgg.inTrips).toFixed(1) : '—';
      const outAvgPerTrip = currAgg.outTrips ? (currAgg.outMt / currAgg.outTrips).toFixed(1) : '—';
      const topInProd = Object.entries(currAgg.inProducts).sort((a, b) => b[1] - a[1])[0];
      const topOutCust = Object.entries(currAgg.outPartners).sort((a, b) => b[1] - a[1])[0];

      addCallouts(s2, [
        {
          title: '✔ 進貨量能與車次摘要',
          fill: 'F8FBFF', border: '3B82F6', titleColor: '1D4ED8',
          bullets: [
            `本期進貨 ${fmtNum(currAgg.inMt, 0)} MT，${fmtDiff(currAgg.inMt, prevAgg.inMt, ' MT').text}。`,
            `累計進廠 ${fmtNum(currAgg.inTrips, 0)} 車次，平均單車載重 ${inAvgPerTrip} MT/車。`,
            topInProd ? `主力進貨品項：${topInProd[0]} (${fmtNum(topInProd[1], 0)} MT)。` : '各項原物料進貨穩定。',
          ],
        },
        {
          title: '🚀 出貨表現與運輸效率',
          fill: 'FFFBEB', border: 'F59E0B', titleColor: 'B45309',
          bullets: [
            `本期出貨 ${fmtNum(currAgg.outMt, 0)} MT，${fmtDiff(currAgg.outMt, prevAgg.outMt, ' MT').text}。`,
            `累計出貨 ${fmtNum(currAgg.outTrips, 0)} 車次，平均單車載重 ${outAvgPerTrip} MT/車。`,
            topOutCust ? `主力出貨客戶：${topOutCust[0].slice(0, 14)} (${fmtNum(topOutCust[1], 0)} MT)。` : '業務與調撥出貨維持水準。',
          ],
        },
        {
          title: '🎯 整體運輸與專案進度',
          fill: 'F0FDF4', border: '22C55E', titleColor: '15803D',
          bullets: [
            `大車進出廠總計 ${fmtNum(currAgg.inTrips + currAgg.outTrips, 0)} 車次，總吞吐量 ${fmtNum(currAgg.inMt + currAgg.outMt, 0)} MT。`,
            `日常管理已建檔 ${state.management.length} 筆（品質・工安・稽核）。`,
            `重點專案：進行中 ${state.projects.filter((p) => p.status === '進行中').length} 項、已完成 ${state.projects.filter((p) => p.status === '已完成').length} 項。`,
          ],
        },
      ]);

      // Slide 3: 重量 (MT) 原生圖表
      const s3 = pptx.addSlide();
      addHeader(s3, `二、${currLabel} 進貨與出貨重量對照圖表 (MT)`, 3);
      const chartLabels = currMonths.map((ym) => `${Number(ym.slice(5))}月`);
      const getVals = (months, cat, field) => months.map((ym) => Number(scoped.get(`${ym}|${cat}`)?.[field] || 0));

      s3.addText('進貨工作量對照 (MT)', { x: 0.45, y: 1.05, w: 6.0, h: 0.35, fontFace: FONT, fontSize: 14, bold: true, color: NAVY });
      s3.addChart(
        pptx.ChartType.bar,
        [
          { name: `${prevLabel} (MT)`, labels: chartLabels, values: getVals(prevMonths, 'inbound', 'mt') },
          { name: `${currLabel} (MT)`, labels: chartLabels, values: getVals(currMonths, 'inbound', 'mt') },
        ],
        {
          x: 0.45, y: 1.45, w: 6.0, h: 4.2, barDir: 'col', barGrouping: 'clustered',
          chartColors: ['94A3B8', '0284C7'], showLegend: true, legendPos: 't', showValue: true,
          dataLabelFontSize: 9, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
        }
      );

      s3.addText('出貨工作量對照 (MT)', { x: 6.85, y: 1.05, w: 6.0, h: 0.35, fontFace: FONT, fontSize: 14, bold: true, color: '047857' });
      s3.addChart(
        pptx.ChartType.bar,
        [
          { name: `${prevLabel} (MT)`, labels: chartLabels, values: getVals(prevMonths, 'outbound', 'mt') },
          { name: `${currLabel} (MT)`, labels: chartLabels, values: getVals(currMonths, 'outbound', 'mt') },
        ],
        {
          x: 6.85, y: 1.45, w: 6.0, h: 4.2, barDir: 'col', barGrouping: 'clustered',
          chartColors: ['94A3B8', '10B981'], showLegend: true, legendPos: 't', showValue: true,
          dataLabelFontSize: 9, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
        }
      );

      s3.addShape(pptx.ShapeType.roundRect, {
        x: 0.45, y: 5.85, w: 12.43, h: 1.05, rectRadius: 0.1,
        fill: { color: 'F8FAFC' }, line: { color: 'CBD5E1', width: 1 },
      });
      s3.addText(
        `• 進貨重量：${currLabel} 進貨 ${fmtNum(currAgg.inMt, 0)} MT（${fmtDiff(currAgg.inMt, prevAgg.inMt, ' MT').text}）。\n` +
        `• 出貨重量：${currLabel} 出貨 ${fmtNum(currAgg.outMt, 0)} MT（${fmtDiff(currAgg.outMt, prevAgg.outMt, ' MT').text}）。`,
        { x: 0.65, y: 5.95, w: 12.0, h: 0.85, fontFace: FONT, fontSize: 12, color: DARK, lineSpacingMultiple: 1.4, valign: 'middle' }
      );

      // Slide 4: 車次 (Trips) 原生圖表
      const s4 = pptx.addSlide();
      addHeader(s4, `三、${currLabel} 進貨與出貨運輸車次對照圖表 (車次)`, 4);

      s4.addText('進貨大車車次對照 (車次)', { x: 0.45, y: 1.05, w: 6.0, h: 0.35, fontFace: FONT, fontSize: 14, bold: true, color: NAVY });
      s4.addChart(
        pptx.ChartType.bar,
        [
          { name: `${prevLabel} (車次)`, labels: chartLabels, values: getVals(prevMonths, 'inbound', 'trips') },
          { name: `${currLabel} (車次)`, labels: chartLabels, values: getVals(currMonths, 'inbound', 'trips') },
        ],
        {
          x: 0.45, y: 1.45, w: 6.0, h: 4.2, barDir: 'col', barGrouping: 'clustered',
          chartColors: ['94A3B8', '0EA5E9'], showLegend: true, legendPos: 't', showValue: true,
          dataLabelFontSize: 9, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
        }
      );

      s4.addText('出貨大車車次對照 (車次)', { x: 6.85, y: 1.05, w: 6.0, h: 0.35, fontFace: FONT, fontSize: 14, bold: true, color: 'D97706' });
      s4.addChart(
        pptx.ChartType.bar,
        [
          { name: `${prevLabel} (車次)`, labels: chartLabels, values: getVals(prevMonths, 'outbound', 'trips') },
          { name: `${currLabel} (車次)`, labels: chartLabels, values: getVals(currMonths, 'outbound', 'trips') },
        ],
        {
          x: 6.85, y: 1.45, w: 6.0, h: 4.2, barDir: 'col', barGrouping: 'clustered',
          chartColors: ['94A3B8', 'F59E0B'], showLegend: true, legendPos: 't', showValue: true,
          dataLabelFontSize: 9, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
        }
      );

      s4.addShape(pptx.ShapeType.roundRect, {
        x: 0.45, y: 5.85, w: 12.43, h: 1.05, rectRadius: 0.1,
        fill: { color: 'F8FAFC' }, line: { color: 'CBD5E1', width: 1 },
      });
      s4.addText(
        `• 進貨車次：${currLabel} ${fmtNum(currAgg.inTrips, 0)} 車次（${fmtDiff(currAgg.inTrips, prevAgg.inTrips, ' 車次').text}），平均單車載重 ${inAvgPerTrip} MT/車。\n` +
        `• 出貨車次：${currLabel} ${fmtNum(currAgg.outTrips, 0)} 車次（${fmtDiff(currAgg.outTrips, prevAgg.outTrips, ' 車次').text}），平均單車載重 ${outAvgPerTrip} MT/車。`,
        { x: 0.65, y: 5.95, w: 12.0, h: 0.85, fontFace: FONT, fontSize: 12, color: DARK, lineSpacingMultiple: 1.4, valign: 'middle' }
      );

      // Slide 5: 日常管理
      const s5 = pptx.addSlide();
      addHeader(s5, `四、日常管理重點（品質・工安・客戶稽核）`, 5);
      const mgmtRows = [
        [
          { text: '期別', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
          { text: '日期', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
          { text: '類別', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
          { text: '管理與稽核事項說明', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
        ],
        ...state.management.slice(0, 10).map((m, idx) => {
          const bg = idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF';
          return [
            { text: m.period || '', options: { fill: { color: bg }, align: 'center', bold: true } },
            { text: m.date || '', options: { fill: { color: bg }, align: 'center' } },
            { text: m.type || '', options: { fill: { color: bg }, align: 'center', bold: true, color: m.type === '工安異常' ? 'DC2626' : '0284C7' } },
            { text: m.content || '', options: { fill: { color: bg }, align: 'left' } },
          ];
        }),
      ];
      s5.addTable(mgmtRows, {
        x: 0.45, y: 1.15, w: 12.43, colW: [1.5, 1.6, 1.6, 7.73],
        fontFace: FONT, fontSize: 11.5, rowH: 0.5, valign: 'middle',
        border: { pt: 0.75, color: 'E2E8F0' },
      });

      // Slide 6+: 重要工作進度 (分年度篩選，避免跨年舊已完成塞滿新年度簡報)
      const reportProjects = getProjectsForReportYear(year, false);
      const perPage = 7;
      for (let start = 0; start < reportProjects.length; start += perPage) {
        const pageIdx = 6 + Math.floor(start / perPage);
        const sp = pptx.addSlide();
        addHeader(sp, `五、${year}年度 重要工作進度追蹤（${start + 1}~${Math.min(start + perPage, reportProjects.length)}）`, pageIdx);
        const chunk = reportProjects.slice(start, start + perPage);
        const pRows = [
          [
            { text: '項次', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
            { text: '主題', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
            { text: '說明', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
            { text: '成效', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
            { text: '預估時間', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
            { text: '狀態', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
          ],
          ...chunk.map((p, idx) => {
            const bg = idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF';
            const stBg = p.status === '已完成' ? 'ECFDF5' : p.status === '暫緩' ? 'FEF2F2' : 'EFF6FF';
            const stCol = p.status === '已完成' ? '047857' : p.status === '暫緩' ? 'DC2626' : '1D4ED8';
            return [
              { text: String(start + idx + 1), options: { fill: { color: bg }, align: 'center', bold: true } },
              { text: p.title || '', options: { fill: { color: bg }, align: 'left', bold: true } },
              { text: p.desc || '', options: { fill: { color: bg }, align: 'left' } },
              { text: p.effect || '', options: { fill: { color: bg }, align: 'left' } },
              { text: p.eta || '', options: { fill: { color: bg }, align: 'center' } },
              { text: p.status || '', options: { fill: { color: stBg }, color: stCol, align: 'center', bold: true } },
            ];
          }),
        ];
        sp.addTable(pRows, {
          x: 0.45, y: 1.12, w: 12.43, colW: [0.65, 2.5, 4.0, 2.6, 1.38, 1.3],
          fontFace: FONT, fontSize: 10.5, rowH: 0.68, valign: 'middle',
          border: { pt: 0.75, color: 'E2E8F0' },
        });
      }
    } else {
      // ==================== PPT②：倉庫棧板作業簡報 ====================
      const s2 = pptx.addSlide();
      addHeader(s2, `一、${currLabel} 倉庫作業項目明細統計（vs ${prevLabel}）`, 2);

      const whHeader = [
        { text: '作業項目 (棧板數) ＼ 月份', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
        ...showCols.map((c) => ({ text: c.label, options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } })),
        { text: '區間合計', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
        { text: '佔比 / 備註', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
      ];

      const whRows = WH_ITEMS.map((item, idx) => {
        const bg = idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF';
        let tot = 0;
        const cells = showCols.map((c) => {
          const v = c.months.reduce((a, ym) => a + (Number(scoped.get(`${ym}|warehouse`)?.breakdown?.[item]) || 0), 0);
          tot += v;
          return { text: v > 0 ? fmtNum(v, 0) : '—', options: { fill: { color: bg }, color: DARK, align: 'center' } };
        });
        const share = currAgg.whPallets > 0 && tot > 0 ? `${((tot / currAgg.whPallets) * 100).toFixed(1)}%` : '—';
        return [
          { text: item, options: { fill: { color: bg }, color: DARK, bold: true, align: 'left' } },
          ...cells,
          { text: tot > 0 ? fmtNum(tot, 0) : '—', options: { fill: { color: 'EFF6FF' }, color: NAVY, bold: true, align: 'center' } },
          { text: share, options: { fill: { color: bg }, color: SLATE, align: 'center' } },
        ];
      });

      const whPrevRow = [
        { text: `${prevLabel} (棧板數)`, options: { fill: { color: 'ECFDF5' }, color: '047857', bold: true, align: 'left' } },
        ...prevShowCols.map((c) => {
          const v = c.months.reduce((a, ym) => a + (Number(scoped.get(`${ym}|warehouse`)?.pallets) || 0), 0);
          return { text: v > 0 ? fmtNum(v, 0) : '—', options: { fill: { color: 'ECFDF5' }, color: '047857', bold: true, align: 'center' } };
        }),
        { text: prevAgg.whCount ? fmtNum(prevAgg.whPallets, 0) : '—', options: { fill: { color: 'ECFDF5' }, color: '047857', bold: true, align: 'center' } },
        { text: '對照基期', options: { fill: { color: 'ECFDF5' }, color: '047857', align: 'center' } },
      ];

      const whDiff = fmtDiff(currAgg.whCount ? currAgg.whPallets : null, prevAgg.whCount ? prevAgg.whPallets : null, ' 板', 0);
      const whCurrRow = [
        { text: `${currLabel} (棧板數)`, options: { fill: { color: 'EFF6FF' }, color: '1D4ED8', bold: true, align: 'left' } },
        ...showCols.map((c) => {
          const v = c.months.reduce((a, ym) => a + (Number(scoped.get(`${ym}|warehouse`)?.pallets) || 0), 0);
          return { text: v > 0 ? fmtNum(v, 0) : '—', options: { fill: { color: 'EFF6FF' }, color: '1D4ED8', bold: true, align: 'center' } };
        }),
        { text: currAgg.whCount ? fmtNum(currAgg.whPallets, 0) : '—', options: { fill: { color: 'DBEAFE' }, color: NAVY, bold: true, align: 'center' } },
        { text: whDiff.text, options: { fill: { color: 'EFF6FF' }, color: whDiff.delta >= 0 ? '047857' : 'DC2626', bold: true, align: 'center' } },
      ];

      const avgDaily = currAgg.whDailyAvgList.length
        ? Math.round(currAgg.whDailyAvgList.reduce((a, b) => a + b, 0) / currAgg.whDailyAvgList.length)
        : null;
      const whDailyRow = [
        { text: '平均每工作日作業棧板數', options: { fill: { color: 'FEF3C7' }, color: '92400E', bold: true, align: 'left' } },
        ...showCols.map((c) => {
          const ds = c.months
            .map((ym) => scoped.get(`${ym}|warehouse`)?.breakdown?.['平均工作日棧板數'])
            .filter((x) => x != null && Number(x) > 0)
            .map(Number);
          const avg = ds.length ? Math.round(ds.reduce((a, b) => a + b, 0) / ds.length) : 0;
          return { text: avg > 0 ? fmtNum(avg, 0) : '—', options: { fill: { color: 'FEF3C7' }, color: '92400E', bold: true, align: 'center' } };
        }),
        { text: avgDaily != null ? fmtNum(avgDaily, 0) : '—', options: { fill: { color: 'FEF3C7' }, color: '92400E', bold: true, align: 'center' } },
        { text: '日均板數', options: { fill: { color: 'FEF3C7' }, color: '92400E', align: 'center' } },
      ];

      s2.addTable([whHeader, ...whRows, whPrevRow, whCurrRow, whDailyRow], {
        x: 0.45, y: 1.02, w: 12.43,
        fontFace: FONT, fontSize: 10.5, rowH: 0.34, valign: 'middle',
        border: { pt: 0.75, color: 'E2E8F0' },
      });

      const pkgSum = (currAgg.whBreakdown['客供包材進貨'] || 0) + (currAgg.whBreakdown['自用包材進貨'] || 0);
      const top3Pct =
        currAgg.whPallets > 0
          ? (((pkgSum + (currAgg.whBreakdown['成品入庫'] || 0) + (currAgg.whBreakdown['出貨'] || 0)) / currAgg.whPallets) * 100).toFixed(1)
          : null;

      addCallouts(
        s2,
        [
          {
            title: '✔ 作業總量與基期差異',
            fill: 'F8FBFF', border: '3B82F6', titleColor: '1D4ED8',
            bullets: [
              `本期倉庫作業總量 ${fmtNum(currAgg.whPallets, 0)} 板。`,
              `較 ${prevLabel}（${fmtNum(prevAgg.whPallets, 0)} 板）：${whDiff.text}。`,
              `平均每工作日作業 ${avgDaily != null ? fmtNum(avgDaily, 0) + ' 板/日' : '—'}。`,
            ],
          },
          {
            title: '📦 主力作業集中度',
            fill: 'FFFBEB', border: 'F59E0B', titleColor: 'B45309',
            bullets: [
              `包材進貨（客供+自用）：${fmtNum(pkgSum, 0)} 板。`,
              `成品入庫：${fmtNum(currAgg.whBreakdown['成品入庫'], 0)} 板 ｜ 出貨：${fmtNum(currAgg.whBreakdown['出貨'], 0)} 板。`,
              `三大作業佔倉庫總負荷 ${top3Pct ? top3Pct + '%' : '—'}。`,
            ],
          },
          {
            title: '🎯 調撥與儲位管理建議',
            fill: 'F0FDF4', border: '22C55E', titleColor: '15803D',
            bullets: [
              `調撥作業 ${fmtNum(currAgg.whBreakdown['調撥'], 0)} 板，換標/理貨 ${fmtNum(currAgg.whBreakdown['換標或理貨作業'], 0)} 板。`,
              '工作量主要集中在包材進貨、成品入庫與出貨三項作業。',
              '建議配合包材業務成長動態評估儲位餘量。',
            ],
          },
        ],
        5.12,
        1.85
      );

      // Slide 3: 倉庫原生可編輯雙圖表
      const s3 = pptx.addSlide();
      addHeader(s3, `二、${currLabel} 倉庫作業趨勢與 7 項作業佔比分析`, 3);

      const chartLabels = currMonths.map((ym) => `${Number(ym.slice(5))}月`);
      const getWhSeries = (months) => months.map((ym) => Number(scoped.get(`${ym}|warehouse`)?.pallets || 0));

      s3.addText(`總作業棧板數同期對照 (${currLabel} vs ${prevLabel})`, {
        x: 0.45, y: 1.05, w: 6.0, h: 0.35, fontFace: FONT, fontSize: 13.5, bold: true, color: NAVY,
      });
      s3.addChart(
        pptx.ChartType.bar,
        [
          { name: `${prevLabel} (板)`, labels: chartLabels, values: getWhSeries(prevMonths) },
          { name: `${currLabel} (板)`, labels: chartLabels, values: getWhSeries(currMonths) },
        ],
        {
          x: 0.45, y: 1.45, w: 6.0, h: 4.15, barDir: 'col', barGrouping: 'clustered',
          chartColors: ['94A3B8', 'F59E0B'], showLegend: true, legendPos: 't', showValue: true,
          dataLabelFontSize: 9, catAxisLabelFontSize: 10, valAxisLabelFontSize: 10,
        }
      );

      s3.addText(`${currLabel} 7 大作業項目棧板分佈`, {
        x: 6.85, y: 1.05, w: 6.0, h: 0.35, fontFace: FONT, fontSize: 13.5, bold: true, color: 'B45309',
      });
      s3.addChart(
        pptx.ChartType.bar,
        [{ name: '作業棧板數', labels: WH_ITEMS, values: WH_ITEMS.map((k) => Number(currAgg.whBreakdown[k] || 0)) }],
        {
          x: 6.85, y: 1.45, w: 6.0, h: 4.15, barDir: 'bar',
          chartColors: ['0284C7'], showLegend: false, showValue: true,
          dataLabelFontSize: 9, catAxisLabelFontSize: 9.5, valAxisLabelFontSize: 10,
        }
      );

      s3.addShape(pptx.ShapeType.roundRect, {
        x: 0.45, y: 5.82, w: 12.43, h: 1.05, rectRadius: 0.1,
        fill: { color: 'FFFBEB' }, line: { color: 'F59E0B', width: 1.2 },
      });
      const whExplain =
        currAgg.whCount && prevAgg.whCount
          ? `說明：${currLabel}作業量 ${fmtNum(currAgg.whPallets, 0)} 板，較${prevLabel}作業量 ${fmtNum(prevAgg.whPallets, 0)} 板${currAgg.whPallets - prevAgg.whPallets >= 0 ? '增加' : '減少'} ${fmtNum(Math.abs(currAgg.whPallets - prevAgg.whPallets), 0)} 板 (${currAgg.whPallets - prevAgg.whPallets >= 0 ? '+' : ''}${(((currAgg.whPallets - prevAgg.whPallets) / Math.abs(prevAgg.whPallets)) * 100).toFixed(2)}%)。`
          : `說明：${currLabel}作業量 ${fmtNum(currAgg.whPallets, 0)} 板。`;
      s3.addText(`${whExplain}\n作業重點主要集中在包材進貨（${fmtNum(pkgSum, 0)} 板）、成品入庫（${fmtNum(currAgg.whBreakdown['成品入庫'], 0)} 板）與出貨（${fmtNum(currAgg.whBreakdown['出貨'], 0)} 板）。`, {
        x: 0.65, y: 5.92, w: 12.0, h: 0.85, fontFace: FONT, fontSize: 12, bold: true, color: DARK, lineSpacingMultiple: 1.4, valign: 'middle',
      });

      // Slide 4: 倉庫相關日常管理與重要專案摘要
      const s4 = pptx.addSlide();
      addHeader(s4, `三、${year}年度 倉庫相關日常管理與重要改善專案進度`, 4);
      const showProjs = getProjectsForReportYear(year, true).slice(0, 8);
      const wpRows = [
        [
          { text: '項次', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
          { text: '主題', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
          { text: '說明', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
          { text: '成效', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'left' } },
          { text: '預估時間', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
          { text: '狀態', options: { fill: { color: NAVY }, color: 'FFFFFF', bold: true, align: 'center' } },
        ],
        ...showProjs.map((p, idx) => {
          const bg = idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF';
          const stBg = p.status === '已完成' ? 'ECFDF5' : p.status === '暫緩' ? 'FEF2F2' : 'EFF6FF';
          const stCol = p.status === '已完成' ? '047857' : p.status === '暫緩' ? 'DC2626' : '1D4ED8';
          return [
            { text: String(idx + 1), options: { fill: { color: bg }, align: 'center', bold: true } },
            { text: p.title || '', options: { fill: { color: bg }, align: 'left', bold: true } },
            { text: p.desc || '', options: { fill: { color: bg }, align: 'left' } },
            { text: p.effect || '', options: { fill: { color: bg }, align: 'left' } },
            { text: p.eta || '', options: { fill: { color: bg }, align: 'center' } },
            { text: p.status || '', options: { fill: { color: stBg }, color: stCol, align: 'center', bold: true } },
          ];
        }),
      ];
      s4.addTable(wpRows, {
        x: 0.45, y: 1.12, w: 12.43, colW: [0.65, 2.5, 4.0, 2.6, 1.38, 1.3],
        fontFace: FONT, fontSize: 10.5, rowH: 0.65, valign: 'middle',
        border: { pt: 0.75, color: 'E2E8F0' },
      });
    }

    const outName = isWh
      ? `鴻勝資材部_${currLabel}_倉庫作業統計報表_${getTodayStr().replace(/\//g, '')}.pptx`
      : `鴻勝資材部_${currLabel}_原料進出貨報表_${getTodayStr().replace(/\//g, '')}.pptx`;
    await pptx.writeFile({ fileName: outName });
    showToast(`已下載可編輯 PowerPoint 簡報：${outName}`, 'success');
  };

  window.exportFullExcel = function () {
    const wb = XLSX.utils.book_new();
    const scoped = getScopedMetrics();
    const bulkRows = [];
    const whRows = [];
    const yms = Array.from(new Set(state.metrics.map((m) => m.ym))).sort();

    for (const ym of yms) {
      const i = scoped.get(`${ym}|inbound`);
      const o = scoped.get(`${ym}|outbound`);
      const w = scoped.get(`${ym}|warehouse`);
      if (i || o) {
        bulkRows.push({
          月份: ym,
          '進貨(MT)': i?.mt ?? '',
          進貨車次: i?.trips ?? '',
          '出貨(MT)': o?.mt ?? '',
          出貨車次: o?.trips ?? '',
          進貨口徑: i?.source ?? '',
          出貨口徑: o?.source ?? '',
        });
      }
      if (w) {
        whRows.push({
          月份: ym,
          總作業棧板數: w.pallets ?? '',
          原料進貨: w.breakdown?.['原料進貨'] ?? '',
          客供包材進貨: w.breakdown?.['客供包材進貨'] ?? '',
          自用包材進貨: w.breakdown?.['自用包材進貨'] ?? '',
          成品入庫: w.breakdown?.['成品入庫'] ?? '',
          調撥: w.breakdown?.['調撥'] ?? '',
          換標或理貨作業: w.breakdown?.['換標或理貨作業'] ?? '',
          出貨: w.breakdown?.['出貨'] ?? '',
          平均每工作日作業棧板數: w.breakdown?.['平均工作日棧板數'] ?? '',
          來源口徑: w.source ?? '',
        });
      }
    }
    const mapProjExcel = (list) =>
      list.map((p, idx) => ({
        項次: idx + 1,
        所屬年度: formatProjectYearGroupLabel(getProjectYearGroup(p)).replace(/^[^ ]+ /, ''),
        主題: p.title || '',
        說明: p.desc || '',
        成效: p.effect || '',
        預估時間: p.eta || '',
        狀態: p.status || '',
      }));
    const activeProjs = state.projects.filter((p) => p.status !== '已完成');
    const doneProjs = state.projects.filter((p) => p.status === '已完成');

    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(bulkRows), '1_原料大車進出貨');
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(whRows), '2_倉庫棧板7項明細');
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(state.management), '3_日常管理');
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(mapProjExcel(activeProjs)), '4_重要工作進度_追蹤中');
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(mapProjExcel(doneProjs)), '5_重要工作進度_已完成歸檔');
    XLSX.writeFile(wb, `鴻勝資材部_雙報表分析彙總_${getTodayStr().replace(/\//g, '')}.xlsx`);
    showToast('雙報表完整 Excel 已匯出！', 'success');
  };

  // ==================== 異常波動預警 ====================
  function renderAnomalyAlerts(scoped) {
    const threshold = state.alertThreshold;
    document.getElementById('alertThresholdInfo').textContent = `目前警戒門檻：±${threshold}%（可於總覽表上方滑桿調整）`;

    const yms = Array.from(new Set(Array.from(scoped.keys()).map((k) => k.split('|')[0]))).sort().reverse();
    const alerts = [];
    const checks = [
      { cat: 'inbound', field: 'mt', label: '進貨重量 (MT)' },
      { cat: 'inbound', field: 'trips', label: '進貨車次' },
      { cat: 'outbound', field: 'mt', label: '出貨重量 (MT)' },
      { cat: 'outbound', field: 'trips', label: '出貨車次' },
      { cat: 'warehouse', field: 'pallets', label: '倉庫棧板數' },
    ];

    for (const ym of yms) {
      const y = Number(ym.slice(0, 4));
      const m = Number(ym.slice(5, 7));
      const yoyYm = `${y - 1}-${String(m).padStart(2, '0')}`;
      const momYm = m === 1 ? `${y - 1}-12` : `${y}-${String(m - 1).padStart(2, '0')}`;

      for (const ck of checks) {
        const curr = scoped.get(`${ym}|${ck.cat}`)?.[ck.field];
        if (curr == null) continue;
        for (const [mode, refYm] of [['YoY 去年同期', yoyYm], ['MoM 上月比', momYm]]) {
          const prev = scoped.get(`${refYm}|${ck.cat}`)?.[ck.field];
          if (!prev) continue;
          const pct = ((curr - prev) / Math.abs(prev)) * 100;
          if (Math.abs(pct) >= threshold) {
            alerts.push({ ym, refYm, mode, label: ck.label, curr, prev, pct });
          }
        }
      }
    }

    const badge = document.getElementById('alertCountBadge');
    if (alerts.length) {
      badge.textContent = alerts.length;
      badge.classList.remove('hidden');
    } else {
      badge.classList.add('hidden');
    }

    const list = document.getElementById('alertList');
    if (!alerts.length) {
      list.innerHTML = `<div class="p-6 text-center text-emerald-300 bg-emerald-500/10 rounded-xl border border-emerald-500/30">✅ 目前所有月份波動皆在 ±${threshold}% 正常範圍內！</div>`;
      return;
    }

    list.innerHTML = alerts
      .slice(0, 40)
      .map((a) => {
        const up = a.pct > 0;
        return `<div class="p-4 rounded-xl bg-slate-900/80 border ${up ? 'border-rose-500/40' : 'border-amber-500/40'} flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="flex items-center gap-2">
              <span class="px-2 py-0.5 rounded text-xs font-bold ${up ? 'bg-rose-600 text-white' : 'bg-amber-600 text-white'}">${up ? '📈 暴增' : '📉 驟降'} ${a.pct > 0 ? '+' : ''}${a.pct.toFixed(1)}%</span>
              <span class="font-bold text-white">${a.ym}｜${a.label}</span>
              <span class="text-xs text-slate-400">(${a.mode} vs ${a.refYm})</span>
            </div>
            <div class="text-xs text-slate-300 mt-1">本期：<strong>${fmtNum(a.curr, 1)}</strong> ／ 基準期：<strong>${fmtNum(a.prev, 1)}</strong>（差額 ${a.curr - a.prev > 0 ? '+' : ''}${fmtNum(a.curr - a.prev, 1)}）</div>
          </div>
          <button onclick="jumpToMonth('${a.ym}')" class="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-sky-600 text-slate-200 hover:text-white transition">
            🔍 查看該月
          </button>
        </div>`;
      })
      .join('');
  }

  window.jumpToMonth = function (ym) {
    document.getElementById('selPeriodType').value = 'month';
    populateSubPeriodSelector();
    document.getElementById('selYear').value = ym.slice(0, 4);
    document.getElementById('selSubPeriod').value = String(Number(ym.slice(5, 7)));
    switchTab('dashboard');
    renderAll();
  };

  // ==================== 檔案上傳解析引擎 (Excel + BI PDF + Gemini OCR) ====================
  function normalizeMatchKey(str) {
    return String(str || '')
      .replace(/[，。、,.：:；;!！?？\s\-_()（）【】\[\]「」"'·•]/g, '')
      .toLowerCase();
  }

  function sameMetricNum(a, b) {
    const emptyA = a === null || a === undefined || a === '';
    const emptyB = b === null || b === undefined || b === '';
    if (emptyA && emptyB) return true;
    if (emptyA || emptyB) return false;
    return Math.abs(Number(a) - Number(b)) < 0.01;
  }

  async function handleFiles(fileList) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    const statusEl = document.getElementById('parseStatus');
    statusEl.classList.remove('hidden');
    statusEl.innerHTML = `<div class="text-sky-300 font-bold">⏳ 正在解析 ${files.length} 個檔案，請稍候...</div>`;

    const allParsed = [];
    const logs = [];

    for (const file of files) {
      const ext = file.name.split('.').pop().toLowerCase();
      const seenFilename = state.metrics.some((m) => getRecordFilename(m) === file.name);
      try {
        if (['xlsx', 'xls', 'csv'].includes(ext)) {
          const recs = await parseExcelFile(file);
          allParsed.push(...recs);
          logs.push(`✅ <strong>${escHtml(file.name)}</strong>：成功解析 ${recs.length} 個月份彙總`);
        } else if (ext === 'pdf') {
          const recs = await parsePdfFile(file);
          allParsed.push(...recs);
          logs.push(`✅ <strong>${escHtml(file.name)}</strong>：成功解析 ${recs.length} 筆月度數據`);
        } else {
          logs.push(`⚠️ <strong>${escHtml(file.name)}</strong>：不支援的副檔名 (.${escHtml(ext)})`);
          continue;
        }
        if (seenFilename) {
          logs.push(`<div class="pl-5 text-amber-300">⚠️ 注意：檔名「${escHtml(file.name)}」先前已上傳過，下方預覽已標註新舊差異</div>`);
        }
      } catch (err) {
        logs.push(`❌ <strong>${escHtml(file.name)}</strong>：解析失敗 — ${escHtml(err.message)}`);
      }
    }

    statusEl.innerHTML = logs.map((l) => `<div class="py-0.5">${l}</div>`).join('');
    if (allParsed.length) {
      state.parsedPreview = mergePreviewRecords([...state.parsedPreview, ...allParsed]);
      renderPreviewTable();
    }
  }

  function mergePreviewRecords(list) {
    const map = new Map();
    for (const r of list) {
      const key = `${r.ym}|${r.category}`;
      map.set(key, r);
    }
    return Array.from(map.values()).sort((a, b) => a.ym.localeCompare(b.ym));
  }

  async function parseExcelFile(file) {
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(buf, { type: 'array' });
    const tripRule = document.getElementById('selTripRule').value;
    const fname = file.name;

    // Pick best sheet
    let sheetName = wb.SheetNames[0];
    if (wb.SheetNames.includes('日期排序-含22Y')) sheetName = '日期排序-含22Y';
    else if (wb.SheetNames.includes('進貨明細日報表')) sheetName = '進貨明細日報表';
    else if (wb.SheetNames.includes('進貨一覽表')) sheetName = '進貨一覽表';

    const rows = XLSX.utils.sheet_to_json(wb.Sheets[sheetName], { header: 1, raw: true, defval: '' });

    // Find header row in first 12 rows
    let headerIdx = -1;
    let headers = [];
    for (let i = 0; i < Math.min(12, rows.length); i++) {
      const r = rows[i].map((c) => String(c || '').trim());
      if (
        r.some((c) => ['單據日期(C)', '單據日期', '出貨日期', '日期(C)', '日期'].includes(c)) &&
        r.some((c) => ['淨重', '鴻勝淨重', '出廠重量', '參考數量'].includes(c))
      ) {
        headerIdx = i;
        headers = r;
        break;
      }
    }

    if (headerIdx !== -1) {
      // Raw detail Excel!
      const col = (names) => headers.findIndex((h) => names.includes(h));
      const iDate = col(['單據日期(C)', '單據日期', '出貨日期', '日期(C)', '日期']);
      const iNet = col(['淨重', '鴻勝淨重', '參考數量']);
      const iWeigh = col(['地磅單', '進貨地磅單號', '地磅單號']);
      const iPlate = col(['車牌號碼', '車號']);
      const iProd = col(['品名']);
      const iPartner = col(['交易對象全名', '交易對象簡稱', '供應商', '廠商簡稱', '客戶']);

      const isOutbound =
        fname.includes('出貨') || headers.includes('出貨日期') || sheetName.includes('22Y');
      const category = isOutbound ? 'outbound' : 'inbound';

      const buckets = {};
      for (let i = headerIdx + 1; i < rows.length; i++) {
        const row = rows[i];
        let dt = String(row[iDate] || '').replace(/[-/.\s]/g, '');
        if (dt.length < 6 || !/^\d{6,8}$/.test(dt)) continue;
        const ym = `${dt.slice(0, 4)}-${dt.slice(4, 6)}`;
        const netKg = Number(row[iNet] || 0);
        if (Number.isNaN(netKg)) continue;

        if (!buckets[ym]) {
          buckets[ym] = {
            mt: 0, weigh: new Set(), plateDay: new Set(), rows: 0,
            products: {}, partners: {}, prefixes: {},
          };
        }
        const b = buckets[ym];
        b.mt += netKg / 1000;
        b.rows++;
        const wbNo = iWeigh >= 0 ? String(row[iWeigh] || '').trim() : '';
        if (wbNo) {
          b.weigh.add(wbNo);
          const pfx = wbNo.split('-')[0];
          if (!b.prefixes[pfx]) b.prefixes[pfx] = { mt: 0, weigh: new Set() };
          b.prefixes[pfx].mt += netKg / 1000;
          b.prefixes[pfx].weigh.add(wbNo);
        }
        const plate = iPlate >= 0 ? String(row[iPlate] || '').trim() : '';
        if (plate) b.plateDay.add(`${dt}|${plate}`);

        const prod = iProd >= 0 ? String(row[iProd] || '').trim() : '';
        if (prod) b.products[prod] = (b.products[prod] || 0) + netKg / 1000;

        const partner = iPartner >= 0 ? String(row[iPartner] || '').trim() : '';
        if (partner) b.partners[partner] = (b.partners[partner] || 0) + netKg / 1000;
      }

      return Object.entries(buckets).map(([ym, b]) => ({
        ym,
        category,
        mt: Math.round(b.mt * 100) / 100,
        trips: tripRule === 'plate_day' ? b.plateDay.size : b.weigh.size || b.rows,
        pallets: null,
        rows: b.rows,
        filename: fname,
        breakdown: {
          top_products: Object.entries(b.products).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => [k, Math.round(v * 10) / 10]),
          top_partners: Object.entries(b.partners).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => [k, Math.round(v * 10) / 10]),
          prefixes: Object.fromEntries(Object.entries(b.prefixes).map(([k, v]) => [k, { mt: Math.round(v.mt * 100) / 100, trips: v.weigh.size }])),
        },
      }));
    }

    // Fallback: Check if it's a horizontal monthly summary / warehouse pallet table (1月, 2月, ...)
    const parsedSummary = parseHorizontalSummarySheet(rows, fname);
    if (parsedSummary.length) return parsedSummary;

    throw new Error('找不到標準表頭（單據日期/出貨日期 + 淨重）或月度統計表格式');
  }

  function parseHorizontalSummarySheet(rows, fname) {
    const recs = [];
    let monthCols = {};
    let pendingBd = {};
    let pendingDaily = {};
    let blockWhByYear = {};

    const flushWarehouseBlock = () => {
      const yrs = Object.keys(blockWhByYear);
      if (!yrs.length) return;
      const maxYr = String(Math.max(...yrs.map(Number)));
      (blockWhByYear[maxYr] || []).forEach((rec) => {
        const mon = Number(rec.ym.slice(5));
        const bd = { ...(pendingBd[mon] || {}) };
        if (pendingDaily[mon] != null) bd['平均工作日棧板數'] = pendingDaily[mon];
        rec.breakdown = bd;
      });
      pendingBd = {};
      pendingDaily = {};
      blockWhByYear = {};
    };

    for (let r = 0; r < rows.length; r++) {
      const row = rows[r].map((c) => String(c || '').trim());
      const mHits = {};
      row.forEach((cell, idx) => {
        const m = cell.match(/^(\d{1,2})月$/);
        if (m) mHits[idx] = Number(m[1]);
      });
      if (Object.keys(mHits).length >= 3) {
        flushWarehouseBlock();
        monthCols = mHits;
        continue;
      }
      if (!Object.keys(monthCols).length) continue;

      const firstCell = row[0] || row[1] || '';
      const matchedWhItem = WH_ITEMS.find((it) => firstCell === it || firstCell.includes(it));
      if (matchedWhItem && !/(20\d{2})/.test(firstCell)) {
        for (const [colIdx, mon] of Object.entries(monthCols)) {
          const val = Number(String(rows[r][colIdx] || '').replace(/,/g, ''));
          if (!pendingBd[mon]) pendingBd[mon] = {};
          pendingBd[mon][matchedWhItem] = Number.isNaN(val) ? 0 : val;
        }
        continue;
      }

      if (/平均.*工作日/.test(firstCell)) {
        for (const [colIdx, mon] of Object.entries(monthCols)) {
          const val = Number(String(rows[r][colIdx] || '').replace(/,/g, ''));
          if (val && !Number.isNaN(val)) pendingDaily[mon] = val;
        }
        continue;
      }

      const yrMatch = firstCell.match(/(20\d{2})/);
      if (yrMatch) {
        const yr = yrMatch[1];
        const isWh = firstCell.includes('棧板') || fname.includes('倉庫') || fname.includes('板數') || Object.keys(pendingBd).length > 0;
        const isOut = fname.includes('出貨');
        const isTrips = fname.includes('車次');
        for (const [colIdx, mon] of Object.entries(monthCols)) {
          const val = Number(String(rows[r][colIdx] || '').replace(/,/g, ''));
          if (!val || Number.isNaN(val)) continue;
          const ym = `${yr}-${String(mon).padStart(2, '0')}`;
          const rec = {
            ym,
            category: isWh ? 'warehouse' : isOut ? 'outbound' : 'inbound',
            mt: !isWh && !isTrips ? val : null,
            trips: !isWh && isTrips ? val : null,
            pallets: isWh ? val : null,
            rows: 1,
            filename: fname,
            breakdown: {},
          };
          recs.push(rec);
          if (isWh) {
            if (!blockWhByYear[yr]) blockWhByYear[yr] = [];
            blockWhByYear[yr].push(rec);
          }
        }
      }
    }
    flushWarehouseBlock();
    return recs;
  }

  async function parsePdfFile(file) {
    if (!window.pdfjsLib) throw new Error('pdf.js 尚未載入');
    const forceOcr = document.getElementById('chkForceOcr').checked;
    const buf = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: buf }).promise;

    let fullText = '';
    if (!forceOcr) {
      for (let p = 1; p <= pdf.numPages; p++) {
        const page = await pdf.getPage(p);
        const content = await page.getTextContent();
        fullText += content.items.map((it) => it.str).join(' ') + '\n';
      }
    }

    // Try fast zero-cost text extraction first
    if (!forceOcr && fullText.trim().length > 80) {
      const textRecs = extractRecordsFromPdfText(fullText, file.name);
      if (textRecs.length > 0) return textRecs;
    }

    // Fallback to Gemini Vision OCR (renders up to first 4 pages)
    showToast(`偵測到掃描型或不規則 PDF，啟動 Gemini AI 視覺解析 (${file.name})...`, 'info');
    const images = [];
    const maxPages = Math.min(pdf.numPages, 4);
    for (let p = 1; p <= maxPages; p++) {
      const page = await pdf.getPage(p);
      const vp = page.getViewport({ scale: 1.6 });
      const canvas = document.createElement('canvas');
      canvas.width = vp.width;
      canvas.height = vp.height;
      await page.render({ canvasContext: canvas.getContext('2d'), viewport: vp }).promise;
      images.push(canvas.toDataURL('image/jpeg', 0.85).split(',')[1]);
    }

    return await callGeminiOcrWithFallback(images, file.name);
  }

  function extractRecordsFromPdfText(text, fname) {
    const isOut = fname.includes('出貨') || text.includes('出貨明細') || text.includes('ESXM201');
    const category = fname.includes('倉庫') || text.includes('棧板') ? 'warehouse' : isOut ? 'outbound' : 'inbound';

    // Match rows containing YYYYMMDD + ESXM weighbill + weight
    const buckets = {};
    const lines = text.split(/\n+/);
    const dateRegex = /(20\d{2})[-/]?(\d{2})[-/]?(\d{2})/g;
    const weighRegex = /ESXM\d{3}-\d{11}/g;

    for (const line of lines) {
      const dMatch = line.match(/(20\d{2})[-/]?(\d{2})[-/]?(\d{2})/);
      const wMatch = line.match(/ESXM\d{3}-\d{11}/);
      if (dMatch && wMatch) {
        const ym = `${dMatch[1]}-${dMatch[2]}`;
        // Find plausible net weight (kg, typically 100 ~ 50000)
        const nums = (line.match(/\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b/g) || [])
          .map((n) => Number(n.replace(/,/g, '')))
          .filter((n) => n >= 10 && n <= 60000 && !String(n).startsWith('202'));
        const netKg = nums.length ? nums[nums.length - 1] : 0;
        if (!buckets[ym]) buckets[ym] = { mt: 0, weigh: new Set(), rows: 0 };
        buckets[ym].mt += netKg / 1000;
        buckets[ym].weigh.add(wMatch[0]);
        buckets[ym].rows++;
      }
    }

    return Object.entries(buckets).map(([ym, b]) => ({
      ym,
      category,
      mt: Math.round(b.mt * 100) / 100,
      trips: b.weigh.size,
      pallets: null,
      rows: b.rows,
      filename: fname,
      breakdown: {},
    }));
  }

  async function callGeminiOcrWithFallback(base64Images, fname) {
    const prompt = `你是台灣化工資材部報表解析專家。請從這些 BI 報表 / 季報 PDF 圖片中擷取所有月度進出貨或倉庫棧板統計資料，只回傳純 JSON 陣列（不要 markdown 標記），格式如下：
[{"ym":"2026-01","category":"inbound|outbound|warehouse","mt":5622.5,"trips":308,"pallets":null,"rows":1}]
注意：重量單位必須換算為公噸(MT，若原表為公斤kg請除以1000)；category 僅限 inbound、outbound、warehouse。`;

    // 1. Prefer backend proxy /api/ocr if server online
    if (state.apiOnline) {
      const res = await fetch('/api/ocr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images: base64Images, prompt, filename: fname }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || `後端 OCR 失敗 (HTTP ${res.status})`);
      return (data.records || []).map((r) => ({ ...r, filename: fname, breakdown: r.breakdown || {} }));
    }

    // 2. Direct browser Gemini call with strict fallback chain
    const apiKey = localStorage.getItem(STORAGE_KEYS.GEMINI_KEY) || '';
    if (!apiKey) {
      throw new Error('掃描型 PDF 需要 Gemini API Key，請點右上角「⚙️ 設定 / AI OCR」填入後重試');
    }

    let lastError = '所有模型皆無法回應';
    for (const model of GEMINI_MODELS) {
      try {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(apiKey)}`;
        const parts = [{ text: prompt }, ...base64Images.map((b64) => ({ inline_data: { mime_type: 'image/jpeg', data: b64 } }))];
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contents: [{ parts }], generationConfig: { temperature: 0.1 } }),
        });
        if (!res.ok) {
          const errJson = await res.json().catch(() => ({}));
          lastError = `[${model}] HTTP ${res.status}: ${errJson.error?.message || res.statusText}`;
          continue;
        }
        const json = await res.json();
        const raw = json.candidates?.[0]?.content?.parts?.[0]?.text || '';
        const cleaned = raw.replace(/```json|```/g, '').trim();
        const arr = JSON.parse(cleaned);
        if (Array.isArray(arr) && arr.length) {
          showToast(`AI 視覺解析成功 (使用模型：${model})`, 'success');
          return arr.map((r) => ({ ...r, filename: fname, breakdown: r.breakdown || {} }));
        }
        lastError = `[${model}] 回傳空陣列`;
      } catch (e) {
        lastError = `[${model}] ${e.message}`;
      }
    }
    throw new Error(`Gemini Vision OCR 降級鏈耗盡：${lastError}`);
  }

  function analyzeMetricPreviewRow(r, targetSource) {
    const existing = state.metrics.find(
      (m) => m.ym === r.ym && m.category === r.category && m.source === targetSource
    );
    const otherSources = state.metrics
      .filter((m) => m.ym === r.ym && m.category === r.category && m.source !== targetSource)
      .map((m) => m.source);

    if (!existing) return { status: 'new', existing: null, otherSources };
    const isSame =
      sameMetricNum(r.mt, existing.mt) &&
      sameMetricNum(r.trips, existing.trips) &&
      sameMetricNum(r.pallets, existing.pallets);
    return { status: isSame ? 'same' : 'changed', existing, otherSources };
  }

  function renderPreviewTable() {
    const panel = document.getElementById('previewPanel');
    const tbody = document.getElementById('previewTableBody');
    const banner = document.getElementById('metricDupBanner');
    if (!state.parsedPreview.length) {
      panel.classList.add('hidden');
      if (banner) banner.classList.add('hidden');
      return;
    }
    panel.classList.remove('hidden');

    const targetSource = document.getElementById('selTargetSource')?.value || 'BI_EXCEL';
    const policy = document.getElementById('selMetricDupPolicy')?.value || 'skip_same';
    const catName = { inbound: '📦 進貨', outbound: '🚚 出貨', warehouse: '🏭 倉庫棧板' };

    let newCnt = 0;
    let changedCnt = 0;
    let sameCnt = 0;
    const dupFiles = new Set();

    const rowsHtml = state.parsedPreview
      .map((r, idx) => {
        const info = analyzeMetricPreviewRow(r, targetSource);
        if (info.status === 'new') newCnt++;
        else if (info.status === 'changed') changedCnt++;
        else sameCnt++;

        if (r.filename && state.metrics.some((m) => getRecordFilename(m) === r.filename)) {
          dupFiles.add(r.filename);
        }

        const willSkip =
          (policy === 'skip_same' && info.status === 'same') ||
          (policy === 'skip_all' && info.status !== 'new');

        const badge =
          info.status === 'new'
            ? '<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-[11px]">🟢 全新</span>'
            : info.status === 'changed'
            ? '<span class="px-2 py-0.5 rounded bg-amber-500/25 text-amber-300 font-bold text-[11px]">🟠 覆蓋變更</span>'
            : '<span class="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-200 font-bold text-[11px]">🟡 重複(相同)</span>';

        const otherNote = info.otherSources.length
          ? `<div class="text-[10px] text-slate-400 mt-0.5">他口徑已有: ${escHtml(info.otherSources.join(', '))}</div>`
          : '';
        const skipNote = willSkip ? '<div class="text-[10px] text-slate-400 mt-0.5">⏭️ 寫入時略過</div>' : '';

        const diffCell = (newVal, oldVal, dec) => {
          if (info.status === 'changed' && !sameMetricNum(newVal, oldVal)) {
            return `<span class="text-slate-500 line-through">${fmtNum(oldVal, dec)}</span> → <span class="text-amber-300 font-bold">${fmtNum(newVal, dec)}</span>`;
          }
          return fmtNum(newVal, dec);
        };

        return `<tr class="hover:bg-slate-800/40 ${willSkip ? 'opacity-45' : ''}">
          <td class="py-2 px-3">${badge}${otherNote}${skipNote}</td>
          <td class="py-2 px-3 font-bold text-white font-mono">${escHtml(r.ym)}</td>
          <td class="py-2 px-3">${catName[r.category] || escHtml(r.category)}</td>
          <td class="py-2 px-3 text-right font-mono">${diffCell(r.mt, info.existing?.mt, 2)}</td>
          <td class="py-2 px-3 text-right font-mono">${diffCell(r.trips, info.existing?.trips, 0)}</td>
          <td class="py-2 px-3 text-right font-mono">${diffCell(r.pallets, info.existing?.pallets, 0)}</td>
          <td class="py-2 px-3 text-right text-slate-400">${fmtNum(r.rows, 0)}</td>
          <td class="py-2 px-3 text-xs text-slate-400">${escHtml(r.filename || '')}</td>
          <td class="py-2 px-2 text-center"><button type="button" onclick="removeMetricPreviewItem(${idx})" class="text-slate-400 hover:text-rose-400">🗑️</button></td>
        </tr>`;
      })
      .join('');

    tbody.innerHTML = rowsHtml;

    if (banner) {
      if (changedCnt > 0 || sameCnt > 0 || dupFiles.size > 0) {
        const policyHint =
          policy === 'skip_same'
            ? '目前策略將寫入「全新 + 覆蓋變更」，並自動略過完全相同的月份。'
            : policy === 'overwrite_all'
            ? '目前策略將全部覆蓋寫入目標口徑。'
            : '目前策略僅寫入全新月份，所有已存在月份都會略過。';
        const lines = [
          `<div>⚠️ <strong>重複／覆蓋判讀（目標口徑：${escHtml(targetSource)}）</strong>：🟢 全新 <strong>${newCnt}</strong> 筆 ｜ 🟠 數值變更 <strong>${changedCnt}</strong> 筆 ｜ 🟡 完全重複 <strong>${sameCnt}</strong> 筆。${policyHint}</div>`,
        ];
        if (dupFiles.size > 0) {
          lines.push(`<div>📁 偵測到同名檔案先前已上傳：<strong>${escHtml(Array.from(dupFiles).join('、'))}</strong></div>`);
        }
        banner.innerHTML = lines.join('');
        banner.classList.remove('hidden');
      } else {
        banner.classList.add('hidden');
      }
    }
  }

  window.renderPreviewTable = renderPreviewTable;

  window.removeMetricPreviewItem = function (idx) {
    state.parsedPreview.splice(idx, 1);
    renderPreviewTable();
  };

  window.clearPreview = function () {
    state.parsedPreview = [];
    renderPreviewTable();
  };

  window.commitParsedRecords = async function () {
    if (!state.parsedPreview.length) return;
    const targetSource = document.getElementById('selTargetSource').value;
    const policy = document.getElementById('selMetricDupPolicy')?.value || 'skip_same';

    const toSave = [];
    let newWriteCnt = 0;
    let overwriteCnt = 0;
    let skippedCnt = 0;

    for (const r of state.parsedPreview) {
      const info = analyzeMetricPreviewRow(r, targetSource);
      const shouldSkip =
        (policy === 'skip_same' && info.status === 'same') ||
        (policy === 'skip_all' && info.status !== 'new');
      if (shouldSkip) {
        skippedCnt++;
        continue;
      }
      if (info.status === 'new') newWriteCnt++;
      else overwriteCnt++;

      toSave.push({
        ...r,
        source: targetSource,
        breakdown: { ...(r.breakdown || {}), _filename: r.filename || 'UPLOAD' },
      });
    }

    if (!toSave.length) {
      showToast('所有資料皆與資料庫重複，未執行寫入（如需覆蓋請切換上方策略）', 'warning');
      return;
    }

    if (overwriteCnt > 0) {
      const ok = confirm(
        `準備寫入目標口徑：${targetSource}\n\n🟢 全新寫入：${newWriteCnt} 筆\n🟠 覆蓋更新：${overwriteCnt} 筆\n⏭️ 略過重複：${skippedCnt} 筆\n\n確定執行嗎？`
      );
      if (!ok) return;
    }

    upsertLocalMetrics(toSave);
    await pushMetricsBatch(toSave, toSave[0]?.filename || 'UPLOAD');
    state.parsedPreview = [];
    renderPreviewTable();
    populateYearSelector();
    renderAll();
    showToast(`寫入完成：新增 ${newWriteCnt} 筆、覆蓋 ${overwriteCnt} 筆（略過重複 ${skippedCnt} 筆）`, 'success');
  };

  function upsertLocalMetrics(records) {
    for (const r of records) {
      const idx = state.metrics.findIndex(
        (m) => m.ym === r.ym && m.category === r.category && m.source === r.source
      );
      if (idx >= 0) state.metrics[idx] = { ...state.metrics[idx], ...r };
      else state.metrics.push(r);
    }
    saveLocalState();
  }

  window.submitManualMetric = async function (e) {
    e.preventDefault();
    const rec = {
      ym: document.getElementById('manYm').value,
      category: document.getElementById('manCat').value,
      mt: document.getElementById('manMt').value ? Number(document.getElementById('manMt').value) : null,
      trips: document.getElementById('manTrips').value ? Number(document.getElementById('manTrips').value) : null,
      pallets: document.getElementById('manPallets').value ? Number(document.getElementById('manPallets').value) : null,
      source: 'MANUAL',
      breakdown: {},
    };
    upsertLocalMetrics([rec]);
    await pushMetricsBatch([rec], 'MANUAL_ENTRY');
    populateYearSelector();
    renderAll();
    showToast(`已儲存 ${rec.ym} 數據！`, 'success');
  };

  // ==================== 日常管理 & 重要工作進度 通用批次解析引擎 ====================
  function escHtml(str) {
    return String(str ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  function extractJsonArray(raw) {
    const cleaned = String(raw || '').replace(/```json|```/gi, '').trim();
    let jsonStr = cleaned;
    const startIdx = cleaned.indexOf('[');
    const endIdx = cleaned.lastIndexOf(']');
    if (startIdx !== -1 && endIdx > startIdx) {
      jsonStr = cleaned.slice(startIdx, endIdx + 1);
    }
    const arr = JSON.parse(jsonStr);
    if (!Array.isArray(arr)) throw new Error('AI 回傳非陣列格式');
    return arr;
  }

  function getDefaultQuarterPeriod() {
    const inp = document.getElementById('mgmtPastePeriod')?.value?.trim() || document.getElementById('mgmtPeriod')?.value?.trim();
    if (inp) return inp;
    const d = new Date();
    return `${d.getFullYear()}-Q${Math.ceil((d.getMonth() + 1) / 3)}`;
  }

  function normalizeDateStr(val) {
    if (val === null || val === undefined || val === '') return '';
    if (typeof val === 'number' && val > 30000 && val < 80000) {
      return new Date(Math.round((val - 25569) * 86400 * 1000)).toISOString().slice(0, 10);
    }
    const s = String(val).trim();
    const m1 = s.match(/^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$/);
    if (m1) return `${m1[1]}-${m1[2].padStart(2, '0')}-${m1[3].padStart(2, '0')}`;
    const m2 = s.match(/^(\d{4})(\d{2})(\d{2})$/);
    if (m2) return `${m2[1]}-${m2[2]}-${m2[3]}`;
    return s;
  }

  function inferPeriodFromDate(dateStr, fallback) {
    const d = normalizeDateStr(dateStr);
    const m = d.match(/^(\d{4})-(\d{2})-/);
    if (m) return `${m[1]}-Q${Math.ceil(Number(m[2]) / 3)}`;
    return fallback || getDefaultQuarterPeriod();
  }

  function normalizeMgmtType(rawType, content = '') {
    const valid = ['品質作業', '工安異常', '客戶稽核', '其他管理'];
    const t = String(rawType || '').trim();
    if (valid.includes(t)) return t;
    const text = `${t} ${content}`;
    if (/工安|碰撞|撞|傷|意外|洩漏|安全|火|危險|違規/.test(text)) return '工安異常';
    if (/稽核|台積|客戶|查核|客訴|評鑑/.test(text)) return '客戶稽核';
    if (/品質|檢驗|異常|不良|品保|規格/.test(text)) return '品質作業';
    return '其他管理';
  }

  function normalizeProjStatus(raw) {
    const valid = ['進行中', '已完成', '評估中', '暫緩'];
    const s = String(raw || '').trim();
    if (valid.includes(s)) return s;
    if (/完成|結案|OK|done/i.test(s)) return '已完成';
    if (/暫緩|停|取消|hold/i.test(s)) return '暫緩';
    if (/評估|討論|研議|規劃/.test(s)) return '評估中';
    return '進行中';
  }

  function normalizeMgmtItem(item, fallbackPeriod) {
    const content = String(item.content || item.說明 || item.事件 || '').trim();
    const date = normalizeDateStr(item.date || item.日期 || '');
    const period = String(item.period || item.期別 || '').trim() || inferPeriodFromDate(date, fallbackPeriod);
    return {
      period,
      date,
      type: normalizeMgmtType(item.type || item.類別, content),
      content,
      status: String(item.status || item.狀態 || '記錄中').trim() || '記錄中',
    };
  }

  function normalizeProjItem(item) {
    return {
      title: String(item.title || item.主題 || '').trim(),
      desc: String(item.desc || item.說明 || '').trim(),
      effect: String(item.effect || item.成效 || '').trim(),
      eta: String(item.eta || item.預估時間 || '').trim(),
      status: normalizeProjStatus(item.status || item.狀態 || ''),
    };
  }

  async function invokeGeminiWithFallback(prompt, images = []) {
    if (state.apiOnline) {
      const res = await fetch('/api/ocr', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images, prompt }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `後端 AI 解析失敗 (HTTP ${res.status})`);
      if (!Array.isArray(data.records)) throw new Error('後端 AI 回傳格式異常');
      return { records: data.records, model: data.model || 'Cloudflare AI' };
    }

    const apiKey = localStorage.getItem(STORAGE_KEYS.GEMINI_KEY) || '';
    if (!apiKey) {
      throw new Error('單機模式未設定 Gemini API Key，請點右上角「⚙️ 設定 / AI OCR」填入後重試');
    }
    const imageParts = (images || []).map((item) =>
      item && typeof item === 'object' && item.data
        ? { inline_data: { mime_type: item.mime_type || 'image/jpeg', data: item.data } }
        : { inline_data: { mime_type: 'image/jpeg', data: item } }
    );
    const parts = [{ text: prompt }, ...imageParts];

    let lastError = '所有模型皆無法回應';
    for (const model of GEMINI_MODELS) {
      try {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${encodeURIComponent(apiKey)}`;
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ contents: [{ parts }], generationConfig: { temperature: 0.1 } }),
        });
        if (!res.ok) {
          const errJson = await res.json().catch(() => ({}));
          lastError = `[${model}] HTTP ${res.status}: ${errJson.error?.message || res.statusText}`;
          continue;
        }
        const json = await res.json();
        const raw = json.candidates?.[0]?.content?.parts?.[0]?.text || '';
        const arr = extractJsonArray(raw);
        return { records: arr, model };
      } catch (e) {
        lastError = `[${model}] ${e.message}`;
      }
    }
    throw new Error(`Gemini AI 降級鏈耗盡：${lastError}`);
  }

  function parseTextRuleFallback(target, text, defaultPeriod) {
    const rawLines = String(text || '')
      .split(/\r?\n+/)
      .map((l) => l.trim())
      .filter(Boolean);
    const out = [];

    for (const rawLine of rawLines) {
      const line = rawLine.replace(/^(?:第?\s*\d+\s*頁|\[\s*第\s*\d+\s*頁\s*\])/, '').trim();
      if (!line) continue;
      if (/^(?:項次|項目|期別|日期|主題|作業項目).*(?:說明|類別|成效|內容)/.test(line)) continue;

      const cleaned = line.replace(/^(?:\(\d+\)|\d+[.、)）]|[-•*▪])\s*/, '').trim();
      if (!cleaned || cleaned.length < 2) continue;

      if (target === 'mgmt') {
        if (/^(?:四、)?日常管理(?:重點|紀錄)?$/.test(cleaned)) continue;
        const cols = cleaned.split(/\s*[|\t]\s*/).filter(Boolean);
        if (cols.length >= 3) {
          let period = defaultPeriod;
          let date = '';
          let type = '';
          const rest = [];
          for (const c of cols) {
            if (/^20\d{2}[-_]?(?:Q[1-4]|H[12])$/i.test(c)) period = c.toUpperCase();
            else if (/^\d{4}[-/]\d{1,2}[-/]\d{1,2}$/.test(c)) date = normalizeDateStr(c);
            else if (['品質作業', '工安異常', '客戶稽核', '其他管理'].includes(c)) type = c;
            else rest.push(c);
          }
          const content = rest.join('｜') || cleaned;
          out.push(normalizeMgmtItem({ period, date, type, content, status: '記錄中' }, defaultPeriod));
        } else {
          const dMatch = cleaned.match(/(20\d{2})[-/](\d{1,2})[-/](\d{1,2})/) || cleaned.match(/(\d{1,2})\/(\d{1,2})/);
          let date = '';
          if (dMatch) {
            if (dMatch.length === 4) date = `${dMatch[1]}-${dMatch[2].padStart(2, '0')}-${dMatch[3].padStart(2, '0')}`;
            else {
              const yr = (defaultPeriod.match(/20\d{2}/) || [String(new Date().getFullYear())])[0];
              date = `${yr}-${dMatch[1].padStart(2, '0')}-${dMatch[2].padStart(2, '0')}`;
            }
          }
          const pMatch = cleaned.match(/(20\d{2})?[- ]?(Q[1-4]|H[12])/i);
          const yr = (defaultPeriod.match(/20\d{2}/) || [String(new Date().getFullYear())])[0];
          const period = pMatch ? `${pMatch[1] || yr}-${pMatch[2].toUpperCase()}` : inferPeriodFromDate(date, defaultPeriod);
          out.push(normalizeMgmtItem({ period, date, type: '', content: cleaned, status: '記錄中' }, defaultPeriod));
        }
      } else {
        if (/^(?:五、)?重要工作進度(?:報告)?$/.test(cleaned)) continue;
        let cols = cleaned.split(/\s*[|\t]\s*/).filter((x) => x !== '');
        if (cols.length === 1) cols = cleaned.split(/\s{2,}/).filter(Boolean);
        if (cols.length >= 2 && /^\d{1,2}$/.test(cols[0].trim())) cols = cols.slice(1);
        if (cols.length >= 2) {
          out.push(
            normalizeProjItem({
              title: cols[0],
              desc: cols[1] || '',
              effect: cols[2] || '',
              eta: cols[3] || '',
              status: cols[4] || '進行中',
            })
          );
        } else {
          out.push(
            normalizeProjItem({
              title: cleaned.slice(0, 28),
              desc: cleaned,
              effect: '',
              eta: '',
              status: '進行中',
            })
          );
        }
      }
    }
    return out.filter((x) => (target === 'mgmt' ? x.content : x.title));
  }

  async function callGeminiStructuredExtract(target, { text = '', images = [], filename = '輸入文字' }) {
    const defaultPeriod = getDefaultQuarterPeriod();
    const prompt =
      target === 'mgmt'
        ? `你是台灣化工資材部行政報告解析專家。請從以下資料（日常管理報告、稽核紀錄、工安異常或會議內容）中擷取每一筆日常管理紀錄，只回傳純 JSON 陣列（不要任何 markdown 標記或額外文字），格式如下：
[{"period":"${defaultPeriod}","date":"2026-07-26","type":"品質作業|工安異常|客戶稽核|其他管理","content":"具體事件或稽核說明","status":"正常|已改善|通過|記錄中"}]
規則：
1. type 僅能從「品質作業」「工安異常」「客戶稽核」「其他管理」四選一。
2. period 格式盡量為 YYYY-Q1~Q4 或 YYYY-H1~H2（若未註明，請依日期推算或使用 "${defaultPeriod}"）。
3. date 請轉為 YYYY-MM-DD（若只有月/日如 7/26，請依報告年份補齊；真的沒有日期可填 ""）。`
        : `你是台灣化工資材部專案進度解析專家。請從以下資料（重要工作進度報告、改善專案表、PPT 簡報或會議紀錄）中擷取每一項工作進度，只回傳純 JSON 陣列（不要任何 markdown 標記或額外文字），格式如下：
[{"title":"工作主題","desc":"工作詳細說明","effect":"預期或實際成效","eta":"2026Q2 或 全年持續","status":"進行中|已完成|評估中|暫緩"}]
規則：
1. status 僅能從「進行中」「已完成」「評估中」「暫緩」四選一。
2. 若某欄位原文未提及，請填 ""，不可捏造不存在的數字。`;

    const fullPrompt = text ? `${prompt}\n\n來源：${filename}\n內容：\n${text.slice(0, 18000)}` : `${prompt}\n\n來源檔案：${filename}`;

    try {
      const { records, model } = await invokeGeminiWithFallback(fullPrompt, images);
      const normalized = records
        .map((r) => (target === 'mgmt' ? normalizeMgmtItem(r, defaultPeriod) : normalizeProjItem(r)))
        .filter((r) => (target === 'mgmt' ? r.content : r.title));
      if (normalized.length > 0) {
        showToast(`AI 智慧解析成功（模型：${model}，共 ${normalized.length} 筆）`, 'success');
        return normalized;
      }
    } catch (err) {
      if (text && text.trim()) {
        const fallback = parseTextRuleFallback(target, text, defaultPeriod);
        if (fallback.length > 0) {
          showToast(`AI 暫時無法使用，已啟用本機智慧切分解析 ${fallback.length} 筆`, 'warning');
          return fallback;
        }
      }
      throw err;
    }

    if (text && text.trim()) {
      const fallback = parseTextRuleFallback(target, text, defaultPeriod);
      if (fallback.length > 0) return fallback;
    }
    throw new Error('未能從檔案中辨識出有效紀錄');
  }

  async function parseStructuredExcel(file, target) {
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(buf, { type: 'array' });
    const defaultPeriod = getDefaultQuarterPeriod();

    const findColIdx = (headers, aliases) => {
      let idx = headers.findIndex((h) => aliases.includes(h));
      if (idx >= 0) return idx;
      return headers.findIndex((h) => h && h.length <= 16 && aliases.some((a) => h.includes(a)));
    };

    const allSheetText = [];
    for (const sheetName of wb.SheetNames) {
      const rows = XLSX.utils.sheet_to_json(wb.Sheets[sheetName], { header: 1, raw: true, defval: '' });
      if (!rows.length) continue;

      rows.forEach((r) => {
        const line = r.map((c) => String(c ?? '').trim()).filter(Boolean).join(' | ');
        if (line) allSheetText.push(line);
      });

      for (let i = 0; i < Math.min(15, rows.length); i++) {
        const hdrs = rows[i].map((c) => String(c ?? '').trim());
        if (target === 'mgmt') {
          const iContent = findColIdx(hdrs, ['內容', '說明', '事件說明', '事項', '事件或稽核說明', '管理事項', '事件內容', '工作內容']);
          if (iContent < 0) continue;
          const iPeriod = findColIdx(hdrs, ['期別', '季別', '期間', '報告期別', '年度季別']);
          const iDate = findColIdx(hdrs, ['日期', '發生日期', '稽核日期', '紀錄日期', '時間']);
          const iType = findColIdx(hdrs, ['類別', '類型', '分類', '項目', '事件類別']);
          const iStatus = findColIdx(hdrs, ['狀態', '處理狀態', '進度']);

          const out = [];
          for (let r = i + 1; r < rows.length; r++) {
            const row = rows[r];
            const content = String(row[iContent] ?? '').trim();
            if (!content) continue;
            out.push(
              normalizeMgmtItem(
                {
                  period: iPeriod >= 0 ? row[iPeriod] : '',
                  date: iDate >= 0 ? row[iDate] : '',
                  type: iType >= 0 ? row[iType] : '',
                  content,
                  status: iStatus >= 0 ? row[iStatus] : '記錄中',
                },
                defaultPeriod
              )
            );
          }
          if (out.length) return out;
        } else {
          const iTitle = findColIdx(hdrs, ['主題', '項目', '專案名稱', '工作主題', '工作項目', '工作名稱']);
          const iDesc = findColIdx(hdrs, ['說明', '工作說明', '內容', '執行內容', '詳細說明']);
          const iEffect = findColIdx(hdrs, ['成效', '預期成效', '效益', '目標成效']);
          const iEta = findColIdx(hdrs, ['預估時間', '預計完成', '完成時間', '時程', 'ETA', '預計完成時間']);
          if (iTitle < 0 || (iDesc < 0 && iEffect < 0 && iEta < 0)) continue;
          const iStatus = findColIdx(hdrs, ['狀態', '進度', '目前狀態']);

          const out = [];
          for (let r = i + 1; r < rows.length; r++) {
            const row = rows[r];
            const title = String(row[iTitle] ?? '').trim();
            if (!title) continue;
            out.push(
              normalizeProjItem({
                title,
                desc: iDesc >= 0 ? row[iDesc] : '',
                effect: iEffect >= 0 ? row[iEffect] : '',
                eta: iEta >= 0 ? row[iEta] : '',
                status: iStatus >= 0 ? row[iStatus] : '進行中',
              })
            );
          }
          if (out.length) return out;
        }
      }
    }

    const dumped = allSheetText.join('\n');
    if (dumped.trim()) {
      return await callGeminiStructuredExtract(target, { text: dumped, filename: file.name });
    }
    throw new Error('Excel 檔案內容為空');
  }

  async function extractOfficeXmlText(file) {
    if (!window.JSZip) throw new Error('JSZip 尚未載入，請確認網路連線');
    const zip = await JSZip.loadAsync(await file.arrayBuffer());
    const ext = file.name.split('.').pop().toLowerCase();
    const parser = new DOMParser();

    if (ext === 'docx') {
      const docFile = zip.file('word/document.xml');
      if (!docFile) throw new Error('無效的 Word (.docx) 結構');
      const xmlDoc = parser.parseFromString(await docFile.async('string'), 'application/xml');
      const body = Array.from(xmlDoc.getElementsByTagName('*')).find((el) => el.localName === 'body') || xmlDoc.documentElement;
      const lines = [];
      for (const child of Array.from(body.children || [])) {
        if (child.localName === 'tbl') {
          const trs = Array.from(child.getElementsByTagName('*')).filter((el) => el.localName === 'tr');
          for (const tr of trs) {
            const tcs = Array.from(tr.children || []).filter((el) => el.localName === 'tc');
            const cells = tcs.map((tc) =>
              Array.from(tc.getElementsByTagName('*'))
                .filter((el) => el.localName === 't')
                .map((t) => t.textContent)
                .join('')
                .trim()
            );
            if (cells.some(Boolean)) lines.push(cells.join(' | '));
          }
        } else {
          const ps = child.localName === 'p' ? [child] : Array.from(child.getElementsByTagName('*')).filter((el) => el.localName === 'p');
          for (const p of ps) {
            const txt = Array.from(p.getElementsByTagName('*'))
              .filter((el) => el.localName === 't')
              .map((t) => t.textContent)
              .join('')
              .trim();
            if (txt) lines.push(txt);
          }
        }
      }
      return lines.join('\n');
    }

    if (ext === 'pptx') {
      const slideNames = Object.keys(zip.files)
        .filter((n) => /^ppt\/slides\/slide\d+\.xml$/i.test(n))
        .sort((a, b) => Number(a.match(/(\d+)\.xml$/)[1]) - Number(b.match(/(\d+)\.xml$/)[1]));
      if (!slideNames.length) throw new Error('無效的 PowerPoint (.pptx) 結構');
      const allLines = [];
      for (const sName of slideNames) {
        const slideNum = sName.match(/(\d+)\.xml$/)[1];
        allLines.push(`[第 ${slideNum} 頁]`);
        const xmlDoc = parser.parseFromString(await zip.file(sName).async('string'), 'application/xml');
        const tablePs = new Set();
        const tbls = Array.from(xmlDoc.getElementsByTagName('*')).filter((el) => el.localName === 'tbl');
        for (const tbl of tbls) {
          Array.from(tbl.getElementsByTagName('*')).filter((el) => el.localName === 'p').forEach((p) => tablePs.add(p));
          const trs = Array.from(tbl.getElementsByTagName('*')).filter((el) => el.localName === 'tr');
          for (const tr of trs) {
            const tcs = Array.from(tr.children || []).filter((el) => el.localName === 'tc');
            const cells = tcs.map((tc) =>
              Array.from(tc.getElementsByTagName('*'))
                .filter((el) => el.localName === 't')
                .map((t) => t.textContent)
                .join('')
                .trim()
            );
            if (cells.some(Boolean)) allLines.push(cells.join(' | '));
          }
        }
        const ps = Array.from(xmlDoc.getElementsByTagName('*')).filter((el) => el.localName === 'p' && !tablePs.has(el));
        for (const p of ps) {
          const txt = Array.from(p.getElementsByTagName('*'))
            .filter((el) => el.localName === 't')
            .map((t) => t.textContent)
            .join('')
            .trim();
          if (txt) allLines.push(txt);
        }
      }
      return allLines.join('\n');
    }

    throw new Error('不支援的 Office 格式');
  }

  async function extractPdfTextOrImages(file) {
    if (!window.pdfjsLib) throw new Error('pdf.js 尚未載入');
    const pdf = await pdfjsLib.getDocument({ data: await file.arrayBuffer() }).promise;
    let fullText = '';
    for (let p = 1; p <= pdf.numPages; p++) {
      const page = await pdf.getPage(p);
      const content = await page.getTextContent();
      fullText += content.items.map((it) => it.str).join(' ') + '\n';
    }
    if (fullText.trim().length > 40) {
      return { text: fullText, images: [] };
    }
    const images = [];
    const maxPages = Math.min(pdf.numPages, 4);
    for (let p = 1; p <= maxPages; p++) {
      const page = await pdf.getPage(p);
      const vp = page.getViewport({ scale: 1.6 });
      const canvas = document.createElement('canvas');
      canvas.width = vp.width;
      canvas.height = vp.height;
      await page.render({ canvasContext: canvas.getContext('2d'), viewport: vp }).promise;
      images.push({ mime_type: 'image/jpeg', data: canvas.toDataURL('image/jpeg', 0.85).split(',')[1] });
    }
    return { text: '', images };
  }

  function readImageAsBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const res = String(reader.result || '');
        const b64 = res.split(',')[1] || '';
        resolve({ mime_type: file.type || 'image/jpeg', data: b64 });
      };
      reader.onerror = () => reject(new Error('讀取圖片失敗'));
      reader.readAsDataURL(file);
    });
  }

  async function handleStructuredFiles(fileList, target) {
    const files = Array.from(fileList || []);
    if (!files.length) return;
    const statusEl = document.getElementById(target === 'mgmt' ? 'mgmtParseStatus' : 'projParseStatus');
    statusEl.classList.remove('hidden');
    statusEl.innerHTML = `<div class="text-sky-300 font-bold">⏳ 正在解析 ${files.length} 個檔案，請稍候...</div>`;

    const allParsed = [];
    const logs = [];

    for (const file of files) {
      const ext = file.name.split('.').pop().toLowerCase();
      try {
        let recs = [];
        if (['xlsx', 'xls', 'csv'].includes(ext)) {
          recs = await parseStructuredExcel(file, target);
        } else if (['docx', 'pptx'].includes(ext)) {
          const text = await extractOfficeXmlText(file);
          recs = await callGeminiStructuredExtract(target, { text, filename: file.name });
        } else if (ext === 'pdf') {
          const { text, images } = await extractPdfTextOrImages(file);
          recs = await callGeminiStructuredExtract(target, { text, images, filename: file.name });
        } else if (['png', 'jpg', 'jpeg', 'webp'].includes(ext)) {
          const img = await readImageAsBase64(file);
          recs = await callGeminiStructuredExtract(target, { images: [img], filename: file.name });
        } else if (ext === 'txt') {
          const text = await file.text();
          recs = await callGeminiStructuredExtract(target, { text, filename: file.name });
        } else {
          logs.push(`⚠️ <strong>${escHtml(file.name)}</strong>：不支援的副檔名 (.${escHtml(ext)})`);
          continue;
        }
        allParsed.push(...recs);
        logs.push(`✅ <strong>${escHtml(file.name)}</strong>：成功解析 ${recs.length} 筆`);
      } catch (err) {
        logs.push(`❌ <strong>${escHtml(file.name)}</strong>：${escHtml(err.message)}`);
      }
    }

    statusEl.innerHTML = logs.map((l) => `<div class="py-0.5">${l}</div>`).join('');
    if (allParsed.length) {
      if (target === 'mgmt') {
        state.mgmtPreview = [...state.mgmtPreview, ...annotateMgmtPreview(allParsed)];
        renderMgmtPreview();
      } else {
        state.projPreview = [...state.projPreview, ...annotateProjPreview(allParsed)];
        renderProjPreview();
      }
    }
  }

  window.toggleQuickPaste = function (target) {
    const box = document.getElementById(target === 'mgmt' ? 'mgmtPasteBox' : 'projPasteBox');
    if (box) box.classList.toggle('hidden');
  };

  window.parsePastedText = async function (target) {
    const txtEl = document.getElementById(target === 'mgmt' ? 'mgmtPasteText' : 'projPasteText');
    const statusEl = document.getElementById(target === 'mgmt' ? 'mgmtParseStatus' : 'projParseStatus');
    const text = (txtEl?.value || '').trim();
    if (!text) {
      showToast('請先貼上要解析的文字內容', 'warning');
      return;
    }
    statusEl.classList.remove('hidden');
    statusEl.innerHTML = `<div class="text-sky-300 font-bold">⏳ 正在智慧解析貼上文字...</div>`;
    try {
      const recs = await callGeminiStructuredExtract(target, { text, filename: '快速貼上文字' });
      statusEl.innerHTML = `<div class="text-emerald-300">✅ 成功從貼上文字解析出 <strong>${recs.length}</strong> 筆資料！</div>`;
      if (target === 'mgmt') {
        state.mgmtPreview = [...state.mgmtPreview, ...annotateMgmtPreview(recs)];
        renderMgmtPreview();
      } else {
        state.projPreview = [...state.projPreview, ...annotateProjPreview(recs)];
        renderProjPreview();
      }
    } catch (err) {
      statusEl.innerHTML = `<div class="text-rose-400">❌ 解析失敗：${escHtml(err.message)}</div>`;
    }
  };

  window.downloadMgmtTemplate = function () {
    const wb = XLSX.utils.book_new();
    const rows = [
      { 期別: '2026-Q3', 日期: '2026-07-26', 類別: '工安異常', 事件或稽核說明: '7/26 堆高機迴轉時，噸桶不慎碰撞67區鋼構防火板。', 狀態: '已改善' },
      { 期別: '2026-Q3', 日期: '2026-09-30', 類別: '品質作業', 事件或稽核說明: 'Q3品質相關作業無異常。', 狀態: '正常' },
      { 期別: '2026-Q3', 日期: '2026-09-30', 類別: '客戶稽核', 事件或稽核說明: '台積下半年度N系列庫存稽核無大缺失。', 狀態: '通過' },
    ];
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rows), '日常管理匯入範本');
    XLSX.writeFile(wb, '日常管理匯入範本.xlsx');
    showToast('已下載「日常管理匯入範本.xlsx」', 'success');
  };

  window.downloadProjTemplate = function () {
    const wb = XLSX.utils.book_new();
    const rows = [
      { 主題: 'TK669,670儲槽更改存放MEAUPS原料', 說明: '配合業務需求。', 成效: '增加第二貨源，提升原料供應穩定性。', 預估時間: '2026Q2', 狀態: '進行中' },
      { 主題: '加裝儲槽電子式微壓表', 說明: '舊槽區32個儲槽加裝電子式微壓表。', 成效: '偵測氮封有無異常作動。', 預估時間: '2026Q1', 狀態: '進行中' },
    ];
    XLSX.utils.book_append_sheet(wb, XLSX.utils.json_to_sheet(rows), '重要工作進度範本');
    XLSX.writeFile(wb, '重要工作進度匯入範本.xlsx');
    showToast('已下載「重要工作進度匯入範本.xlsx」', 'success');
  };

  // ==================== 日常管理 (P.5) ====================
  function annotateMgmtPreview(items) {
    const periodKeys = new Set();
    const dateKeys = new Set();
    const longContents = [];

    for (const m of state.management) {
      const ck = normalizeMatchKey(m.content);
      if (!ck) continue;
      periodKeys.add(`${m.period}|${ck}`);
      if (m.date) dateKeys.add(`${m.date}|${ck}`);
      if (ck.length >= 8) longContents.push({ key: ck, date: m.date || '' });
    }

    const batchPeriodKeys = new Set();
    const batchDateKeys = new Set();
    const batchLongContents = [];
    for (const m of state.mgmtPreview) {
      const ck = normalizeMatchKey(m.content);
      if (!ck) continue;
      batchPeriodKeys.add(`${m.period}|${ck}`);
      if (m.date) batchDateKeys.add(`${m.date}|${ck}`);
      if (ck.length >= 8) batchLongContents.push({ key: ck, date: m.date || '' });
    }

    const matchLong = (list, ck, dt) =>
      ck.length >= 8 && list.some((it) => it.key === ck && (!dt || !it.date || it.date === dt));

    return items.map((m) => {
      const ck = normalizeMatchKey(m.content);
      const pk = `${m.period}|${ck}`;
      const dk = m.date ? `${m.date}|${ck}` : '';
      let dupStatus = 'new';

      if (periodKeys.has(pk) || (dk && dateKeys.has(dk)) || matchLong(longContents, ck, m.date)) {
        dupStatus = 'dup_db';
      } else if (
        batchPeriodKeys.has(pk) ||
        (dk && batchDateKeys.has(dk)) ||
        matchLong(batchLongContents, ck, m.date)
      ) {
        dupStatus = 'dup_batch';
      } else {
        batchPeriodKeys.add(pk);
        if (dk) batchDateKeys.add(dk);
        if (ck.length >= 8) batchLongContents.push({ key: ck, date: m.date || '' });
      }

      return { ...m, _dupStatus: dupStatus, _selected: dupStatus === 'new' };
    });
  }

  function renderMgmtPreview() {
    const panel = document.getElementById('mgmtPreviewPanel');
    const tbody = document.getElementById('mgmtPreviewBody');
    const banner = document.getElementById('mgmtDupBanner');
    if (!panel || !tbody) return;
    if (!state.mgmtPreview.length) {
      panel.classList.add('hidden');
      if (banner) banner.classList.add('hidden');
      return;
    }
    panel.classList.remove('hidden');

    let dupCnt = 0;
    let newCnt = 0;
    tbody.innerHTML = state.mgmtPreview
      .map((m, idx) => {
        if (m._dupStatus === 'new') newCnt++;
        else dupCnt++;
        const badge =
          m._dupStatus === 'new'
            ? '<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-[11px]">🟢 新增</span>'
            : m._dupStatus === 'dup_db'
            ? '<span class="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-200 font-bold text-[11px]">🟡 資料庫已存在</span>'
            : '<span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-200 font-bold text-[11px]">🟡 檔內重複</span>';
        return `<tr class="hover:bg-slate-800/40 ${m._selected ? '' : 'opacity-45'}">
        <td class="py-2 px-2 text-center"><input type="checkbox" class="accent-emerald-500" ${m._selected ? 'checked' : ''} onchange="toggleMgmtPreviewCheck(${idx}, this.checked)" /></td>
        <td class="py-2 px-2">${badge}</td>
        <td class="py-2 px-2 font-bold text-white">${escHtml(m.period)}</td>
        <td class="py-2 px-2 font-mono text-slate-300">${escHtml(m.date || '—')}</td>
        <td class="py-2 px-2"><span class="px-2 py-0.5 rounded bg-slate-800 text-sky-300 font-semibold">${escHtml(m.type)}</span></td>
        <td class="py-2 px-2 text-slate-200">${escHtml(m.content)}</td>
        <td class="py-2 px-2 text-slate-400">${escHtml(m.status)}</td>
        <td class="py-2 px-2 text-center"><button type="button" onclick="removeMgmtPreviewItem(${idx})" class="text-slate-400 hover:text-rose-400">🗑️</button></td>
      </tr>`;
      })
      .join('');

    if (banner) {
      if (dupCnt > 0) {
        banner.innerHTML = `⚠️ 偵測到 <strong>${dupCnt}</strong> 筆重複紀錄（已預設取消勾選略過，🟢 新增 <strong>${newCnt}</strong> 筆；如需強制匯入請手動勾選）`;
        banner.classList.remove('hidden');
      } else {
        banner.classList.add('hidden');
      }
    }
  }

  window.toggleMgmtPreviewCheck = function (idx, checked) {
    if (state.mgmtPreview[idx]) {
      state.mgmtPreview[idx]._selected = Boolean(checked);
      renderMgmtPreview();
    }
  };

  window.removeMgmtPreviewItem = function (idx) {
    state.mgmtPreview.splice(idx, 1);
    renderMgmtPreview();
  };

  window.clearMgmtPreview = function () {
    state.mgmtPreview = [];
    renderMgmtPreview();
  };

  window.commitMgmtPreview = async function () {
    if (!state.mgmtPreview.length) return;
    const selected = state.mgmtPreview.filter((m) => m._selected);
    const skipped = state.mgmtPreview.length - selected.length;
    if (!selected.length) {
      showToast('沒有勾選要寫入的新資料（重複列已預設略過）', 'warning');
      return;
    }
    const baseId = Date.now();
    const newItems = selected.map((m, idx) => ({
      id: baseId + idx,
      period: m.period || getDefaultQuarterPeriod(),
      date: m.date || '',
      type: m.type || '其他管理',
      content: m.content,
      status: m.status || '記錄中',
    }));
    state.management = [...newItems, ...state.management];
    saveLocalState();
    await apiPost('/api/management', { records: newItems }, `批次匯入 ${newItems.length} 筆日常管理紀錄`);
    state.mgmtPreview = [];
    renderMgmtPreview();
    renderAll();
    showToast(`成功寫入 ${newItems.length} 筆日常管理紀錄${skipped ? `，略過 ${skipped} 筆重複` : ''}！`, 'success');
  };
  function renderManagementList() {
    const box = document.getElementById('mgmtList');
    const yrSel = document.getElementById('mgmtYearFilter');
    const cntEl = document.getElementById('mgmtFilterCount');

    const getMgmtYr = (m) => String(m.period || m.date || '').match(/(20\d{2})/)?.[1] || '未分類';
    if (yrSel) {
      const prevYr = yrSel.value || 'ALL';
      const years = Array.from(new Set(state.management.map(getMgmtYr))).sort((a, b) => {
        if (a === '未分類') return 1;
        if (b === '未分類') return -1;
        return Number(b) - Number(a);
      });
      yrSel.innerHTML =
        `<option value="ALL">全部年度 (${state.management.length}筆)</option>` +
        years.map((y) => `<option value="${y}">${y === '未分類' ? '未分類' : y + ' 年度'}</option>`).join('');
      yrSel.value = prevYr === 'ALL' || years.includes(prevYr) ? prevYr : 'ALL';
    }

    const selYr = yrSel?.value || 'ALL';
    const filtered = state.management.filter((m) => selYr === 'ALL' || getMgmtYr(m) === selYr);
    if (cntEl) cntEl.textContent = `顯示 ${filtered.length} / ${state.management.length} 筆`;

    if (!filtered.length) {
      box.innerHTML = `<div class="text-slate-400 text-sm p-4 rounded-xl bg-slate-900/50 border border-slate-800 text-center">此年度尚無日常管理紀錄</div>`;
      return;
    }
    const badgeCls = {
      品質作業: 'bg-sky-500/20 text-sky-300',
      工安異常: 'bg-rose-500/20 text-rose-300',
      客戶稽核: 'bg-emerald-500/20 text-emerald-300',
      其他管理: 'bg-slate-600/30 text-slate-300',
    };
    box.innerHTML = filtered
      .map(
        (m) => `<div class="p-3.5 rounded-xl bg-slate-900/75 border border-slate-800 flex items-center justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center gap-2 text-xs">
            <span class="font-bold text-white">${escHtml(m.period)}</span>
            <span class="px-2 py-0.5 rounded font-semibold ${badgeCls[m.type] || badgeCls['其他管理']}">${escHtml(m.type)}</span>
            <span class="text-slate-400">${escHtml(m.date || '')}</span>
          </div>
          <div class="text-sm text-slate-200">${escHtml(m.content)}</div>
        </div>
        <button onclick="deleteManagementItem(${m.id})" class="text-xs text-slate-400 hover:text-rose-400 px-2 py-1">🗑️</button>
      </div>`
      )
      .join('');
  }
  window.renderManagementList = renderManagementList;

  window.addManagementItem = async function (e) {
    e.preventDefault();
    const item = {
      id: Date.now(),
      period: document.getElementById('mgmtPeriod').value.trim(),
      date: document.getElementById('mgmtDate').value,
      type: document.getElementById('mgmtType').value,
      content: document.getElementById('mgmtContent').value.trim(),
      status: '記錄中',
    };
    state.management.unshift(item);
    saveLocalState();
    await apiPost('/api/management', item, '新增日常管理紀錄');
    document.getElementById('mgmtContent').value = '';
    renderAll();
    showToast('已新增日常管理紀錄', 'success');
  };

  window.deleteManagementItem = async function (id) {
    state.management = state.management.filter((m) => m.id !== id);
    saveLocalState();
    if (state.apiOnline) {
      fetch(`/api/management?id=${id}`, { method: 'DELETE' }).catch(() => {});
    }
    renderAll();
  };

  // ==================== 重要工作進度 (P.6~P.8) ====================
  function annotateProjPreview(items) {
    const dbMap = new Map();
    for (const p of state.projects) {
      const tk = normalizeMatchKey(p.title);
      if (tk && !dbMap.has(tk)) dbMap.set(tk, p);
    }
    const batchTitles = new Set(state.projPreview.map((p) => normalizeMatchKey(p.title)).filter(Boolean));

    return items.map((p) => {
      const tk = normalizeMatchKey(p.title);
      if (tk && batchTitles.has(tk)) {
        return { ...p, _dupStatus: 'dup_batch', _selected: false, _diffSummary: '同批重複主題' };
      }
      if (tk) batchTitles.add(tk);

      const exist = tk ? dbMap.get(tk) : null;
      if (!exist) {
        return { ...p, _dupStatus: 'new', _selected: true, _diffSummary: '' };
      }

      const diffs = [];
      if (p.desc && normalizeMatchKey(p.desc) !== normalizeMatchKey(exist.desc)) diffs.push('說明更新');
      if (p.effect && normalizeMatchKey(p.effect) !== normalizeMatchKey(exist.effect)) diffs.push('成效更新');
      if (p.eta && normalizeMatchKey(p.eta) !== normalizeMatchKey(exist.eta)) {
        diffs.push(`時程: ${exist.eta || '—'}→${p.eta}`);
      }
      if (p.status && p.status !== exist.status) {
        diffs.push(`狀態: ${exist.status}→${p.status}`);
      }

      if (diffs.length > 0) {
        return {
          ...p,
          _dupStatus: 'update',
          _matchId: exist.id,
          _selected: true,
          _diffSummary: diffs.join('、'),
        };
      }
      return { ...p, _dupStatus: 'dup_db', _matchId: exist.id, _selected: false, _diffSummary: '內容與資料庫相同' };
    });
  }

  function renderProjPreview() {
    const panel = document.getElementById('projPreviewPanel');
    const tbody = document.getElementById('projPreviewBody');
    const banner = document.getElementById('projDupBanner');
    if (!panel || !tbody) return;
    if (!state.projPreview.length) {
      panel.classList.add('hidden');
      if (banner) banner.classList.add('hidden');
      return;
    }
    panel.classList.remove('hidden');

    let newCnt = 0;
    let updCnt = 0;
    let dupCnt = 0;

    tbody.innerHTML = state.projPreview
      .map((p, idx) => {
        if (p._dupStatus === 'new') newCnt++;
        else if (p._dupStatus === 'update') updCnt++;
        else dupCnt++;

        const badge =
          p._dupStatus === 'new'
            ? '<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-bold text-[11px]">🟢 新增</span>'
            : p._dupStatus === 'update'
            ? `<span class="px-2 py-0.5 rounded bg-sky-500/25 text-sky-300 font-bold text-[11px]">🔵 進度更新</span><div class="text-[10px] text-sky-200 mt-0.5">${escHtml(p._diffSummary || '')}</div>`
            : `<span class="px-2 py-0.5 rounded bg-yellow-500/20 text-yellow-200 font-bold text-[11px]">🟡 ${p._dupStatus === 'dup_batch' ? '檔內重複' : '完全重複'}</span>`;

        return `<tr class="hover:bg-slate-800/40 ${p._selected ? '' : 'opacity-45'}">
        <td class="py-2 px-2 text-center"><input type="checkbox" class="accent-emerald-500" ${p._selected ? 'checked' : ''} onchange="toggleProjPreviewCheck(${idx}, this.checked)" /></td>
        <td class="py-2 px-2">${badge}</td>
        <td class="py-2 px-2 font-bold text-white">${escHtml(p.title)}</td>
        <td class="py-2 px-2 text-slate-300">${escHtml(p.desc || '—')}</td>
        <td class="py-2 px-2 text-emerald-300">${escHtml(p.effect || '—')}</td>
        <td class="py-2 px-2 font-mono text-slate-300">${escHtml(p.eta || '—')}</td>
        <td class="py-2 px-2"><span class="px-2 py-0.5 rounded bg-slate-800 text-sky-300 font-semibold">${escHtml(p.status)}</span></td>
        <td class="py-2 px-2 text-center"><button type="button" onclick="removeProjPreviewItem(${idx})" class="text-slate-400 hover:text-rose-400">🗑️</button></td>
      </tr>`;
      })
      .join('');

    if (banner) {
      if (updCnt > 0 || dupCnt > 0) {
        banner.innerHTML = `🔄 智慧比對結果：🟢 新增 <strong>${newCnt}</strong> 筆 ｜ 🔵 將覆寫更新原專案 <strong>${updCnt}</strong> 筆（不產生重複列）｜ 🟡 預設略過重複 <strong>${dupCnt}</strong> 筆`;
        banner.classList.remove('hidden');
      } else {
        banner.classList.add('hidden');
      }
    }
  }

  window.toggleProjPreviewCheck = function (idx, checked) {
    if (state.projPreview[idx]) {
      state.projPreview[idx]._selected = Boolean(checked);
      renderProjPreview();
    }
  };

  window.removeProjPreviewItem = function (idx) {
    state.projPreview.splice(idx, 1);
    renderProjPreview();
  };

  window.clearProjPreview = function () {
    state.projPreview = [];
    renderProjPreview();
  };

  window.commitProjPreview = async function () {
    if (!state.projPreview.length) return;
    const selected = state.projPreview.filter((p) => p._selected);
    const skipped = state.projPreview.length - selected.length;
    if (!selected.length) {
      showToast('沒有勾選要寫入或更新的工作項目（重複列已預設略過）', 'warning');
      return;
    }

    const baseId = Date.now();
    const toSync = [];
    let addedCnt = 0;
    let updatedCnt = 0;

    selected.forEach((p, idx) => {
      if (p._dupStatus === 'update' && p._matchId) {
        const exist = state.projects.find((x) => x.id === p._matchId);
        if (exist) {
          exist.title = p.title || exist.title;
          exist.desc = p.desc || exist.desc;
          exist.effect = p.effect || exist.effect;
          exist.eta = p.eta || exist.eta;
          exist.status = p.status || exist.status;
          toSync.push({ ...exist });
          updatedCnt++;
          return;
        }
      }
      const newItem = {
        id: baseId + idx,
        title: p.title,
        desc: p.desc || '',
        effect: p.effect || '',
        eta: p.eta || '',
        status: p.status || '進行中',
      };
      state.projects.push(newItem);
      toSync.push(newItem);
      addedCnt++;
    });

    saveLocalState();
    await apiPost('/api/projects', { records: toSync }, `批次匯入/更新 ${toSync.length} 筆重要工作進度`);
    state.projPreview = [];
    renderProjPreview();
    renderProjectsTable();
    showToast(`完成：新增 ${addedCnt} 筆、更新既有專案 ${updatedCnt} 筆${skipped ? `，略過 ${skipped} 筆重複` : ''}！`, 'success');
  };

  window.setProjViewMode = function (mode) {
    state.projViewMode = mode;
    renderProjectsTable();
  };

  function renderProjectsTable() {
    const tbody = document.getElementById('projectTableBody');
    if (!tbody) return;
    const total = state.projects.length;
    const doneCount = state.projects.filter((p) => p.status === '已完成').length;
    const activeCount = total - doneCount;
    const pct = total ? Math.round((doneCount / total) * 100) : 0;

    document.getElementById('projectProgressSummary').textContent =
      `進行中 ${activeCount} 項 ｜ 已完成歸檔 ${doneCount} 項 (完成率 ${pct}%)`;

    const setBadge = (id, v) => {
      const el = document.getElementById(id);
      if (el) el.textContent = v;
    };
    setBadge('cntProjActive', activeCount);
    setBadge('cntProjDone', doneCount);
    setBadge('cntProjAll', total);

    const pillStyles = {
      active: ['btnProjTabActive', 'bg-sky-600 text-white shadow'],
      done: ['btnProjTabDone', 'bg-emerald-600 text-white shadow'],
      all: ['btnProjTabAll', 'bg-indigo-600 text-white shadow'],
    };
    Object.entries(pillStyles).forEach(([k, [btnId, activeCls]]) => {
      const btn = document.getElementById(btnId);
      if (!btn) return;
      btn.className =
        state.projViewMode === k
          ? `px-3.5 py-1.5 rounded-xl text-xs font-bold ${activeCls} transition flex items-center gap-1.5`
          : 'px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-800 text-slate-300 hover:text-white transition flex items-center gap-1.5';
    });

    // Update year filter options dynamically without resetting user selection
    const yrSel = document.getElementById('projYearFilter');
    if (yrSel) {
      const prevYr = yrSel.value || 'ALL';
      const groups = sortYearGroups(Array.from(new Set(state.projects.map(getProjectYearGroup))));
      yrSel.innerHTML =
        `<option value="ALL">全部年度（分年度群組）</option>` +
        groups.map((g) => `<option value="${g}">${formatProjectYearGroupLabel(g)}</option>`).join('');
      yrSel.value = prevYr === 'ALL' || groups.includes(prevYr) ? prevYr : 'ALL';
    }

    const selYr = yrSel?.value || 'ALL';
    const chkOngoing = document.getElementById('chkProjIncludeOngoing');
    const isNumericYr = /^20\d{2}$/.test(selYr);
    if (chkOngoing) {
      chkOngoing.disabled = !isNumericYr;
      if (chkOngoing.parentElement) chkOngoing.parentElement.classList.toggle('opacity-40', !isNumericYr);
    }
    const includeOngoing = chkOngoing ? chkOngoing.checked : true;
    const query = (document.getElementById('projSearch')?.value || '').trim().toLowerCase();

    const filtered = state.projects.filter((p) => {
      if (state.projViewMode === 'active' && p.status === '已完成') return false;
      if (state.projViewMode === 'done' && p.status !== '已完成') return false;

      const g = getProjectYearGroup(p);
      if (selYr !== 'ALL') {
        if (isNumericYr) {
          if (g !== selYr && !(includeOngoing && g === 'ONGOING')) return false;
        } else if (g !== selYr) {
          return false;
        }
      }

      if (query) {
        const hay = `${p.title} ${p.desc} ${p.effect} ${p.eta}`.toLowerCase();
        if (!hay.includes(query)) return false;
      }
      return true;
    });

    if (!filtered.length) {
      const hint =
        state.projViewMode === 'active'
          ? '目前條件下無進行中工作項目（已完成項目已獨立移至上方「✅ 已完成歸檔」分頁）'
          : '目前篩選條件下無符合的工作項目';
      tbody.innerHTML = `<tr><td colspan="7" class="py-8 text-center text-slate-400 text-xs">${hint}</td></tr>`;
      return;
    }

    const grouped = {};
    filtered.forEach((p) => {
      const g = getProjectYearGroup(p);
      if (!grouped[g]) grouped[g] = [];
      grouped[g].push(p);
    });
    const orderedGroups = sortYearGroups(Object.keys(grouped));

    let seq = 0;
    tbody.innerHTML = orderedGroups
      .map((gk) => {
        const items = grouped[gk];
        const headerRow = `<tr class="bg-slate-800/80 border-y border-slate-700">
          <td colspan="7" class="py-2 px-3 text-xs font-extrabold text-sky-300">
            ${formatProjectYearGroupLabel(gk)} <span class="text-slate-400 font-normal ml-1">(${items.length} 項)</span>
          </td>
        </tr>`;
        const rowsHtml = items
          .map((p) => {
            seq++;
            const stCls =
              p.status === '已完成'
                ? 'border-emerald-500/50 text-emerald-300'
                : p.status === '暫緩'
                ? 'border-rose-500/50 text-rose-300'
                : p.status === '評估中'
                ? 'border-amber-500/50 text-amber-300'
                : 'border-slate-700 text-white';
            return `<tr class="hover:bg-slate-800/40">
            <td class="py-2.5 px-2 font-mono text-slate-400">${seq}</td>
            <td class="py-2.5 px-3 font-bold text-white">${escHtml(p.title)}</td>
            <td class="py-2.5 px-3 text-xs text-slate-300">${escHtml(p.desc)}</td>
            <td class="py-2.5 px-3 text-xs text-emerald-300">${escHtml(p.effect)}</td>
            <td class="py-2.5 px-3 text-xs font-mono">${escHtml(p.eta)}</td>
            <td class="py-2.5 px-3">
              <select onchange="updateProjectStatus(${p.id}, this.value)" class="bg-slate-900 border ${stCls} rounded-lg px-2 py-1 text-xs font-semibold">
                ${['進行中', '已完成', '評估中', '暫緩'].map((st) => `<option value="${st}" ${p.status === st ? 'selected' : ''}>${st}</option>`).join('')}
              </select>
            </td>
            <td class="py-2.5 px-2 text-center">
              <button onclick="deleteProjectItem(${p.id})" class="text-xs text-slate-400 hover:text-rose-400">🗑️</button>
            </td>
          </tr>`;
          })
          .join('');
        return headerRow + rowsHtml;
      })
      .join('');
  }
  window.renderProjectsTable = renderProjectsTable;

  window.addProjectItem = async function (e) {
    e.preventDefault();
    const item = {
      id: Date.now(),
      title: document.getElementById('projTitle').value.trim(),
      desc: document.getElementById('projDesc').value.trim(),
      effect: document.getElementById('projEffect').value.trim(),
      eta: document.getElementById('projEta').value.trim(),
      status: '進行中',
    };
    state.projects.push(item);
    saveLocalState();
    await apiPost('/api/projects', item, '新增重要工作進度');
    ['projTitle', 'projDesc', 'projEffect', 'projEta'].forEach((id) => (document.getElementById(id).value = ''));
    renderProjectsTable();
    showToast('已新增重要工作項目', 'success');
  };

  window.updateProjectStatus = async function (id, status) {
    const p = state.projects.find((x) => x.id === id);
    if (!p) return;
    const prevStatus = p.status;
    p.status = status;
    saveLocalState();
    await apiPost('/api/projects', p, '更新專案狀態');
    renderProjectsTable();
    if (status === '已完成' && prevStatus !== '已完成' && state.projViewMode === 'active') {
      showToast(`已將「${p.title}」標記為已完成並移至「✅ 已完成歸檔」分頁！`, 'success');
    } else if (status !== '已完成' && prevStatus === '已完成' && state.projViewMode === 'done') {
      showToast(`已將「${p.title}」重啟並移回「🔥 進行中 / 追蹤中」！`, 'info');
    } else {
      showToast(`已更新「${p.title}」為 ${status}`, 'success');
    }
  };

  window.deleteProjectItem = async function (id) {
    state.projects = state.projects.filter((p) => p.id !== id);
    saveLocalState();
    if (state.apiOnline) {
      fetch(`/api/projects?id=${id}`, { method: 'DELETE' }).catch(() => {});
    }
    renderProjectsTable();
  };

  // ==================== 資料管理後台 (稽核 / 修改 / 刪除錯檔) ====================
  function getRecordFilename(r) {
    return r.filename || r.breakdown?._filename || (r.source === 'OFFICIAL_PPT' ? '預載官方基準' : '預載BI資料');
  }

  function renderAdminTable() {
    const tbody = document.getElementById('adminTableBody');
    if (!tbody) return;

    // Populate year filter
    const yrSel = document.getElementById('admYear');
    const prevYr = yrSel.value || 'ALL';
    const years = Array.from(new Set(state.metrics.map((m) => m.ym.slice(0, 4)))).sort().reverse();
    yrSel.innerHTML = `<option value="ALL">全部年份</option>` + years.map((y) => `<option value="${y}">${y} 年</option>`).join('');
    yrSel.value = prevYr === 'ALL' || years.includes(prevYr) ? prevYr : 'ALL';

    // Populate uploaded filenames for 1-click batch rollback
    const fileSel = document.getElementById('admBatchFile');
    const prevFile = fileSel.value;
    const fileCounts = {};
    for (const m of state.metrics) {
      const fn = getRecordFilename(m);
      fileCounts[fn] = (fileCounts[fn] || 0) + 1;
    }
    const fileEntries = Object.entries(fileCounts).sort((a, b) => a[0].localeCompare(b[0]));
    fileSel.innerHTML =
      `<option value="">-- 選擇來源檔名 --</option>` +
      fileEntries.map(([fn, cnt]) => `<option value="${fn.replace(/"/g, '&quot;')}">${fn} (${cnt}筆)</option>`).join('');
    if (prevFile && fileCounts[prevFile]) fileSel.value = prevFile;

    const fYear = yrSel.value;
    const fCat = document.getElementById('admCat').value;
    const fSrc = document.getElementById('admSource').value;
    const fQuery = (document.getElementById('admQuery').value || '').trim().toLowerCase();

    const filtered = state.metrics
      .filter((m) => {
        if (fYear !== 'ALL' && !m.ym.startsWith(fYear)) return false;
        if (fCat !== 'ALL' && m.category !== fCat) return false;
        if (fSrc !== 'ALL' && m.source !== fSrc) return false;
        if (fQuery) {
          const fn = getRecordFilename(m).toLowerCase();
          if (!m.ym.toLowerCase().includes(fQuery) && !fn.includes(fQuery)) return false;
        }
        return true;
      })
      .sort((a, b) => b.ym.localeCompare(a.ym) || a.category.localeCompare(b.category));

    document.getElementById('admSummaryText').textContent = `顯示 ${filtered.length} 筆 ／ 資料庫總計 ${state.metrics.length} 筆`;
    document.getElementById('admCheckAll').checked = false;

    const catMap = { inbound: '📦 進貨', outbound: '🚚 出貨', warehouse: '🏭 倉庫棧板' };
    tbody.innerHTML = filtered
      .map((m) => {
        const key = `${m.ym}|${m.category}|${m.source}`;
        const fn = getRecordFilename(m);
        return `<tr class="hover:bg-slate-800/50 transition">
          <td class="py-2 px-2 text-center">
            <input type="checkbox" class="adm-row-chk accent-rose-500" data-key="${key}" onchange="updateSelectedAdminCount()" />
          </td>
          <td class="py-2 px-3 font-bold text-white font-mono">${m.ym}</td>
          <td class="py-2 px-3">${catMap[m.category] || m.category}</td>
          <td class="py-2 px-3"><span class="text-[11px] px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-sky-300">${m.source}</span></td>
          <td class="py-2 px-3 text-xs text-slate-300 max-w-[180px] truncate" title="${fn}">${fn}</td>
          <td class="py-2 px-3 text-right font-mono">${fmtNum(m.mt, 2)}</td>
          <td class="py-2 px-3 text-right font-mono">${fmtNum(m.trips, 0)}</td>
          <td class="py-2 px-3 text-right font-mono">${fmtNum(m.pallets, 0)}</td>
          <td class="py-2 px-3 text-center space-x-1 whitespace-nowrap">
            <button onclick="openEditMetricModal('${m.ym}','${m.category}','${m.source}')" class="text-xs px-2 py-1 rounded bg-sky-600/30 hover:bg-sky-600 text-sky-200 hover:text-white transition" title="修改此筆">✏️</button>
            <button onclick="deleteSingleMetric('${m.ym}','${m.category}','${m.source}')" class="text-xs px-2 py-1 rounded bg-rose-600/30 hover:bg-rose-600 text-rose-200 hover:text-white transition" title="刪除此筆">🗑️</button>
          </td>
        </tr>`;
      })
      .join('');
    updateSelectedAdminCount();
  }

  window.renderAdminTable = renderAdminTable;

  window.updateSelectedAdminCount = function () {
    const cnt = document.querySelectorAll('.adm-row-chk:checked').length;
    const el = document.getElementById('selectedAdminCount');
    if (el) el.textContent = cnt;
  };

  window.toggleAdminCheckAll = function (checked) {
    document.querySelectorAll('.adm-row-chk').forEach((c) => (c.checked = checked));
    updateSelectedAdminCount();
  };

  window.openEditMetricModal = function (ym, category, source) {
    const rec = state.metrics.find((m) => m.ym === ym && m.category === category && m.source === source);
    if (!rec) return;
    document.getElementById('edYm').value = ym;
    document.getElementById('edCat').value = category;
    document.getElementById('edSource').value = source;
    document.getElementById('edMt').value = rec.mt ?? '';
    document.getElementById('edTrips').value = rec.trips ?? '';
    document.getElementById('edPallets').value = rec.pallets ?? '';
    document.getElementById('editMetricMeta').textContent = `目標紀錄：${ym} ｜ ${category} ｜ 口徑：${source}`;
    document.getElementById('editMetricModal').classList.remove('hidden');
  };

  window.closeEditMetricModal = function () {
    document.getElementById('editMetricModal').classList.add('hidden');
  };

  window.saveEditedMetric = async function (e) {
    e.preventDefault();
    const ym = document.getElementById('edYm').value;
    const category = document.getElementById('edCat').value;
    const source = document.getElementById('edSource').value;
    const rec = state.metrics.find((m) => m.ym === ym && m.category === category && m.source === source);
    if (!rec) return;

    rec.mt = document.getElementById('edMt').value !== '' ? Number(document.getElementById('edMt').value) : null;
    rec.trips = document.getElementById('edTrips').value !== '' ? Number(document.getElementById('edTrips').value) : null;
    rec.pallets = document.getElementById('edPallets').value !== '' ? Number(document.getElementById('edPallets').value) : null;

    saveLocalState();
    await pushMetricsBatch([rec], getRecordFilename(rec));
    closeEditMetricModal();
    renderAll();
    showToast(`已更新 ${ym} (${category}) 數據並同步雲端！`, 'success');
  };

  async function executeBatchDelete(keys) {
    if (!keys.length) return;
    const keySet = new Set(keys.map((k) => `${k.ym}|${k.category}|${k.source}`));
    state.metrics = state.metrics.filter((m) => !keySet.has(`${m.ym}|${m.category}|${m.source}`));
    saveLocalState();
    if (state.apiOnline) {
      await apiPost('/api/metrics', { action: 'delete_many', keys }, `批次刪除 ${keys.length} 筆月度資料`);
    }
    populateYearSelector();
    renderAll();
    showToast(`已成功移除 ${keys.length} 筆錯誤資料！`, 'success');
  }

  window.deleteSingleMetric = async function (ym, category, source) {
    if (!confirm(`確定要永久刪除這筆資料嗎？\n\n月份：${ym}\n類別：${category}\n口徑：${source}`)) return;
    await executeBatchDelete([{ ym, category, source }]);
  };

  window.deleteSelectedMetrics = async function () {
    const checked = Array.from(document.querySelectorAll('.adm-row-chk:checked'));
    if (!checked.length) {
      showToast('請先勾選要刪除的資料列', 'warning');
      return;
    }
    if (!confirm(`確定要永久刪除已勾選的 ${checked.length} 筆雲端資料嗎？`)) return;
    const keys = checked.map((c) => {
      const [ym, category, source] = c.dataset.key.split('|');
      return { ym, category, source };
    });
    await executeBatchDelete(keys);
  };

  window.rollbackByFilename = async function () {
    const fname = document.getElementById('admBatchFile').value;
    if (!fname) {
      showToast('請先選擇要整批撤銷的來源檔名', 'warning');
      return;
    }
    const matched = state.metrics.filter((m) => getRecordFilename(m) === fname);
    if (!matched.length) return;
    const monthsPreview = matched.map((m) => m.ym).slice(0, 6).join(', ') + (matched.length > 6 ? '...' : '');
    if (!confirm(`確定要一鍵撤銷整份檔案的上傳紀錄嗎？\n\n來源檔名：${fname}\n影響筆數：${matched.length} 筆（${monthsPreview}）`)) return;
    await executeBatchDelete(matched.map((m) => ({ ym: m.ym, category: m.category, source: m.source })));
  };

  // ==================== 設定與 Tab 切換 ====================
  function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach((b) => {
      b.classList.toggle('active', b.dataset.tab === tabName);
    });
    ['dashboard', 'warehouse', 'upload', 'report', 'alerts', 'management', 'projects', 'admin'].forEach((t) => {
      const el = document.getElementById(`tab-${t}`);
      if (el) el.classList.toggle('hidden', t !== tabName);
    });
    if (tabName === 'dashboard' || tabName === 'warehouse') {
      renderAll();
    }
  }

  window.openSettingsModal = function () {
    document.getElementById('inpGeminiKey').value = localStorage.getItem(STORAGE_KEYS.GEMINI_KEY) || '';
    document.getElementById('settingsModal').classList.remove('hidden');
  };
  window.closeSettingsModal = function () {
    document.getElementById('settingsModal').classList.add('hidden');
  };
  window.saveSettings = function () {
    localStorage.setItem(STORAGE_KEYS.GEMINI_KEY, document.getElementById('inpGeminiKey').value.trim());
    closeSettingsModal();
    showToast('設定已儲存！', 'success');
  };
  window.resetToSeedData = function () {
    if (!confirm('確定要重置為初始預載數據（2022–2026）嗎？')) return;
    localStorage.removeItem(STORAGE_KEYS.METRICS);
    localStorage.removeItem(STORAGE_KEYS.MGMT);
    localStorage.removeItem(STORAGE_KEYS.PROJECTS);
    loadLocalState();
    populateYearSelector();
    renderAll();
    closeSettingsModal();
    showToast('已還原初始預載數據', 'info');
  };
  window.refreshFromServer = detectApiAndSync;
  window.renderAll = renderAll;

  // ==================== PWA Service Worker & 離線同步 ====================
  function initPwa() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      state.deferredPrompt = e;
      document.getElementById('pwa-install-banner')?.classList.remove('hidden');
    });

    document.getElementById('btnPwaInstall')?.addEventListener('click', async () => {
      if (!state.deferredPrompt) return;
      state.deferredPrompt.prompt();
      await state.deferredPrompt.userChoice;
      state.deferredPrompt = null;
      document.getElementById('pwa-install-banner')?.classList.add('hidden');
    });

    if ('serviceWorker' in navigator && location.protocol.startsWith('http')) {
      navigator.serviceWorker
        .register('sw.js')
        .then((reg) => {
          reg.update();
          reg.onupdatefound = () => {
            const nw = reg.installing;
            if (!nw) return;
            nw.onstatechange = () => {
              if (nw.state === 'installed' && navigator.serviceWorker.controller) {
                document.getElementById('updateBanner')?.classList.remove('hidden');
              }
            };
          };
        })
        .catch(() => {});
    }

    if (window.OfflineSyncManager) {
      syncMgr = new OfflineSyncManager({
        storageKey: 'hs_report_offline_queue',
        badgeElementId: 'syncBadge',
      });
    }
  }

  // ==================== 啟動 ====================
  document.addEventListener('DOMContentLoaded', async () => {
    loadLocalState();
    populateYearSelector();

    document.getElementById('mgmtDate').value = new Date().toISOString().slice(0, 10);
    document.getElementById('rngThreshold').value = state.alertThreshold;
    document.getElementById('lblThreshold').textContent = state.alertThreshold;

    // Bind events
    document.querySelectorAll('.tab-btn').forEach((btn) =>
      btn.addEventListener('click', () => switchTab(btn.dataset.tab))
    );
    ['selScope', 'selYear', 'selSubPeriod', 'selCompareMode'].forEach((id) =>
      document.getElementById(id).addEventListener('change', renderAll)
    );
    document.getElementById('selPeriodType').addEventListener('change', () => {
      populateSubPeriodSelector();
      renderAll();
    });
    document.getElementById('rngThreshold').addEventListener('input', (e) => {
      state.alertThreshold = Number(e.target.value);
      localStorage.setItem(STORAGE_KEYS.THRESHOLD, state.alertThreshold);
      document.getElementById('lblThreshold').textContent = state.alertThreshold;
      renderAll();
    });

    // Drag & drop upload helper
    const bindUpload = (dzId, fiId, onFiles) => {
      const dzEl = document.getElementById(dzId);
      const fiEl = document.getElementById(fiId);
      if (!dzEl || !fiEl) return;
      dzEl.addEventListener('dragover', (e) => { e.preventDefault(); dzEl.classList.add('dragover'); });
      dzEl.addEventListener('dragleave', () => dzEl.classList.remove('dragover'));
      dzEl.addEventListener('drop', (e) => {
        e.preventDefault();
        dzEl.classList.remove('dragover');
        onFiles(e.dataTransfer.files);
      });
      fiEl.addEventListener('change', (e) => {
        onFiles(e.target.files);
        fiEl.value = '';
      });
    };

    bindUpload('dropZone', 'fileInput', handleFiles);
    bindUpload('mgmtDropZone', 'mgmtFileInput', (files) => handleStructuredFiles(files, 'mgmt'));
    bindUpload('projDropZone', 'projFileInput', (files) => handleStructuredFiles(files, 'proj'));

    initPwa();
    renderAll();
    await detectApiAndSync(false);
  });
})();
