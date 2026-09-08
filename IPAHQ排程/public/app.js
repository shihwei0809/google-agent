// Global State
let ordersData = [];
let driversData = [];
let currentTechMatched = [];
let currentTransportMatched = [];
let selectedOrderForEdit = null;
let currentUser = null;

// DOM Elements
const navTabs = document.querySelectorAll('.nav-tab');
const tabContents = document.querySelectorAll('.tab-content');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  setupLogin();
  checkLogin();
  loadData();
  setupUploadZones();
  setupSearchAndFilters();
  setupEditModal();
  setupUserManagement();
  setupPermissionsManagement();
  setupChangePasswordModal();
  setupOrderDetailModal();
  setupLiveSync();
});

// Login & Permissions Handling
function checkLogin() {
  const userJson = localStorage.getItem('user');
  const overlay = document.getElementById('login-overlay');
  const profile = document.getElementById('user-profile');
  const displayName = document.getElementById('user-display-name');
  
  if (userJson) {
    currentUser = JSON.parse(userJson);
    overlay.classList.add('hidden');
    profile.classList.remove('hidden');
    displayName.textContent = currentUser.displayName;
    applyRolePermissions(currentUser);
    initPushNotification(currentUser);
  } else {
    currentUser = null;
    overlay.classList.remove('hidden');
    profile.classList.add('hidden');
    initPushNotification(null);
  }
}

let systemRoles = [];
let systemPermissions = {};
let systemFeatures = [];

async function applyRolePermissions(user) {
  try {
    const res = await fetch('/api/permissions');
    const data = await res.json();
    if (data.success) {
      systemRoles = data.roles || [];
      systemPermissions = data.permissions || {};
      systemFeatures = data.features || [];
    }
  } catch (err) {
    console.error('Failed to load permissions:', err);
  }

  const role = user.role;
  let allowedTabs = systemPermissions[role];
  if (!allowedTabs) {
    if (role === 'admin') allowedTabs = ['tab-dashboard', 'tab-sales', 'tab-production', 'tab-tech', 'tab-transport', 'tab-query', 'tab-users', 'tab-permissions', 'tab-logs'];
    else if (role === 'production') allowedTabs = ['tab-dashboard', 'tab-sales', 'tab-production'];
    else if (role === 'sales') allowedTabs = ['tab-dashboard', 'tab-sales', 'tab-tech', 'tab-transport', 'tab-query'];
    else if (role === 'tech_manager') allowedTabs = ['tab-dashboard', 'tab-sales', 'tab-tech', 'tab-transport', 'tab-query'];
    else if (role === 'tech_staff') allowedTabs = ['tab-query'];
    else if (role === 'transporter') allowedTabs = ['tab-dashboard', 'tab-transport'];
    else allowedTabs = ['tab-dashboard'];
  }

  // 根據該角色的權限設定動態顯示/隱藏各分頁
  navTabs.forEach(t => {
    const tabName = t.getAttribute('data-tab');
    if (allowedTabs.includes(tabName)) {
      t.classList.remove('hidden');
    } else {
      t.classList.add('hidden');
    }
  });

  const queryNameGroup = document.getElementById('query-name-group');
  if (queryNameGroup) {
    if (role === 'tech_staff') {
      // 技服人員登入：自動鎖定其姓名
      const targetName = user.displayName || user.username;
      queryNameGroup.innerHTML = `
        <label>目前登入技服同仁：</label>
        <div style="font-size: 1.15rem; color: #38bdf8; font-weight: bold; padding: 0.5rem 0;">👤 ${escapeHtml(targetName)}</div>
        <input type="hidden" id="query-tech-name" value="${escapeHtml(targetName)}">
      `;
      document.querySelector('[data-tab="tab-query"]')?.click();
      if (ordersData && ordersData.length > 0) {
        queryTechSchedule();
      }
    } else {
      // 管理員 / 業務 / 主管：提供技服人員下拉選單
      queryNameGroup.innerHTML = `
        <label for="query-tech-name">技服充填手姓名：</label>
        <select id="query-tech-name" class="select-input">
          <option value="">-- 請選擇技服人員 --</option>
        </select>
      `;
      const select = document.getElementById('query-tech-name');
      if (select) {
        select.addEventListener('change', queryTechSchedule);
      }
      populateTechNamesDropdown();
    }
  }

  // 若當前頁籤不在允許列表中，自動跳轉至第一個可見頁籤
  const activeTab = document.querySelector('.nav-tab.active');
  if (!activeTab || activeTab.classList.contains('hidden')) {
    const firstVisible = Array.from(navTabs).find(t => !t.classList.contains('hidden'));
    if (firstVisible) {
      firstVisible.click();
    }
  }
}

function setupLogin() {
  const form = document.getElementById('login-form');
  const errorMsg = document.getElementById('login-error-msg');
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    
    errorMsg.classList.add('hidden');
    
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      
      const json = await res.json();
      if (res.ok && json.success) {
        localStorage.setItem('user', JSON.stringify(json.user));
        document.getElementById('login-username').value = '';
        document.getElementById('login-password').value = '';
        checkLogin();
      } else {
        errorMsg.classList.remove('hidden');
        errorMsg.textContent = json.message || '登入失敗！';
      }
    } catch (err) {
      console.error(err);
      errorMsg.classList.remove('hidden');
      errorMsg.textContent = '連線伺服器出錯，請重試！';
    }
  });

  document.getElementById('btn-logout').addEventListener('click', () => {
    localStorage.removeItem('user');
    currentUser = null;
    checkLogin();
  });
}

// -----------------------------------------------------------------------------
// Web Push 即時推播模組 (PWA 背景通知、改時間/派工自動提醒)
// -----------------------------------------------------------------------------

function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/\-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

let swRegistration = null;

async function initPushNotification(user) {
  if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
    console.warn('[WebPush] 此瀏覽器或連線模式不支援 Service Worker / Push API');
    const toggleBtn = document.getElementById('btn-push-toggle');
    if (toggleBtn) toggleBtn.classList.add('hidden');
    return;
  }

  try {
    swRegistration = await navigator.serviceWorker.register('/sw.js');
    console.log('[WebPush] Service Worker 註冊就緒，範圍:', swRegistration.scope);
  } catch (err) {
    console.warn('[WebPush] Service Worker 註冊失敗 (如非 HTTPS 或本機可能受限):', err);
    return;
  }

  updatePushUI(user);
  setupPushEventListeners();

  // 若已獲取通知權限且已登入，背景自動將此設備訂閱憑證同步登記至伺服器
  if (Notification.permission === 'granted' && user) {
    subscribeUserToPush(false);
  }
}

function updatePushUI(user) {
  const toggleBtn = document.getElementById('btn-push-toggle');
  const testBtn = document.getElementById('btn-push-test');
  const banner = document.getElementById('push-prompt-banner');

  if (!toggleBtn) return;

  if (Notification.permission === 'granted') {
    toggleBtn.textContent = '🔔 通知已開啟';
    toggleBtn.classList.add('active');
    toggleBtn.title = '點擊可重新同步推播設定';
    if (testBtn) testBtn.classList.remove('hidden');
    if (banner) banner.classList.add('hidden');
  } else if (Notification.permission === 'denied') {
    toggleBtn.textContent = '🔕 通知已被封鎖';
    toggleBtn.classList.remove('active');
    toggleBtn.title = '請至瀏覽器或手機設定允許本站通知';
    if (testBtn) testBtn.classList.add('hidden');
    if (banner) banner.classList.add('hidden');
  } else {
    toggleBtn.textContent = '🔔 開啟通知';
    toggleBtn.classList.remove('active');
    toggleBtn.title = '點擊開啟手機即時推播';
    if (testBtn) testBtn.classList.add('hidden');
    if (banner && user) {
      if (!sessionStorage.getItem('push_banner_dismissed')) {
        banner.classList.remove('hidden');
      }
    }
  }
}

let pushEventsSetup = false;
function setupPushEventListeners() {
  if (pushEventsSetup) return;
  pushEventsSetup = true;

  const toggleBtn = document.getElementById('btn-push-toggle');
  const testBtn = document.getElementById('btn-push-test');
  const enableBannerBtn = document.getElementById('btn-enable-push');
  const dismissBannerBtn = document.getElementById('btn-dismiss-push');

  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      subscribeUserToPush(true);
    });
  }

  if (enableBannerBtn) {
    enableBannerBtn.addEventListener('click', () => {
      subscribeUserToPush(true);
    });
  }

  if (dismissBannerBtn) {
    dismissBannerBtn.addEventListener('click', () => {
      const banner = document.getElementById('push-prompt-banner');
      if (banner) banner.classList.add('hidden');
      sessionStorage.setItem('push_banner_dismissed', '1');
    });
  }

  if (testBtn) {
    testBtn.addEventListener('click', async () => {
      if (!currentUser) {
        alert('請先登入帳號後再進行推播測試！');
        return;
      }
      testBtn.disabled = true;
      testBtn.textContent = '⏳ 發送中...';
      try {
        const res = await fetch('/api/push/test', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: currentUser.username || currentUser.displayName })
        });
        const json = await res.json();
        if (json.success) {
          alert('✅ 測試推播已發送！請檢視您的螢幕頂部通知橫幅或手機通知中心。');
        } else {
          alert('❌ 發送失敗：' + json.message);
        }
      } catch (err) {
        alert('❌ 連線出錯：' + err.message);
      } finally {
        testBtn.disabled = false;
        testBtn.textContent = '📲 測試';
      }
    });
  }
}

