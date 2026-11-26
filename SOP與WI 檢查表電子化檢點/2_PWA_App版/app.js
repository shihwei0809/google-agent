// ============================================================================
// SOP / WI 電子化檢點與模板控管系統 — 核心前端引擎 (v1.0.0)
// 支援 6.1~6.5 全部 5 張表單、3 種通用版型、主管常用簽名檔庫、離線補傳、Cloudflare D1 API
// ============================================================================

const CONFIG = window.APP_CONFIG || { mode: 'local', envLabel: 'Web 網頁版', apiBase: '', demoMode: false };
const ROLE_PINS = { supervisor: '8888', admin: '9999' }; // 正式上線可改由後端/環境變數控管
let unlockedRole = null; // null | 'supervisor' | 'admin'
let pendingAuthTarget = null; // { tab, tplId }
const LS_KEYS = {
  templates: 'wi_sys_templates_v1',
  records: 'wi_sys_records_v1',
  drafts: 'wi_sys_drafts_v1',
  sigs: 'wi_sys_saved_sigs_v1',
  queue: 'wi_sys_offline_queue_v1'
};

// -------------------- STATE --------------------
let templates = [];
let records = [];
let drafts = [];
let savedSigs = {};
let offlineQueue = [];
let isOnline = navigator.onLine !== false;
let requirePin = false;

let activeGroupKey = '6.1';
let activeDraftId = null;
let draftPlantFilter = 'ALL';
let pendingDeleteDraftId = null;
let editingTplId = '';
let selectedReviewId = '';
let currentMeta = {};
let currentAnswers = {};
let currentStage1Sigs = {}; // 保存已簽好的暫存簽名 PNG
const pads = {};

// -------------------- UTILITIES --------------------
function nowTaipei() {
  return new Intl.DateTimeFormat('zh-TW', {
    timeZone: 'Asia/Taipei',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hour12: false
  }).format(new Date());
}

function todayIso() {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Taipei' }).format(new Date());
  return parts; // YYYY-MM-DD
}

function makeDemoSig(name) {
  const c = document.createElement('canvas');
  c.width = 300; c.height = 90;
  const ctx = c.getContext('2d');
  ctx.strokeStyle = '#0f172a';
  ctx.lineWidth = 2.4;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(25, 58);
  ctx.bezierCurveTo(55, 18, 85, 76, 125, 42);
  ctx.bezierCurveTo(155, 22, 185, 70, 245, 46);
  ctx.stroke();
  ctx.font = 'italic bold 24px serif';
  ctx.fillStyle = '#0f172a';
  ctx.fillText(name || '簽名', 85, 62);
  return c.toDataURL('image/png');
}

function showToast(msg, icon = '✅') {
  const el = document.getElementById('toast');
  if (!el) return;
  document.getElementById('toast-icon').textContent = icon;
  document.getElementById('toast-msg').textContent = msg;
  el.classList.remove('hidden');
  clearTimeout(window._toastTimer);
  window._toastTimer = setTimeout(() => el.classList.add('hidden'), 3400);
}

function getLatestTemplate(groupKey) {
  return templates.find(t => t.groupKey === groupKey && t.isLatest)
    || templates.find(t => t.groupKey === groupKey)
    || templates[0];
}

function getAllLatestTemplates() {
  const seen = new Set();
  const out = [];
  templates.filter(t => t.isLatest).forEach(t => {
    if (!seen.has(t.groupKey)) { seen.add(t.groupKey); out.push(t); }
  });
  return out;
}

// -------------------- STORAGE & CLOUD SYNC --------------------
function saveLocal() {
  try {
    localStorage.setItem(LS_KEYS.templates, JSON.stringify(templates));
    localStorage.setItem(LS_KEYS.records, JSON.stringify(records));
    localStorage.setItem(LS_KEYS.drafts, JSON.stringify(drafts));
    localStorage.setItem(LS_KEYS.sigs, JSON.stringify(savedSigs));
    localStorage.setItem(LS_KEYS.queue, JSON.stringify(offlineQueue));
  } catch (e) {}
}

function isCloudEnabled() {
  return CONFIG.mode === 'cloud' || Boolean(CONFIG.apiBase);
}

