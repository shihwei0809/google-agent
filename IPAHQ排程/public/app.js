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
});

// Login & Permissions Handling
function checkLogin() {
  const userJson = sessionStorage.getItem('user');
  const overlay = document.getElementById('login-overlay');
  const profile = document.getElementById('user-profile');
  const displayName = document.getElementById('user-display-name');
  
  if (userJson) {
    currentUser = JSON.parse(userJson);
    overlay.classList.add('hidden');
    profile.classList.remove('hidden');
    displayName.textContent = currentUser.displayName;
    applyRolePermissions(currentUser);
  } else {
    currentUser = null;
    overlay.classList.remove('hidden');
    profile.classList.add('hidden');
  }
}

function applyRolePermissions(user) {
  // Reset navigation tabs visibility
  navTabs.forEach(t => t.classList.remove('hidden'));
  
  const querySelect = document.getElementById('query-tech-name');
  querySelect.disabled = false;

  if (user.role === 'sales' || user.role === 'tech_manager') {
    // Full access: can see and click all tabs including logs
    const activeTab = document.querySelector('.nav-tab.active');
    if (!activeTab || activeTab.classList.contains('hidden')) {
      document.querySelector('[data-tab="tab-dashboard"]').click();
    }
  } else {
    // Non-admin roles cannot see logs tab
    document.querySelector('[data-tab="tab-logs"]').classList.add('hidden');
    
    if (user.role === 'tech_staff') {
      // Only query tab
      navTabs.forEach(t => {
        if (t.getAttribute('data-tab') !== 'tab-query') {
          t.classList.add('hidden');
        }
      });
      
      // Auto-select user name and lock it
      querySelect.value = user.username;
      querySelect.disabled = true;
      
      // Switch to query tab
      document.querySelector('[data-tab="tab-query"]').click();
      
      // Auto query schedule
      queryTechSchedule();
    } else if (user.role === 'transporter') {
      // Only see Dashboard and Transporter tabs
      navTabs.forEach(t => {
        const tabName = t.getAttribute('data-tab');
        if (tabName !== 'tab-dashboard' && tabName !== 'tab-transport') {
          t.classList.add('hidden');
        }
      });
      
      const activeTab = document.querySelector('.nav-tab.active');
      if (!activeTab || activeTab.classList.contains('hidden')) {
        document.querySelector('[data-tab="tab-dashboard"]').click();
      }
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
        sessionStorage.setItem('user', JSON.stringify(json.user));
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
    sessionStorage.removeItem('user');
    currentUser = null;
    checkLogin();
  });
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
      populateTechNamesDropdown(ordersData);
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

// 3. Render Dashboard Table
function renderDashboardTable(orders) {
  const tbody = document.getElementById('dashboard-table-body');
  const cardsContainer = document.getElementById('dashboard-cards-list');
  
  if (orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="16" class="text-center">請先至「業務專區」上傳基準出貨清單 Excel</td></tr>`;
    if (cardsContainer) {
      cardsContainer.innerHTML = `<div class="no-results">請先至「業務專區」上傳基準出貨清單 Excel</div>`;
    }
    return;
  }

  // Render desktop table
  tbody.innerHTML = orders.map(o => {
    const statusBadge = getStatusBadge(o);
    const idText = o.id || '<span class="text-muted">無</span>';
    const batchText = o.batch || '-';
    
    const showEdit = currentUser && (currentUser.role === 'sales' || currentUser.role === 'tech_manager' || currentUser.role === 'transporter');
    const actionCell = showEdit 
      ? `<td><span class="action-link" onclick="openEditModal('${o.id}', '${o.destination}', '${o.product}', '${o.expected_date}', '${o.arrival_time}')">編輯</span></td>`
      : `<td>-</td>`;

    return `
      <tr>
        <td>${idText}</td>
        <td>${batchText}</td>
        <td>${o.client || '-'}</td>
        <td title="${o.destination || ''}">${truncateStr(o.destination, 18)}</td>
        <td>${o.product || '-'}</td>
        <td>${o.expected_date || '-'}</td>
        <td>${o.arrival_time || '-'}</td>
        <td>${o.transport_type || '-'}</td>
        <td>${formatFillHand(o.fill_hand)}</td>
        <td>${o.plate || '-'}</td>
        <td>${o.driver || '-'}</td>
        <td>${o.phone || '-'}</td>
        <td>${o.departure_date || '-'}</td>
        <td>${o.departure_time || '-'}</td>
        <td>${o.driver_code || '-'}</td>
        ${actionCell}
      </tr>
    `;
  }).join('');

  // Render mobile cards list
  if (cardsContainer) {
    cardsContainer.innerHTML = orders.map(o => {
      const statusBadge = getStatusBadge(o);
      const idText = o.id || '無單號';
      const showEdit = currentUser && (currentUser.role === 'sales' || currentUser.role === 'tech_manager' || currentUser.role === 'transporter');
      const editBtn = showEdit 
        ? `<button class="btn btn-secondary btn-sm" onclick="openEditModal('${o.id}', '${o.destination}', '${o.product}', '${o.expected_date}', '${o.arrival_time}')">編輯</button>`
        : '';
        
      return `
        <div class="mobile-order-card">
          <div class="mobile-card-header">
            <div class="card-title-group">
              <span class="card-time">${o.arrival_time || '時間未定'}</span>
              <span class="card-date">${o.expected_date || ''}</span>
            </div>
            <div>${statusBadge}</div>
          </div>
          <div class="mobile-card-body">
            <div class="card-detail"><strong>對象：</strong>${o.client || '-'}</div>
            <div class="card-detail" title="${o.destination || ''}"><strong>指送地：</strong>${o.destination || '-'}</div>
            <div class="card-detail"><strong>品名：</strong>${o.product || '-'} | <strong>批號：</strong>${o.batch || '-'}</div>
            <div class="card-detail"><strong>運輸方式：</strong>${o.transport_type || '-'}</div>
            <div class="card-detail-divider"></div>
            <div class="card-detail"><strong>技服充填手：</strong>${formatFillHand(o.fill_hand)}</div>
            <div class="card-detail"><strong>車牌司機：</strong>${o.plate ? `${o.plate} (${o.driver})` : '⏳ 尚未排定'}</div>
            ${o.phone ? `<div class="card-detail"><strong>司機電話：</strong>${o.phone}</div>` : ''}
            ${o.departure_date ? `<div class="card-detail"><strong>出車時間：</strong>${o.departure_date} ${o.departure_time || ''}</div>` : ''}
          </div>
          <div class="mobile-card-footer">
            <span>單號：${idText}</span>
            ${editBtn}
          </div>
        </div>
      `;
    }).join('');
  }
}

// Helper to truncate long strings
function truncateStr(str, len) {
  if (!str) return '';
  return str.length > len ? str.substring(0, len) + '...' : str;
}

// Helper to format fill_hand for display (replace \n with spaces or small tags)
function formatFillHand(val) {
  if (!val) return '-';
  return val.replace(/\n/g, ' / ');
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
function populateTechNamesDropdown(orders) {
  const select = document.getElementById('query-tech-name');
  const currentSelection = select.value;
  
  // Extract unique names
  const names = new Set();
  orders.forEach(o => {
    if (o.fill_hand) {
      // Split by newline or slash to get name only
      const nameOnly = o.fill_hand.split(/[\n/]/)[0].trim();
      if (nameOnly) names.add(nameOnly);
    }
  });

  // Keep default option
  select.innerHTML = '<option value="">-- 請選擇您的姓名 --</option>';
  Array.from(names).sort().forEach(name => {
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
            <td>${item.uploaded.id || '<span class="text-muted">無</span>'}</td>
            <td>${item.uploaded.destination || '-'}</td>
            <td>${item.uploaded.product || '-'}</td>
            <td>${item.uploaded.expected_date || '-'}</td>
            <td>${item.uploaded.arrival_time || '-'}</td>
            <td><span class="badge badge-info">${item.uploaded.fill_hand || '-'}</span></td>
            <td><span class="badge badge-success">比對成功 (${item.matchBy === 'id' ? '訂單單號' : '關鍵欄位'})</span></td>
          </tr>
        `;
      });

      // Show mismatched ones
      json.results.mismatched.forEach(item => {
        tbody.innerHTML += `
          <tr class="preview-mismatched">
            <td>${item.rowNum}</td>
            <td>${item.uploaded.id || '<span class="text-muted">無</span>'}</td>
            <td>${item.uploaded.destination || '-'}</td>
            <td>${item.uploaded.product || '-'}</td>
            <td>${item.uploaded.expected_date || '-'}</td>
            <td>${item.uploaded.arrival_time || '-'}</td>
            <td>${item.uploaded.fill_hand || '-'}</td>
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
        const driverCodeDisplay = item.uploaded.driver_code ? `${item.uploaded.driver_code} (${item.uploaded.driver || '-'})` : '-';
        const carInfo = `${item.uploaded.plate || '-'} / ${item.uploaded.phone || '-'}`;
        const timeDisplay = `${item.uploaded.departure_date || '-'} ${item.uploaded.departure_time || '-'}`;
        
        tbody.innerHTML += `
          <tr class="preview-matched">
            <td>${item.rowNum}</td>
            <td>${item.uploaded.id || '<span class="text-muted">無</span>'}</td>
            <td>${item.uploaded.destination || '-'}</td>
            <td>${item.uploaded.product || '-'}</td>
            <td>${item.uploaded.expected_date || '-'}</td>
            <td>${item.uploaded.arrival_time || '-'}</td>
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
            <td>${item.uploaded.id || '<span class="text-muted">無</span>'}</td>
            <td>${item.uploaded.destination || '-'}</td>
            <td>${item.uploaded.product || '-'}</td>
            <td>${item.uploaded.expected_date || '-'}</td>
            <td>${item.uploaded.arrival_time || '-'}</td>
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

  // Refresh logs button
  const refreshLogsBtn = document.getElementById('btn-refresh-logs');
  if (refreshLogsBtn) {
    refreshLogsBtn.addEventListener('click', loadAndRenderLogs);
  }
}

// 9. Tech Service Query Logic
function queryTechSchedule() {
  const techName = document.getElementById('query-tech-name').value;
  const selectDate = document.getElementById('query-date').value; // YYYY-MM-DD
  const grid = document.getElementById('query-results-grid');
  const title = document.getElementById('query-results-title');

  if (!techName) {
    alert('請選擇技服充填手姓名！');
    return;
  }

  // Filter local memory orders
  const filtered = ordersData.filter(o => {
    if (!o.fill_hand) return false;
    
    // Check if fill_hand contains the name
    const matchName = o.fill_hand.toLowerCase().includes(techName.toLowerCase());
    
    if (selectDate) {
      return matchName && o.expected_date === selectDate;
    }
    return matchName;
  });

  title.classList.remove('hidden');
  title.textContent = `查詢結果：${techName} (共 ${filtered.length} 筆)`;

  if (filtered.length === 0) {
    grid.innerHTML = `<div class="no-results">查無您負責的出貨日程。${selectDate ? '可以清除日期再試一次。' : ''}</div>`;
    return;
  }

  grid.innerHTML = filtered.map(o => {
    const isCompleted = o.plate && o.driver;
    const transportInfo = isCompleted 
      ? `<div class="query-card-driver">🚚 司機: ${o.driver} | ${o.plate} | 📞 ${o.phone}</div>`
      : `<div class="query-card-driver" style="color: var(--accent-orange);">⏳ 運輸車輛尚未排定</div>`;
      
    const departureInfo = o.departure_date 
      ? `<div>🕒 出車時間: ${o.departure_date} ${o.departure_time || ''}</div>`
      : `<div>🕒 預計到貨時間: ${o.expected_date} ${o.arrival_time || ''}</div>`;

    return `
      <div class="query-card">
        <div class="query-card-header">
          <span class="query-card-time">${o.arrival_time || '到貨時間未定'}</span>
          <span class="query-card-date">${o.expected_date}</span>
        </div>
        <div class="query-card-body">
          <div class="query-card-client">${o.client || '對象未提供'}</div>
          <div class="query-card-dest" title="${o.destination || ''}">📍 ${truncateStr(o.destination, 24)}</div>
          <div class="query-card-product">品名: ${o.product || '-'} | 批號: ${o.batch || '-'}</div>
        </div>
        <div class="query-card-footer">
          ${departureInfo}
          ${transportInfo}
          <div class="query-card-status">
            <span>出貨單號: ${o.id || '無'}</span>
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
            <td>${log.timestamp}</td>
            <td>${log.operator}</td>
            <td><span class="badge ${badgeClass}">${log.role}</span></td>
            <td><strong>${log.action}</strong></td>
            <td title="${log.details || ''}">${log.details || ''}</td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Error loading logs:', err);
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">載入作業日誌失敗！</td></tr>`;
  }
}