async function subscribeUserToPush(isUserAction) {
  if (!swRegistration) {
    if (isUserAction) alert('Service Worker 尚未就緒，請重新整理頁面後再試！');
    return;
  }

  try {
    // 1. 請求瀏覽器通知權限
    const permission = await Notification.requestPermission();
    updatePushUI(currentUser);

    if (permission !== 'granted') {
      if (isUserAction) {
        alert('您尚未允許通知權限。若想即時接收派工與改時間通知，請至瀏覽器或手機設定中開啟通知！');
      }
      return;
    }

    // 2. 向伺服器取得 VAPID 公鑰
    const res = await fetch('/api/push/vapid-public-key');
    const keyData = await res.json();
    if (!keyData.success || !keyData.publicKey) {
      throw new Error('無法自伺服器取得 VAPID 推播公鑰');
    }

    // 3. 透過 PushManager 向瀏覽器/系統推播伺服器訂閱
    const applicationServerKey = urlBase64ToUint8Array(keyData.publicKey);
    let subscription = await swRegistration.pushManager.getSubscription();
    if (!subscription) {
      subscription = await swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: applicationServerKey
      });
    }

    // 4. 將這台設備的推播憑證回傳後端，與目前登入之技服人員姓名綁定
    const targetUsername = currentUser ? (currentUser.username || currentUser.displayName) : '未知技服';
    const subRes = await fetch('/api/push/subscribe', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: targetUsername,
        subscription: subscription
      })
    });
    const subJson = await subRes.json();

    if (subJson.success) {
      updatePushUI(currentUser);
      if (isUserAction) {
        alert('🎉 成功啟用手機即時推播！\n無論 App 是否開啟或登入，當有新派工或到貨時間修改時，手機都會立即收到提醒！');
      }
    } else {
      throw new Error(subJson.message || '訂閱憑證儲存失敗');
    }
  } catch (err) {
    console.error('[WebPush] 訂閱流程出錯:', err);
    if (isUserAction) {
      alert('啟用推播通知失敗：' + err.message);
    }
  }
}


// 1. Navigation Tabs
function setupTabs() {
  navTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const targetTab = tab.getAttribute('data-tab');
      
      navTabs.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      
      tab.classList.add('active');
      document.getElementById(targetTab).classList.add('active');
      
      if (targetTab === 'tab-logs') {
        loadAndRenderLogs();
      } else if (targetTab === 'tab-users') {
        loadUsersData();
      } else if (targetTab === 'tab-permissions') {
        loadPermissionsMatrix();
      } else if (targetTab === 'tab-production') {
        loadProductionData();
      } else {
        // Auto-reload data on switching tabs to ensure freshness
        loadData();
      }
    });
  });
}

// Date Filter Helpers
let activeDateFilter = 'today_plus_2'; // default

function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

function getFilteredOrders() {
  const today = new Date();
  
  if (activeDateFilter === 'all') {
    return ordersData;
  }
  
  let startStr = '';
  let endStr = '';
  
  if (activeDateFilter === 'today') {
    startStr = formatDate(today);
    endStr = startStr;
  } else if (activeDateFilter === 'today_plus_2') {
    startStr = formatDate(today);
    const future = new Date();
    future.setDate(today.getDate() + 2);
    endStr = formatDate(future);
  } else if (activeDateFilter === 'custom') {
    startStr = document.getElementById('filter-start-date').value;
    endStr = document.getElementById('filter-end-date').value;
    if (!startStr || !endStr) return ordersData; // fallback if dates not filled
  }
  
  return ordersData.filter(o => {
    if (!o.expected_date) return false;
    return o.expected_date >= startStr && o.expected_date <= endStr;
  });
}

function refreshDashboardUI() {
  const filtered = getFilteredOrders();
  renderDashboardTable(filtered);
  updateStats(filtered); // Calculate statistics based on the filtered set!
  updateFilterInfoLabel();
}

function updateFilterInfoLabel() {
  const label = document.getElementById('table-filter-info');
  const today = new Date();
  
  if (activeDateFilter === 'all') {
    label.textContent = '顯示範圍：全部';
  } else if (activeDateFilter === 'today') {
    label.textContent = `顯示範圍：今天 (${formatDate(today)})`;
  } else if (activeDateFilter === 'today_plus_2') {
    const future = new Date();
    future.setDate(today.getDate() + 2);
    label.textContent = `顯示範圍：今天至後天 (${formatDate(today)} ~ ${formatDate(future)})`;
  } else if (activeDateFilter === 'custom') {
    const s = document.getElementById('filter-start-date').value || '?';
    const e = document.getElementById('filter-end-date').value || '?';
    label.textContent = `顯示範圍：${s} ~ ${e}`;
  }
}

// 2. Load Core Data from API
async function loadData() {
  try {
    const ordersRes = await fetch('/api/orders');
    const ordersJson = await ordersRes.json();
    if (ordersJson.success) {
      ordersData = ordersJson.data;
      
      // Smart fallback: if "today_plus_2" range has no orders, fallback to "all" so they can see the test data immediately!
      if (ordersData.length > 0) {
        activeDateFilter = 'today_plus_2';
        const testFiltered = getFilteredOrders();
        if (testFiltered.length === 0) {
          activeDateFilter = 'all';
          document.getElementById('date-range-select').value = 'all';
          console.log('Today+2 range is empty. Auto fall back to "all" to show uploaded test data.');
        }
      }
      
      refreshDashboardUI();
      populateTechNamesDropdown();

      // 若已有選定或登入的技服人員，資料載入後自動查詢行程
      const currentTechInput = document.getElementById('query-tech-name');
      if (currentTechInput && currentTechInput.value) {
        queryTechSchedule();
      }

      // 檢查網址是否由推播點擊開啟 (?openOrder=xxx)
      checkUrlForOpenOrder();
    }

    const driversRes = await fetch('/api/drivers');
    const driversJson = await driversRes.json();
    if (driversJson.success) {
      driversData = driversJson.data;
    }
  } catch (err) {
    console.error('Error loading data:', err);
  }
}

// // Helper for HTML escaping (prevents XSS vulnerabilities)
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

let currentDashboardOrders = [];

// 3. Render Dashboard Table
function renderDashboardTable(orders) {
  currentDashboardOrders = orders || [];
  const tbody = document.getElementById('dashboard-table-body');
  const cardsContainer = document.getElementById('dashboard-cards-list');
  
  if (!orders || orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="16" class="text-center">請先至「業務專區」上傳基準出貨清單 Excel</td></tr>`;
    if (cardsContainer) {
      cardsContainer.innerHTML = `<div class="no-results">請先至「業務專區」上傳基準出貨清單 Excel</div>`;
    }
    return;
  }

  // Render desktop table
  tbody.innerHTML = orders.map((o, idx) => {
    const statusBadge = getStatusBadge(o);
    const idText = o.id ? escapeHtml(o.id) : '<span class="text-muted">無</span>';
    const batchText = o.batch ? escapeHtml(o.batch) : '-';
    
    const showEdit = currentUser && (currentUser.role === 'admin' || currentUser.role === 'sales' || currentUser.role === 'tech_manager' || currentUser.role === 'transporter' || currentUser.role === 'production');
    let editLink = '';
    if (showEdit) {
      editLink = `<span class="action-link" onclick="openEditModalByIndex(${idx})">編輯</span>`;
    }
    const actionCell = editLink ? `<td>${editLink}</td>` : `<td>-</td>`;
    
    // 三合一單獨立一欄 (無批號不顯示)
    let printLink = '-';
    if (o.client && (o.client.includes('台積') || o.client.includes('TSMC')) && o.batch && String(o.batch).trim() !== '' && o.batch !== '-' && o.batch !== 'null') {
      printLink = `<button class="btn btn-primary btn-sm" onclick="download3in1ByIndex(${idx})" style="padding: 2px 8px; font-size: 0.85rem;">🖨️ 下載</button>`;
    }
    const printCell = `<td>${printLink}</td>`;
    const readStatusCell = `<td>${getReadStatusBadge(o)}</td>`;

    return `
      <tr onclick="onOrderRowClick(event, ${idx})" style="cursor: pointer;" title="點擊可直接檢視單筆詳細資訊">
        <td>${idText}</td>
        <td>${batchText}</td>
        <td>${escapeHtml(o.client) || '-'}</td>
        <td title="${escapeHtml(o.destination) || ''}">${escapeHtml(truncateStr(o.destination, 18))}</td>
        <td>${escapeHtml(o.product) || '-'}</td>
        <td>${escapeHtml(o.expected_date) || '-'}</td>
        <td>${escapeHtml(o.arrival_time) || '-'}</td>
        <td>${escapeHtml(o.transport_type) || '-'}</td>
        <td>${formatFillHand(o.fill_hand)}</td>
        <td>${escapeHtml(o.plate) || '-'}</td>
        <td>${escapeHtml(o.driver) || '-'}</td>
        <td>${escapeHtml(o.phone) || '-'}</td>
        <td>${escapeHtml(o.departure_date) || '-'}</td>
        <td>${escapeHtml(o.departure_time) || '-'}</td>
        <td>${escapeHtml(o.driver_code) || '-'}</td>
        ${printCell}
        ${readStatusCell}
        ${actionCell}
      </tr>
    `;
  }).join('');

  // Render mobile cards list
  if (cardsContainer) {
    cardsContainer.innerHTML = orders.map((o, idx) => {
      const statusBadge = getStatusBadge(o);
      const readBadge = getReadStatusBadge(o);
      const idText = o.id ? escapeHtml(o.id) : '無單號';
      const showEdit = currentUser && (currentUser.role === 'admin' || currentUser.role === 'sales' || currentUser.role === 'tech_manager' || currentUser.role === 'transporter' || currentUser.role === 'production');
      const editBtn = showEdit 
        ? `<button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); openEditModalByIndex(${idx})">編輯</button>`
        : '';
        
      return `
        <div class="mobile-order-card" onclick="openOrderDetailModalByIndex(${idx})" style="cursor: pointer;">
          <div class="mobile-card-header">
            <div class="card-title-group">
              <span class="card-time">${escapeHtml(o.arrival_time) || '時間未定'}</span>
              <span class="card-date">${escapeHtml(o.expected_date) || ''}</span>
            </div>
            <div style="display: flex; gap: 6px; align-items: center;">
              ${readBadge}
              ${statusBadge}
            </div>
          </div>
          <div class="mobile-card-body">
            <div class="card-detail"><strong>對象：</strong>${escapeHtml(o.client) || '-'}</div>
            <div class="card-detail" title="${escapeHtml(o.destination) || ''}"><strong>指送地：</strong>${escapeHtml(o.destination) || '-'}</div>
            <div class="card-detail"><strong>品名：</strong>${escapeHtml(o.product) || '-'} | <strong>批號：</strong>${escapeHtml(o.batch) || '-'}</div>
            <div class="card-detail"><strong>運輸方式：</strong>${escapeHtml(o.transport_type) || '-'}</div>
            <div class="card-detail-divider"></div>
            <div class="card-detail"><strong>技服充填手：</strong>${formatFillHand(o.fill_hand)}</div>
            <div class="card-detail"><strong>車牌司機：</strong>${o.plate ? `${escapeHtml(o.plate)} (${escapeHtml(o.driver)})` : '⏳ 尚未排定'}</div>
            ${o.phone ? `<div class="card-detail"><strong>司機電話：</strong>${escapeHtml(o.phone)}</div>` : ''}
            ${o.departure_date ? `<div class="card-detail"><strong>出車時間：</strong>${escapeHtml(o.departure_date)} ${escapeHtml(o.departure_time) || ''}</div>` : ''}
          </div>
          <div class="mobile-card-footer">
            <span>單號：${idText}</span>
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-outline-cyan btn-sm" onclick="event.stopPropagation(); openOrderDetailModalByIndex(${idx})">📋 查看詳細</button>
              ${editBtn}
            </div>
          </div>
        </div>
      `;
    }).join('');
  }
}