async function apiFetch(path, opts = {}) {
  if (!isCloudEnabled()) return null;
  const res = await fetch((CONFIG.apiBase || '') + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

async function bootData() {
  // Load defaults or localStorage first
  try {
    templates = JSON.parse(localStorage.getItem(LS_KEYS.templates) || 'null') || JSON.parse(JSON.stringify(window.WI_DEFAULT_TEMPLATES));
    records = JSON.parse(localStorage.getItem(LS_KEYS.records) || 'null') || [];
    drafts = JSON.parse(localStorage.getItem(LS_KEYS.drafts) || '[]');
    savedSigs = JSON.parse(localStorage.getItem(LS_KEYS.sigs) || 'null') || {
      leader: { roleLabel: '組長', name: '李組長', pin: '1234', dataUrl: makeDemoSig('李組長'), updatedAt: nowTaipei() },
      manager: { roleLabel: '課(副)長 / 主管', name: '林課長', pin: '1234', dataUrl: makeDemoSig('林課長'), updatedAt: nowTaipei() }
    };
    offlineQueue = JSON.parse(localStorage.getItem(LS_KEYS.queue) || '[]');
  } catch (e) {
    templates = JSON.parse(JSON.stringify(window.WI_DEFAULT_TEMPLATES));
  }

  // Cloud mode: pull latest from D1 (templates, records, signatures, AND shared drafts!)
  if (isCloudEnabled() && isOnline) {
    try {
      const [tRes, rRes, sRes, dRes] = await Promise.all([
        apiFetch('/api/templates'),
        apiFetch('/api/records'),
        apiFetch('/api/signatures'),
        apiFetch('/api/drafts')
      ]);
      if (tRes && tRes.templates && tRes.templates.length) templates = tRes.templates;
      if (rRes && rRes.records) records = rRes.records;
      if (sRes && sRes.signatures && Object.keys(sRes.signatures).length) savedSigs = { ...savedSigs, ...sRes.signatures };
      if (dRes && Array.isArray(dRes.drafts)) drafts = dRes.drafts;
      saveLocal();
    } catch (e) {
      console.warn('Cloud sync fallback to local cache:', e);
    }
  }

  // Seed 1 sample record if completely empty so user can inspect immediately
  if (records.length === 0) {
    const t61 = getLatestTemplate('6.1');
    const ans = {};
    t61.items.forEach(it => {
      if (it.id === 'p2') ans[it.id] = { choice: '是', num: '4.2', note: '' };
      else if (it.id === 'p5') ans[it.id] = { choice: '否', num: '', note: '' };
      else if (it.id === 'd3') ans[it.id] = { choice: '是', num: '2.8', note: '' };
      else if (it.id === 'd4') ans[it.id] = { choice: '是', num: '1.4', note: '' };
      else ans[it.id] = { choice: '是', num: '', note: '' };
    });
    records.push({
      id: 'CHK-SAMPLE-01',
      createdAt: nowTaipei(),
      status: 'pending',
      templateSnapshot: JSON.parse(JSON.stringify(t61)),
      meta: { plant: t61.plants[0], date: todayIso(), tankNo: 'T-101', pumpNo: 'P-101B', material: '異丙醇 (IPA)', volA: 120, volB: 50, volC: 70, sg: 0.79, mtAvail: 55.3, trucks: 2.2, mtPlan: 20, remark: '範例檢點紀錄' },
      answers: ans,
      signatures: {
        inspector: { name: '陳大華', dataUrl: makeDemoSig('陳大華'), signedAt: nowTaipei() }
      }
    });
    saveLocal();
  }

  editingTplId = templates[0].id;
  selectedReviewId = records[0].id;
  initMetaForTemplate(getLatestTemplate(activeGroupKey));
  updateBadges();
  switchTab('lobby');
}

async function flushOfflineQueue() {
  if (!isOnline || offlineQueue.length === 0) return;
  const items = [...offlineQueue];
  if (CONFIG.apiBase) {
    const remaining = [];
    for (const rec of items) {
      try {
        await apiFetch('/api/records', { method: 'POST', body: JSON.stringify(rec) });
      } catch (e) {
        remaining.push(rec);
      }
    }
    offlineQueue = remaining;
  } else {
    records.unshift(...items);
    offlineQueue = [];
  }
  saveLocal();
  updateBadges();
  showToast(`連線恢復！已自動補傳 ${items.length - offlineQueue.length} 筆離線紀錄`, '🔄');
}

function toggleNetwork() {
  isOnline = !isOnline;
  syncNetworkBadge();
  if (isOnline) flushOfflineQueue();
  else showToast('已切換離線模式：現場仍可正常填寫與手寫簽名，連網後自動補傳', '📡');
}

function syncNetworkBadge() {
  const dot = document.getElementById('net-dot');
  const lbl = document.getElementById('net-label');
  if (dot) dot.className = isOnline ? 'w-2 h-2 rounded-full bg-emerald-500' : 'w-2 h-2 rounded-full bg-amber-500';
  if (lbl) lbl.textContent = isOnline ? `連線中 (${CONFIG.envLabel})` : '離線模式 (本機佇列)';
  updateBadges();
}

function updateBadges() {
  const pending = records.filter(r => r.status !== 'approved').length;
  const pb = document.getElementById('pending-badge');
  if (pb) pb.textContent = pending;
  const qb = document.getElementById('queue-badge');
  if (qb) {
    qb.classList.toggle('hidden', offlineQueue.length === 0);
    document.getElementById('queue-count').textContent = offlineQueue.length;
  }
}

// -------------------- SIGNATURE PAD --------------------
function initPad(key, canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let down = false, inked = false;
  const pt = e => {
    const r = canvas.getBoundingClientRect();
    const x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
    const y = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
    return { x: x * (canvas.width / r.width), y: y * (canvas.height / r.height) };
  };
  const start = e => { e.preventDefault(); down = true; inked = true; const p = pt(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); };
  const move = e => {
    if (!down) return; e.preventDefault();
    const p = pt(e);
    ctx.strokeStyle = '#0f172a'; ctx.lineWidth = 2.5; ctx.lineCap = 'round';
    ctx.lineTo(p.x, p.y); ctx.stroke();
  };
  const end = () => { down = false; if (key.startsWith('stage1_')) validateCheckForm(); };
  canvas.onmousedown = start; canvas.onmousemove = move; window.addEventListener('mouseup', end);
  canvas.ontouchstart = start; canvas.ontouchmove = move; canvas.ontouchend = end;
  pads[key] = {
    canvas, ctx,
    isEmpty: () => !inked,
    mark: () => { inked = true; },
    clear: () => { ctx.clearRect(0, 0, canvas.width, canvas.height); inked = false; if (key.startsWith('stage1_')) validateCheckForm(); },
    toDataURL: () => canvas.toDataURL('image/png')
  };
}

function clearSig(key) { if (pads[key]) pads[key].clear(); }
function drawDemoSig(key, label = '示範簽名') {
  const pad = pads[key]; if (!pad) return;
  pad.clear();
  const img = new Image();
  img.onload = () => {
    pad.ctx.drawImage(img, 10, 5, pad.canvas.width - 20, pad.canvas.height - 10);
    pad.mark();
    if (key.startsWith('stage1_')) validateCheckForm();
  };
  img.src = makeDemoSig(label);
}

// -------------------- ROLE AUTH GATE (保護 Tab 2 主管頁 & Tab 3 模板頁) --------------------
function hasAccess(tab) {
  if (tab === 'review') return unlockedRole === 'supervisor' || unlockedRole === 'admin';
  if (tab === 'template') return unlockedRole === 'admin';
  return true;
}

function openAuthModal(tab, tplId = null) {
  pendingAuthTarget = { tab, tplId };
  const isTpl = tab === 'template';
  document.getElementById('auth-modal-title').textContent = isTpl ? '🔒 模板管理員 / DCC 權限驗證' : '🔒 主管簽核權限驗證';
  document.getElementById('auth-modal-desc').textContent = isTpl
    ? '「模板編輯與改版」僅限管理員 / DCC 進入，請輸入管理員密碼（預設 9999）：'
    : '「主管補簽與簽名庫」僅限組長／課(副)長進入，請輸入主管密碼（預設 8888，管理員 9999 亦可）：';
  const input = document.getElementById('auth-pin-input');
  input.value = '';
  document.getElementById('auth-error-msg').classList.add('hidden');
  document.getElementById('auth-modal').classList.remove('hidden');
  setTimeout(() => input.focus(), 50);
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.add('hidden');
  pendingAuthTarget = null;
}

function submitAuthPin() {
  const pin = document.getElementById('auth-pin-input').value.trim();
  const errEl = document.getElementById('auth-error-msg');
  if (!pendingAuthTarget) return;
  const { tab, tplId } = pendingAuthTarget;

  if (tab === 'template') {
    if (pin !== ROLE_PINS.admin) {
      errEl.textContent = '❌ 管理員密碼錯誤，無權進入模板編輯頁！';
      errEl.classList.remove('hidden');
      return;
    }
    unlockedRole = 'admin';
  } else if (tab === 'review') {
    if (pin === ROLE_PINS.admin) unlockedRole = 'admin';
    else if (pin === ROLE_PINS.supervisor) unlockedRole = 'supervisor';
    else {
      errEl.textContent = '❌ 主管密碼錯誤，現場人員無法進入補簽頁！';
      errEl.classList.remove('hidden');
      return;
    }
  }

  updateRoleUI();
  const nextTab = tab;
  const nextTpl = tplId;
  closeAuthModal();
  if (nextTpl) editingTplId = nextTpl;
  showToast(unlockedRole === 'admin' ? '已驗證管理員權限（全功能解鎖）' : '已驗證主管權限（可進行補簽與管理簽名庫）', '🔓');
  switchTab(nextTab);
}

function logoutRole() {
  unlockedRole = null;
  updateRoleUI();
  showToast('已鎖定主管／管理員權限，切回一般現場檢點模式', '🔒');
  switchTab('lobby');
}

function updateRoleUI() {
  const badge = document.getElementById('role-badge');
  const btnOut = document.getElementById('btn-logout-role');
  if (!badge || !btnOut) return;
  if (unlockedRole) {
    badge.textContent = unlockedRole === 'admin' ? '🔓 管理員/DCC' : '🔓 主管';
    badge.classList.remove('hidden');
    btnOut.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
    btnOut.classList.add('hidden');
  }
}

// -------------------- NAVIGATION --------------------
function switchTab(tab) {
  if (!hasAccess(tab)) {
    openAuthModal(tab);
    return;
  }
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
  const target = document.getElementById('tab-' + tab);
  if (target) target.classList.remove('hidden');
  document.querySelectorAll('.tab-btn').forEach(b => {
    const act = b.dataset.tab === tab;
    b.className = act
      ? 'tab-btn px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5 bg-[var(--primary)] text-[var(--primary-foreground)]'
      : 'tab-btn px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5 bg-[var(--background)] text-[var(--muted-foreground)] border border-[var(--border)]';
  });
  if (tab === 'lobby') renderLobby();
  if (tab === 'check') renderCheckTab();
  if (tab === 'review') renderReviewTab();
  if (tab === 'template') renderTemplateTab();
  if (tab === 'export') renderExportTab();
}

// -------------------- TAB 0: LOBBY (表單選擇大廳 + 共享作業中暫存區) --------------------
async function refreshCloudDrafts() {
  if (isCloudEnabled() && isOnline) {
    try {
      const dRes = await apiFetch('/api/drafts');
      if (dRes && Array.isArray(dRes.drafts)) {
        drafts = dRes.drafts;
        saveLocal();
        renderLobby();
        showToast(`已同步雲端共享暫存區（共 ${drafts.length} 筆作業中）`, '🔄');
        return;
      }
    } catch (e) {}
  }
  renderLobby();
  showToast('已更新暫存清單（本機模式）', '🔄');
}

function renderLobby() {
  // 1. Render In-Progress Drafts with Plant Filter
  const dPanel = document.getElementById('lobby-drafts-panel');
  const dGrid = document.getElementById('lobby-drafts-grid');
  const dBadge = document.getElementById('drafts-count-badge');
  const plantFilterEl = document.getElementById('draft-plant-filter');
  if (dPanel && dGrid) {
    dPanel.classList.toggle('hidden', drafts.length === 0);
    // Collect unique plants from templates + drafts
    const plantSet = new Set();
    templates.forEach(t => (t.plants || []).forEach(p => plantSet.add(p)));
    drafts.forEach(d => { if (d.meta && d.meta.plant) plantSet.add(d.meta.plant); });
    if (plantFilterEl) {
      plantFilterEl.innerHTML = `<option value="ALL" ${draftPlantFilter === 'ALL' ? 'selected' : ''}>全部廠區 (${drafts.length})</option>` +
        Array.from(plantSet).map(p => {
          const cnt = drafts.filter(d => d.meta && d.meta.plant === p).length;
          return `<option value="${p}" ${draftPlantFilter === p ? 'selected' : ''}>${p} (${cnt})</option>`;
        }).join('');
    }
    const visibleDrafts = draftPlantFilter === 'ALL' ? drafts : drafts.filter(d => d.meta && d.meta.plant === draftPlantFilter);
    if (dBadge) dBadge.textContent = `${visibleDrafts.length} 筆作業中`;
    dGrid.innerHTML = visibleDrafts.length === 0
      ? '<div class="col-span-full text-xs text-[var(--muted-foreground)] py-2">此廠區目前無作業中暫存單</div>'
      : visibleDrafts.map(d => {
        const m = d.meta || {};
        const tag = m.plateNo ? `車牌 ${m.plateNo}` : m.isoNo ? `ISO ${m.isoNo}` : m.tankNo ? `儲槽 ${m.tankNo}` : '未填編號';
        const sigCnt = Object.keys(d.stage1Sigs || {}).length;
        return `
          <div class="rounded-lg border border-amber-500/40 bg-[var(--card)] p-3 flex flex-col justify-between gap-2 text-xs">
            <div>
              <div class="flex items-center justify-between gap-1">
                <span class="font-mono font-bold text-amber-400">${d.shortCode} · ${tag}</span>
                <span class="text-[11px] text-[var(--muted-foreground)]">${d.savedAt}</span>
              </div>
              <div class="font-semibold mt-0.5">${d.title}</div>
              <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">
                ${m.plant || ''} ${m.material ? '· ' + m.material : ''} ｜ 已簽 ${sigCnt}/${d.totalStage1Sigs || 1} 人
              </div>
            </div>
            <div class="flex items-center justify-end gap-1.5 pt-1.5 border-t border-[var(--border)]">
              <button onclick="requestDeleteDraft('${d.id}')" class="px-2 py-1 rounded text-red-400 hover:bg-red-500/10 text-[11px]">刪除</button>
              <button onclick="resumeDraft('${d.id}')" class="px-3 py-1 rounded bg-amber-500 text-slate-950 font-bold text-xs hover:opacity-90">▶ 繼續檢點</button>
            </div>
          </div>
        `;
      }).join('');
  }

  // 2. Render 5 Form Cards
  const latestList = getAllLatestTemplates();
  const grid = document.getElementById('lobby-grid');
  const layoutLabels = {
    single_stage: '單欄分階段＋容積試算',
    dual_compare: '雙欄比對（運輸公司 vs 現場）',
    before_after: '前後對照（接合前 vs 拆卸後）'
  };

  grid.innerHTML = latestList.map(t => {
    const recCount = records.filter(r => r.templateSnapshot.groupKey === t.groupKey).length;
    const pendingCnt = records.filter(r => r.templateSnapshot.groupKey === t.groupKey && r.status !== 'approved').length;
    return `
      <div class="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 flex flex-col justify-between gap-3 hover:border-[var(--primary)] transition">
        <div class="space-y-2">
          <div class="flex items-center justify-between gap-2">
            <span class="px-2 py-0.5 rounded bg-[var(--primary)]/15 text-[var(--primary)] font-mono text-xs font-bold">${t.shortCode} · ${t.category}</span>
            <span class="text-[11px] font-mono text-[var(--muted-foreground)]">${t.formCode}</span>
          </div>
          <h3 class="text-base font-bold leading-snug">${t.title}</h3>
          <div class="text-xs text-[var(--muted-foreground)] space-y-0.5">
            <div>版型：${layoutLabels[t.layoutType] || t.layoutType}（共 ${t.items.length} 項）</div>
            <div>簽核：${t.signers.map(s => s.label).join(' → ')}</div>
          </div>
        </div>
        <div class="pt-3 border-t border-[var(--border)] flex items-center justify-between gap-2">
          <div class="text-[11px] text-[var(--muted-foreground)]">
            已填 ${recCount} 筆 ${pendingCnt > 0 ? `<span class="text-amber-500 font-bold">(${pendingCnt} 待簽)</span>` : ''}
          </div>
          <div class="flex gap-1.5">
            <button onclick="openTemplateEditor('${t.id}')" class="px-2.5 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)] text-xs hover:opacity-80">🔒 改模板</button>
            <button onclick="startChecklist('${t.groupKey}')" class="px-3 py-1.5 rounded-md bg-[var(--primary)] text-[var(--primary-foreground)] text-xs font-bold hover:opacity-90">開始檢點 →</button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function initMetaForTemplate(tpl) {
  activeDraftId = null;
  currentMeta = {
    plant: (tpl.plants && tpl.plants[0]) || '彰濱1廠(線西)',
    date: todayIso(),
    tankNo: 'T-102',
    pumpNo: 'P-102A',
    material: '醋酸 (GAA)',
    volA: 100, volB: 45, volC: 55, sg: 1.05, mtAvail: 57.8, trucks: 2.3, mtPlan: 25,
    carrier: '', plateNo: '', shipNotice: '', isoNo: '',
    opType: (tpl.opTypeOptions && tpl.opTypeOptions[0]) || '',
    remark: ''
  };
  currentAnswers = {};
  currentStage1Sigs = {};
}

function captureCurrentStage1Sigs(tpl) {
  const stage1Signers = tpl.signers.filter(s => s.role === 'operator' || s.role === 'qc');
  const out = {};
  stage1Signers.forEach(s => {
    const pad = pads['stage1_' + s.key];
    if (pad && !pad.isEmpty()) {
      out[s.key] = pad.toDataURL();
    } else if (currentStage1Sigs[s.key]) {
      out[s.key] = currentStage1Sigs[s.key];
    }
  });
  return out;
}

async function saveAsDraft() {
  const tpl = getLatestTemplate(activeGroupKey);
  const stage1Signers = tpl.signers.filter(s => s.role === 'operator' || s.role === 'qc');
  const sigs = captureCurrentStage1Sigs(tpl);
  const draftObj = {
    id: activeDraftId || ('DRAFT-' + Date.now().toString().slice(-6)),
    groupKey: tpl.groupKey,
    shortCode: tpl.shortCode,
    title: tpl.title,
    savedAt: nowTaipei(),
    meta: JSON.parse(JSON.stringify(currentMeta)),
    answers: JSON.parse(JSON.stringify(currentAnswers)),
    stage1Sigs: sigs,
    totalStage1Sigs: stage1Signers.length
  };
  const idx = drafts.findIndex(d => d.id === draftObj.id);
  if (idx >= 0) drafts[idx] = draftObj;
  else drafts.unshift(draftObj);
  saveLocal();
  if (isCloudEnabled() && isOnline) {
    apiFetch('/api/drafts', { method: 'POST', body: JSON.stringify(draftObj) }).catch(() => {});
  }
  showToast(`已暫存「${tpl.shortCode} ${tpl.title}」進度！可先去開別台檢點表`, '💾');
  switchTab('lobby');
}

function resumeDraft(draftId) {
  const d = drafts.find(x => x.id === draftId);
  if (!d) return;
  activeGroupKey = d.groupKey;
  activeDraftId = d.id;
  currentMeta = JSON.parse(JSON.stringify(d.meta || {}));
  currentAnswers = JSON.parse(JSON.stringify(d.answers || {}));
  currentStage1Sigs = JSON.parse(JSON.stringify(d.stage1Sigs || {}));
  switchTab('check');
  showToast(`已還原暫存單「${d.shortCode} ${d.title}」，可接著完成剩餘項目與簽名`, '▶');
}

function requestDeleteDraft(draftId) {
  const d = drafts.find(x => x.id === draftId);
  if (!d) return;
  pendingDeleteDraftId = draftId;
  const m = d.meta || {};
  const tag = m.plateNo ? `車牌 ${m.plateNo}` : m.isoNo ? `ISO ${m.isoNo}` : m.tankNo ? `儲槽 ${m.tankNo}` : '未填編號';
  const sigCnt = Object.keys(d.stage1Sigs || {}).length;
  document.getElementById('delete-draft-desc').innerHTML =
    `確定要刪除以下作業中暫存單嗎？刪除後<strong>無法復原</strong>：<br/><br/>` +
    `• 表單：<strong>${d.shortCode} ${d.title}</strong><br/>` +
    `• 對象：<strong>${m.plant || ''} · ${tag} ${m.material ? '(' + m.material + ')' : ''}</strong><br/>` +
    `• 已簽人數：<strong>${sigCnt}/${d.totalStage1Sigs || 1} 人</strong>（暫存於 ${d.savedAt}）`;
  document.getElementById('delete-draft-modal').classList.remove('hidden');
}

function closeDeleteDraftModal() {
  document.getElementById('delete-draft-modal').classList.add('hidden');
  pendingDeleteDraftId = null;
}

async function confirmDeleteDraft() {
  if (!pendingDeleteDraftId) return;
  const delId = pendingDeleteDraftId;
  drafts = drafts.filter(d => d.id !== delId);
  if (activeDraftId === delId) activeDraftId = null;
  saveLocal();
  if (isCloudEnabled() && isOnline) {
    apiFetch(`/api/drafts/${encodeURIComponent(delId)}`, { method: 'DELETE' }).catch(() => {});
  }
  closeDeleteDraftModal();
  renderLobby();
  showToast('已確認刪除該筆暫存檢點單', '🗑️');
}

function startChecklist(groupKey) {
  activeGroupKey = groupKey;
  initMetaForTemplate(getLatestTemplate(groupKey));
  switchTab('check');
}

function openTemplateEditor(tplId) {
  if (!hasAccess('template')) {
    openAuthModal('template', tplId);
    return;
  }
  editingTplId = tplId;
  switchTab('template');
}

// -------------------- TAB 1: DYNAMIC CHECKLIST ENGINE --------------------
function isItemFail(tpl, it, a) {
  if (!a) return false;
  if (tpl.layoutType === 'single_stage') {
    const normal = it.normalChoice || '是';
    const abnormal = normal === '是' ? '否' : '是';
    if (it.mode !== 'num_only' && a.choice === abnormal) return true;
    if (it.maxOk && a.num !== '' && !isNaN(parseFloat(a.num)) && parseFloat(a.num) > it.maxOk) return true;
    return false;
  }
  if (tpl.layoutType === 'dual_compare') {
    const normal = it.normalChoice || '是';
    const abnormal = normal === '是' ? '否' : '是';
    if (it.mode === 'yn' || it.mode === 'yn_num') {
      if (!it.leftDisabled && a.left === abnormal) return true;
      if (a.right === abnormal) return true;
    }
    if (it.maxOk && a.num !== '' && !isNaN(parseFloat(a.num)) && parseFloat(a.num) > it.maxOk) return true;
    return false;
  }
  if (tpl.layoutType === 'before_after') {
    if (a.before === 'X' || a.after === 'X') return true;
    if (it.mode === 'num') {
      const checkNum = v => {
        if (v === '' || v === undefined) return false;
        const n = parseFloat(v);
        if (isNaN(n)) return false;
        if (it.maxOk !== undefined && n > it.maxOk) return true;
        if (it.minOk !== undefined && n < it.minOk) return true;
        return false;
      };
      if (!it.beforeDisabled && checkNum(a.before)) return true;
      if (checkNum(a.after)) return true;
    }
    return false;
  }
  return false;
}

function setPumpNA() {
  const el = document.getElementById('m-pump');
  if (el) el.value = '＼ (無此項)';
  currentMeta.pumpNo = '＼';
  const tpl = getLatestTemplate(activeGroupKey);
  tpl.items.filter(it => it.pumpRelated).forEach(it => {
    currentAnswers[it.id] = { choice: '＼', num: '', note: '' };
  });
  renderCheckTab();
  showToast('已標記泵浦為「＼ 無此項」，並自動帶入泵浦相關項為「不適用」', '＼');
}

function recalcVolume() {
  const a = parseFloat(document.getElementById('m-volA')?.value) || 0;
  const b = parseFloat(document.getElementById('m-volB')?.value) || 0;
  const sg = parseFloat(document.getElementById('m-sg')?.value) || 1;
  const plan = parseFloat(document.getElementById('m-mtPlan')?.value) || 0;
  const c = Math.max(0, +(a - b).toFixed(1));
  const mt = +(c * sg).toFixed(1);
  const trucks = +(mt / 25).toFixed(1);
  Object.assign(currentMeta, { volA: a, volB: b, volC: c, sg, mtAvail: mt, trucks, mtPlan: plan });
  if (document.getElementById('m-volC')) document.getElementById('m-volC').value = c;
  if (document.getElementById('m-mtAvail')) document.getElementById('m-mtAvail').value = `${mt} (約${trucks}車)`;
  const warn = document.getElementById('vol-warning');
  if (warn) {
    if (plan > mt) {
      warn.textContent = `⚠️ 警告：預定入槽量 (${plan} M/T) 超過可存數量 (${mt} M/T)，有溢槽風險！`;
      warn.classList.remove('hidden');
    } else warn.classList.add('hidden');
  }
}

function renderCheckTab() {
  const tpl = getLatestTemplate(activeGroupKey);
  // Top switcher
  document.getElementById('check-form-switcher').innerHTML = getAllLatestTemplates().map(t =>
    `<option value="${t.groupKey}" ${t.groupKey === activeGroupKey ? 'selected' : ''}>${t.shortCode} ${t.title} (${t.formCode})</option>`
  ).join('');
  document.getElementById('chk-form-code').textContent = tpl.formCode;
  document.getElementById('chk-wi-ver').textContent = tpl.wiVersion + '（最新生效）';
  document.getElementById('chk-title').textContent = `${tpl.company} — ${tpl.title}`;

  // Dynamic header fields based on layoutType
  const plants = (tpl.plants && tpl.plants.length) ? tpl.plants : ['彰濱1廠(線西)', '彰濱2廠(崙尾)'];
  if (!plants.includes(currentMeta.plant)) currentMeta.plant = plants[0];

  let metaHtml = `
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
      <label class="space-y-1">
        <span class="text-[var(--muted-foreground)] block font-semibold">廠區選擇</span>
        <select onchange="currentMeta.plant=this.value" class="w-full px-2.5 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)]">
          ${plants.map(p => `<option value="${p}" ${p === currentMeta.plant ? 'selected' : ''}>${p}</option>`).join('')}
        </select>
      </label>
      <label class="space-y-1">
        <span class="text-[var(--muted-foreground)] block font-semibold">檢查日期</span>
        <input type="date" value="${currentMeta.date}" onchange="currentMeta.date=this.value" class="w-full px-2.5 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)] font-mono" />
      </label>
  `;

  if (tpl.opTypeOptions && tpl.opTypeOptions.length) {
    metaHtml += `
      <div class="space-y-1">
        <span class="text-[var(--muted-foreground)] block font-semibold">作業別</span>
        <div class="flex gap-2">
          ${tpl.opTypeOptions.map(op => `
            <label class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)] cursor-pointer">
              <input type="radio" name="opType" value="${op}" ${currentMeta.opType === op ? 'checked' : ''} onchange="currentMeta.opType=this.value" />
              <span>${op}</span>
            </label>
          `).join('')}
        </div>
      </div>
    `;
  } else {
    metaHtml += `<div></div>`;
  }

  if (tpl.layoutType === 'single_stage') {
    metaHtml += `
      <label class="space-y-1">
        <span class="text-[var(--muted-foreground)] block font-semibold">儲槽編號</span>
        <input value="${currentMeta.tankNo || ''}" oninput="currentMeta.tankNo=this.value" class="w-full px-2.5 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)] font-mono" />
      </label>
      <label class="space-y-1">
        <span class="text-[var(--muted-foreground)] block font-semibold">卸貨泵浦編號</span>
        <div class="flex gap-1.5">
          <input id="m-pump" value="${currentMeta.pumpNo || ''}" oninput="currentMeta.pumpNo=this.value" class="flex-1 min-w-0 px-2.5 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)] font-mono" />
          <button type="button" onclick="setPumpNA()" class="shrink-0 px-2 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)] hover:opacity-80 font-semibold text-[11px]">＼ 無此項</button>
        </div>
      </label>
      <label class="space-y-1">
        <span class="text-[var(--muted-foreground)] block font-semibold">儲存料品名稱</span>
        <input value="${currentMeta.material || ''}" oninput="currentMeta.material=this.value" class="w-full px-2.5 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)]" />
      </label>
    </div>
    <div class="rounded-lg border border-[var(--border)] bg-[var(--background)] p-3 space-y-2 text-xs mt-3">
      <div class="font-bold text-[var(--primary)]">🧮 儲槽容積自動試算（防溢槽防呆）</div>
      <div class="grid grid-cols-2 sm:grid-cols-6 gap-2 items-end">
        <label class="space-y-1"><span class="text-[11px] text-[var(--muted-foreground)] block">(A) 最大容積 KL</span><input id="m-volA" type="number" step="0.1" value="${currentMeta.volA}" oninput="recalcVolume()" class="w-full px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] font-mono" /></label>
        <label class="space-y-1"><span class="text-[11px] text-[var(--muted-foreground)] block">(B) 目前容積 KL</span><input id="m-volB" type="number" step="0.1" value="${currentMeta.volB}" oninput="recalcVolume()" class="w-full px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] font-mono" /></label>
        <label class="space-y-1"><span class="text-[11px] text-emerald-500 font-bold block">(C) 可存容積 KL</span><input id="m-volC" readonly class="w-full px-2 py-1 rounded border border-emerald-500/40 bg-emerald-500/10 font-mono font-bold text-emerald-500" /></label>
        <label class="space-y-1"><span class="text-[11px] text-[var(--muted-foreground)] block">比重</span><input id="m-sg" type="number" step="0.01" value="${currentMeta.sg}" oninput="recalcVolume()" class="w-full px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] font-mono" /></label>
        <label class="space-y-1"><span class="text-[11px] text-emerald-500 font-bold block">可存數量 M/T</span><input id="m-mtAvail" readonly class="w-full px-2 py-1 rounded border border-emerald-500/40 bg-emerald-500/10 font-mono font-bold text-emerald-500" /></label>
        <label class="space-y-1"><span class="text-[11px] text-[var(--muted-foreground)] block">預定入槽 M/T</span><input id="m-mtPlan" type="number" step="0.1" value="${currentMeta.mtPlan}" oninput="recalcVolume()" class="w-full px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] font-mono" /></label>
      </div>
      <div id="vol-warning" class="hidden text-red-500 font-bold text-xs"></div>
    </div>`;
  } else {
    metaHtml += (tpl.extraHeaderFields || []).map(f => `
      <label class="space-y-1">
        <span class="text-[var(--muted-foreground)] block font-semibold">${f.label}</span>
        <input value="${currentMeta[f.key] || ''}" placeholder="${f.placeholder || ''}" oninput="currentMeta['${f.key}']=this.value" class="w-full px-2.5 py-1.5 rounded-md border border-[var(--border)] bg-[var(--background)]" />
      </label>
    `).join('') + '</div>';
  }
  document.getElementById('dynamic-meta-box').innerHTML = metaHtml;
  if (tpl.layoutType === 'single_stage') recalcVolume();

  // Render items according to layoutType
  const secBox = document.getElementById('checklist-sections');
  if (tpl.layoutType === 'single_stage') {
    const groups = {};
    tpl.items.forEach(it => { (groups[it.section] = groups[it.section] || []).push(it); });
    secBox.innerHTML = Object.entries(groups).map(([sec, list]) => `
      <div class="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 space-y-2">
        <h3 class="text-xs font-bold text-[var(--primary)] border-b border-[var(--border)] pb-1.5">■ ${sec}（${list.length} 項）</h3>
        ${list.map((it, idx) => renderSingleRow(tpl, it, idx)).join('')}
      </div>
    `).join('');
  } else if (tpl.layoutType === 'dual_compare') {
    const groups = {};
    tpl.items.forEach(it => { (groups[it.section] = groups[it.section] || []).push(it); });
    secBox.innerHTML = Object.entries(groups).map(([sec, list]) => `
      <div class="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 space-y-2">
        <div class="flex items-center justify-between border-b border-[var(--border)] pb-1.5 text-xs font-bold">
          <span class="text-[var(--primary)]">■ ${sec}</span>
          <span class="text-[var(--muted-foreground)] hidden sm:inline">${tpl.colLeftLabel} ｜ ${tpl.colRightLabel}</span>
        </div>
        ${list.map(it => renderDualRow(tpl, it)).join('')}
      </div>
    `).join('');
  } else {
    secBox.innerHTML = `
      <div class="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4 space-y-2">
        <div class="flex items-center justify-between border-b border-[var(--border)] pb-1.5 text-xs font-bold">
          <span class="text-[var(--primary)]">■ ISO TANK 檢點項目（V 正常 / X 異常）</span>
          <span class="text-[var(--muted-foreground)]">接合前 ｜ 拆卸後</span>
        </div>
        ${tpl.items.map(it => renderBeforeAfterRow(tpl, it)).join('')}
      </div>
    `;
  }

  // 僅模擬模式顯示一鍵帶入按鈕，正式版嚴禁顯示！
  const demoBtn = document.getElementById('btn-demo-autofill');
  if (demoBtn) demoBtn.classList.toggle('hidden', !CONFIG.demoMode);

  // 現場第一階段簽核：包含操作人員 (operator) 與現場品管人員 (qc)
  const stage1Signers = tpl.signers.filter(s => s.role === 'operator' || s.role === 'qc');

  document.getElementById('stage1-sigs-box').innerHTML = stage1Signers.map(s => `
    <div class="space-y-1.5">
      <div class="flex items-center justify-between gap-2">
        <span class="text-xs font-bold">✍️ ${s.label}手寫簽名</span>
        <div class="flex gap-2">
          ${CONFIG.demoMode ? `<button type="button" onclick="drawDemoSig('stage1_${s.key}','${s.label.slice(0,3)}')" class="px-2 py-0.5 rounded border border-[var(--border)] bg-[var(--background)] text-[11px]">✨ 示範簽名</button>` : ''}
          <button type="button" onclick="clearSig('stage1_${s.key}')" class="px-2 py-0.5 rounded border border-[var(--border)] bg-[var(--background)] text-[11px]">清除</button>
        </div>
      </div>
      <div class="rounded-lg border border-[var(--border)] bg-white p-1.5 max-w-md">
        <canvas id="canvas-stage1-${s.key}" width="400" height="100" class="sig-canvas w-full h-[90px] rounded border border-dashed border-gray-300"></canvas>
      </div>
    </div>
  `).join('');
  stage1Signers.forEach(s => {
    const padKey = 'stage1_' + s.key;
    initPad(padKey, 'canvas-stage1-' + s.key);
    // 若是從暫存還原，直接把之前已簽好的簽名畫回畫布！
    if (currentStage1Sigs[s.key]) {
      const img = new Image();
      img.onload = () => {
        pads[padKey].ctx.drawImage(img, 0, 0, pads[padKey].canvas.width, pads[padKey].canvas.height);
        pads[padKey].mark();
        validateCheckForm();
      };
      img.src = currentStage1Sigs[s.key];
    }
  });

  validateCheckForm();
}

function renderSingleRow(tpl, it, idx) {
  if (!currentAnswers[it.id]) currentAnswers[it.id] = { choice: '', num: '', note: '' };
  const a = currentAnswers[it.id];
  const normal = it.normalChoice || '是';
  const abnormal = normal === '是' ? '否' : '是';
  const fail = isItemFail(tpl, it, a);
  const numHtml = (it.mode === 'yn_num' || it.mode === 'num_only') ? `
    <div class="flex items-center gap-1">
      <input type="number" step="0.1" value="${a.num}" placeholder="實測值"
        oninput="onSingleNum('${it.id}', this.value)"
        class="w-20 px-2 py-1 rounded border border-[var(--border)] bg-[var(--background)] font-mono text-xs" />
      <span class="text-[11px] text-[var(--muted-foreground)]">${it.unit || ''}</span>
    </div>` : '';
  const btnHtml = it.mode !== 'num_only' ? `
    <div id="btns-${it.id}" class="flex gap-1">
      ${['是', '否', '＼'].map(opt => {
        const act = a.choice === opt;
        let cls = 'border-[var(--border)] bg-[var(--background)] text-[var(--muted-foreground)]';
        if (act && opt === normal) cls = 'border-emerald-500 bg-emerald-600 text-white';
        if (act && opt === abnormal) cls = 'border-red-500 bg-red-600 text-white';
        if (act && opt === '＼') cls = 'border-slate-500 bg-slate-600 text-white';
        return `<button type="button" data-opt="${opt}" onclick="onSingleChoice('${it.id}','${opt}')" class="px-2.5 py-1 rounded border text-xs font-bold ${cls}">${opt === '＼' ? '不適用' : opt}</button>`;
      }).join('')}
    </div>` : '';
  return `
    <div id="row-${it.id}" class="p-2.5 rounded-lg border transition ${fail ? 'border-red-500/60 bg-red-500/5' : 'border-[var(--border)] bg-[var(--background)]'}">
      <div class="flex flex-wrap items-center justify-between gap-2">
        <div class="text-xs font-medium">
          <span class="font-mono text-[var(--muted-foreground)] mr-1">${idx + 1}.</span>${it.name}
          ${it.normalChoice === '否' ? '<span class="text-[11px] text-[var(--muted-foreground)]">（正常為「否」）</span>' : ''}
          <span id="warn-${it.id}" class="ml-1.5 text-red-500 font-bold ${fail ? '' : 'hidden'}">⚠️ 異常，請備註原因</span>
        </div>
        <div class="flex flex-wrap items-center gap-2">${numHtml}${btnHtml}</div>
      </div>
      <div id="notebox-${it.id}" class="mt-2 pt-2 border-t border-red-500/30 ${fail ? '' : 'hidden'}">
        <input value="${a.note || ''}" placeholder="⚠️ 請填寫異常原因或立即處置（必填）..." oninput="currentAnswers['${it.id}'].note=this.value; validateCheckForm();" class="w-full px-2.5 py-1 rounded border border-red-500/50 bg-[var(--card)] text-xs" />
      </div>
    </div>
  `;
}

function renderDualRow(tpl, it) {
  if (!currentAnswers[it.id]) currentAnswers[it.id] = { left: '', right: '', num: '', note: '' };
  const a = currentAnswers[it.id];
  const fail = isItemFail(tpl, it, a);
  const opts = it.mode === 'single_double' ? ['單槽', '雙槽'] : it.mode === 'yn_na' ? ['是', '無此項'] : ['是', '否'];

  const mkSide = (side, disabled) => {
    if (disabled) return '<span class="text-xs text-[var(--muted-foreground)] font-mono">＼ (不適用)</span>';
    if (it.mode === 'num_only') {
      return `<input type="number" value="${a[side] || ''}" placeholder="填數字" oninput="currentAnswers['${it.id}']['${side}']=this.value; syncRowState('${it.id}');" class="w-16 px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] font-mono text-xs" /> <span class="text-[11px]">${it.unit || ''}</span>`;
    }
    const normal = it.normalChoice || '是';
    const abnormal = normal === '是' ? '否' : '是';
    return `<div id="btns-${it.id}-${side}" class="flex gap-1">
      ${opts.map(o => {
        const act = a[side] === o;
        let cls = 'border-[var(--border)] bg-[var(--card)] text-[var(--muted-foreground)]';
        if (act && (o === normal || o === '單槽' || o === '雙槽')) cls = 'border-emerald-500 bg-emerald-600 text-white';
        if (act && o === abnormal) cls = 'border-red-500 bg-red-600 text-white';
        if (act && o === '無此項') cls = 'border-slate-500 bg-slate-600 text-white';
        return `<button type="button" data-opt="${o}" onclick="onDualChoice('${it.id}','${side}','${o}')" class="px-2 py-1 rounded border text-[11px] font-bold ${cls}">${o}</button>`;
      }).join('')}
      ${side === 'right' && it.mode === 'yn_num' ? `<input type="number" step="0.1" value="${a.num || ''}" placeholder="${it.unit}" oninput="onDualNum('${it.id}', this.value)" class="w-16 px-1.5 py-0.5 rounded border border-[var(--border)] bg-[var(--card)] font-mono text-xs" />` : ''}
    </div>`;
  };

  return `
    <div id="row-${it.id}" class="p-2.5 rounded-lg border transition ${fail ? 'border-red-500/60 bg-red-500/5' : 'border-[var(--border)] bg-[var(--background)]'}">
      <div class="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center text-xs">
        <div class="sm:col-span-6 font-medium">${it.name}${it.normalChoice === '否' ? ' <span class="text-[11px] text-[var(--muted-foreground)]">(正常=否)</span>' : ''}</div>
        <div class="sm:col-span-3 flex items-center gap-1"><span class="sm:hidden text-[11px] text-[var(--muted-foreground)]">運輸:</span>${mkSide('left', it.leftDisabled)}</div>
        <div class="sm:col-span-3 flex items-center gap-1"><span class="sm:hidden text-[11px] text-[var(--muted-foreground)]">現場:</span>${mkSide('right', false)}</div>
      </div>
      <div id="notebox-${it.id}" class="mt-2 pt-2 border-t border-red-500/30 ${fail ? '' : 'hidden'}">
        <input value="${a.note || ''}" placeholder="⚠️ 異常原因或處置備註（必填）..." oninput="currentAnswers['${it.id}'].note=this.value; validateCheckForm();" class="w-full px-2.5 py-1 rounded border border-red-500/50 bg-[var(--card)] text-xs" />
      </div>
    </div>
  `;
}

function renderBeforeAfterRow(tpl, it) {
  if (!currentAnswers[it.id]) currentAnswers[it.id] = { before: '', after: '', note: '' };
  const a = currentAnswers[it.id];
  const fail = isItemFail(tpl, it, a);
  const mkPhase = (phase, disabled) => {
    if (disabled) return '<span class="text-xs text-[var(--muted-foreground)] font-mono">＼</span>';
    if (it.mode === 'vx') {
      return `<div id="btns-${it.id}-${phase}" class="flex gap-1">
        ${['V', 'X'].map(o => {
          const act = a[phase] === o;
          const cls = act ? (o === 'V' ? 'border-emerald-500 bg-emerald-600 text-white' : 'border-red-500 bg-red-600 text-white') : 'border-[var(--border)] bg-[var(--card)] text-[var(--muted-foreground)]';
          return `<button type="button" data-opt="${o}" onclick="onBeforeAfter('${it.id}','${phase}','${o}')" class="px-2.5 py-1 rounded border text-xs font-bold ${cls}">${o}</button>`;
        }).join('')}
      </div>`;
    }
    return `<input type="${it.mode === 'num' ? 'number' : 'text'}" step="0.1" value="${a[phase] || ''}" placeholder="${it.unit || '輸入紀錄'}" oninput="currentAnswers['${it.id}']['${phase}']=this.value; syncRowState('${it.id}');" class="w-24 px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] font-mono text-xs" />`;
  };
  return `
    <div id="row-${it.id}" class="p-2.5 rounded-lg border transition ${fail ? 'border-red-500/60 bg-red-500/5' : 'border-[var(--border)] bg-[var(--background)]'}">
      <div class="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center text-xs">
        <div class="sm:col-span-5 font-medium">${it.name} <span class="text-[11px] text-[var(--muted-foreground)]">[${it.stateLabel}]</span></div>
        <div class="sm:col-span-2 flex items-center gap-1"><span class="sm:hidden text-[11px]">前:</span>${mkPhase('before', it.beforeDisabled)}</div>
        <div class="sm:col-span-2 flex items-center gap-1"><span class="sm:hidden text-[11px]">後:</span>${mkPhase('after', false)}</div>
        <div class="sm:col-span-3"><input value="${a.note || ''}" placeholder="備註" oninput="currentAnswers['${it.id}'].note=this.value; validateCheckForm();" class="w-full px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] text-xs" /></div>
      </div>
    </div>
  `;
}

// In-place UI sync (NEVER rebuilds inputs, so cursor never jumps!)
function syncRowState(id) {
  const tpl = getLatestTemplate(activeGroupKey);
  const it = tpl.items.find(x => x.id === id);
  if (!it) return;
  const a = currentAnswers[id] || {};
  const fail = isItemFail(tpl, it, a);
  const row = document.getElementById('row-' + id);
  if (row) row.className = `p-2.5 rounded-lg border transition ${fail ? 'border-red-500/60 bg-red-500/5' : 'border-[var(--border)] bg-[var(--background)]'}`;
  const warn = document.getElementById('warn-' + id);
  if (warn) warn.classList.toggle('hidden', !fail);
  const notebox = document.getElementById('notebox-' + id);
  if (notebox) notebox.classList.toggle('hidden', !fail);

  // Sync button active styles
  const normal = it.normalChoice || '是';
  const abnormal = normal === '是' ? '否' : '是';
  const singleBtns = document.getElementById('btns-' + id);
  if (singleBtns) {
    singleBtns.querySelectorAll('button').forEach(b => {
      const o = b.dataset.opt, act = a.choice === o;
      let cls = 'border-[var(--border)] bg-[var(--background)] text-[var(--muted-foreground)]';
      if (act && o === normal) cls = 'border-emerald-500 bg-emerald-600 text-white';
      if (act && o === abnormal) cls = 'border-red-500 bg-red-600 text-white';
      if (act && o === '＼') cls = 'border-slate-500 bg-slate-600 text-white';
      b.className = `px-2.5 py-1 rounded border text-xs font-bold ${cls}`;
    });
  }
  ['left', 'right', 'before', 'after'].forEach(side => {
    const grp = document.getElementById(`btns-${id}-${side}`);
    if (!grp) return;
    grp.querySelectorAll('button').forEach(b => {
      const o = b.dataset.opt, act = a[side] === o;
      let cls = 'border-[var(--border)] bg-[var(--card)] text-[var(--muted-foreground)]';
      if (act && (o === normal || o === 'V' || o === '單槽' || o === '雙槽')) cls = 'border-emerald-500 bg-emerald-600 text-white';
      if (act && (o === abnormal || o === 'X')) cls = 'border-red-500 bg-red-600 text-white';
      if (act && o === '無此項') cls = 'border-slate-500 bg-slate-600 text-white';
      b.className = `px-2 py-1 rounded border text-[11px] font-bold ${cls}`;
    });
  });
  validateCheckForm();
}

function onSingleChoice(id, opt) { currentAnswers[id].choice = opt; syncRowState(id); }
function onSingleNum(id, val) {
  const tpl = getLatestTemplate(activeGroupKey);
  const it = tpl.items.find(x => x.id === id);
  currentAnswers[id].num = val;
  if (val !== '' && it.maxOk) {
    const n = parseFloat(val);
    if (!isNaN(n)) currentAnswers[id].choice = n <= it.maxOk ? '是' : '否';
  }
  syncRowState(id);
}
function onDualChoice(id, side, opt) { currentAnswers[id][side] = opt; syncRowState(id); }
function onDualNum(id, val) {
  const tpl = getLatestTemplate(activeGroupKey);
  const it = tpl.items.find(x => x.id === id);
  currentAnswers[id].num = val;
  if (val !== '' && it.maxOk) {
    const n = parseFloat(val);
    if (!isNaN(n)) currentAnswers[id].right = n <= it.maxOk ? '是' : '否';
  }
  syncRowState(id);
}
function onBeforeAfter(id, phase, opt) { currentAnswers[id][phase] = opt; syncRowState(id); }

function quickFillNormal() {
  const tpl = getLatestTemplate(activeGroupKey);
  tpl.items.forEach(it => {
    if (tpl.layoutType === 'single_stage') {
      const n = it.normalChoice || '是';
      currentAnswers[it.id] = { choice: n, num: it.maxOk ? String(+(it.maxOk * 0.5).toFixed(1)) : '', note: '' };
    } else if (tpl.layoutType === 'dual_compare') {
      const n = it.mode === 'single_double' ? '單槽' : it.mode === 'num_only' ? '2' : (it.normalChoice || '是');
      currentAnswers[it.id] = { left: it.leftDisabled ? '' : n, right: n, num: it.maxOk ? String(+(it.maxOk * 0.5).toFixed(1)) : '', note: '' };
    } else {
      const val = it.mode === 'vx' ? 'V' : it.mode === 'num' ? String(it.minOk ? 0.8 : 4.2) : '0';
      currentAnswers[it.id] = { before: it.beforeDisabled ? '' : val, after: val, note: '' };
    }
  });
  renderCheckTab();
  showToast(`已一鍵帶入「${tpl.shortCode} ${tpl.title}」全部示範正常值`, '⚡');
}

function validateCheckForm() {
  const tpl = getLatestTemplate(activeGroupKey);
  let ng = 0, missingNote = 0;
  tpl.items.forEach(it => {
    const a = currentAnswers[it.id] || {};
    if (isItemFail(tpl, it, a)) {
      ng++;
      if (!a.note || !a.note.trim()) missingNote++;
    }
  });
  const stage1Signers = tpl.signers.filter(s => s.role === 'operator' || s.role === 'qc');
  const missingSigners = stage1Signers.filter(s => !pads['stage1_' + s.key] || pads['stage1_' + s.key].isEmpty());

  const guard = document.getElementById('submit-guard');
  const btn = document.getElementById('btn-submit');
  const errs = [];
  if (missingNote > 0) errs.push(`有 ${missingNote} 項異常尚未填寫備註原因`);
  if (missingSigners.length > 0) errs.push(`尚缺 ${missingSigners.map(s => s.label).join('、')} 手寫簽名（可先按「💾 暫存進度」稍後補簽）`);
  document.getElementById('progress-text').textContent = `表單：${tpl.shortCode}（共 ${tpl.items.length} 項）｜異常項：${ng}`;
  if (errs.length) {
    guard.textContent = '送出前防呆檢查：' + errs.join('、');
    guard.classList.remove('hidden');
    btn.disabled = true;
  } else {
    guard.classList.add('hidden');
    btn.disabled = false;
  }
}

async function submitChecklist() {
  const tpl = getLatestTemplate(activeGroupKey);
  const now = nowTaipei();
  const stage1Signers = tpl.signers.filter(s => s.role === 'operator' || s.role === 'qc');
  const signatures = {};
  stage1Signers.forEach(s => {
    signatures[s.key] = { name: s.label, dataUrl: pads['stage1_' + s.key].toDataURL(), signedAt: now };
  });

  const rec = {
    id: `CHK-${tpl.shortCode.replace('.', '')}-${Date.now().toString().slice(-5)}`,
    createdAt: now,
    status: 'pending',
    templateSnapshot: JSON.parse(JSON.stringify(tpl)),
    meta: JSON.parse(JSON.stringify(currentMeta)),
    answers: JSON.parse(JSON.stringify(currentAnswers)),
    signatures
  };

  // 若此單來自暫存區，正式送出後自動移除該筆暫存（同步清除雲端 D1 暫存）
  const finishedDraftId = activeDraftId;
  if (finishedDraftId) {
    drafts = drafts.filter(d => d.id !== finishedDraftId);
    activeDraftId = null;
    if (isCloudEnabled() && isOnline) {
      apiFetch(`/api/drafts/${encodeURIComponent(finishedDraftId)}`, { method: 'DELETE' }).catch(() => {});
    }
  }

  initMetaForTemplate(tpl);
  if (isOnline) {
    records.unshift(rec);
    if (CONFIG.apiBase) {
      try { await apiFetch('/api/records', { method: 'POST', body: JSON.stringify(rec) }); }
      catch (e) { offlineQueue.push(rec); }
    }
    saveLocal();
    selectedReviewId = rec.id;
    updateBadges();
    showToast(`已送出 ${rec.id}（鎖定版面 ${tpl.formCode}），已通知主管補簽`, '✅');
    // 現場人員無權進主管頁，送出後導向匯出預覽或回大廳
    if (hasAccess('review')) switchTab('review');
    else openExport(rec.id);
  } else {
    offlineQueue.push(rec);
    saveLocal();
    updateBadges();
    renderCheckTab();
    showToast(`目前離線：已暫存至本機佇列 (${rec.id})`, '📦');
  }
}

// -------------------- TAB 2: MULTI-TIER REVIEW & SAVED SIG VAULT --------------------
function renderReviewTab() {
  document.getElementById('review-list').innerHTML = records.map(r => {
    const act = r.id === selectedReviewId;
    const done = r.status === 'approved';
    const badge = done
      ? '<span class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-500 text-[11px] font-bold">簽核完成鎖定</span>'
      : '<span class="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-500 text-[11px] font-bold">待主管補簽</span>';
    return `
      <button onclick="selectedReviewId='${r.id}'; renderReviewTab();" class="w-full text-left p-3 rounded-lg border transition ${act ? 'border-[var(--primary)] bg-[var(--primary)]/10' : 'border-[var(--border)] bg-[var(--background)]'}">
        <div class="flex items-center justify-between gap-2">
          <span class="font-mono text-xs font-bold">${r.id}</span>
          ${badge}
        </div>
        <div class="text-xs font-semibold mt-1">${r.templateSnapshot.shortCode} ${r.templateSnapshot.title}</div>
        <div class="text-[11px] text-[var(--muted-foreground)] mt-0.5">${r.templateSnapshot.formCode} ｜ ${r.createdAt}</div>
      </button>
    `;
  }).join('');

  const rec = records.find(r => r.id === selectedReviewId) || records[0];
  const pane = document.getElementById('review-detail');
  if (!rec) return;

  const signers = rec.templateSnapshot.signers || [];
  pane.innerHTML = `
    <div class="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-[var(--border)]">
      <div>
        <div class="text-xs font-mono text-[var(--muted-foreground)]">${rec.id} ｜ 鎖定版次：${rec.templateSnapshot.formCode}</div>
        <h3 class="text-sm font-bold">${rec.templateSnapshot.title}（${rec.meta.plant || ''}）</h3>
      </div>
      <button onclick="openExport('${rec.id}')" class="px-2.5 py-1.5 rounded-md bg-[var(--primary)] text-[var(--primary-foreground)] text-xs font-bold hover:opacity-90">
        📄 預覽 / 匯出 PDF & .xlsx
      </button>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
      ${signers.map(s => {
        const sig = rec.signatures && rec.signatures[s.key];
        const vaultKey = savedSigs[s.role] ? s.role : (s.role === 'manager' ? 'manager' : s.role === 'leader' ? 'leader' : s.role === 'qc' ? 'qc' : null);
        const hasVault = vaultKey && savedSigs[vaultKey] && savedSigs[vaultKey].dataUrl;
        return `
          <div class="rounded-lg border ${sig ? 'border-emerald-500/40' : 'border-amber-500/50'} bg-[var(--background)] p-3 space-y-1.5">
            <div class="font-bold ${sig ? 'text-emerald-500' : 'text-amber-500'}">${s.label}${sig ? '（已簽）' : '（待簽）'}</div>
            ${sig ? `
              <div class="bg-white rounded p-1 border border-gray-200"><img src="${sig.dataUrl}" class="h-10 mx-auto object-contain" /></div>
              <div class="text-[11px] text-[var(--muted-foreground)]">${sig.name || ''}<br/>${sig.signedAt || ''}</div>
            ` : `
              ${hasVault ? `<button type="button" onclick="applyVaultSig('${rec.id}','${s.key}','${vaultKey}')" class="w-full py-1.5 rounded bg-[var(--primary)] text-[var(--primary-foreground)] font-bold text-xs hover:opacity-90">📌 一鍵呼叫「${savedSigs[vaultKey].name}」簽名</button>` : ''}
              <div class="flex justify-between text-[11px] pt-0.5">
                ${CONFIG.demoMode ? `<button type="button" onclick="drawDemoSig('rev_${s.key}','${s.label.slice(0,3)}')" class="underline text-[var(--primary)]">示範手寫</button>` : '<span></span>'}
                ${vaultKey ? `<button type="button" onclick="savePadToVault('rev_${s.key}','${vaultKey}')" class="underline text-emerald-500">💾 存入常用</button>` : ''}
                <button type="button" onclick="clearSig('rev_${s.key}')" class="underline text-[var(--muted-foreground)]">清除</button>
              </div>
              <div class="bg-white rounded p-1 border border-gray-300"><canvas id="sig-rev-${s.key}" width="220" height="68" class="sig-canvas w-full h-[58px]"></canvas></div>
              <button onclick="signReviewPad('${rec.id}','${s.key}','${s.label}')" class="w-full py-1 rounded bg-emerald-600 text-white font-bold text-xs">以手寫確認簽核</button>
            `}
          </div>
        `;
      }).join('')}
    </div>
  `;

  signers.forEach(s => {
    if (!(rec.signatures && rec.signatures[s.key])) initPad('rev_' + s.key, 'sig-rev-' + s.key);
  });
  renderSigVault();
}

function renderSigVault() {
  const grid = document.getElementById('sig-vault-grid');
  if (!grid) return;
  grid.innerHTML = ['leader', 'manager'].map(role => {
    const s = savedSigs[role];
    return `
      <div class="rounded-lg border border-[var(--border)] bg-[var(--background)] p-3 space-y-2 text-xs">
        <div class="flex items-center justify-between">
          <span class="font-bold">${s.roleLabel}</span>
          <span class="text-[11px] text-[var(--muted-foreground)]">${s.updatedAt || ''}</span>
        </div>
        <div class="flex items-center gap-1.5">
          <input value="${s.name}" onchange="savedSigs['${role}'].name=this.value; saveLocal(); renderReviewTab();" class="flex-1 min-w-0 px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] text-xs" />
          <label class="px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)] cursor-pointer font-semibold text-[11px]">📎 上傳<input type="file" accept="image/*" class="hidden" onchange="uploadVaultSig(event,'${role}')" /></label>
          <button onclick="savedSigs['${role}'].dataUrl=''; saveLocal(); renderReviewTab();" class="px-1.5 py-1 text-red-500 text-[11px]">清</button>
        </div>
        <div class="bg-white rounded border border-gray-200 p-1.5 h-[56px] flex items-center justify-center">
          ${s.dataUrl ? `<img src="${s.dataUrl}" class="max-h-[44px] object-contain" />` : '<span class="text-gray-400 text-[11px]">尚未存入簽名</span>'}
        </div>
      </div>
    `;
  }).join('');
}

function uploadVaultSig(e, role) {
  const f = e.target.files[0]; if (!f) return;
  const r = new FileReader();
  r.onload = () => {
    savedSigs[role].dataUrl = r.result;
    savedSigs[role].updatedAt = nowTaipei();
    saveLocal();
    if (CONFIG.apiBase && isOnline) apiFetch('/api/signatures', { method: 'POST', body: JSON.stringify({ role, ...savedSigs[role] }) }).catch(() => {});
    renderReviewTab();
    showToast(`已儲存 ${savedSigs[role].roleLabel} 常用簽名圖檔`, '📎');
  };
  r.readAsDataURL(f);
}

function savePadToVault(padKey, role) {
  if (!pads[padKey] || pads[padKey].isEmpty()) return showToast('請先在畫布手寫再存入', '⚠️');
  savedSigs[role].dataUrl = pads[padKey].toDataURL();
  savedSigs[role].updatedAt = nowTaipei();
  saveLocal();
  if (CONFIG.apiBase && isOnline) apiFetch('/api/signatures', { method: 'POST', body: JSON.stringify({ role, ...savedSigs[role] }) }).catch(() => {});
  renderReviewTab();
  showToast(`已存成「${savedSigs[role].name}」常用簽名檔`, '💾');
}

async function commitSignature(recId, signerKey, name, dataUrl) {
  const rec = records.find(r => r.id === recId);
  if (!rec) return;
  rec.signatures = rec.signatures || {};
  rec.signatures[signerKey] = { name, dataUrl, signedAt: nowTaipei() };
  const allSigned = (rec.templateSnapshot.signers || []).every(s => rec.signatures[s.key]);
  if (allSigned) rec.status = 'approved';
  saveLocal();
  if (CONFIG.apiBase && isOnline) {
    apiFetch(`/api/records/${encodeURIComponent(recId)}/sign`, {
      method: 'POST',
      body: JSON.stringify({ signerKey, name, dataUrl, status: rec.status })
    }).catch(() => {});
  }
  updateBadges();
  renderReviewTab();
  showToast(allSigned ? `全部簽核完成並鎖定 (${recId})！` : `已完成「${name}」簽核`, allSigned ? '🔒' : '✍️');
}

function applyVaultSig(recId, signerKey, vaultKey) {
  const s = savedSigs[vaultKey];
  if (!s || !s.dataUrl) return;
  if (requirePin) {
    const p = prompt(`請輸入 ${s.name} 的簽核 PIN 碼（預設 1234）：`);
    if (p === null) return;
    if (p.trim() !== s.pin) return showToast('PIN 碼錯誤！', '🚫');
  }
  commitSignature(recId, signerKey, s.name, s.dataUrl);
}

function signReviewPad(recId, signerKey, label) {
  const pad = pads['rev_' + signerKey];
  if (!pad || pad.isEmpty()) return showToast('請先手寫簽名或點示範手寫', '⚠️');
  commitSignature(recId, signerKey, label, pad.toDataURL());
}

// -------------------- TAB 3: TEMPLATE EDITOR & REV UPGRADE --------------------
function renderTemplateTab() {
  const sel = document.getElementById('tpl-select');
  sel.innerHTML = templates.map(t => `<option value="${t.id}" ${t.id === editingTplId ? 'selected' : ''}>${t.shortCode} ${t.formCode} ${t.isLatest ? '(最新)' : '(舊版)'}</option>`).join('');
  const tpl = templates.find(t => t.id === editingTplId) || templates[0];
  editingTplId = tpl.id;

  document.getElementById('ed-company').value = tpl.company;
  document.getElementById('ed-title').value = tpl.title;
  document.getElementById('ed-formcode').value = tpl.formCode;
  document.getElementById('ed-wiver').value = tpl.wiVersion;
  document.getElementById('ed-plants').value = (tpl.plants || []).join(', ');
  document.getElementById('ed-plantmode').value = tpl.plantDisplayMode || 'checkbox';

  document.getElementById('ed-items').innerHTML = tpl.items.map((it, idx) => `
    <div class="grid grid-cols-1 sm:grid-cols-12 gap-2 items-center p-2 rounded border border-[var(--border)] bg-[var(--background)] text-xs">
      <input value="${it.section || it.stateLabel || ''}" onchange="updateTplField(${idx},'${it.section !== undefined ? 'section' : 'stateLabel'}',this.value)" class="sm:col-span-2 px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)]" placeholder="分類/狀態" />
      <input value="${it.name}" onchange="updateTplField(${idx},'name',this.value)" class="sm:col-span-6 px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)]" />
      <select onchange="updateTplField(${idx},'normalChoice',this.value)" class="sm:col-span-3 px-2 py-1 rounded border border-[var(--border)] bg-[var(--card)]">
        <option value="是" ${(it.normalChoice || '是') === '是' ? 'selected' : ''}>正常=是 / V</option>
        <option value="否" ${it.normalChoice === '否' ? 'selected' : ''}>正常=否 (反向異常)</option>
      </select>
      <button onclick="removeTplItem(${idx})" class="sm:col-span-1 text-red-500 font-bold">✕</button>
    </div>
  `).join('');
}

function updateTplField(idx, field, val) {
  const tpl = templates.find(t => t.id === editingTplId);
  if (tpl && tpl.items[idx]) tpl.items[idx][field] = val;
}
function addTplItem() {
  const tpl = templates.find(t => t.id === editingTplId);
  const sample = tpl.layoutType === 'before_after'
    ? { id: 'n_' + Date.now(), name: '新增檢點項目', stateLabel: '檢查', mode: 'vx' }
    : { id: 'n_' + Date.now(), section: tpl.items[0]?.section || '檢查項目', name: '新增檢點項目', mode: 'yn', normalChoice: '是' };
  tpl.items.push(sample);
  renderTemplateTab();
}
function removeTplItem(idx) {
  const tpl = templates.find(t => t.id === editingTplId);
  if (tpl.items.length <= 1) return;
  tpl.items.splice(idx, 1);
  renderTemplateTab();
}
async function saveTpl() {
  const tpl = templates.find(t => t.id === editingTplId);
  tpl.company = document.getElementById('ed-company').value.trim();
  tpl.title = document.getElementById('ed-title').value.trim();
  tpl.formCode = document.getElementById('ed-formcode').value.trim();
  tpl.wiVersion = document.getElementById('ed-wiver').value.trim();
  tpl.plants = document.getElementById('ed-plants').value.split(/[,，]/).map(s => s.trim()).filter(Boolean);
  tpl.plantDisplayMode = document.getElementById('ed-plantmode').value;
  saveLocal();
  if (CONFIG.apiBase && isOnline) apiFetch('/api/templates', { method: 'POST', body: JSON.stringify(tpl) }).catch(() => {});
  showToast(`已儲存 ${tpl.formCode} 模板設定！可切 Tab 4 即時預覽版面`, '💾');
  renderTemplateTab();
}
async function upgradeVersion() {
  const cur = templates.find(t => t.id === editingTplId);
  templates.forEach(t => { if (t.groupKey === cur.groupKey) t.isLatest = false; });
  const next = JSON.parse(JSON.stringify(cur));
  next.id = 'tpl-' + Date.now();
  next.isLatest = true;
  next.formCode = cur.formCode.replace(/\((\d+)\)/, (_, n) => `(${String(parseInt(n, 10) + 1).padStart(2, '0')})`);
  next.wiVersion = cur.wiVersion.replace(/(\d+)\.(\d+)/, (_, a, b) => `${a}.${parseInt(b, 10) + 1}`);
  templates.unshift(next);
  editingTplId = next.id;
  saveLocal();
  if (CONFIG.apiBase && isOnline) apiFetch('/api/templates', { method: 'POST', body: JSON.stringify(next) }).catch(() => {});
  renderTemplateTab();
  showToast(`已升版至 ${next.formCode}！舊紀錄永久鎖定 ${cur.formCode} 原版面`, '🚀');
}

// -------------------- TAB 4: 1:1 A4 & XLSX EXPORT --------------------
function openExport(recId) {
  switchTab('export');
  document.getElementById('export-select').value = recId;
  renderExportPreview(recId);
}

function renderExportTab() {
  const sel = document.getElementById('export-select');
  const latestPreviews = getAllLatestTemplates().map(t =>
    `<option value="__TPL__:${t.id}">📐 [最新模板預覽] ${t.shortCode} ${t.title} (${t.formCode})</option>`
  ).join('');
  const recOpts = records.map(r =>
    `<option value="${r.id}">${r.id} ｜ ${r.templateSnapshot.shortCode} ${r.templateSnapshot.formCode} [歷史鎖版]</option>`
  ).join('');
  sel.innerHTML = latestPreviews + recOpts;
  renderExportPreview(sel.value);
}

function getSelectedExportRecord() {
  const val = document.getElementById('export-select').value;
  if (val && val.startsWith('__TPL__:')) {
    const id = val.replace('__TPL__:', '');
    const tpl = templates.find(t => t.id === id) || templates[0];
    return {
      id: 'TEMPLATE-PREVIEW',
      status: 'draft',
      templateSnapshot: tpl,
      meta: { plant: (tpl.plants && tpl.plants[0]) || '', date: todayIso(), tankNo: 'T-102', pumpNo: 'P-102A', material: '醋酸 (GAA)', volA: 100, volB: 45, volC: 55, sg: 1.05, mtAvail: 57.8, trucks: 2.3, mtPlan: 25 },
      answers: {},
      signatures: {}
    };
  }
  return records.find(r => r.id === val) || records[0];
}

function renderExportPreview() {
  const rec = getSelectedExportRecord();
  if (!rec) return;
  const tpl = rec.templateSnapshot;
  const m = rec.meta || {};
  const [yy, mm, dd] = (m.date || todayIso()).split('-');
  const plantBar = tpl.plantDisplayMode === 'text'
    ? `<strong>廠區：</strong><u>&nbsp;&nbsp;${m.plant || ''}&nbsp;&nbsp;</u>`
    : (tpl.plants || []).map(p => `${m.plant === p ? '☑' : '☐'}${p}`).join('　　');

  const itemNotes = tpl.items.map(it => {
    const a = rec.answers && rec.answers[it.id];
    return a && a.note ? `【${it.name}】${a.note}` : '';
  }).filter(Boolean);
  const fullRemark = [m.remark, ...itemNotes].filter(Boolean).join('；');

  let tableHtml = '';
  if (tpl.layoutType === 'single_stage') {
    const secs = {};
    tpl.items.forEach(it => { (secs[it.section] = secs[it.section] || []).push(it); });
    const bodyRows = Object.entries(secs).map(([sec, list]) => list.map((it, i) => {
      const a = (rec.answers && rec.answers[it.id]) || {};
      const normal = it.normalChoice || '是';
      let res = '';
      if (it.mode === 'num_only') res = `<div style="text-align:right;font-family:monospace;"><u>&nbsp;${a.num || '____'}&nbsp;</u> ${it.unit || ''}</div>`;
      else {
        const y = a.choice === '是' ? (normal === '否' ? '<strong style="color:#dc2626">☑是</strong>' : '☑是') : '☐是';
        const n = a.choice === '否' ? (normal === '是' ? '<strong style="color:#dc2626">☑否</strong>' : '☑否') : '☐否';
        res = `<div>${y}　${n}${a.choice === '＼' ? ' (＼)' : ''}</div>` + (it.mode === 'yn_num' ? `<div style="text-align:right;font-family:monospace;"><u>&nbsp;${a.num || '____'}&nbsp;</u> ${it.unit || ''}</div>` : '');
      }
      return `<tr>${i === 0 ? `<td rowspan="${list.length}" class="v-text" style="width:28px;">${sec}</td>` : ''}<td colspan="4">${it.name}</td><td style="width:130px;text-align:center;">${res}</td></tr>`;
    }).join('')).join('');

    tableHtml = `
      <table class="wi-outer-table">
        <tr><td colspan="6" style="line-height:1.75;">
          <div>儲槽編號：<u>&nbsp;${m.tankNo || ''}&nbsp;</u>　卸貨泵浦編號：<u>&nbsp;${m.pumpNo || ''}&nbsp;</u>　儲存料品名稱：<u>&nbsp;${m.material || ''}&nbsp;</u></div>
          <div>(A)儲槽最大容積：<u>&nbsp;${m.volA || ''}&nbsp;</u> KL － (B)目前容積：<u>&nbsp;${m.volB || ''}&nbsp;</u> KL ＝ (C)目前可存容積：<u>&nbsp;${m.volC || ''}&nbsp;</u> KL</div>
          <div>目前可存數量：<u>&nbsp;${m.mtAvail || ''}&nbsp;</u> M/T 約 <u>&nbsp;${m.trucks || ''}&nbsp;</u> 台車，本日預定入槽量：<u>&nbsp;${m.mtPlan || ''}&nbsp;</u> M/T [(C)×比重 ${m.sg || ''}]</div>
        </td></tr>
        <tr style="text-align:center;font-weight:700;background:#f9fafb;"><td colspan="5" style="letter-spacing:10px;">檢查項目</td><td>檢查結果</td></tr>
        ${bodyRows}
        <tr><td class="v-text">備註</td><td colspan="5" style="height:40px;vertical-align:top;"><div>${tpl.footerNote || ''}</div>${fullRemark ? `<div style="color:#b91c1c;margin-top:2px;"><strong>備註：</strong>${fullRemark}</div>` : ''}</td></tr>
      </table>`;
  } else if (tpl.layoutType === 'dual_compare') {
    const infoLine = (tpl.extraHeaderFields || []).map(f => `${f.label}：<u>&nbsp;${m[f.key] || '________'}&nbsp;</u>`).join('　');
    const opLine = tpl.opTypeOptions ? `　${tpl.opTypeOptions.map(o => `${m.opType === o ? '☑' : '☐'}${o}`).join(' ')}` : '';
    const secs = {};
    tpl.items.forEach(it => { (secs[it.section] = secs[it.section] || []).push(it); });
    const bodyRows = Object.entries(secs).map(([sec, list]) => list.map((it, i) => {
      const a = (rec.answers && rec.answers[it.id]) || {};
      const fmt = (v, dis) => {
        if (dis) return '＼';
        if (it.mode === 'num_only') return `<u>&nbsp;${v || '___'}&nbsp;</u> ${it.unit || ''}`;
        if (it.mode === 'single_double') return `${v === '單槽' ? '☑' : '☐'}單槽　${v === '雙槽' ? '☑' : '☐'}雙槽`;
        if (it.mode === 'yn_na') return `${v === '是' ? '☑' : '☐'}是　${v === '無此項' ? '☑' : '☐'}無此項`;
        return `${v === '是' ? '☑' : '☐'}是　${v === '否' ? '☑' : '☐'}否`;
      };
      return `<tr>${i === 0 ? `<td rowspan="${list.length}" class="v-text" style="width:26px;">${sec}</td>` : ''}<td>${it.name}</td><td style="width:120px;text-align:center;">${fmt(a.left, it.leftDisabled)}</td><td style="width:130px;text-align:center;">${fmt(a.right, false)}${a.num ? ` (${a.num}${it.unit || ''})` : ''}</td></tr>`;
    }).join('')).join('');
    tableHtml = `
      <div style="font-size:11px;margin-bottom:4px;">${infoLine}${opLine}</div>
      <table class="wi-outer-table">
        <tr style="text-align:center;font-weight:700;background:#f9fafb;"><td colspan="2">安檢 / 清潔度檢核項目</td><td>${tpl.colLeftLabel}</td><td>${tpl.colRightLabel}</td></tr>
        ${bodyRows}
      </table>`;
  } else {
    const infoLine = (tpl.extraHeaderFields || []).map(f => `${f.label}：<u>&nbsp;${m[f.key] || '________'}&nbsp;</u>`).join('　');
    const bodyRows = tpl.items.map((it, i) => {
      const a = (rec.answers && rec.answers[it.id]) || {};
      return `<tr>${i === 0 ? `<td rowspan="${tpl.items.length}" style="width:46px;text-align:center;font-weight:700;">ISO<br/>TANK</td>` : ''}<td>${it.name}</td><td style="width:46px;text-align:center;">${it.stateLabel}</td><td style="width:66px;text-align:center;">${it.beforeDisabled ? '＼' : (a.before || '')}</td><td style="width:66px;text-align:center;">${a.after || ''}</td><td style="width:95px;">${a.note || ''}</td></tr>`;
    }).join('');
    tableHtml = `
      <div style="font-size:11px;margin-bottom:4px;">${infoLine}</div>
      <table class="wi-outer-table">
        <tr style="text-align:center;font-weight:700;background:#f9fafb;"><td>設備</td><td>檢查項目</td><td>狀態</td><td>接合前</td><td>拆卸後</td><td>備註</td></tr>
        ${bodyRows}
        ${tpl.footnotes ? `<tr><td class="v-text">附註</td><td colspan="5" style="font-size:10px;line-height:1.45;">${tpl.footnotes.join('<br/>')}</td></tr>` : ''}
      </table>`;
  }

  // Unified Signature Table
  const sigs = tpl.signers || [];
  const sigRowHtml = `
    <table class="wi-outer-table" style="margin-top:-1px;">
      <tr style="background:#f9fafb;text-align:center;font-weight:700;">
        ${sigs.map(s => `<td>${s.label}</td>`).join('')}
      </tr>
      <tr>
        ${sigs.map(s => {
          const d = rec.signatures && rec.signatures[s.key];
          return `<td style="height:64px;text-align:center;position:relative;">
            ${d ? `<img src="${d.dataUrl}" style="max-height:46px;margin:0 auto;display:block;" /><div style="font-size:9px;color:#4b5563;">${d.name || ''} ${d.signedAt || ''}</div>` : '<span style="color:#9ca3af;font-size:10px;">(未簽)</span>'}
          </td>`;
        }).join('')}
      </tr>
    </table>
  `;

  document.getElementById('a4-print-area').innerHTML = `
    <div style="text-align:center;font-size:14px;font-weight:700;letter-spacing:2px;">${tpl.company}</div>
    <div style="text-align:center;font-size:16px;font-weight:800;text-decoration:underline;letter-spacing:3px;margin:2px 0 6px;">${tpl.title}</div>
    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;font-size:11px;margin-bottom:4px;">
      <div>${plantBar}</div>
      <div>${yy} 年 ${mm} 月 ${dd} 日</div>
    </div>
    ${tableHtml}
    ${sigRowHtml}
    <div style="text-align:right;font-size:12px;font-family:monospace;margin-top:4px;font-weight:700;">${tpl.formCode}</div>
  `;
}

async function handleExportXlsx() {
  const rec = getSelectedExportRecord();
  if (!rec) return;
  const res = await window.exportRecordToXlsx(rec);
  showToast(`已匯出 ${res.fileName} (${res.mode === 'xlsx' ? '原生 .xlsx 含簽名圖' : 'Excel 表格'})`, '📥');
}

// -------------------- BOOT --------------------
window.addEventListener('online', () => { isOnline = true; syncNetworkBadge(); flushOfflineQueue(); });
window.addEventListener('offline', () => { isOnline = false; syncNetworkBadge(); });
window.addEventListener('DOMContentLoaded', bootData);
