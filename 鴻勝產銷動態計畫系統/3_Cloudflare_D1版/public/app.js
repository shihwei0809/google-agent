/**
 * 鴻勝產銷動態計畫系統 - 主控應用程式 (ES6)
 * 支援多人線上協作、Cloudflare D1 / 本機 SQLite 樂觀鎖同步、離線暫存補傳、
 * SheetJS 匯入與 ExcelJS 多頁跨表公式匯出。
 */
(function () {
  'use strict';

  const STORAGE_PLAN_KEY = 'sp_current_plan_v1';
  const STORAGE_META_KEY = 'sp_cloud_meta_v1';
  const STORAGE_OPERATOR_KEY = 'sp_operator_name_v1';
  const STORAGE_LOCAL_ARCHIVES_KEY = 'sp_local_archives_v1';
  const IS_FILE_MODE = window.location.protocol === 'file:';

  const state = {
    plan: cloneObj(window.DEFAULT_SALES_PLAN),
    calc: null,
    activeTab: 'summary',
    summaryFilter: 'all', // all | active | alerts | overrides
    summaryKindFilter: 'nonraw', // nonraw | all
    searchQuery: '',
    scheduleMonthIdx: 0,
    scheduleViewMode: 'month', // month | horizon
    cloudVersion: 0,
    cloudUpdatedBy: '初始範本',
    cloudUpdatedAt: '',
    isDirty: false,
    autoSaveTimer: null,
    operator: localStorage.getItem(STORAGE_OPERATOR_KEY) || '生管人員',
    deferredPrompt: null
  };

  let syncMgr = null;

  function cloneObj(o) {
    return JSON.parse(JSON.stringify(o));
  }

  function esc(str) {
    return String(str === null || str === undefined ? '' : str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function fmtNum(v, decimals = 2) {
    if (v === null || v === undefined || v === '') return '-';
    const n = Number(v);
    if (!Number.isFinite(n)) return '-';
    const factor = Math.pow(10, decimals);
    const rounded = Math.round(n * factor) / factor;
    return rounded.toLocaleString('zh-TW', { maximumFractionDigits: decimals });
  }

  function showToast(msg, ms = 2800) {
    const el = document.getElementById('toastMsg');
    if (!el) return;
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove('show'), ms);
  }

  function saveLocalDraft() {
    try {
      localStorage.setItem(STORAGE_PLAN_KEY, JSON.stringify(state.plan));
      localStorage.setItem(STORAGE_META_KEY, JSON.stringify({
        version: state.cloudVersion,
        updatedBy: state.cloudUpdatedBy,
        updatedAt: state.cloudUpdatedAt
      }));
    } catch (_) {}
  }

  function loadLocalDraft() {
    try {
      const raw = localStorage.getItem(STORAGE_PLAN_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.items)) {
          state.plan = parsed;
        }
      }
      const metaRaw = localStorage.getItem(STORAGE_META_KEY);
      if (metaRaw) {
        const m = JSON.parse(metaRaw);
        state.cloudVersion = Number(m.version || 0);
        state.cloudUpdatedBy = m.updatedBy || '本機暫存';
        state.cloudUpdatedAt = m.updatedAt || '';
      }
    } catch (_) {}
  }

  function recompute(summaryMsg = null) {
    state.calc = window.SalesPlannerEngine.recalculatePlan(state.plan);
    saveLocalDraft();
    renderAll();
    if (summaryMsg) scheduleCloudSave(summaryMsg);
  }

  function updateCloudBadge() {
    const el = document.getElementById('cloudVerBadge');
    if (!el) return;
    if (IS_FILE_MODE) {
      el.textContent = '📁 單機網頁模式 (本機自動儲存)';
      return;
    }
    const verTxt = state.cloudVersion > 0 ? `☁️ 雲端 v${state.cloudVersion}` : '☁️ 準備同步';
    const byTxt = state.cloudUpdatedBy ? ` · ${state.cloudUpdatedBy}` : '';
    const dirtyTxt = state.isDirty ? ' (未儲存*)' : '';
    el.textContent = verTxt + byTxt + dirtyTxt;
  }

  function scheduleCloudSave(summary = '線上更新產銷計畫') {
    state.isDirty = true;
    updateCloudBadge();
    if (IS_FILE_MODE) return;
    clearTimeout(state.autoSaveTimer);
    state.autoSaveTimer = setTimeout(() => pushPlanToCloud(false, summary, true), 1800);
  }

  async function apiFetch(url, options = {}) {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  }

  async function pullPlanFromCloud(autoSeedIfEmpty = true, isStartup = false) {
    if (IS_FILE_MODE) {
      updateCloudBadge();
      return;
    }
    if (isStartup && syncMgr && syncMgr.getQueue().length > 0) {
      updateCloudBadge();
      showToast(`偵測到 ${syncMgr.getQueue().length} 筆待補傳離線變更，將優先上傳同步`);
      return;
    }
    try {
      const { ok, data } = await apiFetch('/api/plan');
      if (!ok || !data.ok) throw new Error(data.error || '讀取失敗');
      if (data.exists && data.plan) {
        state.plan = data.plan;
        state.cloudVersion = Number(data.version || 1);
        state.cloudUpdatedBy = data.updatedBy || '系統';
        state.cloudUpdatedAt = data.updatedAt || '';
        state.isDirty = false;
        saveLocalDraft();
        recompute(null);
        showToast(`已同步雲端最新計畫 v${state.cloudVersion}`);
      } else if (autoSeedIfEmpty) {
        // Seed initial database with parsed baseline plan
        await pushPlanToCloud(true, '初次建立 20260511 基準產銷計畫', true);
      }
    } catch (err) {
      console.warn('無法連線至後端 API，使用本機暫存:', err);
      updateCloudBadge();
    }
  }

  async function pushPlanToCloud(force = false, summary = '更新產銷計畫', silent = false) {
    if (IS_FILE_MODE) {
      saveLocalDraft();
      if (!silent) showToast('已儲存至本機瀏覽器暫存');
      return;
    }
    const payload = {
      plan: state.plan,
      version: state.cloudVersion,
      force: !!force,
      updatedBy: state.operator || '線上人員',
      summary
    };

    try {
      const { ok, status, data } = await apiFetch('/api/plan', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      if (status === 409) {
        openConflictModal(data);
        return;
      }
      if (!ok || !data.ok) {
        throw new Error(data.error || `HTTP ${status}`);
      }
      state.cloudVersion = Number(data.version || state.cloudVersion + 1);
      state.cloudUpdatedBy = data.updatedBy || state.operator;
      state.cloudUpdatedAt = data.updatedAt || '';
      state.isDirty = false;
      saveLocalDraft();
      updateCloudBadge();
      if (syncMgr) syncMgr.updateBadge();
      if (!silent) showToast(`已儲存至雲端 (v${state.cloudVersion})`);
    } catch (err) {
      if (syncMgr) {
        syncMgr.enqueue({
          url: '/api/plan',
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payload,
          title: summary
        });
      }
      if (!silent) showToast('目前離線或連線異常，已寫入待補傳佇列');
    }
  }

  // ==================== Modal Helpers ====================
  function openModal(title, bodyHtml, footerHtml = '') {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = bodyHtml;
    document.getElementById('modalFooter').innerHTML = footerHtml;
    document.getElementById('appModal').classList.add('open');
  }

  function closeModal() {
    document.getElementById('appModal').classList.remove('open');
  }

  function openConflictModal(conflictData) {
    const body = `
      <div style="background:#fef2f2;border:1px solid #fecaca;padding:12px;border-radius:8px;color:#991b1b;margin-bottom:12px;">
        <strong>⚠️ 偵測到多人同時編輯衝突！</strong><br/>
        ${esc(conflictData.message || '')}<br/>
        <span style="font-size:12px;">雲端時間：${esc(conflictData.serverUpdatedAt || '')}</span>
      </div>
      <p>您可以選擇：</p>
      <ul style="margin:6px 0 0 18px;font-size:12.5px;">
        <li><strong>拉取雲端最新版：</strong>放棄自己剛剛未存的畫面變更，載入「${esc(conflictData.serverUpdatedBy)}」的版本。</li>
        <li><strong>強制覆寫雲端：</strong>以目前畫面上的計畫強行覆蓋為最新雲端版本 v${Number(conflictData.serverVersion || 0) + 1}。</li>
      </ul>`;
    const ftr = `
      <button id="btnPullServerConflict" class="btn btn-teal">📥 拉取雲端最新版</button>
      <button id="btnForcePushConflict" class="btn btn-danger">⚠️ 強制覆寫雲端</button>`;
    openModal('版本同步衝突', body, ftr);
    document.getElementById('btnPullServerConflict').onclick = () => {
      if (conflictData.serverPlan) {
        state.plan = conflictData.serverPlan;
        state.cloudVersion = conflictData.serverVersion;
        state.cloudUpdatedBy = conflictData.serverUpdatedBy;
        state.cloudUpdatedAt = conflictData.serverUpdatedAt;
        state.isDirty = false;
        recompute(null);
      }
      closeModal();
      showToast('已拉取雲端最新版本');
    };
    document.getElementById('btnForcePushConflict').onclick = async () => {
      closeModal();
      await pushPlanToCloud(true, '強制覆寫解決協作衝突', false);
    };
  }

  // ==================== Rendering ====================
  function renderAll() {
    if (!state.calc) state.calc = window.SalesPlannerEngine.recalculatePlan(state.plan);
    const bd = document.getElementById('baseDateInput');
    if (bd && state.plan.meta && state.plan.meta.baseDate) {
      bd.value = state.plan.meta.baseDate;
    }
    updateCloudBadge();
    renderKpiGrid();
    renderTabs();
    renderWorkspace();
  }

  function renderKpiGrid() {
    const s = state.calc.stats;
    const grid = document.getElementById('kpiGrid');
    const cards = [
      { id: 'all', cls: '', label: '管理品項總數', val: s.totalItems, sub: '含精餾/充填/初餾/調配/原料', action: () => { state.activeTab = 'summary'; state.summaryFilter = 'all'; } },
      { id: 'critical', cls: 'k-red', label: '🔴 負庫存 / 缺料預警', val: s.criticalCount, sub: '點選立即篩選缺料品項', action: () => { state.activeTab = 'summary'; state.summaryFilter = 'alerts'; } },
      { id: 'over', cls: 'k-orange', label: '🟠 超出儲槽容量', val: s.overCapCount, sub: '年末/月末 > 槽體容量', action: () => { state.activeTab = 'summary'; state.summaryFilter = 'alerts'; } },
      { id: 'min', cls: 'k-amber', label: '🟡 低於安全庫存', val: s.belowMinCount, sub: '月末結存 < 安全最低量', action: () => { state.activeTab = 'summary'; state.summaryFilter = 'alerts'; } },
      { id: 'conflict', cls: 'k-red', label: '⚡ 塔槽排程重疊/避讓', val: s.conflictCount, sub: '點選切換甘特圖排程', action: () => { state.activeTab = 'schedule'; } },
      { id: 'override', cls: '', label: '✍️ 手動覆寫與特規調整', val: s.overrideCount, sub: '點此查看含手動覆寫欄位', action: () => { state.activeTab = 'summary'; state.summaryFilter = 'overrides'; } }
    ];
    grid.innerHTML = cards.map((c) => `
      <div class="kpi-card ${c.cls}" data-kpi="${esc(c.id)}">
        <div class="kpi-label">${esc(c.label)}</div>
        <div class="kpi-value">${c.val}</div>
        <div class="kpi-sub">${esc(c.sub)}</div>
      </div>`).join('');

    cards.forEach((c) => {
      const el = grid.querySelector(`[data-kpi="${c.id}"]`);
      if (el) el.onclick = () => { c.action(); renderAll(); };
    });
  }

  function renderTabs() {
    const bar = document.getElementById('tabsBar');
    bar.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.tab === state.activeTab);
    });
  }

  function renderWorkspace() {
    const ws = document.getElementById('workspace');
    if (state.activeTab === 'summary') ws.innerHTML = buildSummaryHtml();
    else if (state.activeTab === 'rectification') ws.innerHTML = buildProcessHtml('精餾', '🏭 精餾與充填產銷計劃表');
    else if (state.activeTab === 'primary') ws.innerHTML = buildProcessHtml('初餾', '🧪 初餾產銷計劃表（含代工入庫正向累計）');
    else if (state.activeTab === 'blending') ws.innerHTML = buildProcessHtml('調配', '⚗️ 調配產銷計劃表（與精餾 EGUPS 即時連動）');
    else if (state.activeTab === 'schedule') ws.innerHTML = buildScheduleHtml();
    else if (state.activeTab === 'bom') ws.innerHTML = buildBomHtml();

    bindWorkspaceEvents();
  }

  function buildEndStockCellHtml(item, mCell) {
    const cls = (mCell.alerts && mCell.alerts.length) ? mCell.alerts[0] : '';
    let pctBar = '';
    if (item.capacity > 0) {
      const pct = Math.max(0, Math.min(100, mCell.capPct || 0));
      const fillCls = (mCell.endStock > item.capacity) ? 'danger' : (mCell.endStock < 0 ? 'danger' : (pct > 85 ? 'warn' : ''));
      pctBar = `<div class="cap-bar-wrap" title="儲槽利用率 ${fmtNum(mCell.capPct, 1)}% (${fmtNum(mCell.endStock)} / ${item.capacity})"><div class="cap-bar-fill ${fillCls}" style="width:${pct}%"></div></div>`;
    }
    return `
      <span class="end-stock-pill ${cls}" title="期末結存 ${fmtNum(mCell.endStock, 3)} MT">${fmtNum(mCell.endStock, 2)}</span>
      ${pctBar}`;
  }

  function buildUsageCellHtml(item, mIdx, mCell) {
    const hasBom = mCell.bomUsage > 0 || (state.calc.bomBreakdownByTarget[item.name] && state.calc.bomBreakdownByTarget[item.name].length > 0);
    if (mCell.isUsageOverridden) {
      return `
        <div class="num-override" title="已手動覆寫耗用（公式原值=${fmtNum(mCell.directUsage + mCell.bomUsage, 3)}）">
          <input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mIdx}" data-field="usageOverride" type="number" step="0.001" value="${esc(item.months[mIdx].usageOverride)}" />
          <button class="btn btn-xs js-reset-usage" data-id="${esc(item.id)}" data-m="${mIdx}" title="還原為自動 BOM 公式">↺</button>
        </div>`;
    }
    if (hasBom) {
      return `
        <div style="display:inline-flex;align-items:center;gap:3px;">
          <span class="num-auto js-show-bom" data-name="${esc(item.name)}" data-m="${mIdx}" title="BOM自動計算=${fmtNum(mCell.bomUsage, 3)}；點擊查看來源組成">${fmtNum(mCell.effectiveUsage, 3)}</span>
          <button class="btn btn-xs js-enable-usage-ov" data-id="${esc(item.id)}" data-m="${mIdx}" title="手動覆寫本月總耗用（例如短期停車1~2天微調）">✍️</button>
        </div>`;
    }
    return `<input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mIdx}" data-field="directUsage" type="number" step="0.1" value="${esc(mCell.directUsage)}" />`;
  }

  function renderPlanRowsHtml(itemsList, options = {}) {
    const { showContractIn = false, showRawCols = false, compactMode = false } = options;
    const months = state.calc.monthsMeta;
    const lineOptions = (state.plan.lines || []).map((l) => l.id);

    const headColsTop = `
      <tr>
        <th class="col-sticky-1" rowspan="2">品名 / 儲槽 / 容量</th>
        <th rowspan="2">資材</th>
        <th rowspan="2">製2</th>
        <th rowspan="2">桶底</th>
        <th rowspan="2">期初可用</th>
        ${months.map((m) => `<th colspan="${compactMode ? 4 : (showRawCols ? 6 : (showContractIn ? 8 : 7))}">${esc(m.label)} (${esc(m.periodLabel)})</th>`).join('')}
        <th colspan="2">安全庫存 / 操作</th>
      </tr>
      <tr class="subhdr">
        ${months.map(() => {
          if (compactMode) {
            return `<th>銷售(-)</th><th>總耗用(-)</th><th>自產/入庫(+)</th><th>月末結存</th>`;
          }
          if (showRawCols) {
            return `<th>銷售(-)</th><th>進貨(+)</th><th>其他/回收(+)</th><th>總耗用(-)</th><th>手動調整</th><th>月末結存</th>`;
          }
          return `<th>銷售(-)</th>${showContractIn ? '<th>代工入庫(+)</th>' : ''}<th>總耗用(-)</th><th>線別</th><th>排程區間</th><th>自產量(+)</th><th>調整(+/-)</th><th>月末結存</th>`;
        }).join('')}
        <th>安全最低</th>
        <th>明細</th>
      </tr>`;

    const rowsHtml = itemsList.map((item) => {
      const w = state.calc.computedById[item.id];
      const tagCls = item.kind === 'raw' ? 'tag-raw' : (item.kind === 'filling' ? 'tag-fill' : 'tag-proc');
      const kindLbl = item.kind === 'raw' ? '原料' : (item.kind === 'filling' ? '充填' : item.process);
      const bugTag = item.sourceBugNote ? `<span class="tag tag-fix" title="${esc(item.sourceBugNote)}">已修Excel錯位</span>` : '';
      const ovOpenTag = w.isOpeningOverridden ? `<span class="tag tag-warn" title="Excel原值固定期初 (${w.opening})，系統公式應為 ${fmtNum(w.autoOpening, 2)}">固定期初</span>` : '';
      const rollupBadge = item.rollupTo ? `<span class="tag tag-proc" title="可將產量併入 ${esc(item.rollupTo)} 結存">↳ 併入 ${esc(item.rollupTo)}</span>` : '';

      const monthCells = [0, 1, 2, 3].map((mi) => {
        const mr = (item.months && item.months[mi]) || {};
        const mc = w.months[mi];
        const endHtml = buildEndStockCellHtml(item, mc);
        const useHtml = buildUsageCellHtml(item, mi, mc);

        if (compactMode) {
          const totalIn = mc.effectiveProdQty + mc.childRollupProd + mc.purchase + mc.effectiveOtherIn + mc.contractIn;
          return `
            <td><input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="sales" type="number" step="0.1" value="${esc(mr.sales || 0)}" /></td>
            <td>${useHtml}</td>
            <td style="text-align:right;">
              ${item.kind === 'raw'
                ? `<input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="purchase" type="number" step="0.1" value="${esc(mr.purchase || 0)}" title="進貨量" />`
                : (mr.prodFormulaMode === 'sales_plus_usage'
                    ? `<span class="num-auto" title="充填自動 = 銷售+耗用；點明細可切換">${fmtNum(mc.effectiveProdQty, 1)}</span>`
                    : `<input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="prodQty" type="number" step="0.1" value="${esc(mr.prodQty || 0)}" />`)}
              ${mc.childRollupProd > 0 ? `<div style="font-size:10px;color:#0369a1;">+併入 ${fmtNum(mc.childRollupProd)}</div>` : ''}
            </td>
            <td style="text-align:center;">${endHtml}</td>`;
        }

        if (showRawCols) {
          const recHtml = mc.autoOtherIn > 0
            ? `<div style="font-size:10px;color:#0d9488;" title="自動回收/轉入量">+自動 ${fmtNum(mc.autoOtherIn, 1)}</div>`
            : '';
          return `
            <td><input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="sales" type="number" step="0.1" value="${esc(mr.sales || 0)}" /></td>
            <td><input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="purchase" type="number" step="0.1" value="${esc(mr.purchase || 0)}" /></td>
            <td>
              <input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="otherIn" type="number" step="0.1" value="${esc(mr.otherIn || 0)}" />
              ${recHtml}
            </td>
            <td>${useHtml}</td>
            <td><input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="adjBalance" type="number" step="0.1" value="${esc(mr.adjBalance || 0)}" title="${esc(mr.adjNote || '單月手動額外加減')}" /></td>
            <td style="text-align:center;">${endHtml}</td>`;
        }

        // Full Process Finished Product columns
        const curLine = mr.line || '';
        const optsList = lineOptions.includes(curLine) || !curLine ? lineOptions : [curLine, ...lineOptions];
        const prodCell = mr.prodFormulaMode === 'sales_plus_usage'
          ? `<span class="num-auto js-toggle-fillmode" data-id="${esc(item.id)}" data-m="${mi}" title="充填自動 = 銷售+耗用；點擊可切換手動輸入">${fmtNum(mc.effectiveProdQty, 1)}</span>`
          : `<input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="prodQty" type="number" step="0.1" value="${esc(mr.prodQty || 0)}" />
             ${mc.childRollupProd > 0 ? `<div style="font-size:10px;color:#0369a1;">+併入 ${fmtNum(mc.childRollupProd)}</div>` : ''}`;

        return `
          <td><input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="sales" type="number" step="0.1" value="${esc(mr.sales || 0)}" /></td>
          ${showContractIn ? `<td><input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="contractIn" type="number" step="0.1" value="${esc(mr.contractIn || 0)}" /></td>` : ''}
          <td>${useHtml}</td>
          <td>
            <select class="cell-select js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="line">
              <option value="">-</option>
              ${optsList.map((ln) => `<option value="${esc(ln)}" ${ln === curLine ? 'selected' : ''}>${esc(ln)}</option>`).join('')}
            </select>
          </td>
          <td>
            <input class="cell-input wide js-edit-cell" style="width:74px;font-size:11px;" data-id="${esc(item.id)}" data-m="${mi}" data-field="periodStr" type="text" placeholder="1~31" value="${esc((mr.periodStr || '').replace(/\n/g, ','))}" title="支援多段天期如 11~12,18~22；已排 ${mc.scheduleDayCount} 天" />
            ${mc.scheduleDayCount > 0 ? `<div style="font-size:10px;color:#475569;">${mc.scheduleDayCount}天</div>` : ''}
          </td>
          <td>${prodCell}</td>
          <td>
            <input class="cell-input tiny js-edit-cell" data-id="${esc(item.id)}" data-m="${mi}" data-field="adjBalance" type="number" step="0.1" value="${esc(mr.adjBalance || 0)}" title="${esc(mr.adjNote || '期末調整(+/-)')}" />
          </td>
          <td style="text-align:center;">${endHtml}</td>`;
      }).join('');

      const rollupBtns = item.rollupTo ? `
        <div style="margin-top:3px;font-size:10.5px;">
          併入月:
          ${[0, 1, 2, 3].map((mi) => `<label style="margin-right:4px;cursor:pointer;"><input type="checkbox" class="js-toggle-rollup" data-id="${esc(item.id)}" data-m="${mi}" ${item.rollupMonths && item.rollupMonths[mi] ? 'checked' : ''} />${months[mi].label}</label>`).join('')}
        </div>` : '';

      return `
        <tr data-row-id="${esc(item.id)}">
          <td class="col-sticky-1">
            <div style="font-weight:800;font-size:12.5px;color:#0f172a;">
              <span class="tag ${tagCls}">${esc(kindLbl)}</span>${esc(item.name)}
            </div>
            <div style="font-size:10.5px;color:#475569;margin-top:2px;">
              ${esc(item.tanks || '未設儲槽')} ${item.capacity ? `· <b>${item.capacity} MT</b>` : ''}
            </div>
            <div>${ovOpenTag}${bugTag}${rollupBadge}</div>
            ${rollupBtns}
          </td>
          <td><input class="cell-input tiny js-edit-item" data-id="${esc(item.id)}" data-field="invMaterial" type="number" step="0.1" value="${esc(item.invMaterial || 0)}" /></td>
          <td><input class="cell-input tiny js-edit-item" data-id="${esc(item.id)}" data-field="invProcess2" type="number" step="0.1" value="${esc(item.invProcess2 || 0)}" /></td>
          <td><input class="cell-input tiny js-edit-item" data-id="${esc(item.id)}" data-field="tankBottom" type="number" step="0.1" value="${esc(item.tankBottom || 0)}" /></td>
          <td style="text-align:right;font-weight:700;cursor:pointer;" class="js-open-item" data-id="${esc(item.id)}" title="點擊編輯固定期初或儲槽上限">
            ${fmtNum(w.opening, 2)}
          </td>
          ${monthCells}
          <td><input class="cell-input tiny js-edit-item" data-id="${esc(item.id)}" data-field="safetyMin" type="number" step="0.1" placeholder="-" value="${item.safetyMin !== null && item.safetyMin !== undefined ? esc(item.safetyMin) : ''}" /></td>
          <td><button class="btn btn-xs js-open-item" data-id="${esc(item.id)}">⚙️明細</button></td>
        </tr>`;
    }).join('');

    return `
      <div class="table-scroll">
        <table class="plan-table">
          <thead>${headColsTop}</thead>
          <tbody>${rowsHtml || '<tr><td colspan="40" style="text-align:center;padding:24px;color:#64748b;">無符合條件的資料列</td></tr>'}</tbody>
        </table>
      </div>`;
  }

  function buildSummaryHtml() {
    const q = state.searchQuery.trim().toLowerCase();
    let list = state.plan.items.filter((it) => {
      if (state.summaryKindFilter === 'nonraw' && it.kind === 'raw') return false;
      const w = state.calc.computedById[it.id];
      if (state.summaryFilter === 'active' && !it.showInSummary) return false;
      if (state.summaryFilter === 'alerts') {
        const hasAlert = w.months.some((m) => m.alerts && m.alerts.length > 0);
        if (!hasAlert) return false;
      }
      if (state.summaryFilter === 'overrides') {
        const hasOv = w.isOpeningOverridden || w.months.some((m) => m.isUsageOverridden || m.isOtherInOverridden || m.adjBalance !== 0);
        if (!hasOv) return false;
      }
      if (q) {
        const hay = `${it.name} ${it.tanks || ''} ${it.process} ${it.section}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    const topAlerts = (state.calc.alerts || []).slice(0, 8);
    const alertPanel = topAlerts.length ? `
      <div class="panel">
        <div class="panel-hdr">
          <div class="panel-title">🚨 即時預警摘要（前 ${topAlerts.length} / 共 ${state.calc.alerts.length} 項）</div>
          <span style="font-size:11.5px;color:#64748b;">點擊「前往」可直接檢視與修改排產</span>
        </div>
        <div class="alert-list">
          ${topAlerts.map((a) => `
            <div class="alert-item ${esc(a.severity)}">
              <span>${esc(a.message)}</span>
              <button class="btn btn-xs js-open-item" data-id="${esc(a.itemId)}">調整</button>
            </div>`).join('')}
        </div>
      </div>` : '';

    return `
      ${alertPanel}
      <div class="toolbar">
        <div class="filter-group">
          <span style="font-weight:700;">範圍：</span>
          <button class="chip ${state.summaryKindFilter === 'nonraw' ? 'active' : ''}" data-skind="nonraw">成品與充填</button>
          <button class="chip ${state.summaryKindFilter === 'all' ? 'active' : ''}" data-skind="all">全部含原料 (${state.plan.items.length})</button>
          <span style="margin-left:8px;font-weight:700;">狀態：</span>
          <button class="chip ${state.summaryFilter === 'all' ? 'active' : ''}" data-sfilter="all">全部</button>
          <button class="chip ${state.summaryFilter === 'active' ? 'active' : ''}" data-sfilter="active">僅有異動量</button>
          <button class="chip ${state.summaryFilter === 'alerts' ? 'active' : ''}" data-sfilter="alerts">僅看預警 🔴🟠🟡</button>
          <button class="chip ${state.summaryFilter === 'overrides' ? 'active' : ''}" data-sfilter="overrides">含手動覆寫 ✍️</button>
        </div>
        <div class="filter-group">
          <input id="summarySearchInput" class="search-input" type="text" placeholder="搜尋品名、儲槽 (如 EGUPS, TK604)..." value="${esc(state.searchQuery)}" />
          <button id="btnAddNewItem" class="btn btn-primary">➕ 新增品項</button>
        </div>
      </div>
      <div class="panel">
        <div class="panel-hdr">
          <div class="panel-title">📊 產銷動態總表（共 ${list.length} 項｜直接點黃底格即可修改並自動重算全廠 BOM）</div>
          <span style="font-size:11.5px;color:#475569;">點擊藍色 BOM 數字旁「✍️」可單月手動覆寫耗用；期初公式 = MAX(0, 資材+製2-桶底)</span>
        </div>
        ${renderPlanRowsHtml(list, { compactMode: true })}
      </div>`;
  }

  function buildProcessHtml(processName, title) {
    const prods = state.plan.items.filter((it) => it.process === processName && it.kind !== 'raw');
    let raws = state.plan.items.filter((it) => it.process === processName && it.kind === 'raw');

    // In 調配產銷, include EGUPS (linked directly from 精餾產銷) at top of Blending Raw Materials!
    let crossLinkedHtml = '';
    if (processName === '調配') {
      const egups = state.plan.items.find((x) => x.name === 'EGUPS');
      if (egups) {
        raws = [egups, ...raws];
        crossLinkedHtml = `<div style="padding:8px 14px;background:#eff6ff;border-bottom:1px solid #bfdbfe;font-size:12px;color:#1e40af;">
          🔗 <strong>跨製程即時連動：</strong>調配區「EGUPS」原料直接同步連結精餾成品「EGUPS」，任一處調整 NSE/ACT790 排產或 S02 自產，庫存即時雙向一致。
        </div>`;
      }
    }

    const extraBtn = processName === '初餾'
      ? `<span class="tag tag-fix">已修正原 Excel「代工入庫」加減方向：本表代工入庫(+)將正向增加結存</span>`
      : '';

    return `
      <div class="panel">
        <div class="panel-hdr">
          <div class="panel-title">${esc(title)} - 成品與排產區 (${prods.length} 項) ${extraBtn}</div>
          <button id="btnAddNewItem" class="btn btn-xs btn-primary">➕ 新增本製程品項</button>
        </div>
        ${renderPlanRowsHtml(prods, { showContractIn: processName === '初餾', showRawCols: false, compactMode: false })}
      </div>
      <div class="panel">
        <div class="panel-hdr">
          <div class="panel-title">🧪 ${esc(processName)}專屬原料消耗與進貨計劃 (${raws.length} 項)</div>
          <span style="font-size:11.5px;color:#475569;">點擊藍色「總耗用(-)」數字可展開上游產品展開公式；點 ✍️ 可暫時覆寫單月用量</span>
        </div>
        ${crossLinkedHtml}
        ${renderPlanRowsHtml(raws, { showRawCols: true, compactMode: false })}
      </div>`;
  }

  function buildScheduleHtml() {
    const mIdx = state.scheduleMonthIdx;
    const mMeta = state.calc.monthsMeta[mIdx];
    const lines = ['S01', 'S02', 'S03', 'R01', 'R02', '參配', 'S07', '充填', '外購', '委外加工'];
    const isHorizon = state.scheduleViewMode === 'horizon';
    const conflicts = isHorizon ? state.calc.conflicts : state.calc.conflicts.filter((c) => c.monthIdx === mIdx);

    const BAR_COLORS = [
      '#2563eb', '#0d9488', '#7c3aed', '#0284c7',
      '#059669', '#4f46e5', '#c026d3', '#d97706'
    ];
    function colorForItem(name) {
      let h = 0;
      const s = String(name || '');
      for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
      return BAR_COLORS[h % BAR_COLORS.length];
    }
    function daysToSegments(daysArr) {
      if (!daysArr || !daysArr.length) return [];
      const sorted = Array.from(new Set(daysArr)).sort((a, b) => a - b);
      const segs = [];
      let start = sorted[0];
      let end = sorted[0];
      for (let i = 1; i < sorted.length; i++) {
        if (sorted[i] === end + 1) {
          end = sorted[i];
        } else {
          segs.push({ start, end });
          start = end = sorted[i];
        }
      }
      segs.push({ start, end });
      return segs;
    }

    let ganttChartHtml = '';
    if (!isHorizon) {
      // Single-month horizontal Gantt timeline bars (1..endDay)
      const totalDays = mMeta.endDay || 31;
      const ticks = [];
      for (let d = 1; d <= totalDays; d++) ticks.push(`<div class="gantt-tick">${d}</div>`);

      const laneBlocks = lines.map((ln) => {
        const ents = state.calc.scheduleEntriesByLineMonth[`${ln}|${mIdx}`] || [];
        if (ents.length === 0 && !['S01', 'S02', 'S03', 'R01', 'R02', '參配'].includes(ln)) return '';
        const isExclusive = ['S01', 'S02', 'S03', 'R01', 'R02'].includes(ln);

        // Compute overlapping day sets on exclusive continuous lines
        const dayCounts = {};
        ents.forEach((e) => e.days.forEach((d) => { dayCounts[d] = (dayCounts[d] || 0) + 1; }));
        const conflictDays = isExclusive
          ? Object.keys(dayCounts).map(Number).filter((d) => dayCounts[d] > 1)
          : [];
        const conflictBandsHtml = daysToSegments(conflictDays).map((seg) => {
          const leftPct = ((seg.start - 1) / totalDays) * 100;
          const widthPct = ((seg.end - seg.start + 1) / totalDays) * 100;
          return `<div class="gantt-overlap-band" style="left:${leftPct.toFixed(3)}%;width:${widthPct.toFixed(3)}%;" title="第 ${seg.start}${seg.end > seg.start ? '~' + seg.end : ''} 日同塔重疊排產"></div>`;
        }).join('');

        const totalLineQty = ents.reduce((acc, e) => acc + (e.prodQty || 0), 0);
        const laneHdr = `
          <div class="gantt-lane-hdr">
            <div class="gantt-label-col">
              <span>${esc(ln)} 產線</span>
              <span style="font-size:10.5px;color:#475569;font-weight:600;">${ents.length} 筆 · ${fmtNum(totalLineQty, 0)} MT</span>
            </div>
            <div class="gantt-track" style="--days:${totalDays};">
              ${conflictBandsHtml}
            </div>
          </div>`;

        if (ents.length === 0) {
          return laneHdr + `
            <div class="gantt-row">
              <div class="gantt-label-col" style="color:#94a3b8;font-weight:400;">（本區間無排產）</div>
              <div class="gantt-track" style="--days:${totalDays};"><div class="gantt-baseline"></div></div>
            </div>`;
        }

        const itemRows = ents.map((e) => {
          const isFallbackFull = !e.days || e.days.length === 0;
          const segs = isFallbackFull ? [{ start: 1, end: totalDays }] : daysToSegments(e.days);
          const bg = isFallbackFull ? '#64748b' : colorForItem(e.itemName);
          const hasConflict = isExclusive && !isFallbackFull && e.days.some((d) => conflictDays.includes(d));
          const barsHtml = segs.map((seg) => {
            const leftPct = ((seg.start - 1) / totalDays) * 100;
            const widthPct = ((seg.end - seg.start + 1) / totalDays) * 100;
            const spanDays = seg.end - seg.start + 1;
            const rangeLbl = isFallbackFull
              ? `${e.periodStr ? e.periodStr.replace(/\n/g, ',') : '全月'} · 未分日`
              : (seg.start === seg.end ? `${seg.start}日` : `${seg.start}~${seg.end}日`);
            const innerTxt = spanDays >= 5 ? `${e.itemName} (${rangeLbl} · ${fmtNum(e.prodQty, 0)}MT)` : (spanDays >= 2 ? rangeLbl : '');
            const outLbl = spanDays < 5
              ? `<span class="gantt-bar-label-outside" style="left:calc(${(leftPct + widthPct).toFixed(3)}% + 5px);">${esc(e.itemName)} (${rangeLbl})</span>`
              : '';
            return `
              <div class="gantt-bar ${hasConflict ? 'is-conflict' : ''} js-edit-sched"
                   data-id="${esc(e.itemId)}" data-m="${mIdx}"
                   style="left:${leftPct.toFixed(3)}%;width:calc(${widthPct.toFixed(3)}% - 2px);background:${bg};${isFallbackFull ? 'opacity:0.75;' : ''}"
                   title="${esc(e.itemName)} | ${esc(ln)} | ${rangeLbl} | ${fmtNum(e.prodQty, 1)} MT — 點擊調整排程">
                ${hasConflict ? '⚡ ' : ''}${esc(innerTxt)}
              </div>${outLbl}`;
          }).join('');

          return `
            <div class="gantt-row">
              <div class="gantt-label-col js-edit-sched" data-id="${esc(e.itemId)}" data-m="${mIdx}" style="cursor:pointer;" title="點擊編輯 ${esc(e.itemName)} 排程">
                <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${esc(e.itemName)}</span>
                <span style="font-size:11px;color:#0369a1;flex-shrink:0;">${fmtNum(e.prodQty, 0)} MT</span>
              </div>
              <div class="gantt-track" style="--days:${totalDays};">
                <div class="gantt-baseline"></div>
                ${conflictBandsHtml}
                ${barsHtml}
              </div>
            </div>`;
        }).join('');

        return laneHdr + itemRows;
      }).join('');

      ganttChartHtml = `
        <div class="panel">
          <div class="panel-hdr">
            <div class="panel-title">📅 ${esc(mMeta.label)} 產線甘特條圖時間軸 (1~${totalDays} 日)</div>
            <span style="font-size:11px;color:#64748b;">水平線條為實際連續排產日段；紅底斜線與紅框＝同塔重疊；點擊任一色條即可編輯排程</span>
          </div>
          <div class="table-scroll" style="max-height:64vh;">
            <div class="gantt-board">
              <div class="gantt-header">
                <div class="gantt-label-col">產線 / 產品品項</div>
                <div class="gantt-ruler">${ticks.join('')}</div>
              </div>
              ${laneBlocks}
            </div>
          </div>
        </div>`;
    } else {
      // 4-Month continuous horizon Gantt view
      const monthsMeta = state.calc.monthsMeta;
      const monthOffsets = [];
      let totalHorizonDays = 0;
      monthsMeta.forEach((mm) => {
        const dCount = mm.endDay || 30;
        monthOffsets.push({ offset: totalHorizonDays, days: dCount, meta: mm });
        totalHorizonDays += dCount;
      });

      const monthHdrTicks = monthOffsets.map((mo) =>
        `<div class="gantt-month-tick" style="flex:${mo.days};">${esc(mo.meta.label)} (${esc(mo.meta.periodLabel)})</div>`
      ).join('');

      const monthDividersHtml = monthOffsets.slice(1).map((mo) =>
        `<div style="position:absolute;left:${((mo.offset / totalHorizonDays) * 100).toFixed(3)}%;top:0;bottom:0;border-left:1px dashed #cbd5e1;pointer-events:none;"></div>`
      ).join('');

      const laneBlocks = lines.map((ln) => {
        // Group unique items scheduled across any of the 4 months on this line
        const byItem = {};
        for (let mi = 0; mi < 4; mi++) {
          const ents = state.calc.scheduleEntriesByLineMonth[`${ln}|${mi}`] || [];
          ents.forEach((e) => {
            if (!byItem[e.itemId]) byItem[e.itemId] = { itemName: e.itemName, itemId: e.itemId, perMonth: [] };
            byItem[e.itemId].perMonth.push({ mi, entry: e });
          });
        }
        const itemIds = Object.keys(byItem);
        if (itemIds.length === 0 && !['S01', 'S02', 'S03', 'R01', 'R02', '參配'].includes(ln)) return '';

        const totalQty = itemIds.reduce((s, id) => s + byItem[id].perMonth.reduce((a, b) => a + b.entry.prodQty, 0), 0);
        const laneHdr = `
          <div class="gantt-lane-hdr">
            <div class="gantt-label-col">
              <span>${esc(ln)} 產線</span>
              <span style="font-size:10.5px;color:#475569;font-weight:600;">${itemIds.length} 品項 · ${fmtNum(totalQty, 0)} MT</span>
            </div>
            <div class="gantt-track" style="--days:1;">${monthDividersHtml}</div>
          </div>`;

        const rows = itemIds.map((id) => {
          const rec = byItem[id];
          const allBars = rec.perMonth.map(({ mi, entry }) => {
            const mo = monthOffsets[mi];
            const isFallbackFull = !entry.days || entry.days.length === 0;
            const bg = isFallbackFull ? '#64748b' : colorForItem(rec.itemName);
            const segs = isFallbackFull ? [{ start: 1, end: mo.days }] : daysToSegments(entry.days);
            return segs.map((seg) => {
              const gStart = mo.offset + (seg.start - 1);
              const gSpan = seg.end - seg.start + 1;
              const leftPct = (gStart / totalHorizonDays) * 100;
              const widthPct = (gSpan / totalHorizonDays) * 100;
              const rangeLbl = `${mo.meta.label} ${isFallbackFull ? '全月(未分日)' : `${seg.start}${seg.end > seg.start ? '~' + seg.end : ''}日`}`;
              return `
                <div class="gantt-bar js-edit-sched"
                     data-id="${esc(id)}" data-m="${mi}"
                     style="left:${leftPct.toFixed(3)}%;width:max(6px,calc(${widthPct.toFixed(3)}% - 1px));background:${bg};${isFallbackFull ? 'opacity:0.75;' : ''}"
                     title="${esc(rec.itemName)} | ${rangeLbl} | ${fmtNum(entry.prodQty, 1)} MT — 點擊調整">
                  ${widthPct > 6 ? esc(isFallbackFull ? `${mo.meta.label} (${fmtNum(entry.prodQty, 0)})` : `${seg.start}~${seg.end} (${fmtNum(entry.prodQty, 0)})`) : ''}
                </div>`;
            }).join('');
          }).join('');

          return `
            <div class="gantt-row">
              <div class="gantt-label-col">
                <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${esc(rec.itemName)}</span>
              </div>
              <div class="gantt-track" style="--days:1;">
                <div class="gantt-baseline"></div>
                ${monthDividersHtml}
                ${allBars}
              </div>
            </div>`;
        }).join('');

        return laneHdr + (rows || `<div class="gantt-row"><div class="gantt-label-col" style="color:#94a3b8;">（四個月內無排產）</div><div class="gantt-track" style="--days:1;">${monthDividersHtml}</div></div>`);
      }).join('');

      ganttChartHtml = `
        <div class="panel">
          <div class="panel-hdr">
            <div class="panel-title">📆 四個月全期連貫甘特條圖時間軸</div>
            <span style="font-size:11px;color:#64748b;">一覽跨月連續生產波段；點擊任一段色條即可編輯該月份排程</span>
          </div>
          <div class="table-scroll" style="max-height:64vh;">
            <div class="gantt-board">
              <div class="gantt-header">
                <div class="gantt-label-col">產線 / 產品品項</div>
                <div class="gantt-ruler">${monthHdrTicks}</div>
              </div>
              ${laneBlocks}
            </div>
          </div>
        </div>`;
    }

    // Detailed list for current month
    const scheduledItems = [];
    state.plan.items.forEach((it) => {
      const mc = state.calc.computedById[it.id].months[mIdx];
      const mr = (it.months && it.months[mIdx]) || {};
      if (mc.effectiveProdQty > 0 || (mr.line && mr.periodStr)) {
        scheduledItems.push({ item: it, mc, mr });
      }
    });

    return `
      <div class="toolbar">
        <div class="filter-group">
          <span style="font-weight:700;">視圖：</span>
          <button class="chip ${!isHorizon ? 'active' : ''}" data-schedmode="month">📊 單月甘特條圖</button>
          <button class="chip ${isHorizon ? 'active' : ''}" data-schedmode="horizon">📆 4個月連貫全覽</button>
          <span style="margin-left:8px;font-weight:700;">月份：</span>
          ${state.calc.monthsMeta.map((m, idx) => `
            <button class="chip ${mIdx === idx ? 'active' : ''}" data-schedm="${idx}">${esc(m.label)} (${esc(m.periodLabel)})</button>`).join('')}
        </div>
        <div style="font-size:12px;color:#475569;">點擊任意甘特圖條線或下方按鈕，即可編輯線別、區間與日產能</div>
      </div>

      ${conflicts.length ? `
        <div class="panel">
          <div class="panel-hdr"><div class="panel-title">⚡ ${isHorizon ? '全期' : esc(mMeta.label)} 產線重疊與避讓警告 (${conflicts.length})</div></div>
          <div class="alert-list">
            ${conflicts.map((c) => `
              <div class="alert-item ${c.type === 'nmp_sequence_notice' ? 'below_min' : 'critical'}">
                <span>${esc(c.message)}</span>
              </div>`).join('')}
          </div>
        </div>` : `<div class="panel" style="padding:10px 14px;background:#f0fdf4;color:#166534;font-weight:700;">✅ ${isHorizon ? '全期' : esc(mMeta.label)} 目前無連續精餾/初餾塔槽日期重疊衝突</div>`}

      ${ganttChartHtml}

      <div class="panel">
        <div class="panel-hdr"><div class="panel-title">📋 ${esc(mMeta.label)} 各品項排產清單 (${scheduledItems.length} 筆)</div></div>
        <div class="table-scroll">
          <table class="plan-table">
            <thead>
              <tr>
                <th>品名</th><th>製程</th><th>生產線別</th><th>排程區間</th><th>天數</th><th>當月排產量 (MT)</th><th>日均 (MT/日)</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              ${scheduledItems.map(({ item, mc, mr }) => `
                <tr>
                  <td style="font-weight:700;">${esc(item.name)}</td>
                  <td>${esc(item.process)}</td>
                  <td>${esc(mr.line || (item.kind === 'filling' ? '充填' : '-'))}</td>
                  <td>${esc((mr.periodStr || '-').replace(/\n/g, ' , '))}</td>
                  <td style="text-align:center;">${mc.scheduleDayCount}</td>
                  <td style="text-align:right;font-weight:700;">${fmtNum(mc.effectiveProdQty, 1)}</td>
                  <td style="text-align:right;">${mc.scheduleDayCount > 0 ? fmtNum(mc.effectiveProdQty / mc.scheduleDayCount, 2) : '-'}</td>
                  <td><button class="btn btn-xs btn-primary js-edit-sched" data-id="${esc(item.id)}" data-m="${mIdx}">🗓️ 編輯排程</button></td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>`;
  }

  function buildBomHtml() {
    const months = state.calc.monthsMeta;
    const rules = state.plan.bomRules || [];
    const recRules = state.plan.recoveryRules || [];

    return `
      <div class="panel">
        <div class="panel-hdr">
          <div class="panel-title">🧬 秏料公式管理（多階 BOM 配方）(${rules.length} 條)</div>
          <div style="display:flex;gap:8px;align-items:center;">
            <label style="font-size:12px;cursor:pointer;">
              <input id="chkEbrFixed" type="checkbox" ${state.plan.meta.ebrRUseFixed110 ? 'checked' : ''} />
              EBR95 耗用 EBR(R) 套用初餾表 1.1x（關閉則用秏料表 1.1103x）
            </label>
            <button id="btnAddBomRule" class="btn btn-xs btn-primary">➕ 新增 BOM 配方</button>
          </div>
        </div>
        <div class="table-scroll" style="max-height:46vh;">
          <table class="plan-table">
            <thead>
              <tr>
                <th>啟用</th><th>上階產品</th><th>消耗原料/半成品</th><th>收率 (Yield)</th><th>占比 (Ratio)</th><th>進位小數位</th>
                ${months.map((m) => `<th>${esc(m.label)}計算用量</th>`).join('')}
                <th>刪除</th>
              </tr>
            </thead>
            <tbody>
              ${rules.map((r, idx) => {
                const bd = (state.calc.bomBreakdownByTarget[r.rawMaterial] || []).find((b) => b.ruleId === r.id);
                return `
                  <tr>
                    <td style="text-align:center;"><input type="checkbox" class="js-bom-toggle" data-idx="${idx}" ${r.active !== false ? 'checked' : ''} /></td>
                    <td style="font-weight:700;">${esc(r.product)}</td>
                    <td style="font-weight:700;color:#6b21a8;">${esc(r.rawMaterial)}</td>
                    <td><input class="cell-input js-bom-edit" data-idx="${idx}" data-field="yieldRate" type="number" step="0.0001" value="${esc(r.yieldRate)}" /></td>
                    <td><input class="cell-input js-bom-edit" data-idx="${idx}" data-field="ratio" type="number" step="0.0001" value="${esc(r.ratio)}" /></td>
                    <td style="text-align:center;">
                      <select class="cell-select js-bom-edit" data-idx="${idx}" data-field="roundingDecimals">
                        <option value="0" ${Number(r.roundingDecimals) === 0 ? 'selected' : ''}>整數 (0)</option>
                        <option value="3" ${Number(r.roundingDecimals) === 3 ? 'selected' : ''}>三位小數 (3)</option>
                      </select>
                    </td>
                    ${[0, 1, 2, 3].map((mi) => `<td style="text-align:right;">${bd ? fmtNum(bd.months[mi], Number(r.roundingDecimals) || 0) : '0'}</td>`).join('')}
                    <td style="text-align:center;"><button class="btn btn-xs btn-danger js-bom-del" data-idx="${idx}">🗑️</button></td>
                  </tr>`;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <div class="panel">
        <div class="panel-hdr">
          <div class="panel-title">♻️ 自動回收與跨區轉入規則</div>
          <div style="display:flex;gap:8px;">
            <button id="btnViewCloudLogs" class="btn btn-xs btn-teal">📜 查看雲端異動紀錄</button>
            <button id="btnResetFactorySeed" class="btn btn-xs btn-danger">⚠️ 重設為原始範本 (20260511)</button>
          </div>
        </div>
        <div style="padding:10px 14px;">
          ${recRules.map((rr, idx) => `
            <div style="display:flex;align-items:center;justify-content:space-between;padding:6px 0;border-bottom:1px solid #e2e8f0;">
              <div>
                <label style="cursor:pointer;font-weight:700;">
                  <input type="checkbox" class="js-rec-toggle" data-idx="${idx}" ${rr.active !== false ? 'checked' : ''} />
                  ${esc(rr.sourceItem)} (${esc(rr.sourceField)} × ${rr.factor}) → 轉入 <strong>${esc(rr.targetRaw)}</strong> 其他入庫
                </label>
                <span style="margin-left:8px;font-size:11.5px;color:#64748b;">${esc(rr.note || '')}</span>
              </div>
            </div>`).join('')}
        </div>
      </div>`;
  }

  // ==================== Event Binding ====================
  function bindWorkspaceEvents() {
    // Summary chips & search
    document.querySelectorAll('[data-sfilter]').forEach((el) => {
      el.onclick = () => { state.summaryFilter = el.dataset.sfilter; renderWorkspace(); };
    });
    document.querySelectorAll('[data-skind]').forEach((el) => {
      el.onclick = () => { state.summaryKindFilter = el.dataset.skind; renderWorkspace(); };
    });
    const searchEl = document.getElementById('summarySearchInput');
    if (searchEl) {
      searchEl.oninput = (e) => {
        state.searchQuery = e.target.value;
        const pos = e.target.selectionStart;
        renderWorkspace();
        const nextInput = document.getElementById('summarySearchInput');
        if (nextInput) { nextInput.focus(); nextInput.setSelectionRange(pos, pos); }
      };
    }

    // Inline month cell edits (fires on change so typing never steals focus)
    document.querySelectorAll('.js-edit-cell').forEach((el) => {
      el.onchange = () => {
        const it = state.plan.items.find((x) => x.id === el.dataset.id);
        if (!it) return;
        const mIdx = Number(el.dataset.m);
        const field = el.dataset.field;
        const mr = it.months[mIdx];
        if (field === 'line') {
          mr.line = el.value;
        } else if (field === 'periodStr') {
          mr.periodStr = el.value.replace(/,\s*/g, '\n');
        } else if (field === 'usageOverride') {
          mr.usageOverride = el.value === '' ? null : Number(el.value);
        } else {
          mr[field] = el.value === '' ? 0 : Number(el.value);
        }
        recompute(`修改 ${it.name} ${state.calc.monthsMeta[mIdx].label} ${field}`);
      };
    });

    // Item top-level edits (invMaterial, invProcess2, tankBottom, safetyMin)
    document.querySelectorAll('.js-edit-item').forEach((el) => {
      el.onchange = () => {
        const it = state.plan.items.find((x) => x.id === el.dataset.id);
        if (!it) return;
        const f = el.dataset.field;
        if (f === 'safetyMin') {
          it.safetyMin = el.value === '' ? null : Number(el.value);
        } else {
          it[f] = el.value === '' ? 0 : Number(el.value);
        }
        recompute(`調整 ${it.name} 基礎庫存/安全設定`);
      };
    });

    // Enable manual usageOverride button
    document.querySelectorAll('.js-enable-usage-ov').forEach((btn) => {
      btn.onclick = () => {
        const it = state.plan.items.find((x) => x.id === btn.dataset.id);
        if (!it) return;
        const mIdx = Number(btn.dataset.m);
        const curEff = state.calc.computedById[it.id].months[mIdx].effectiveUsage;
        it.months[mIdx].usageOverride = curEff;
        recompute(`開啟 ${it.name} 手動耗用覆寫`);
      };
    });

    // Reset manual usageOverride
    document.querySelectorAll('.js-reset-usage').forEach((btn) => {
      btn.onclick = () => {
        const it = state.plan.items.find((x) => x.id === btn.dataset.id);
        if (!it) return;
        const mIdx = Number(btn.dataset.m);
        it.months[mIdx].usageOverride = null;
        recompute(`還原 ${it.name} 自動 BOM 耗用`);
      };
    });

    // Toggle filling formula mode
    document.querySelectorAll('.js-toggle-fillmode').forEach((el) => {
      el.onclick = () => {
        const it = state.plan.items.find((x) => x.id === el.dataset.id);
        if (!it) return;
        const mIdx = Number(el.dataset.m);
        const curMode = it.months[mIdx].prodFormulaMode;
        if (curMode === 'sales_plus_usage') {
          it.months[mIdx].prodQty = state.calc.computedById[it.id].months[mIdx].effectiveProdQty;
          it.months[mIdx].prodFormulaMode = 'manual';
          showToast('已切換為手動輸入充填產量');
        } else {
          it.months[mIdx].prodFormulaMode = 'sales_plus_usage';
          showToast('已切回充填自動計算 (=銷售+耗用)');
        }
        recompute(`切換 ${it.name} 充填計算模式`);
      };
    });

    // Toggle child-to-parent rollup per month
    document.querySelectorAll('.js-toggle-rollup').forEach((chk) => {
      chk.onchange = () => {
        const it = state.plan.items.find((x) => x.id === chk.dataset.id);
        if (!it) return;
        const mIdx = Number(chk.dataset.m);
        if (!Array.isArray(it.rollupMonths)) it.rollupMonths = [false, false, false, false];
        it.rollupMonths[mIdx] = chk.checked;
        recompute(`${chk.checked ? '啟用' : '停用'} ${it.name} 併入 ${it.rollupTo}`);
      };
    });

    // Show BOM breakdown modal
    document.querySelectorAll('.js-show-bom').forEach((el) => {
      el.onclick = () => openBomBreakdownModal(el.dataset.name, Number(el.dataset.m));
    });

    // Open item detail modal
    document.querySelectorAll('.js-open-item').forEach((el) => {
      el.onclick = () => openItemDetailModal(el.dataset.id);
    });

    // Add new item modal
    const btnAdd = document.getElementById('btnAddNewItem');
    if (btnAdd) btnAdd.onclick = openAddItemModal;

    // Schedule tab buttons
    document.querySelectorAll('[data-schedmode]').forEach((el) => {
      el.onclick = () => { state.scheduleViewMode = el.dataset.schedmode; renderWorkspace(); };
    });
    document.querySelectorAll('[data-schedm]').forEach((el) => {
      el.onclick = () => { state.scheduleMonthIdx = Number(el.dataset.schedm); renderWorkspace(); };
    });
    document.querySelectorAll('.js-edit-sched').forEach((el) => {
      el.onclick = () => openScheduleEditorModal(el.dataset.id, Number(el.dataset.m));
    });

    // BOM tab handlers
    const chkEbr = document.getElementById('chkEbrFixed');
    if (chkEbr) {
      chkEbr.onchange = () => {
        state.plan.meta.ebrRUseFixed110 = chkEbr.checked;
        recompute('切換 EBR(R) 耗用倍率模式');
      };
    }
    document.querySelectorAll('.js-bom-toggle').forEach((el) => {
      el.onchange = () => {
        state.plan.bomRules[Number(el.dataset.idx)].active = el.checked;
        recompute('切換 BOM 規則狀態');
      };
    });
    document.querySelectorAll('.js-bom-edit').forEach((el) => {
      el.onchange = () => {
        const rule = state.plan.bomRules[Number(el.dataset.idx)];
        rule[el.dataset.field] = Number(el.value);
        recompute(`修改 BOM 配方 ${rule.product}->${rule.rawMaterial}`);
      };
    });
    document.querySelectorAll('.js-bom-del').forEach((el) => {
      el.onclick = () => {
        const idx = Number(el.dataset.idx);
        const removed = state.plan.bomRules.splice(idx, 1)[0];
        recompute(`刪除 BOM 配方 ${removed ? removed.product : ''}`);
      };
    });
    document.querySelectorAll('.js-rec-toggle').forEach((el) => {
      el.onchange = () => {
        state.plan.recoveryRules[Number(el.dataset.idx)].active = el.checked;
        recompute('切換回收連動規則');
      };
    });
    const btnAddBom = document.getElementById('btnAddBomRule');
    if (btnAddBom) btnAddBom.onclick = openAddBomModal;

    const btnResetSeed = document.getElementById('btnResetFactorySeed');
    if (btnResetSeed) {
      btnResetSeed.onclick = () => {
        if (!confirm('確定要還原回原始 20260511 Excel 基準計畫嗎？未存快照的變更將遺失。')) return;
        state.plan = cloneObj(window.DEFAULT_SALES_PLAN);
        recompute('還原基準計畫範本');
        showToast('已還原為 20260511 基準計畫');
      };
    }
    const btnLogs = document.getElementById('btnViewCloudLogs');
    if (btnLogs) btnLogs.onclick = openCloudLogsModal;
  }

  // ==================== Modals ====================
  function openBomBreakdownModal(itemName, mIdx) {
    const mMeta = state.calc.monthsMeta[mIdx];
    const rows = state.calc.bomBreakdownByTarget[itemName] || [];
    const recs = state.calc.recoveryBreakdownByTarget[itemName] || [];
    const html = `
      <p style="margin-top:0;"><strong>${esc(itemName)}</strong> 在 <strong>${esc(mMeta.label)}</strong> 的系統自動計算明細：</p>
      <table class="plan-table" style="width:100%;margin-bottom:12px;">
        <thead><tr><th>來源品項</th><th>收率</th><th>占比</th><th>本月用量 (MT)</th></tr></thead>
        <tbody>
          ${rows.map((r) => `
            <tr>
              <td style="font-weight:700;">${esc(r.product)}</td>
              <td style="text-align:right;">${fmtNum(r.yieldRate, 4)}</td>
              <td style="text-align:right;">${fmtNum(r.ratio, 4)}</td>
              <td style="text-align:right;font-weight:700;color:#0369a1;">${fmtNum(r.months[mIdx], r.roundingDecimals)}</td>
            </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;">無上游 BOM 耗用</td></tr>'}
        </tbody>
      </table>
      ${recs.length ? `
        <p><strong>♻️ 自動回收／轉入來源：</strong></p>
        <ul style="font-size:12px;">
          ${recs.map((r) => `<li>${esc(r.sourceItem)} (係數 ${r.factor}) → +${fmtNum(r.months[mIdx], 2)} MT（${esc(r.note || '')}）</li>`).join('')}
        </ul>` : ''}`;
    openModal(`BOM 耗用明細 - ${itemName}`, html, `<button class="btn btn-primary" onclick="document.getElementById('btnCloseModal').click()">確定</button>`);
  }

  function openItemDetailModal(itemId) {
    const it = state.plan.items.find((x) => x.id === itemId);
    if (!it) return;
    const w = state.calc.computedById[it.id];
    const html = `
      <div class="form-grid">
        <div class="form-field"><label>品名</label><input id="mdName" type="text" value="${esc(it.name)}" /></div>
        <div class="form-field"><label>存放儲槽</label><input id="mdTanks" type="text" value="${esc(it.tanks || '')}" /></div>
        <div class="form-field"><label>儲槽容量 (MT)</label><input id="mdCap" type="number" step="0.1" value="${esc(it.capacity || 0)}" /></div>
        <div class="form-field"><label>固定期初覆寫 (留空則自動 D+E-F)</label><input id="mdOpenOv" type="number" step="0.1" placeholder="自動 (${fmtNum(w.autoOpening, 2)})" value="${it.openingOverride !== null && it.openingOverride !== undefined ? esc(it.openingOverride) : ''}" /></div>
        <div class="form-field"><label>安全最低庫存</label><input id="mdSafeMin" type="number" step="0.1" value="${it.safetyMin !== null && it.safetyMin !== undefined ? esc(it.safetyMin) : ''}" /></div>
        <div class="form-field"><label>安全最高庫存</label><input id="mdSafeMax" type="number" step="0.1" value="${it.safetyMax !== null && it.safetyMax !== undefined ? esc(it.safetyMax) : ''}" /></div>
      </div>
      <div style="margin-top:12px;">
        <strong>各月進階模式與調整註記：</strong>
        <table class="plan-table" style="width:100%;margin-top:6px;">
          <thead><tr><th>月份</th><th>產量計算模式</th><th>額外期末調整(+/-)</th><th>調整說明</th></tr></thead>
          <tbody>
            ${state.calc.monthsMeta.map((m, mi) => {
              const mr = it.months[mi];
              return `
                <tr>
                  <td>${esc(m.label)}</td>
                  <td>
                    <select class="js-md-pmode" data-m="${mi}">
                      <option value="manual" ${mr.prodFormulaMode === 'manual' ? 'selected' : ''}>手動輸入產量</option>
                      <option value="sales_plus_usage" ${mr.prodFormulaMode === 'sales_plus_usage' ? 'selected' : ''}>充填自動 (=銷售+耗用)</option>
                      <option value="daily_rate" ${mr.prodFormulaMode === 'daily_rate' ? 'selected' : ''}>天數 × 日產能</option>
                    </select>
                  </td>
                  <td><input class="cell-input js-md-adj" data-m="${mi}" type="number" step="0.1" value="${esc(mr.adjBalance || 0)}" /></td>
                  <td><input class="cell-input wide js-md-adjnote" data-m="${mi}" style="width:180px;" type="text" value="${esc(mr.adjNote || '')}" /></td>
                </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>`;

    openModal(`品項設定與進階調整 - ${it.name}`, html, `<button id="btnSaveItemModal" class="btn btn-primary">💾 套用設定</button>`);
    document.getElementById('btnSaveItemModal').onclick = () => {
      it.name = document.getElementById('mdName').value.trim() || it.name;
      it.tanks = document.getElementById('mdTanks').value.trim();
      it.capacity = Number(document.getElementById('mdCap').value || 0);
      const ovVal = document.getElementById('mdOpenOv').value;
      it.openingOverride = ovVal === '' ? null : Number(ovVal);
      const sMin = document.getElementById('mdSafeMin').value;
      const sMax = document.getElementById('mdSafeMax').value;
      it.safetyMin = sMin === '' ? null : Number(sMin);
      it.safetyMax = sMax === '' ? null : Number(sMax);

      document.querySelectorAll('.js-md-pmode').forEach((sel) => {
        it.months[Number(sel.dataset.m)].prodFormulaMode = sel.value;
      });
      document.querySelectorAll('.js-md-adj').forEach((inp) => {
        it.months[Number(inp.dataset.m)].adjBalance = Number(inp.value || 0);
      });
      document.querySelectorAll('.js-md-adjnote').forEach((inp) => {
        it.months[Number(inp.dataset.m)].adjNote = inp.value;
      });
      closeModal();
      recompute(`更新 ${it.name} 主檔與調整規則`);
    };
  }

  function openScheduleEditorModal(itemId, mIdx) {
    const it = state.plan.items.find((x) => x.id === itemId);
    if (!it) return;
    const mr = it.months[mIdx];
    const mMeta = state.calc.monthsMeta[mIdx];
    const lineOpts = (state.plan.lines || []).map((l) => l.id);
    const curLine = mr.line || '';
    const allLines = lineOpts.includes(curLine) || !curLine ? lineOpts : [curLine, ...lineOpts];

    const html = `
      <p style="margin-top:0;">編輯 <strong>${esc(it.name)}</strong> 於 <strong>${esc(mMeta.label)} (${esc(mMeta.periodLabel)})</strong> 之產線排程：</p>
      <div class="form-grid">
        <div class="form-field">
          <label>生產線別</label>
          <select id="scLine">
            <option value="">(未排)</option>
            ${allLines.map((ln) => `<option value="${esc(ln)}" ${ln === curLine ? 'selected' : ''}>${esc(ln)}</option>`).join('')}
          </select>
        </div>
        <div class="form-field">
          <label>排程天期區間 (多段請換行或逗號，如 11~12,18~22)</label>
          <input id="scPeriod" type="text" value="${esc((mr.periodStr || '').replace(/\n/g, ','))}" />
        </div>
        <div class="form-field">
          <label>日產能參考 (MT/日，可選)</label>
          <input id="scDaily" type="number" step="0.1" placeholder="例如 36" value="${mr.dailyRate ? esc(mr.dailyRate) : ''}" />
        </div>
        <div class="form-field">
          <label>本月排產總量 (MT)</label>
          <div style="display:flex;gap:6px;">
            <input id="scQty" type="number" step="0.1" value="${esc(mr.prodQty || 0)}" style="flex:1;" />
            <button id="btnCalcByDays" class="btn btn-xs btn-teal" type="button">天數×日產換算</button>
          </div>
        </div>
      </div>
      <div id="scPreviewDays" style="margin-top:10px;font-size:12px;color:#0369a1;"></div>`;

    openModal(`快速產線排程 - ${it.name}`, html, `<button id="btnSaveSched" class="btn btn-primary">💾 儲存排程</button>`);

    function updatePreview() {
      const parsed = window.SalesPlannerEngine.parsePeriodDays(document.getElementById('scPeriod').value.replace(/,/g, '\n'), mMeta);
      document.getElementById('scPreviewDays').textContent = `解析排程天數：共 ${parsed.count} 天 (${parsed.days.join(', ') || '無'})`;
      return parsed;
    }
    updatePreview();
    document.getElementById('scPeriod').oninput = updatePreview;
    document.getElementById('btnCalcByDays').onclick = () => {
      const parsed = updatePreview();
      const rate = Number(document.getElementById('scDaily').value || 0);
      if (parsed.count > 0 && rate > 0) {
        document.getElementById('scQty').value = Math.round(parsed.count * rate * 100) / 100;
      } else {
        showToast('請輸入有效區間與日產能');
      }
    };
    document.getElementById('btnSaveSched').onclick = () => {
      mr.line = document.getElementById('scLine').value;
      mr.periodStr = document.getElementById('scPeriod').value.replace(/,\s*/g, '\n');
      const dr = document.getElementById('scDaily').value;
      mr.dailyRate = dr === '' ? null : Number(dr);
      mr.prodQty = Number(document.getElementById('scQty').value || 0);
      mr.prodFormulaMode = 'manual';
      closeModal();
      recompute(`更新 ${it.name} ${mMeta.label} 排程 (${mr.line} / ${mr.prodQty} MT)`);
    };
  }

  function openAddItemModal() {
    const html = `
      <div class="form-grid">
        <div class="form-field"><label>品項名稱 *</label><input id="niName" type="text" placeholder="例如 IPAUPS-2" /></div>
        <div class="form-field"><label>製程歸屬</label>
          <select id="niProc"><option value="精餾">精餾</option><option value="初餾">初餾</option><option value="調配">調配</option></select>
        </div>
        <div class="form-field"><label>類型</label>
          <select id="niKind"><option value="product">成品</option><option value="filling">充填成品</option><option value="raw">原料/半成品</option></select>
        </div>
        <div class="form-field"><label>儲槽位置</label><input id="niTanks" type="text" placeholder="TKxxx" /></div>
        <div class="form-field"><label>儲槽容量 (MT)</label><input id="niCap" type="number" step="0.1" value="100" /></div>
        <div class="form-field"><label>期初資材庫存 (MT)</label><input id="niInv" type="number" step="0.1" value="0" /></div>
      </div>`;
    openModal('➕ 新增產銷品項主檔', html, `<button id="btnConfirmNewItem" class="btn btn-primary">新增品項</button>`);
    document.getElementById('btnConfirmNewItem').onclick = () => {
      const name = document.getElementById('niName').value.trim();
      if (!name) return showToast('請輸入品項名稱');
      const proc = document.getElementById('niProc').value;
      const kind = document.getElementById('niKind').value;
      const section = kind === 'raw' ? `${proc}原料` : (kind === 'filling' ? '充填成品' : `${proc}成品`);
      state.plan.items.push({
        id: `${kind}_${proc}_${Date.now()}_${name}`,
        name,
        kind,
        process: proc,
        section,
        sourceSheet: `${proc}產銷`,
        sourceRow: 999,
        tanks: document.getElementById('niTanks').value.trim(),
        capacity: Number(document.getElementById('niCap').value || 0),
        invMaterial: Number(document.getElementById('niInv').value || 0),
        invProcess2: 0,
        tankBottom: 0,
        openingOverride: null,
        safetyMax: null,
        safetyMin: null,
        rollupTo: null,
        rollupMonths: [false, false, false, false],
        showInSummary: true,
        months: [0, 1, 2, 3].map(() => ({
          sales: 0, contractIn: 0, directUsage: 0, usageOverride: null,
          purchase: 0, otherIn: 0, otherInOverride: null, adjBalance: 0, adjNote: '',
          line: '', periodStr: '', prodQty: 0, prodFormulaMode: kind === 'filling' ? 'sales_plus_usage' : 'manual', dailyRate: null
        }))
      });
      closeModal();
      recompute(`新增品項 ${name}`);
      showToast(`已新增 ${name}`);
    };
  }

  function openAddBomModal() {
    const names = Array.from(new Set(state.plan.items.map((x) => x.name)));
    const html = `
      <div class="form-grid">
        <div class="form-field"><label>上階產品 *</label>
          <input id="nbProd" list="dlItems" placeholder="選擇或輸入產品" />
        </div>
        <div class="form-field"><label>消耗原料 / 半成品 *</label>
          <input id="nbRaw" list="dlItems" placeholder="選擇或輸入原料" />
        </div>
        <div class="form-field"><label>收率 (Yield, 預設 1 或 1/收率)</label><input id="nbYield" type="number" step="0.0001" value="1" /></div>
        <div class="form-field"><label>配方占比 (Ratio, 0~1)</label><input id="nbRatio" type="number" step="0.0001" value="1" /></div>
        <div class="form-field"><label>進位小數位</label>
          <select id="nbDec"><option value="0">0 (整數)</option><option value="3">3 (小數三位)</option></select>
        </div>
      </div>
      <datalist id="dlItems">${names.map((n) => `<option value="${esc(n)}"></option>`).join('')}</datalist>`;
    openModal('➕ 新增 BOM 配方規則', html, `<button id="btnConfirmBom" class="btn btn-primary">加入配方</button>`);
    document.getElementById('btnConfirmBom').onclick = () => {
      const product = document.getElementById('nbProd').value.trim();
      const rawMaterial = document.getElementById('nbRaw').value.trim();
      if (!product || !rawMaterial) return showToast('請輸入產品與原料名稱');
      state.plan.bomRules.push({
        id: 'bom_' + Date.now(),
        product,
        rawMaterial,
        yieldRate: Number(document.getElementById('nbYield').value || 1),
        ratio: Number(document.getElementById('nbRatio').value || 1),
        roundingDecimals: Number(document.getElementById('nbDec').value || 0),
        active: true,
        note: '線上新增'
      });
      closeModal();
      recompute(`新增 BOM ${product} -> ${rawMaterial}`);
    };
  }

  async function openArchivesModal() {
    let list = [];
    if (IS_FILE_MODE) {
      try { list = JSON.parse(localStorage.getItem(STORAGE_LOCAL_ARCHIVES_KEY) || '[]'); } catch (_) {}
    } else {
      const { ok, data } = await apiFetch('/api/archives');
      if (ok && data.ok) list = data.archives || [];
    }

    const body = `
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px;padding:10px;background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">
        <input id="arcNewName" type="text" placeholder="新快照名稱（如：20260511 調整二版）" style="flex:1;min-width:200px;padding:6px 8px;border:1px solid #cbd5e1;border-radius:6px;" />
        <input id="arcNewDesc" type="text" placeholder="備註（可空白）" style="flex:1;min-width:140px;padding:6px 8px;border:1px solid #cbd5e1;border-radius:6px;" />
        <button id="btnSaveNewArc" class="btn btn-primary">💾 存為新快照</button>
      </div>
      <table class="plan-table" style="width:100%;">
        <thead><tr><th>快照名稱</th><th>建立者</th><th>更新時間</th><th>操作</th></tr></thead>
        <tbody>
          ${list.map((a) => `
            <tr>
              <td><strong>${esc(a.name)}</strong><div style="font-size:11px;color:#64748b;">${esc(a.description || '')}</div></td>
              <td>${esc(a.created_by || '-')}</td>
              <td style="font-size:11px;">${esc((a.updated_at || a.created_at || '').slice(0, 19).replace('T', ' '))}</td>
              <td>
                <button class="btn btn-xs btn-teal js-arc-load" data-id="${esc(a.id)}">載入</button>
                <button class="btn btn-xs btn-amber js-arc-ow" data-id="${esc(a.id)}" data-name="${esc(a.name)}">覆蓋</button>
                <button class="btn btn-xs js-arc-ren" data-id="${esc(a.id)}" data-name="${esc(a.name)}">改名</button>
                <button class="btn btn-xs btn-danger js-arc-del" data-id="${esc(a.id)}">刪除</button>
              </td>
            </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;padding:18px;color:#64748b;">尚無已儲存快照</td></tr>'}
        </tbody>
      </table>`;

    openModal('📸 歷史計畫快照管理', body);

    document.getElementById('btnSaveNewArc').onclick = async () => {
      const name = document.getElementById('arcNewName').value.trim();
      const desc = document.getElementById('arcNewDesc').value.trim();
      if (!name) return showToast('請輸入快照名稱');
      if (IS_FILE_MODE) {
        list.unshift({ id: Date.now(), name, description: desc, created_by: state.operator, updated_at: new Date().toISOString(), plan: cloneObj(state.plan) });
        localStorage.setItem(STORAGE_LOCAL_ARCHIVES_KEY, JSON.stringify(list));
      } else {
        await apiFetch('/api/archives', { method: 'POST', body: JSON.stringify({ name, description: desc, created_by: state.operator, plan: state.plan }) });
      }
      showToast(`已儲存快照「${name}」`);
      openArchivesModal();
    };

    document.querySelectorAll('.js-arc-load').forEach((btn) => {
      btn.onclick = async () => {
        if (!confirm('載入此快照將會替換目前編輯中的畫面內容，確定嗎？')) return;
        let loadedPlan = null;
        if (IS_FILE_MODE) {
          const found = list.find((x) => String(x.id) === String(btn.dataset.id));
          loadedPlan = found ? found.plan : null;
        } else {
          const { ok, data } = await apiFetch(`/api/archives/${btn.dataset.id}`);
          if (ok && data.ok && data.archive) loadedPlan = data.archive.plan;
        }
        if (loadedPlan) {
          state.plan = loadedPlan;
          closeModal();
          recompute(`載入快照 ${btn.dataset.id}`);
          showToast('已載入快照並套用同步');
        }
      };
    });

    document.querySelectorAll('.js-arc-ow').forEach((btn) => {
      btn.onclick = async () => {
        if (!confirm(`確定以目前計畫覆蓋快照「${btn.dataset.name}」？`)) return;
        if (IS_FILE_MODE) {
          const found = list.find((x) => String(x.id) === String(btn.dataset.id));
          if (found) { found.plan = cloneObj(state.plan); found.updated_at = new Date().toISOString(); }
          localStorage.setItem(STORAGE_LOCAL_ARCHIVES_KEY, JSON.stringify(list));
        } else {
          await apiFetch('/api/archives', {
            method: 'POST',
            body: JSON.stringify({ overwrite_id: Number(btn.dataset.id), name: btn.dataset.name, created_by: state.operator, plan: state.plan })
          });
        }
        showToast('已覆蓋快照');
        openArchivesModal();
      };
    });

    document.querySelectorAll('.js-arc-ren').forEach((btn) => {
      btn.onclick = async () => {
        const newName = prompt('請輸入新快照名稱：', btn.dataset.name);
        if (!newName || !newName.trim()) return;
        if (IS_FILE_MODE) {
          const found = list.find((x) => String(x.id) === String(btn.dataset.id));
          if (found) found.name = newName.trim();
          localStorage.setItem(STORAGE_LOCAL_ARCHIVES_KEY, JSON.stringify(list));
        } else {
          await apiFetch(`/api/archives/${btn.dataset.id}`, { method: 'PUT', body: JSON.stringify({ name: newName.trim() }) });
        }
        openArchivesModal();
      };
    });

    document.querySelectorAll('.js-arc-del').forEach((btn) => {
      btn.onclick = async () => {
        const pwd = prompt('請輸入刪除密碼（預設 8888）：');
        if (pwd === null) return;
        if (IS_FILE_MODE) {
          if (pwd !== '8888') return showToast('密碼錯誤');
          const filtered = list.filter((x) => String(x.id) !== String(btn.dataset.id));
          localStorage.setItem(STORAGE_LOCAL_ARCHIVES_KEY, JSON.stringify(filtered));
          openArchivesModal();
          return;
        }
        const { ok, data } = await apiFetch(`/api/archives/${btn.dataset.id}`, { method: 'DELETE', body: JSON.stringify({ password: pwd }) });
        if (!ok || !data.ok) return showToast(data.error || '刪除失敗');
        showToast('已刪除快照');
        openArchivesModal();
      };
    });
  }

  async function openCloudLogsModal() {
    if (IS_FILE_MODE) return showToast('單機檔案模式無雲端日誌');
    const { ok, data } = await apiFetch('/api/logs');
    const logs = (ok && data.logs) || [];
    openModal('📜 雲端協作異動紀錄（最近 40 筆）', `
      <table class="plan-table" style="width:100%;">
        <thead><tr><th>時間</th><th>操作人</th><th>動作</th><th>摘要</th></tr></thead>
        <tbody>
          ${logs.map((l) => `
            <tr>
              <td style="font-size:11px;">${esc((l.created_at || '').slice(0, 19).replace('T', ' '))}</td>
              <td style="font-weight:700;">${esc(l.actor)}</td>
              <td><span class="tag tag-proc">${esc(l.action)}</span></td>
              <td style="white-space:normal;">${esc(l.summary)}</td>
            </tr>`).join('') || '<tr><td colspan="4" style="text-align:center;">尚無紀錄</td></tr>'}
        </tbody>
      </table>`);
  }

  // ==================== Global Toolbar & PWA Setup ====================
  function initToolbar() {
    const opInput = document.getElementById('operatorInput');
    opInput.value = state.operator;
    opInput.onchange = () => {
      state.operator = opInput.value.trim() || '生管人員';
      localStorage.setItem(STORAGE_OPERATOR_KEY, state.operator);
      showToast(`已切換操作人員：${state.operator}`);
    };

    document.getElementById('btnApplyBaseDate').onclick = () => {
      const val = document.getElementById('baseDateInput').value;
      if (!val) return;
      state.plan.meta.baseDate = val;
      state.plan.meta.months = window.SalesPlannerEngine.buildMonthsFromBaseDate(val);
      recompute(`變更基準日期為 ${val}`);
      showToast(`已重算 4 個月區間：${state.plan.meta.months.map((m) => m.label).join(' / ')}`);
    };

    document.getElementById('tabsBar').querySelectorAll('.tab-btn').forEach((btn) => {
      btn.onclick = () => { state.activeTab = btn.dataset.tab; renderAll(); };
    });

    document.getElementById('btnCloseModal').onclick = closeModal;
    document.getElementById('appModal').onclick = (e) => {
      if (e.target.id === 'appModal') closeModal();
    };

    document.getElementById('excelFileInput').onchange = async (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      try {
        const ab = await file.arrayBuffer();
        const parsedPlan = window.SalesExcelParser.parseWorkbookToPlan(new Uint8Array(ab), file.name, window.XLSX);
        if (!confirm(`成功解析「${file.name}」：\n• 共 ${parsedPlan.items.length} 個品項\n• 共 ${parsedPlan.bomRules.length} 條 BOM 配方\n• 基準日：${parsedPlan.meta.baseDate}\n\n確定匯入並替換目前線上計畫嗎？`)) {
          e.target.value = '';
          return;
        }
        state.plan = parsedPlan;
        recompute(`匯入 Excel ${file.name}`);
        showToast(`成功匯入 ${file.name} (${parsedPlan.items.length} 項)`);
      } catch (err) {
        alert('Excel 匯入失敗：' + (err.message || err));
      } finally {
        e.target.value = '';
      }
    };

    document.getElementById('btnExportExcel').onclick = async () => {
      try {
        showToast('正在產生公式著色 Excel...');
        const buf = await window.SalesExcelExporter.buildExcelBuffer(state.plan, state.calc, window.ExcelJS);
        const blob = new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        const dStr = (state.plan.meta && state.plan.meta.baseDate ? state.plan.meta.baseDate.replace(/-/g, '') : 'export');
        a.download = `鴻勝產銷動態計畫_優化公式版_${dStr}.xlsx`;
        a.click();
        URL.revokeObjectURL(a.href);
        showToast('Excel 匯出完成！');
      } catch (err) {
        alert('Excel 匯出失敗：' + (err.message || err));
      }
    };

    document.getElementById('btnOpenArchives').onclick = openArchivesModal;
    document.getElementById('btnPullCloud').onclick = () => pullPlanFromCloud(false);
    document.getElementById('btnForceSave').onclick = () => pushPlanToCloud(false, '手動儲存產銷計畫', false);
  }

  function initPwaAndSync() {
    if (!IS_FILE_MODE && typeof window.OfflineSyncManager === 'function') {
      syncMgr = new window.OfflineSyncManager({
        storageKey: 'sp_offline_queue_v1',
        badgeElementId: 'syncBadge',
        syncHandler: async (item) => {
          const res = await fetch(item.url, {
            method: item.method || 'POST',
            headers: item.headers || { 'Content-Type': 'application/json' },
            body: typeof item.body === 'string' ? item.body : JSON.stringify(item.body)
          });
          if (res.status === 409) {
            const cData = await res.json();
            openConflictModal(cData);
            throw new Error('協作衝突，需使用者確認');
          }
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const d = await res.json();
          if (d.version) state.cloudVersion = d.version;
          if (d.updatedBy) state.cloudUpdatedBy = d.updatedBy;
          state.isDirty = false;
          updateCloudBadge();
          return d;
        }
      });
    } else {
      const sb = document.getElementById('syncBadge');
      if (sb) sb.textContent = '💾 本機單機暫存';
    }

    // Install banner
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      state.deferredPrompt = e;
      document.getElementById('pwaInstallBanner').classList.add('show');
    });
    document.getElementById('btnInstallPwa').onclick = async () => {
      if (!state.deferredPrompt) return;
      state.deferredPrompt.prompt();
      await state.deferredPrompt.userChoice;
      state.deferredPrompt = null;
      document.getElementById('pwaInstallBanner').classList.remove('show');
    };
    document.getElementById('btnDismissInstall').onclick = () => {
      document.getElementById('pwaInstallBanner').classList.remove('show');
    };
    document.getElementById('btnReloadPwa').onclick = () => window.location.reload();

    if (!IS_FILE_MODE && 'serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
      navigator.serviceWorker.addEventListener('message', (evt) => {
        if (evt.data && evt.data.type === 'VERSION_UPDATED') {
          document.getElementById('pwaUpdateBanner').classList.add('show');
        }
      });
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadLocalDraft();
    initToolbar();
    initPwaAndSync();
    recompute(null);
    pullPlanFromCloud(true, true);
  });
})();