window.openEditModalByIndex = function(idx) {
  const o = currentDashboardOrders[idx];
  if (!o) return;
  openEditModal(o.id, o.destination, o.product, o.expected_date, o.arrival_time);
};

window.download3in1ByIndex = function(idx) {
  const o = currentDashboardOrders[idx];
  if (!o) return;
  download3in1(o.id || '', o.batch);
};

// 點擊表格行開啟單筆聚焦卡片 (排除點擊按鈕或連結)
window.onOrderRowClick = function(event, idx) {
  if (event.target.closest('button') || event.target.closest('.action-link')) {
    return; // 若點擊的是下載或編輯按鈕，不觸發開單
  }
  openOrderDetailModalByIndex(idx);
};

let currentFocusedOrderKey = null;

window.openOrderDetailModalByIndex = function(idx) {
  const o = currentDashboardOrders[idx];
  if (!o) return;
  openOrderDetailModalByOrder(o);
};

window.openOrderDetailModalByKey = function(orderKey) {
  const o = ordersData.find(item => (item.id && item.id === orderKey) || (`${item.destination}_${item.expected_date}_${item.arrival_time}` === orderKey));
  if (o) openOrderDetailModalByOrder(o);
};

window.openOrderDetailModalByOrder = function(o) {
  const modal = document.getElementById('order-detail-modal');
  const content = document.getElementById('order-detail-content');
  const timeSpan = document.getElementById('detail-read-timestamp');
  if (!modal || !content) return;

  const orderKey = o.id || `${o.destination}_${o.expected_date}_${o.arrival_time}`;
  currentFocusedOrderKey = orderKey;

  const isRead = o.read_status === 'read';
  if (isRead) {
    timeSpan.textContent = `✓ 技服已於 ${o.read_at || ''} 確認 (${o.read_by || ''})`;
    timeSpan.style.color = '#34d399';
  } else {
    timeSpan.textContent = '⏳ 尚未確認讀取';
    timeSpan.style.color = '#f87171';
  }

  content.innerHTML = `
    <div style="background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); border-radius: 12px; padding: 1.25rem;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
        <div>
          <span style="font-size: 0.85rem; color: var(--text-muted);">出貨單號</span>
          <h4 style="font-size: 1.2rem; color: #38bdf8; margin: 0.2rem 0 0 0;">${escapeHtml(o.id || '無單號')}</h4>
        </div>
        <div>${getStatusBadge(o)}</div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; font-size: 0.95rem;">
        <div><strong>指送地：</strong><span style="color: #facc15; font-weight: 600;">${escapeHtml(o.destination || '-')}</span></div>
        <div><strong>對象簡稱：</strong>${escapeHtml(o.client || '-')}</div>
        <div><strong>品名：</strong><span class="product-badge">${escapeHtml(o.product || '-')}</span></div>
        <div><strong>批號：</strong><b>${escapeHtml(o.batch || '-')}</b></div>
        <div><strong>預計到貨：</strong><span style="color: #38bdf8; font-weight: bold;">${escapeHtml(o.expected_date || '')} ${escapeHtml(o.arrival_time || '')}</span></div>
        <div><strong>運輸方式：</strong>${escapeHtml(o.transport_type || '-')}</div>
      </div>

      <div style="margin: 1rem 0; border-top: 1px dashed var(--card-border);"></div>

      <div style="display: grid; grid-template-columns: 1fr; gap: 0.6rem; font-size: 0.95rem;">
        <div><strong>🔧 技服充填手：</strong><span style="font-size: 1.05rem; color: #a78bfa; font-weight: bold;">${formatFillHand(o.fill_hand)}</span></div>
        <div><strong>🚚 司機 / 車牌：</strong>${o.plate ? `${escapeHtml(o.plate)} (${escapeHtml(o.driver || '')})` : '⏳ 運輸車輛尚未排定'}</div>
        <div><strong>📞 司機電話：</strong>${o.phone ? `<a href="tel:${escapeHtml(o.phone)}" style="color: #38bdf8;">${escapeHtml(o.phone)}</a>` : '-'}</div>
        <div><strong>🕒 預計出車：</strong>${o.departure_date ? `${escapeHtml(o.departure_date)} ${escapeHtml(o.departure_time || '')}` : '-'}</div>
      </div>
    </div>
  `;

  modal.classList.add('open');

  // 自動送出「已讀」登記 (若當前登入者身分為該充填手或技服人員)
  if (currentUser) {
    markOrderAsRead(orderKey, currentUser.displayName || currentUser.username);
  }
};

async function markOrderAsRead(orderKey, username) {
  try {
    const res = await fetch('/api/orders/mark-read', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ orderKey, username })
    });
    const json = await res.json();
    if (json.success) {
      // 即時更新本機快取
      const order = ordersData.find(o => (o.id && o.id === orderKey) || (`${o.destination}_${o.expected_date}_${o.arrival_time}` === orderKey));
      if (order) {
        order.read_status = 'read';
        order.read_at = json.read_at;
        order.read_by = json.read_by;
      }
      const timeSpan = document.getElementById('detail-read-timestamp');
      if (timeSpan) {
        timeSpan.textContent = `✓ 技服已於 ${json.read_at} 確認 (${json.read_by})`;
        timeSpan.style.color = '#34d399';
      }
      // 即時刷新主表格與手機日程卡片
      refreshDashboardUI();
      const currentTechInput = document.getElementById('query-tech-name');
      if (currentTechInput && currentTechInput.value) {
        queryTechSchedule();
      }
    }
  } catch (e) {
    console.warn('Auto mark read failed:', e);
  }
}

// 檢查網址列是否有 ?openOrder=... 參數，若有則直接開啟單筆專屬聚焦彈窗
function checkUrlForOpenOrder() {
  const urlParams = new URLSearchParams(window.location.search);
  const openOrderKey = urlParams.get('openOrder');
  if (!openOrderKey) return;

  const target = ordersData.find(o => (o.id && o.id === openOrderKey) || (`${o.destination}_${o.expected_date}_${o.arrival_time}` === openOrderKey));
  if (target) {
    console.log('[WebPush] 偵測到推播跳轉單號，自動聚焦開啟訂單：', openOrderKey);
    openOrderDetailModalByOrder(target);
  }
}

function setupOrderDetailModal() {
  const closeBtn = document.getElementById('close-order-detail-modal');
  const confirmBtn = document.getElementById('btn-confirm-order-read');
  const modal = document.getElementById('order-detail-modal');

  const reRenderAll = () => {
    refreshDashboardUI();
    const currentTechInput = document.getElementById('query-tech-name');
    if (currentTechInput && currentTechInput.value) {
      queryTechSchedule();
    }
  };

  if (closeBtn && modal) {
    closeBtn.addEventListener('click', () => {
      modal.classList.remove('open');
      reRenderAll();
    });
  }
  if (confirmBtn && modal) {
    confirmBtn.addEventListener('click', () => {
      if (currentFocusedOrderKey && currentUser) {
        markOrderAsRead(currentFocusedOrderKey, currentUser.displayName || currentUser.username);
      }
      modal.classList.remove('open');
      reRenderAll();
    });
  }
}

// 雙向即時狀態同步機制 (SSE 毫秒廣播 + 5 秒心跳比對輪詢)
function setupLiveSync() {
  // 1. SSE 即時推播事件流監聽 (當手機端已讀，電腦端立刻自動翻綠)
  try {
    const evtSource = new EventSource('/api/events');
    
    evtSource.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'order_read') {
          const { orderKey, orderId, read_status, read_at, read_by, destination, expected_date, arrival_time } = msg.data;
          // 比對並更新 ordersData 快取
          const found = ordersData.find(o => 
            (orderId && o.id === orderId) || 
            (orderKey && o.id === orderKey) || 
            (`${o.destination}_${o.expected_date}_${o.arrival_time}` === `${destination}_${expected_date}_${arrival_time}`) || 
            (`${o.destination}_${o.expected_date}_${o.arrival_time}` === orderKey)
          );
          if (found) {
            found.read_status = read_status;
            found.read_at = read_at;
            found.read_by = read_by;
            console.log(`[LiveSync] 收到同仁「${read_by}」已讀推播通知，自動刷新畫面！`);
            refreshDashboardUI();
            const currentTechInput = document.getElementById('query-tech-name');
            if (currentTechInput && currentTechInput.value) {
              queryTechSchedule();
            }
          }
        } else if (msg.type === 'orders_changed') {
          console.log('[LiveSync] 收到排程資料異動廣播，自動重新載入...');
          loadData();
        }
      } catch (err) {}
    };

    evtSource.onerror = () => {
      // 網路瞬斷時 EventSource 會自動重連
    };
  } catch (e) {
    console.warn('SSE not initialized:', e);
  }

  // 2. 雙重保險：在背景低頻檢驗訂單狀態 (主要由即時 SSE 推播，此處維持 30 秒以大幅減輕伺服器負擔)
  setInterval(async () => {
    try {
      const res = await fetch('/api/orders?t=' + Date.now());
      const json = await res.json();
      if (json.success && Array.isArray(json.data)) {
        // 快速檢查 read_status 與 read_at 是否有變更
        const remoteSig = json.data.map(o => `${o.id || o.destination}_${o.read_status}_${o.read_at}`).join('|');
        const localSig = ordersData.map(o => `${o.id || o.destination}_${o.read_status}_${o.read_at}`).join('|');
        if (remoteSig !== localSig) {
          console.log('[LiveSync Poll] 偵測到伺服器有已讀或資料變更，自動對齊畫面！');
          ordersData = json.data;
          refreshDashboardUI();
          const currentTechInput = document.getElementById('query-tech-name');
          if (currentTechInput && currentTechInput.value) {
            queryTechSchedule();
          }
        }
      }
    } catch (e) {}
  }, 30000);
}

// Helper to truncate long strings
function truncateStr(str, len) {
  if (!str) return '';
  return str.length > len ? str.substring(0, len) + '...' : str;
}

// Helper to format fill_hand for display (replace \n with spaces or small tags)
function formatFillHand(val) {
  if (!val) return '-';
  return escapeHtml(val).replace(/\n/g, ' / ');
}

// Helper to calculate order status
function getStatusBadge(o) {
  if (o.fill_hand && o.plate && o.driver) {
    return '<span class="badge badge-success">完全就緒</span>';
  }
  if (o.plate || o.driver) {
    return '<span class="badge badge-warning">運輸已排</span>';
  }
  if (o.fill_hand) {
    return '<span class="badge badge-info">技服已填</span>';
  }
  return '<span class="badge badge-secondary">已建檔</span>';
}

// 取得技服人員讀取狀態 Badge (已讀 / 未讀)
function getReadStatusBadge(o) {
  if (!o.fill_hand) {
    return '<span class="text-muted" style="font-size: 0.85rem;">未派工</span>';
  }
  if (o.read_status === 'read') {
    const timeShort = o.read_at ? o.read_at.split(' ')[1] || o.read_at : '';
    const reader = o.read_by ? ` (${escapeHtml(o.read_by)})` : '';
    return `<span class="badge badge-success" title="已讀時間: ${escapeHtml(o.read_at || '')}${reader}">🟢 已讀 ${timeShort}</span>`;
  }
  return '<span class="badge badge-danger" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4);">🔴 未讀</span>';
}

// 4. Update Stats Cards
function updateStats(orders) {
  const total = orders.length;
  const techFilled = orders.filter(o => o.fill_hand).length;
  const transportFilled = orders.filter(o => o.plate || o.driver).length;

  document.getElementById('stat-total-orders').textContent = total;
  
  const techPct = total > 0 ? Math.round((techFilled / total) * 100) : 0;
  document.getElementById('stat-tech-filled').innerHTML = `${techFilled} <span class="stat-percent" id="stat-tech-pct">(${techPct}%)</span>`;

  const transPct = total > 0 ? Math.round((transportFilled / total) * 100) : 0;
  document.getElementById('stat-transport-filled').innerHTML = `${transportFilled} <span class="stat-percent" id="stat-transport-pct">(${transPct}%)</span>`;
}

// 5. Populate Tech Names Dropdown for Query Portal
const OFFICIAL_TECHS = [
  '林聖龍', '楊立凱', '胡富閔', '陳國安', '陳俊佑', '陳志彥', '陳志源', '廖家民', 
  '蘇昭溢', '王善禾', '葉仁豪', '吳柏昇', '黃國欽', '魏柏勳', '陳志聰', '謝嘉泰', 
  '邱建銘', '楊家勝', '蘇哲儀', '王品揚', '江韋徵', '郭泰緒', '林聖壹', '周昆賢', 
  '黃子峻', '黃宗勝', '何森寅', '洪宇勤', '葉志杰', '資材'
];

function populateTechNamesDropdown() {
  const select = document.getElementById('query-tech-name');
  if (!select || select.tagName !== 'SELECT') return;
  const currentSelection = select.value;
  
  // 嚴格僅採用官方 35 名單中的技服名冊與 tech_staff 帳號名單，杜絕任何測試字串或標題雜訊
  const names = new Set(OFFICIAL_TECHS);

  if (allUsersList && allUsersList.length > 0) {
    allUsersList.forEach(u => {
      if (u.role === 'tech_staff') {
        const n = u.displayName || u.username;
        if (n && n !== 'admin') names.add(n);
      }
    });
  }

  // Keep default option
  select.innerHTML = '<option value="">-- 請選擇技服人員 --</option>';
  Array.from(names).sort((a, b) => a.localeCompare(b, 'zh-Hant')).forEach(name => {
    select.innerHTML += `<option value="${name}">${name}</option>`;
  });

  // Restore selection
  if (Array.from(names).includes(currentSelection)) {
    select.value = currentSelection;
  }
}

// 6. Setup Drag & Drop File Upload Zones
function setupUploadZones() {
  const zones = [
    { id: 'sales', color: 'primary' },
    { id: 'tech', color: 'accent' },
    { id: 'transport', color: 'success' }
  ];

  zones.forEach(z => {
    const zone = document.getElementById(`${z.id}-upload-zone`);
    const fileInput = document.getElementById(`${z.id}-file-input`);
    const fileInfo = document.getElementById(`${z.id}-file-info`);
    const uploadBtn = document.getElementById(`btn-${z.id}-upload`);

    // Click zone triggers file input
    zone.addEventListener('click', () => fileInput.click());

    // File selected event
    fileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (file) {
        fileInfo.textContent = `${file.name} (${formatBytes(file.size)})`;
        uploadBtn.disabled = false;
      }
    });

    // Drag & Drop events
    zone.addEventListener('dragover', (e) => {
      e.preventDefault();
      zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
      zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      zone.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
        fileInput.files = e.dataTransfer.files;
        fileInfo.textContent = `${file.name} (${formatBytes(file.size)})`;
        uploadBtn.disabled = false;
      } else {
        alert('請上傳 Excel 格式檔案 (.xlsx, .xls)');
      }
    });
  });

  // Triggering uploads
  document.getElementById('btn-sales-upload').addEventListener('click', uploadSalesExcel);
  document.getElementById('btn-tech-upload').addEventListener('click', compareTechExcel);
  document.getElementById('btn-transport-upload').addEventListener('click', compareTransportExcel);
}

// Helper to format file size
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 7. Upload Actions
// 7.1. Sales Baseline Upload
async function uploadSalesExcel() {
  const input = document.getElementById('sales-file-input');
  const btn = document.getElementById('btn-sales-upload');
  
  if (!input.files[0]) return;
  
  const formData = new FormData();
  formData.append('file', input.files[0]);
  
  btn.disabled = true;
  btn.textContent = '上傳並解析中...';
  
  try {
    const res = await fetch(`/api/upload/sales?operator=${encodeURIComponent(currentUser.username)}&role=${encodeURIComponent(currentUser.role)}`, {
      method: 'POST',
      body: formData
    });
    const json = await res.json();
    
    if (json.success) {
      alert(json.message);
      // reset file input
      input.value = '';
      document.getElementById('sales-file-info').textContent = '未選擇檔案';
      btn.disabled = true;
      btn.textContent = '解析並匯入基準資料';
      
      // Reload UI
      loadData();
      // Switch back to dashboard
      document.querySelector('[data-tab="tab-dashboard"]').click();
    } else {
      alert(`錯誤: ${json.message}`);
      btn.disabled = false;
      btn.textContent = '解析並匯入基準資料';
    }
  } catch (err) {
    console.error(err);
    alert('伺服器連線錯誤！');
    btn.disabled = false;
    btn.textContent = '解析並匯入基準資料';
  }
}

// 7.2. Tech Service Compare & Preview
async function compareTechExcel() {
  const input = document.getElementById('tech-file-input');
  const btn = document.getElementById('btn-tech-upload');
  const container = document.getElementById('tech-preview-container');
  const tbody = document.getElementById('tech-preview-body');
  
  if (!input.files[0]) return;
  
  const formData = new FormData();
  formData.append('file', input.files[0]);
  
  btn.disabled = true;
  btn.textContent = '比對中...';
  
  try {
    const res = await fetch('/api/compare/tech', {
      method: 'POST',
      body: formData
    });
    const json = await res.json();
    
    if (json.success) {
      container.classList.remove('hidden');
      document.getElementById('tech-matched-count').textContent = json.results.matched.length;
      document.getElementById('tech-mismatched-count').textContent = json.results.mismatched.length;
      
      currentTechMatched = json.results.matched.map(item => ({
        id: item.existing.id,
        destination: item.existing.destination,
        product: item.existing.product,
        expected_date: item.existing.expected_date,
        arrival_time: item.existing.arrival_time,
        fill_hand: item.fillHandNew
      }));

      // Render Preview rows
      tbody.innerHTML = '';
      
      // Show matched ones
      json.results.matched.forEach(item => {
        tbody.innerHTML += `
          <tr class="preview-matched">
            <td>${item.rowNum}</td>
            <td>${item.uploaded.id ? escapeHtml(item.uploaded.id) : '<span class="text-muted">無</span>'}</td>
            <td>${escapeHtml(item.uploaded.destination) || '-'}</td>
            <td>${escapeHtml(item.uploaded.product) || '-'}</td>
            <td>${escapeHtml(item.uploaded.expected_date) || '-'}</td>
            <td>${escapeHtml(item.uploaded.arrival_time) || '-'}</td>
            <td><span class="badge badge-info">${escapeHtml(item.uploaded.fill_hand) || '-'}</span></td>
            <td><span class="badge badge-success">比對成功 (${item.matchBy === 'id' ? '訂單單號' : '關鍵欄位'})</span></td>
          </tr>
        `;
      });

      // Show mismatched ones
      json.results.mismatched.forEach(item => {
        tbody.innerHTML += `
          <tr class="preview-mismatched">
            <td>${item.rowNum}</td>
            <td>${item.uploaded.id ? escapeHtml(item.uploaded.id) : '<span class="text-muted">無</span>'}</td>
            <td>${escapeHtml(item.uploaded.destination) || '-'}</td>
            <td>${escapeHtml(item.uploaded.product) || '-'}</td>
            <td>${escapeHtml(item.uploaded.expected_date) || '-'}</td>
            <td>${escapeHtml(item.uploaded.arrival_time) || '-'}</td>
            <td>${escapeHtml(item.uploaded.fill_hand) || '-'}</td>
            <td><span class="badge badge-danger">查無基準訂單 (不予更新)</span></td>
          </tr>
        `;
      });

      btn.disabled = false;
      btn.textContent = '重新比對上傳';
      
      // Setup action buttons inside preview
      document.getElementById('btn-tech-confirm').onclick = confirmTechImport;
      document.getElementById('btn-tech-cancel').onclick = () => {
        container.classList.add('hidden');
      };
    } else {
      alert(`比對錯誤: ${json.message}`);
      btn.disabled = false;
      btn.textContent = '比對上傳資料';
    }
  } catch (err) {
    console.error(err);
    alert('伺服器連線錯誤！');
    btn.disabled = false;
    btn.textContent = '比對上傳資料';
  }
}

async function confirmTechImport() {
  if (currentTechMatched.length === 0) {
    alert('沒有可匯入的成功比對項目！');
    return;
  }
  
  try {
    const res = await fetch('/api/import/tech', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        matchedRows: currentTechMatched,
        operator: currentUser.username,
        role: currentUser.role
      })
    });
    const json = await res.json();
    if (json.success) {
      alert(json.message);
      document.getElementById('tech-preview-container').classList.add('hidden');
      // Reset upload inputs
      document.getElementById('tech-file-input').value = '';
      document.getElementById('tech-file-info').textContent = '未選擇檔案';
      document.getElementById('btn-tech-upload').disabled = true;
      loadData();
      document.querySelector('[data-tab="tab-dashboard"]').click();
    } else {
      alert(`更新失敗: ${json.message}`);
    }
  } catch (err) {
    console.error(err);
    alert('匯入提交錯誤！');
  }
}

// 7.3. Transporter Compare & Preview
async function compareTransportExcel() {
  const input = document.getElementById('transport-file-input');
  const btn = document.getElementById('btn-transport-upload');
  const container = document.getElementById('transport-preview-container');
  const tbody = document.getElementById('transport-preview-body');
  
  if (!input.files[0]) return;
  
  const formData = new FormData();
  formData.append('file', input.files[0]);
  
  btn.disabled = true;
  btn.textContent = '比對中...';
  
  try {
    const res = await fetch('/api/compare/transport', {
      method: 'POST',
      body: formData
    });
    const json = await res.json();
    
    if (json.success) {
      container.classList.remove('hidden');
      document.getElementById('transport-matched-count').textContent = json.results.matched.length;
      document.getElementById('transport-mismatched-count').textContent = json.results.mismatched.length;
      
      currentTransportMatched = json.results.matched.map(item => ({
        id: item.existing.id,
        destination: item.existing.destination,
        product: item.existing.product,
        expected_date: item.existing.expected_date,
        arrival_time: item.existing.arrival_time,
        plate: item.uploaded.plate,
        driver: item.uploaded.driver,
        phone: item.uploaded.phone,
        departure_date: item.uploaded.departure_date,
        departure_time: item.uploaded.departure_time,
        driver_code: item.uploaded.driver_code
      }));

      // Render Preview rows
      tbody.innerHTML = '';
      
      // Show matched ones
      json.results.matched.forEach(item => {
        // Highlight auto-filled fields if code matched but details came from DB
        const isAutoFilled = item.uploaded.driver && !item.existing.driver;
        const driverCodeDisplay = item.uploaded.driver_code ? `${escapeHtml(item.uploaded.driver_code)} (${escapeHtml(item.uploaded.driver) || '-'})` : '-';
        const carInfo = `${escapeHtml(item.uploaded.plate) || '-'} / ${escapeHtml(item.uploaded.phone) || '-'}`;
        const timeDisplay = `${escapeHtml(item.uploaded.departure_date) || '-'} ${escapeHtml(item.uploaded.departure_time) || '-'}`;
        
        tbody.innerHTML += `
          <tr class="preview-matched">
            <td>${item.rowNum}</td>
            <td>${item.uploaded.id ? escapeHtml(item.uploaded.id) : '<span class="text-muted">無</span>'}</td>
            <td>${escapeHtml(item.uploaded.destination) || '-'}</td>
            <td>${escapeHtml(item.uploaded.product) || '-'}</td>
            <td>${escapeHtml(item.uploaded.expected_date) || '-'}</td>
            <td>${escapeHtml(item.uploaded.arrival_time) || '-'}</td>
            <td>${timeDisplay}</td>
            <td><span class="badge badge-success">${driverCodeDisplay}</span></td>
            <td>${carInfo} ${isAutoFilled ? '<span class="badge badge-info" style="font-size: 0.65rem;">代碼自動補齊</span>' : ''}</td>
            <td><span class="badge badge-success">比對成功</span></td>
          </tr>
        `;
      });

      // Show mismatched ones
      json.results.mismatched.forEach(item => {
        tbody.innerHTML += `
          <tr class="preview-mismatched">
            <td>${item.rowNum}</td>
            <td>${item.uploaded.id ? escapeHtml(item.uploaded.id) : '<span class="text-muted">無</span>'}</td>
            <td>${escapeHtml(item.uploaded.destination) || '-'}</td>
            <td>${escapeHtml(item.uploaded.product) || '-'}</td>
            <td>${escapeHtml(item.uploaded.expected_date) || '-'}</td>
            <td>${escapeHtml(item.uploaded.arrival_time) || '-'}</td>
            <td>-</td>
            <td>-</td>
            <td>-</td>
            <td><span class="badge badge-danger">查無基準訂單 (不予更新)</span></td>
          </tr>
        `;
      });

      btn.disabled = false;
      btn.textContent = '重新比對上傳';
      
      // Setup action buttons inside preview
      document.getElementById('btn-transport-confirm').onclick = confirmTransportImport;
      document.getElementById('btn-transport-cancel').onclick = () => {
        container.classList.add('hidden');
      };
    } else {
      alert(`比對錯誤: ${json.message}`);
      btn.disabled = false;
      btn.textContent = '比對上傳資料';
    }
  } catch (err) {
    console.error(err);
    alert('伺服器連線錯誤！');
    btn.disabled = false;
    btn.textContent = '比對上傳資料';
  }
}

async function confirmTransportImport() {
  if (currentTransportMatched.length === 0) {
    alert('沒有可匯入的成功比對項目！');
    return;
  }
  
  try {
    const res = await fetch('/api/import/transport', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        matchedRows: currentTransportMatched,
        operator: currentUser.username,
        role: currentUser.role
      })
    });
    const json = await res.json();
    if (json.success) {
      alert(json.message);
      document.getElementById('transport-preview-container').classList.add('hidden');
      document.getElementById('transport-file-input').value = '';
      document.getElementById('transport-file-info').textContent = '未選擇檔案';
      document.getElementById('btn-transport-upload').disabled = true;
      loadData();
      document.querySelector('[data-tab="tab-dashboard"]').click();
    } else {
      alert(`更新失敗: ${json.message}`);
    }
  } catch (err) {
    console.error(err);
    alert('匯入提交錯誤！');
  }
}

// 8. Search & Filters Setup
function setupSearchAndFilters() {
  const searchInput = document.getElementById('dashboard-search');
  searchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    const currentFiltered = getFilteredOrders();
    if (!query) {
      renderDashboardTable(currentFiltered);
      return;
    }
    const filtered = currentFiltered.filter(o => {
      return (
        (o.id && o.id.toLowerCase().includes(query)) ||
        (o.client && o.client.toLowerCase().includes(query)) ||
        (o.destination && o.destination.toLowerCase().includes(query)) ||
        (o.product && o.product.toLowerCase().includes(query)) ||
        (o.driver && o.driver.toLowerCase().includes(query)) ||
        (o.plate && o.plate.toLowerCase().includes(query)) ||
        (o.fill_hand && o.fill_hand.toLowerCase().includes(query))
      );
    });
    renderDashboardTable(filtered);
  });

  // Date Range Select Listener
  const dateRangeSelect = document.getElementById('date-range-select');
  const customInputs = document.getElementById('custom-date-inputs');
  const startDateInput = document.getElementById('filter-start-date');
  const endDateInput = document.getElementById('filter-end-date');

  dateRangeSelect.addEventListener('change', (e) => {
    activeDateFilter = e.target.value;
    if (activeDateFilter === 'custom') {
      customInputs.classList.remove('hidden');
    } else {
      customInputs.classList.add('hidden');
      refreshDashboardUI();
    }
  });

  startDateInput.addEventListener('change', refreshDashboardUI);
  endDateInput.addEventListener('change', refreshDashboardUI);

  // Export excel
  document.getElementById('btn-export').addEventListener('click', () => {
    if (ordersData.length === 0) {
      alert('無出貨班表資料可供匯出！');
      return;
    }
    window.location.href = '/api/export';
  });

  // Tech personal query search
  document.getElementById('btn-query-search').addEventListener('click', queryTechSchedule);
  document.getElementById('query-tech-name')?.addEventListener('change', queryTechSchedule);

  // Refresh logs button
  const refreshLogsBtn = document.getElementById('btn-refresh-logs');
  if (refreshLogsBtn) {
    refreshLogsBtn.addEventListener('click', loadAndRenderLogs);
  }
}

// 9. Tech Service Query Logic
let currentTechDateMode = 'today_tmr'; // 'today_tmr' | 'past' | 'all'

function setupTechDateFilterButtons() {
  const btnTodayTmr = document.getElementById('btn-tech-range-today-tmr');
  const btnPast = document.getElementById('btn-tech-range-past');
  const btnAll = document.getElementById('btn-tech-range-all');

  function updateActive(activeBtn, mode) {
    [btnTodayTmr, btnPast, btnAll].forEach(b => {
      if (b) {
        b.classList.remove('active', 'btn-cyan');
        b.classList.add('btn-secondary');
      }
    });
    if (activeBtn) {
      activeBtn.classList.remove('btn-secondary');
      activeBtn.classList.add('active', 'btn-cyan');
    }
    currentTechDateMode = mode;
    queryTechSchedule();
  }

  if (btnTodayTmr && !btnTodayTmr.hasAttribute('data-bound')) {
    btnTodayTmr.setAttribute('data-bound', '1');
    btnTodayTmr.addEventListener('click', () => updateActive(btnTodayTmr, 'today_tmr'));
  }
  if (btnPast && !btnPast.hasAttribute('data-bound')) {
    btnPast.setAttribute('data-bound', '1');
    btnPast.addEventListener('click', () => updateActive(btnPast, 'past'));
  }
  if (btnAll && !btnAll.hasAttribute('data-bound')) {
    btnAll.setAttribute('data-bound', '1');
    btnAll.addEventListener('click', () => updateActive(btnAll, 'all'));
  }
}

function queryTechSchedule() {
  const techInput = document.getElementById('query-tech-name');
  const techName = techInput ? techInput.value : '';
  const grid = document.getElementById('query-results-grid');
  const title = document.getElementById('query-results-title');

  setupTechDateFilterButtons();

  if (!techName) {
    if (grid) grid.innerHTML = `<div class="no-results">請選擇技服人員姓名並點選查詢。</div>`;
    return;
  }

  // 取得今天與明天的 YYYY-MM-DD
  const now = new Date();
  const todayStr = formatDate(now);
  const tmr = new Date(now);
  tmr.setDate(tmr.getDate() + 1);
  const tmrStr = formatDate(tmr);

  // Filter local memory orders
  const filtered = ordersData.filter(o => {
    if (!o.fill_hand) return false;
    
    // Check if fill_hand contains the name
    const matchName = o.fill_hand.toLowerCase().includes(techName.toLowerCase());
    if (!matchName) return false;

    const oDate = o.expected_date || '';
    if (currentTechDateMode === 'today_tmr') {
      // 包含今天與明天 (若當天/明天無資料，且無任何近期資料，則寬鬆顯示)
      return oDate === todayStr || oDate === tmrStr;
    } else if (currentTechDateMode === 'past') {
      // 之前歷史排程
      return oDate && oDate < todayStr;
    }
    // 'all'
    return true;
  });

  // 智能防呆：若「今天與明天」剛好沒有排程，但該人員有其他日程，自動提示並引導切換
  let modeLabel = '當天與明天 (今天/明天)';
  if (currentTechDateMode === 'past') modeLabel = '歷史排程 (今天之前)';
  if (currentTechDateMode === 'all') modeLabel = '全部日程';

  title.classList.remove('hidden');
  title.textContent = `📋 ${techName} 的出貨日程【${modeLabel}】：共 ${filtered.length} 筆`;

  if (filtered.length === 0) {
    const totalForPerson = ordersData.filter(o => o.fill_hand && o.fill_hand.toLowerCase().includes(techName.toLowerCase())).length;
    let hint = '';
    if (currentTechDateMode === 'today_tmr' && totalForPerson > 0) {
      hint = `<div style="margin-top: 10px; font-size: 0.9rem; color: #38bdf8;">💡 提示：您今天與明天目前無出貨任務。系統中您尚有 <b>${totalForPerson} 筆</b> 其他日程，可點擊上方「<b>📜 之前歷史排程</b>」或「<b>🌐 全部日程</b>」查看！</div>`;
    }
    grid.innerHTML = `<div class="no-results">查無此時段之出貨日程。${hint}</div>`;
    return;
  }

  grid.innerHTML = filtered.map(o => {
    const isCompleted = o.plate && o.driver;
    const transportInfo = isCompleted 
      ? `<div class="query-card-driver">🚚 司機: ${escapeHtml(o.driver)} | ${escapeHtml(o.plate)} | 📞 ${escapeHtml(o.phone)}</div>`
      : `<div class="query-card-driver" style="color: var(--accent-orange);">⏳ 運輸車輛尚未排定</div>`;
      
    const departureInfo = o.departure_date 
      ? `<div>🕒 出車時間: ${escapeHtml(o.departure_date)} ${escapeHtml(o.departure_time) || ''}</div>`
      : `<div>🕒 預計到貨時間: ${escapeHtml(o.expected_date)} ${escapeHtml(o.arrival_time) || ''}</div>`;

    const readBadge = getReadStatusBadge(o);
    const orderKey = o.id || `${o.destination}_${o.expected_date}_${o.arrival_time}`;

    return `
      <div class="query-card" onclick="openOrderDetailModalByKey('${escapeHtml(orderKey)}')" style="cursor: pointer;" title="點擊確認並標記已讀">
        <div class="query-card-header">
          <span class="query-card-time">${escapeHtml(o.arrival_time) || '到貨時間未定'}</span>
          <span class="query-card-date">${escapeHtml(o.expected_date)}</span>
        </div>
        <div class="query-card-body">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="query-card-client">${escapeHtml(o.client) || '對象未提供'}</span>
            ${readBadge}
          </div>
          <div class="query-card-dest" title="${escapeHtml(o.destination) || ''}">📍 ${escapeHtml(truncateStr(o.destination, 24))}</div>
          <div class="query-card-product">品名: ${escapeHtml(o.product) || '-'} | 批號: ${escapeHtml(o.batch) || '-'}</div>
        </div>
        <div class="query-card-footer">
          ${departureInfo}
          ${transportInfo}
          <div class="query-card-status">
            <span>出貨單號: ${escapeHtml(o.id) || '無'}</span>
            <span>${getStatusBadge(o)}</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// 10. Manual Edit Modal Logic
const editModal = document.getElementById('edit-modal');
const editForm = document.getElementById('edit-order-form');

window.openEditModal = function(id, destination, product, expected_date, arrival_time) {
  // Find order in local data
  let order = null;
  if (id && id !== 'null' && id !== 'undefined' && id !== '') {
    order = ordersData.find(o => o.id === id);
  } else {
    // Find by unique A-H details
    order = ordersData.find(o => 
      o.destination === destination && 
      o.product === product && 
      o.expected_date === expected_date && 
      o.arrival_time === arrival_time
    );
  }

  if (!order) {
    alert('找不到對應訂單！');
    return;
  }

  selectedOrderForEdit = order;

  // Populate readonly fields
  document.getElementById('edit-id').value = order.id || '無';
  document.getElementById('edit-batch').value = order.batch || '-';
  document.getElementById('edit-client').value = order.client || '-';
  document.getElementById('edit-destination').value = order.destination || '-';
  document.getElementById('edit-product').value = order.product || '-';
  document.getElementById('edit-datetime').value = `${order.expected_date} ${order.arrival_time}`;

  // Populate editable fields
  document.getElementById('edit-fill-hand').value = order.fill_hand || '';
  document.getElementById('edit-driver-code').value = order.driver_code || '';
  document.getElementById('edit-plate').value = order.plate || '';
  document.getElementById('edit-driver').value = order.driver || '';
  document.getElementById('edit-phone').value = order.phone || '';
  document.getElementById('edit-departure-date').value = order.departure_date || '';
  document.getElementById('edit-departure-time').value = order.departure_time || '';

  // Transporter edits constraint: disable fill hand
  const fillHandInput = document.getElementById('edit-fill-hand');
  if (currentUser && currentUser.role === 'transporter') {
    fillHandInput.disabled = true;
    fillHandInput.style.opacity = '0.5';
    fillHandInput.style.cursor = 'not-allowed';
  } else {
    fillHandInput.disabled = false;
    fillHandInput.style.opacity = '1';
    fillHandInput.style.cursor = 'auto';
  }

  // Setup driver code auto-lookup trigger in modal
  const codeInput = document.getElementById('edit-driver-code');
  codeInput.oninput = (e) => {
    const code = e.target.value.trim();
    if (code) {
      const match = driversData.find(d => d.code === code);
      if (match) {
        document.getElementById('edit-plate').value = match.plate;
        document.getElementById('edit-driver').value = match.name;
        document.getElementById('edit-phone').value = match.phone;
      }
    }
  };

  // Open modal
  editModal.classList.add('open');
};

function setupEditModal() {
  document.getElementById('close-edit-modal').addEventListener('click', closeEditModal);
  document.getElementById('btn-edit-cancel').addEventListener('click', closeEditModal);
  
  editForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!selectedOrderForEdit) return;

    const payload = {
      order: {
        // Identity columns (A-H)
        id: selectedOrderForEdit.id,
        batch: selectedOrderForEdit.batch,
        client: selectedOrderForEdit.client,
        destination: selectedOrderForEdit.destination,
        product: selectedOrderForEdit.product,
        expected_date: selectedOrderForEdit.expected_date,
        arrival_time: selectedOrderForEdit.arrival_time,
        
        // Updates (I-O)
        fill_hand: document.getElementById('edit-fill-hand').value,
        driver_code: document.getElementById('edit-driver-code').value,
        plate: document.getElementById('edit-plate').value,
        driver: document.getElementById('edit-driver').value,
        phone: document.getElementById('edit-phone').value,
        departure_date: document.getElementById('edit-departure-date').value,
        departure_time: document.getElementById('edit-departure-time').value,
      },
      operator: currentUser.username,
      role: currentUser.role
    };

    try {
      const res = await fetch('/api/orders/update-single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.success) {
        alert(json.message);
        closeEditModal();
        loadData();
      } else {
        alert(`更新失敗: ${json.message}`);
      }
    } catch (err) {
      console.error(err);
      alert('更新儲存錯誤！');
    }
  });
}

function closeEditModal() {
  editModal.classList.remove('open');
  selectedOrderForEdit = null;
}

// 10. Load and Render Operation Logs
async function loadAndRenderLogs() {
  const tbody = document.getElementById('logs-table-body');
  if (!tbody) return;
  
  try {
    const res = await fetch('/api/logs');
    const json = await res.json();
    if (json.success) {
      const logs = json.data;
      if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center">目前無任何作業記錄。</td></tr>`;
        return;
      }
      tbody.innerHTML = [...logs].reverse().map(log => {
        let badgeClass = 'badge-info';
        if (log.role === 'sales') badgeClass = 'badge-success';
        else if (log.role === 'tech_manager') badgeClass = 'badge-primary';
        else if (log.role === 'transporter') badgeClass = 'badge-warning';
        
        return `
          <tr>
            <td>${escapeHtml(log.timestamp)}</td>
            <td>${escapeHtml(log.operator)}</td>
            <td><span class="badge ${badgeClass}">${escapeHtml(log.role)}</span></td>
            <td><strong>${escapeHtml(log.action)}</strong></td>
            <td title="${escapeHtml(log.details) || ''}">${escapeHtml(log.details) || ''}</td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading logs:', err);
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">載入作業日誌失敗！</td></tr>`;
  }
}


window.isTSMCOrder = function(o) {
  if (!o || !o.destination) return false;
  return o.destination.includes('台積') || o.destination.includes('F20') || o.destination.includes('TSMC');
};

window.download3in1 = async function(id, batch) {
  if (id === 'null' || !id) {
      id = 'batch:' + batch;
  }
  try {
    const res = await fetch(`/api/orders/${encodeURIComponent(id)}/tsmc-3in1`);
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `三合一單-${id}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } else {
      const data = await res.json();
      alert('生成失敗: ' + (data.message || ''));
    }
  } catch (err) {
    alert('下載錯誤: ' + err.message);
  }
};


// --- Location Mappings ---
const btnManageLocations = document.getElementById('btn-manage-locations');
const locationMappingModal = document.getElementById('location-mapping-modal');
const closeLocationModal = document.getElementById('close-location-modal');
const btnAddLocation = document.getElementById('btn-add-location');
const btnSaveLocation = document.getElementById('btn-save-location');
const locationMappingTable = document.getElementById('location-mapping-table') ? document.getElementById('location-mapping-table').querySelector('tbody') : null;

let currentLocationMappings = [];

if (btnManageLocations) {
  btnManageLocations.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/location-mappings');
      const data = await res.json();
      if (data.success) {
        currentLocationMappings = data.data;
        renderLocationMappings();
        locationMappingModal.classList.add('open');
      } else {
        alert(data.message);
      }
    } catch (err) {
      console.error(err);
      alert('無法載入地點代號對照表');
    }
  });
}

if (closeLocationModal) {
  closeLocationModal.addEventListener('click', () => {
    locationMappingModal.classList.remove('open');
  });
}

if (btnAddLocation) {
  btnAddLocation.addEventListener('click', () => {
    currentLocationMappings.push({ shortName: '', longCode: '' });
    renderLocationMappings();
  });
}

if (btnSaveLocation) {
  btnSaveLocation.addEventListener('click', async () => {
    const rows = locationMappingTable.querySelectorAll('tr');
    const newMappings = [];
    rows.forEach(row => {
      const inputs = row.querySelectorAll('input');
      if (inputs.length >= 3) {
        const shortName = inputs[0].value.trim();
        const fullName  = inputs[1].value.trim();
        const code      = inputs[2].value.trim();
        if (shortName || code) {
          newMappings.push({ shortName, fullName, code });
        }
      }
    });

    try {
      btnSaveLocation.disabled = true;
      btnSaveLocation.textContent = '儲存中...';
      const res = await fetch('/api/location-mappings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          mappings: newMappings,
          operator: currentUser ? currentUser.displayName : '未知',
          role: currentUser ? currentUser.role : 'admin'
        })
      });
      const data = await res.json();
      if (data.success) {
        alert('儲存成功！');
        locationMappingModal.classList.remove('open');
      } else {
        alert(data.message);
      }
    } catch (err) {
      console.error(err);
      alert('儲存失敗: ' + err.message);
    } finally {
      btnSaveLocation.disabled = false;
      btnSaveLocation.textContent = '儲存並反寫回 Excel';
    }
  });
}

function renderLocationMappings() {
  if (!locationMappingTable) return;
  locationMappingTable.innerHTML = '';
  currentLocationMappings.forEach((mapping, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="text" class="form-control" value="${mapping.shortName || ''}" placeholder="如: 15P5"></td>
      <td><input type="text" class="form-control" value="${mapping.fullName || ''}" placeholder="如: 台積電竹科15廠P5"></td>
      <td><input type="text" class="form-control" value="${mapping.code || ''}" placeholder="如: E1550155A"></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="removeLocationMapping(${index})">刪除</button>
      </td>
    `;
    locationMappingTable.appendChild(tr);
  });
}

window.removeLocationMapping = function(index) {
  currentLocationMappings.splice(index, 1);
  renderLocationMappings();
};

// =============================================================================
// 使用者帳號管理 (User Management)
// =============================================================================
let allUsersList = [];

function setupUserManagement() {
  const searchInput = document.getElementById('user-search-input');
  const roleFilter = document.getElementById('user-role-filter');
  const statusFilter = document.getElementById('user-status-filter');
  const btnAddUser = document.getElementById('btn-add-user');
  const userModal = document.getElementById('user-modal');
  const closeUserModal = document.getElementById('close-user-modal');
  const userForm = document.getElementById('user-form');
  const btnImportExcel = document.getElementById('btn-import-users-excel');
  const userExcelFile = document.getElementById('user-excel-file');
  const btnDownloadTemplate = document.getElementById('btn-download-users-template');

  if (searchInput) {
    searchInput.addEventListener('input', filterAndRenderUsers);
  }
  if (roleFilter) {
    roleFilter.addEventListener('change', filterAndRenderUsers);
  }
  if (statusFilter) {
    statusFilter.addEventListener('change', filterAndRenderUsers);
  }

  if (btnAddUser) {
    btnAddUser.addEventListener('click', () => {
      openUserModal('create');
    });
  }

  if (closeUserModal) {
    closeUserModal.addEventListener('click', () => {
      userModal.classList.remove('open');
    });
  }

  if (userForm) {
    userForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const mode = document.getElementById('user-modal-mode').value;
      const username = document.getElementById('user-username').value.trim();
      const displayName = document.getElementById('user-displayname').value.trim();
      const password = document.getElementById('user-password').value.trim();
      const role = document.getElementById('user-role').value;
      const status = document.getElementById('user-status').value;

      if (mode === 'create' && !password) {
        alert('新增帳號時密碼為必填！');
        return;
      }

      try {
        const url = mode === 'create' ? '/api/users' : `/api/users/${encodeURIComponent(username)}`;
        const method = mode === 'create' ? 'POST' : 'PUT';
        const payload = {
          username,
          displayName,
          role,
          status,
          operator: currentUser ? currentUser.displayName : 'admin'
        };
        if (password) {
          payload.password = password;
        }

        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const json = await res.json();
        if (json.success) {
          alert(json.message);
          userModal.classList.remove('open');
          loadUsersData();
        } else {
          alert('操作失敗：' + json.message);
        }
      } catch (err) {
        alert('連線伺服器出錯：' + err.message);
      }
    });
  }

  // Excel 批次匯入
  if (btnImportExcel && userExcelFile) {
    btnImportExcel.addEventListener('click', () => {
      userExcelFile.click();
    });
    userExcelFile.addEventListener('change', async () => {
      if (!userExcelFile.files || userExcelFile.files.length === 0) return;
      const file = userExcelFile.files[0];
      const formData = new FormData();
      formData.append('file', file);
      try {
        btnImportExcel.disabled = true;
        btnImportExcel.textContent = '⏳ 匯入中...';
        const res = await fetch(`/api/users/upload?operator=${encodeURIComponent(currentUser ? currentUser.displayName : 'admin')}`, {
          method: 'POST',
          body: formData
        });
        const json = await res.json();
        if (json.success) {
          alert(json.message);
          loadUsersData();
        } else {
          alert('匯入失敗：' + json.message);
        }
      } catch (err) {
        alert('匯入出錯：' + err.message);
      } finally {
        userExcelFile.value = '';
        btnImportExcel.disabled = false;
        btnImportExcel.textContent = '📥 匯入 Excel';
      }
    });
  }

  // 下載帳號範本
  if (btnDownloadTemplate) {
    btnDownloadTemplate.addEventListener('click', () => {
      window.location.href = '/api/users/download-template';
    });
  }
}

async function loadUsersData() {
  const tbody = document.getElementById('users-table-body');
  if (!tbody) return;
  tbody.innerHTML = '<tr><td colspan="5" class="text-center">載入使用者列表中...</td></tr>';

  try {
    const res = await fetch('/api/users');
    const data = await res.json();
    if (data.success) {
      allUsersList = data.users || [];
      populateUserRoleDropdowns();
      filterAndRenderUsers();
    } else {
      tbody.innerHTML = `<tr><td colspan="5" class="text-center" style="color: #f87171;">載入失敗: ${data.message}</td></tr>`;
    }
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="5" class="text-center" style="color: #f87171;">連線錯誤: ${err.message}</td></tr>`;
  }
}

function populateUserRoleDropdowns() {
  const roleFilter = document.getElementById('user-role-filter');
  const userRoleSelect = document.getElementById('user-role');
  const roles = systemRoles.length > 0 ? systemRoles : [
    { id: 'admin', name: '系統管理員 (admin)' },
    { id: 'production', name: '生產人員 (production)' },
    { id: 'sales', name: '業務人員 (sales)' },
    { id: 'tech_manager', name: '技服主管 (tech_manager)' },
    { id: 'tech_staff', name: '技服人員 (tech_staff)' },
    { id: 'transporter', name: '運輸公司 (transporter)' }
  ];

  if (roleFilter) {
    const curVal = roleFilter.value;
    roleFilter.innerHTML = '<option value="">所有角色</option>';
    roles.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.id;
      opt.textContent = r.name;
      roleFilter.appendChild(opt);
    });
    roleFilter.value = curVal;
  }

  if (userRoleSelect) {
    const curVal = userRoleSelect.value;
    userRoleSelect.innerHTML = '';
    roles.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.id;
      opt.textContent = r.name;
      userRoleSelect.appendChild(opt);
    });
    if (curVal) userRoleSelect.value = curVal;
  }
}

function filterAndRenderUsers() {
  const searchInput = document.getElementById('user-search-input');
  const roleFilter = document.getElementById('user-role-filter');
  const statusFilter = document.getElementById('user-status-filter');

  const q = searchInput ? searchInput.value.trim().toLowerCase() : '';
  const selectedRole = roleFilter ? roleFilter.value : '';
  const selectedStatus = statusFilter ? statusFilter.value : '';

  const filtered = allUsersList.filter(u => {
    const matchQ = !q || (u.username.toLowerCase().includes(q) || (u.displayName && u.displayName.toLowerCase().includes(q)));
    const matchRole = !selectedRole || u.role === selectedRole;
    const matchStatus = !selectedStatus || u.status === selectedStatus;
    return matchQ && matchRole && matchStatus;
  });

  renderUsersTable(filtered);
}

function renderUsersTable(users) {
  const tbody = document.getElementById('users-table-body');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (users.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="text-center">無符合條件的使用者帳號</td></tr>';
    return;
  }

  users.forEach(u => {
    const tr = document.createElement('tr');
    const roleBadgeClass = `badge-role badge-role-${u.role}`;
    const statusBadge = u.status === 'inactive'
      ? '<span class="badge-status badge-status-inactive">停用</span>'
      : '<span class="badge-status badge-status-active">啟用</span>';

    tr.innerHTML = `
      <td><b>${escapeHtml(u.username)}</b></td>
      <td>${escapeHtml(u.displayName || u.username)}</td>
      <td><span class="${roleBadgeClass}">${escapeHtml(u.role)}</span></td>
      <td>${statusBadge}</td>
      <td>
        <button class="user-action-btn btn-edit-user" data-username="${escapeHtml(u.username)}">編輯</button>
        ${u.username === 'admin' ? '' : `<button class="user-action-btn btn-delete-user" data-username="${escapeHtml(u.username)}">刪除</button>`}
      </td>
    `;
    tbody.appendChild(tr);
  });

  // 綁定編輯與刪除事件
  tbody.querySelectorAll('.btn-edit-user').forEach(btn => {
    btn.addEventListener('click', () => {
      const uName = btn.getAttribute('data-username');
      const targetUser = allUsersList.find(u => u.username === uName);
      if (targetUser) {
        openUserModal('edit', targetUser);
      }
    });
  });

  tbody.querySelectorAll('.btn-delete-user').forEach(btn => {
    btn.addEventListener('click', async () => {
      const uName = btn.getAttribute('data-username');
      if (!confirm(`確定要刪除使用者「${uName}」嗎？刪除後將自動同步更新本機 Excel。`)) return;

      try {
        const res = await fetch(`/api/users/${encodeURIComponent(uName)}?operator=${encodeURIComponent(currentUser ? currentUser.displayName : 'admin')}`, {
          method: 'DELETE'
        });
        const json = await res.json();
        if (json.success) {
          alert(json.message);
          loadUsersData();
        } else {
          alert('刪除失敗: ' + json.message);
        }
      } catch (err) {
        alert('刪除出錯: ' + err.message);
      }
    });
  });
}

function openUserModal(mode, user = null) {
  const modal = document.getElementById('user-modal');
  const title = document.getElementById('user-modal-title');
  const modeInput = document.getElementById('user-modal-mode');
  const uInput = document.getElementById('user-username');
  const dInput = document.getElementById('user-displayname');
  const pInput = document.getElementById('user-password');
  const pRequired = document.getElementById('user-pwd-required');
  const rSelect = document.getElementById('user-role');
  const sSelect = document.getElementById('user-status');

  populateUserRoleDropdowns();

  if (mode === 'create') {
    title.textContent = '新增使用者帳號';
    modeInput.value = 'create';
    uInput.value = '';
    uInput.readOnly = false;
    uInput.classList.remove('input-readonly');
    dInput.value = '';
    pInput.value = '123';
    pRequired.style.display = 'inline';
    sSelect.value = 'active';
  } else {
    title.textContent = `編輯使用者：${user.username}`;
    modeInput.value = 'edit';
    uInput.value = user.username;
    uInput.readOnly = true;
    uInput.classList.add('input-readonly');
    dInput.value = user.displayName || user.username;
    pInput.value = '';
    pRequired.style.display = 'none';
    if (user.role && rSelect.querySelector(`option[value="${user.role}"]`)) {
      rSelect.value = user.role;
    }
    sSelect.value = user.status || 'active';
  }

  modal.classList.add('open');
}

// =============================================================================
// 角色功能權限設定 (Permissions Matrix - 復刻圖二)
// =============================================================================
function setupPermissionsManagement() {
  const btnSavePerms = document.getElementById('btn-save-permissions');
  const btnAddRole = document.getElementById('btn-add-role-modal');
  const roleModal = document.getElementById('role-modal');
  const closeRoleModal = document.getElementById('close-role-modal');
  const roleForm = document.getElementById('role-form');

  if (btnSavePerms) {
    btnSavePerms.addEventListener('click', async () => {
      const matrixTable = document.getElementById('permissions-matrix-table');
      if (!matrixTable) return;

      const newPerms = {};
      const checkboxes = matrixTable.querySelectorAll('.perm-checkbox');
      checkboxes.forEach(cb => {
        const role = cb.getAttribute('data-role');
        const feature = cb.getAttribute('data-feature');
        if (!newPerms[role]) newPerms[role] = [];
        if (cb.checked) {
          newPerms[role].push(feature);
        }
      });

      try {
        btnSavePerms.disabled = true;
        btnSavePerms.textContent = '⏳ 儲存中...';
        const res = await fetch('/api/permissions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            permissions: newPerms,
            operator: currentUser ? currentUser.displayName : 'admin'
          })
        });
        const json = await res.json();
        if (json.success) {
          alert('🎉 角色功能權限設定已成功儲存！');
          systemPermissions = newPerms;
          if (currentUser) {
            applyRolePermissions(currentUser);
          }
        } else {
          alert('儲存失敗：' + json.message);
        }
      } catch (err) {
        alert('儲存失敗：' + err.message);
      } finally {
        btnSavePerms.disabled = false;
        btnSavePerms.textContent = '💾 儲存權限對應設定';
      }
    });
  }

  if (btnAddRole) {
    btnAddRole.addEventListener('click', () => {
      document.getElementById('new-role-id').value = '';
      document.getElementById('new-role-name').value = '';
      roleModal.classList.add('open');
    });
  }

  if (closeRoleModal) {
    closeRoleModal.addEventListener('click', () => {
      roleModal.classList.remove('open');
    });
  }

  if (roleForm) {
    roleForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const roleId = document.getElementById('new-role-id').value.trim();
      const roleName = document.getElementById('new-role-name').value.trim();
      try {
        const res = await fetch('/api/roles', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            roleId,
            roleName,
            operator: currentUser ? currentUser.displayName : 'admin'
          })
        });
        const json = await res.json();
        if (json.success) {
          alert(json.message);
          roleModal.classList.remove('open');
          loadPermissionsMatrix();
          populateUserRoleDropdowns();
        } else {
          alert('新增失敗：' + json.message);
        }
      } catch (err) {
        alert('新增出錯：' + err.message);
      }
    });
  }
}

async function loadPermissionsMatrix() {
  const theadRow = document.getElementById('permissions-matrix-head');
  const tbody = document.getElementById('permissions-matrix-body');
  if (!theadRow || !tbody) return;

  try {
    const res = await fetch('/api/permissions');
    const data = await res.json();
    if (!data.success) return;

    systemRoles = data.roles || [];
    systemFeatures = data.features || [];
    systemPermissions = data.permissions || {};

    // 1. 渲染各系統功能表頭
    theadRow.innerHTML = '<th style="min-width: 180px; text-align: left;">權限角色 \\ 系統功能</th>';
    systemFeatures.forEach(feat => {
      const th = document.createElement('th');
      th.textContent = feat.name;
      theadRow.appendChild(th);
    });

    // 2. 渲染各角色核取方塊列
    tbody.innerHTML = '';
    systemRoles.forEach(role => {
      const tr = document.createElement('tr');
      const rolePerms = systemPermissions[role.id] || [];
      
      let cellsHtml = `<td>${escapeHtml(role.name)}</td>`;
      systemFeatures.forEach(feat => {
        const isChecked = rolePerms.includes(feat.id) ? 'checked' : '';
        cellsHtml += `
          <td>
            <input type="checkbox" class="perm-checkbox" data-role="${escapeHtml(role.id)}" data-feature="${escapeHtml(feat.id)}" ${isChecked}>
          </td>
        `;
      });

      tr.innerHTML = cellsHtml;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error('Failed to load permissions matrix:', err);
  }
}

// =============================================================================
// 修改個人密碼 (Change Password Modal)
// =============================================================================
function setupChangePasswordModal() {
  const btnOpen = document.getElementById('btn-change-password');
  const modal = document.getElementById('change-password-modal');
  const btnClose = document.getElementById('close-pwd-modal');
  const form = document.getElementById('change-password-form');

  if (btnOpen) {
    btnOpen.addEventListener('click', () => {
      document.getElementById('pwd-old').value = '';
      document.getElementById('pwd-new').value = '';
      document.getElementById('pwd-confirm').value = '';
      modal.classList.add('open');
    });
  }

  if (btnClose) {
    btnClose.addEventListener('click', () => {
      modal.classList.remove('open');
    });
  }

  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const oldPassword = document.getElementById('pwd-old').value.trim();
      const newPassword = document.getElementById('pwd-new').value.trim();
      const confirmPassword = document.getElementById('pwd-confirm').value.trim();

      if (!currentUser) {
        alert('請先登入帳號！');
        return;
      }
      if (newPassword !== confirmPassword) {
        alert('兩次輸入的新密碼不一致，請重新檢查！');
        return;
      }

      try {
        const res = await fetch('/api/users/change-password', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: currentUser.username,
            oldPassword,
            newPassword
          })
        });
        const json = await res.json();
        if (json.success) {
          alert(json.message);
          modal.classList.remove('open');
        } else {
          alert('修改失敗：' + json.message);
        }
      } catch (err) {
        alert('連線失敗：' + err.message);
      }
    });
  }
}

// =============================================================================
// 生產專區資料載入 (Production Data)
// =============================================================================
function loadProductionData() {
  const tbody = document.getElementById('production-table-body');
  if (!tbody) return;

  if (ordersData.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center">目前無生產充填排程資料</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  ordersData.forEach(o => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${escapeHtml(o.id || '-')}</td>
      <td><b>${escapeHtml(o.batch || '-')}</b></td>
      <td>${escapeHtml(o.destination || '-')}</td>
      <td><span class="product-badge">${escapeHtml(o.product || '-')}</span></td>
      <td>${escapeHtml(o.expected_date || '')} ${escapeHtml(o.arrival_time || '')}</td>
      <td>${escapeHtml(o.fill_hand || '-')}</td>
      <td>${escapeHtml(o.plate || '')} ${escapeHtml(o.driver || '')}</td>
      <td><span class="badge-status badge-status-active">已排程</span></td>
    `;
    tbody.appendChild(tr);
  });

  const exportBtn = document.getElementById('btn-export-production');
  if (exportBtn && !exportBtn.hasAttribute('data-bound')) {
    exportBtn.setAttribute('data-bound', '1');
    exportBtn.addEventListener('click', () => {
      window.location.href = '/api/export';
    });
  }
}

