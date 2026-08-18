
  // ==================== 全域狀態與初始化 ====================
  let state = {
    factories: [],        // 廠區清單
    lines: [],            // 產線清單
    currentFactory: 'all', // 當前檢視廠區篩選
    products: [],         // 產品清單
    tanks: [],            // 儲槽/容器清單
    schedules: [],        // 生產排程清單
    transactionLogs: [],  // 進出庫紀錄明細
    ships: [],            // 船隻狀態清單
    startDateTime: ""     // 排程起始日
  };

  // 用於 Modal 編輯狀態追蹤
  let editingProductId = null;
  let editingFactoryId = null;
  let editingLineId = null;
  let editingTankId = null;
  let editingScheduleId = null;
  let editingShipId = null;

  // 初始化頁面
  document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupClock();
    setupEventListeners();
    loadDataFromCloud();
  });

  // ==================== 時鐘與定時器 ====================
  function setupClock() {
    const clockEl = document.getElementById('live-clock');
    const updateClock = () => {
      const now = new Date();
      const pad = (n) => String(n).padStart(2, '0');
      const yyyy = now.getFullYear();
      const mm = pad(now.getMonth() + 1);
      const dd = pad(now.getDate());
      const hh = pad(now.getHours());
      const min = pad(now.getMinutes());
      const ss = pad(now.getSeconds());
      clockEl.innerHTML = `<i class="fa-regular fa-clock"></i> ${yyyy}/${mm}/${dd} ${hh}:${min}:${ss}`;
    };
    updateClock();
    setInterval(updateClock, 1000);
    
    // 每分鐘自動重算一次儲槽狀態與水位
    setInterval(calculateAndRenderDashboard, 60000);
  }

  // ==================== 頁面分頁切換 ====================
  function setupTabs() {
    const navBtns = document.querySelectorAll('.nav-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    const pageTitle = document.getElementById('page-title');
    const pageSubtitle = document.getElementById('page-subtitle');
    
    const tabMeta = {
      dashboard: { title: "儀表板總覽", desc: "即時儲槽狀態、警報預測與生產進度" },
      schedules: { title: "生產排程管理", desc: "配置生產班表與檢視產能甘特圖" },
      tanks: { title: "儲槽與容器配置", desc: "設定固定式儲槽、行動式 Isotank 的容量上限與當前儲量" },
      products: { title: "產品與廠區設定", desc: "管理系統內的產品配方及廠區" },
      logs: { title: "進出料與交易紀錄", desc: "手動登記儲槽出庫、轉料或進料交易" },
      ships: { title: "船隻位置追蹤", desc: "掌握原料進港與船隻動態" },
      archive: { title: "系統資料備份還原", desc: "建立雲端備份存檔，或還原歷史紀錄" }
    };

    navBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        
        // 切換按鈕狀態
        navBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // 切換視圖狀態
        tabPanes.forEach(pane => pane.classList.remove('active'));
        const activePane = document.getElementById(`tab-${tabId}`);
        if (activePane) activePane.classList.add('active');
        
        // 更新標題
        if (tabMeta[tabId]) {
          pageTitle.innerText = tabMeta[tabId].title;
          pageSubtitle.innerText = tabMeta[tabId].desc;
        }
        
        // 切換分頁時重新渲染特定圖表或列表
        if (tabId === 'dashboard') {
          calculateAndRenderDashboard();
        } else if (tabId === 'schedules') {
          renderSchedules();
          renderGanttChart();
        } else if (tabId === 'tanks') {
          renderTanks();
        } else if (tabId === 'products') {
          renderProducts();
          renderFactories();
          renderLines();
          renderLines();
        } else if (tabId === 'ships') {
          renderShips();
        } else if (tabId === 'logs') {
          renderLogs();
          initBatchGrid();
        } else if (tabId === 'archive') {
          loadArchiveList();
        }
      });
    });
  }

  // ==================== 雲端資料同步 API ====================
  function loadDataFromCloud() {
    showLoading(true, "正在從雲端載入資料...");
    if (typeof google === 'undefined' || !google.script || !google.script.run) {
      showLoading(false);
      showToast("偵測為本地執行模式 (未使用 GAS)，載入模擬範例資料", "warning");
      loadMockData();
      return;
    }
    google.script.run
      .withSuccessHandler(data => {
        showLoading(false);
        if (data._error) {
          showToast("載入資料失敗: " + data._error, "error");
          return;
        }
        
        state.factories = data.factories || [];
        state.lines = data.lines || [];
        state.products = data.products || [];
        state.tanks = data.tanks || [];
        state.schedules = data.schedules || [];
        state.transactionLogs = data.transactionLogs || [];
        state.ships = data.ships || [];
        state.startDateTime = data.startDateTime || "";
        state.continuousStart = data.continuousStart;
        
        showToast("雲端資料同步完成！", "success");
        
        updateAllDropdowns();
        calculateAndRenderDashboard();
        updateStats();
      })
      .withFailureHandler(err => {
        showLoading(false);
        showToast("載入資料時發生系統錯誤", "error");
        console.error(err);
      })
      .loadCloudData();
  }

  function saveDataToCloud(callback) {
    showLoading(true, "正在將資料儲存至雲端...");
    if (typeof google === 'undefined' || !google.script || !google.script.run) {
      showLoading(false);
      showToast("本地模式下無法寫入雲端，資料已儲存！", "success");
      updateStats();
      if (callback) callback();
      return;
    }
    google.script.run
      .withSuccessHandler(result => {
        showLoading(false);
        if (result === "SUCCESS") {
          showToast("資料成功儲存至雲端工作表！", "success");
          updateStats();
          if (callback) callback();
        } else {
          showToast("儲存失敗: " + result, "error");
        }
      })
      .withFailureHandler(err => {
        showLoading(false);
        showToast("儲存資料時發生系統錯誤", "error");
        console.error(err);
      })
      .saveCloudData(state);
  }

  // 本地測試模擬資料載入
  function loadMockData() {
    state.factories = [
      { id: "factory-1", name: "一廠" },
      { id: "factory-2", name: "二廠" }
    ];
    state.products = [
      { id: "p-01", name: "乙二醇 (EG)", code: "EG-10", color: "#00f2fe", desc: "標準工業級乙二醇" },
      { id: "p-02", name: "丙二醇 (PG)", code: "PG-20", color: "#8b5cf6", desc: "醫療化妝品級丙二醇" }
    ];
    state.tanks = [
      { id: "t-01", factoryId: "factory-1", name: "T-101 儲槽", type: "tank", productId: "p-01", capacity: 50000, currentLevel: 21000, outflowRate: 200, safetyLevel: 5000, status: "normal" },
      { id: "t-02", factoryId: "factory-2", name: "T-102 儲槽", type: "tank", productId: "p-02", capacity: 40000, currentLevel: 12000, outflowRate: 150, safetyLevel: 4000, status: "normal" },
      { id: "t-03", factoryId: "factory-1", name: "ISO-08 槽車", type: "isotank", productId: "p-01", capacity: 18000, currentLevel: 15000, outflowRate: 0, safetyLevel: 0, status: "normal" }
    ];
    
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const formatTime = (d) => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    
    // 建立排程時間：一個剛開始，一個預計明天
    const start1 = new Date(now.getTime() - 2 * 3600000);
    const end1 = new Date(now.getTime() + 10 * 3600000);
    const start2 = new Date(now.getTime() + 12 * 3600000);
    const end2 = new Date(now.getTime() + 28 * 3600000);
    
    state.schedules = [
      { id: "s-01", productId: "p-01", tankId: "t-01", rate: 500, start: formatTime(start1), end: formatTime(end1) },
      { id: "s-02", productId: "p-02", tankId: "t-02", rate: 300, start: formatTime(start2), end: formatTime(end2) }
    ];
    state.ships = [
      { id: "ship-01", name: "Ever Green", code: "9811000", location: "南海 (航向高雄港)", eta: formatTime(new Date(now.getTime() + 48 * 3600000)), productId: "p-01", amount: 15000, status: "in_transit" }
    ];
    state.transactionLogs = [
      { id: "l-01", timestamp: new Date(now.getTime() - 3 * 3600000).toISOString(), tankId: "t-01", productId: "p-01", type: "outflow", amount: 2000, remark: "裝載槽車 ISO-02 / 王小明" }
    ];
    
    updateAllDropdowns();
    calculateAndRenderDashboard();
    updateStats();
  }

  // ==================== 統計數據與分析更新 ====================
  function updateStats() {
    document.getElementById('stat-tanks-count').innerText = state.tanks.length;
    document.getElementById('stat-products-count').innerText = state.products.length;
    
    const now = new Date();
    const activeSchedules = state.schedules.filter(s => {
      const start = new Date(s.start);
      const end = new Date(s.end);
      return now >= start && now <= end;
    });
    document.getElementById('stat-schedules-count').innerText = activeSchedules.length;
  }

  // 更新所有表單與分頁篩選中的下拉選單
  function updateAllDropdowns() {
    
    const globalSelect = document.getElementById('global-factory-select');
    const tankFactorySelect = document.getElementById('tank-factory');
    if (globalSelect && tankFactorySelect) {
      const currentGlobalVal = globalSelect.value || state.currentFactory;
      globalSelect.innerHTML = '<option value="all">🏢 總覽 (全部廠區)</option>';

      tankFactorySelect.innerHTML = '';
      const lineFactorySelect = document.getElementById('line-factory');
      if (lineFactorySelect) lineFactorySelect.innerHTML = '';
      
      state.factories.forEach(f => {
        const opt1 = document.createElement('option');
        opt1.value = f.id; opt1.innerText = `🏢 ${f.name}`;
        globalSelect.appendChild(opt1);
        
        const opt2 = document.createElement('option');
        opt2.value = f.id; opt2.innerText = f.name;
        tankFactorySelect.appendChild(opt2);
        
        if (lineFactorySelect) {
          const opt3 = document.createElement('option');
          opt3.value = f.id; opt3.innerText = f.name;
          lineFactorySelect.appendChild(opt3);
        }
      });

      globalSelect.value = state.currentFactory;
    }

    const prodSelects = [
      document.getElementById('tank-product'),
      document.getElementById('schedule-product'),
      document.getElementById('filter-schedule-product'),
      document.getElementById('ship-product')
    ];
    
    const tankSelects = [
      document.getElementById('schedule-tank'),
      document.getElementById('schedule-source-tank'),
      document.getElementById('log-tank'),
      document.getElementById('filter-log-tank'),
      document.getElementById('forecast-tank-select')
    ];

    // 1. 填入產品下拉選單
    prodSelects.forEach(select => {
      if (!select) return;
      const isFilter = select.id.startsWith('filter-');
      select.innerHTML = isFilter ? '<option value="all">全部產品</option>' : '<option value="">-- 未定義產品 / 尚未分配 --</option>';
      state.products.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.innerText = `${p.name} (${p.code})`;
        select.appendChild(opt);
      });
    });

    // 2. 填入儲槽下拉選單
    tankSelects.forEach(select => {
      if (!select) return;
      const isFilter = select.id.startsWith('filter-') || select.id === 'forecast-tank-select' || select.id === 'schedule-source-tank';
      
      let defaultText = '全部儲槽/容器';
      if (select.id === 'forecast-tank-select') defaultText = '-- 選擇監控儲槽 --';
      if (select.id === 'schedule-source-tank') defaultText = '-- 無 (不消耗原料) --';
      
      select.innerHTML = isFilter ? `<option value="">${defaultText}</option>` : '';
      
      
      
    if (select.id === 'forecast-tank-select') {
        const optgroupLines = document.createElement('optgroup');
        optgroupLines.label = "【產線總庫存 (專用+共用)】";
        
        state.lines.forEach(l => {
          if (state.currentFactory !== 'all' && l.factoryId !== state.currentFactory) return;
          const factoryName = state.factories.find(f => f.id === l.factoryId)?.name || '';
          const opt = document.createElement('option');
          opt.value = `group_line_${l.id}`;
          opt.innerText = `🏭 ${factoryName} - ${l.name}`;
          optgroupLines.appendChild(opt);
        });
        if (optgroupLines.children.length > 0) select.appendChild(optgroupLines);

        const optgroupProducts = document.createElement('optgroup');
        optgroupProducts.label = "【廠區產品總庫存 (全廠加總)】";
        
        state.factories.forEach(f => {
          if (state.currentFactory !== 'all' && f.id !== state.currentFactory) return;
          state.products.forEach(p => {
            // Check if there are tanks for this product in this factory
            const hasTanks = state.tanks.some(t => t.factoryId === f.id && t.productId === p.id);
            if (hasTanks) {
              const opt = document.createElement('option');
              opt.value = `group_prod_${f.id}_${p.id}`;
              opt.innerText = `📦 ${f.name} - ${p.name}`;
              optgroupProducts.appendChild(opt);
            }
          });
        });
        if (optgroupProducts.children.length > 0) select.appendChild(optgroupProducts);
        
        const optgroupTanks = document.createElement('optgroup');
        optgroupTanks.label = "【單一儲槽/容器】";
        
        state.tanks.forEach(t => {
          if (state.currentFactory !== 'all' && t.factoryId !== state.currentFactory) return;
          const prod = state.products.find(p => p.id === t.productId);
          const prodName = prod ? prod.name : '未知產品';
          const opt = document.createElement('option');
          opt.value = t.id;
          opt.innerText = `${t.name} [${t.type === 'tank' ? '儲槽' : 'Isotank'}] (${prodName})`;
          optgroupTanks.appendChild(opt);
        });
        if (optgroupTanks.children.length > 0) select.appendChild(optgroupTanks);

      } else {
        // Normal tank behavior for other selects
        state.tanks.forEach(t => {
          if (state.currentFactory !== 'all' && t.factoryId !== state.currentFactory) return;
          const prod = state.products.find(p => p.id === t.productId);
          const prodName = prod ? prod.name : '未知產品';
          const opt = document.createElement('option');
          opt.value = t.id;
          opt.innerText = `${t.name} [${t.type === 'tank' ? '儲槽' : 'Isotank'}] (${prodName})`;
          select.appendChild(opt);
        });
      }
    });
    
    // 初始化預估開車起始日
    const startDateInput = document.getElementById('forecast-start-date');
    const chkContinuous = document.getElementById('chk-continuous-start');
    if (startDateInput && chkContinuous) {
      const today = new Date();
      const yyyy = today.getFullYear();
      const mm = String(today.getMonth() + 1).padStart(2, '0');
      const dd = String(today.getDate()).padStart(2, '0');
      const todayStr = `${yyyy}-${mm}-${dd}`;

      // Default to true if not explicitly set to false
      const isContinuous = state.continuousStart === undefined ? true : state.continuousStart;
      chkContinuous.checked = isContinuous;
      startDateInput.disabled = isContinuous;
      
      if (isContinuous) {
        startDateInput.value = todayStr;
        state.startDateTime = todayStr;
      } else if (state.startDateTime) {
        startDateInput.value = state.startDateTime.slice(0, 10);
      } else {
        startDateInput.value = todayStr;
        state.startDateTime = todayStr;
      }
    }

    // 如果預估表原本有選，維持選取；若沒選，預設選取第一個儲槽
    const forecastSelect = document.getElementById('forecast-tank-select');
    if (forecastSelect && !forecastSelect.value) {
      const firstGroupProdOpt = Array.from(forecastSelect.options).find(opt => opt.value.startsWith('group_prod_'));
      const firstGroupLineOpt = Array.from(forecastSelect.options).find(opt => opt.value.startsWith('group_line_'));
      
      if (firstGroupProdOpt) {
        forecastSelect.value = firstGroupProdOpt.value;
      } else if (firstGroupLineOpt) {
        forecastSelect.value = firstGroupLineOpt.value;
      } else if (state.tanks.length > 0) {
        forecastSelect.value = state.tanks[0].id;
      }
    }
  }

  // ==================== 儀表板動態分析與水位渲染核心 ====================
  function calculateAndRenderDashboard() {
    const container = document.getElementById('tanks-monitor-container');
    const currentProdContainer = document.getElementById('current-production-container');
    const alertLogContainer = document.getElementById('alert-log-container');
    
    if (!container) return;
    
    if (state.tanks.length === 0) {
      container.innerHTML = `
        <div class="no-data-placeholder">
          <i class="fa-solid fa-info-circle"></i>
          <p>目前無儲槽資料，請至「儲槽與容器」分頁新增儲槽</p>
        </div>`;
      if (currentProdContainer) currentProdContainer.innerHTML = '<p class="text-secondary text-sm">無進行中的生產</p>';
      if (alertLogContainer) alertLogContainer.innerHTML = '<p class="text-secondary text-sm">無警報日誌</p>';
      return;
    }

    container.innerHTML = '';
    if (currentProdContainer) currentProdContainer.innerHTML = '';
    if (alertLogContainer) alertLogContainer.innerHTML = '';

    const now = new Date();
    let systemAlertsCount = 0;
    let alertItemsHTML = '';
    let activeProductionHTML = '';

    const activeSchedules = state.schedules.filter(s => {
      const start = new Date(s.start);
      const end = new Date(s.end);
      return now >= start && now <= end;
    });

    
    
    state.tanks.forEach(tank => {
      if (state.currentFactory !== 'all' && tank.factoryId !== state.currentFactory) return;

      if (state.currentFactory !== 'all' && tank.factoryId !== state.currentFactory) return; // Factory filter

      const product = state.products.find(p => p.id === tank.productId);
      const prodName = product ? product.name : '未定義產品';
      const prodColor = product ? product.color : '#4facfe';
      const prodCode = product ? product.code : 'UNKNOWN';
      const safetyLimit = Number(tank.safetyLevel) || 0;

      // 計算當前進料速率 (目標儲槽，需乘上良率作為良品流入)
      const targetSchedules = activeSchedules.filter(s => s.tankId === tank.id);
      let totalInflowRate = 0;
      
      targetSchedules.forEach(s => {
        const yieldFactor = s.yield !== undefined ? (Number(s.yield) / 100) : 1;
        totalInflowRate += Number(s.rate) * yieldFactor;
        
        activeProductionHTML += `
          <div class="current-prod-item">
            <div class="current-prod-details">
              <h5><span class="color-dot" style="background-color: ${prodColor}"></span> ${prodName} 生產中</h5>
              <p>排程時間：${formatDateString(s.start)} ~ ${formatDateString(s.end)}</p>
            </div>
            <div class="current-prod-value">
              <div class="rate">+${formatNumber(s.rate * yieldFactor)} t/hr <span class="text-xs text-secondary">(良率:${s.yield || 100}%)</span></div>
              <div class="target">目標：${tank.name}</div>
            </div>
          </div>`;
      });

      // 計算當前原料消耗速率 (來源儲槽，消耗全量粗料，符合物料守恆)
      const sourceSchedules = activeSchedules.filter(s => s.sourceTankId === tank.id);
      let totalRawConsumptionRate = 0;
      sourceSchedules.forEach(s => {
        totalRawConsumptionRate += Number(s.rate);
      });

      const baseOutflowRate = Number(tank.outflowRate) || 0;
      // 淨流速 = 生產流入速率 - 預設出庫速率 - 生產原料消耗速率
      const netRate = totalInflowRate - baseOutflowRate - totalRawConsumptionRate;
      
      const capacity = Number(tank.capacity);
      const currentLevel = Number(tank.currentLevel);
      const percent = Math.min(100, Math.max(0, (currentLevel / capacity) * 100));

      // 預測算法與水位警報判定
      let predictionText = '水位維持穩定';
      let predictionIcon = '<i class="fa-solid fa-arrows-left-right text-secondary"></i>';
      let alertClass = '';
      
      // 當前庫存是否低於安全設定值 (低水位警報)
      if (currentLevel < safetyLimit) {
        alertClass = 'alert-danger';
        systemAlertsCount++;
        alertItemsHTML += `
          <div class="alert-log-item">
            <div class="alert-log-icon text-danger"><i class="fa-solid fa-circle-exclamation"></i></div>
            <div class="alert-log-text">
              <h5>儲槽 ${tank.name} 處於低安全水位之下！</h5>
              <p>當前儲量：${formatNumber(currentLevel)} L (低於防呆安全限制：${formatNumber(safetyLimit)} L)。請儘速安排生產進料！</p>
            </div>
          </div>`;
      }
      
      if (netRate > 0) {
        const hoursToFull = (capacity - currentLevel) / netRate;
        if (hoursToFull <= 0.01) {
          predictionText = '儲槽已達容量上限！';
          predictionIcon = '<i class="fa-solid fa-circle-exclamation text-danger"></i>';
          alertClass = 'alert-danger';
          
          systemAlertsCount++;
          alertItemsHTML += `
            <div class="alert-log-item">
              <div class="alert-log-icon text-danger"><i class="fa-solid fa-circle-exclamation"></i></div>
              <div class="alert-log-text">
                <h5>儲槽 ${tank.name} 已滿溢！</h5>
                <p>容量已達：${currentLevel.toFixed(1)} / ${capacity.toFixed(0)} L (100%)。請立即停止生產線進料或進行出貨！</p>
              </div>
            </div>`;
        } else {
          const timeStr = formatHours(hoursToFull);
          predictionText = `預計 ${timeStr} 後滿槽`;
          predictionIcon = '<i class="fa-solid fa-angles-up text-danger"></i>';
          
          if (hoursToFull <= 8) {
            alertClass = 'alert-warning';
            systemAlertsCount++;
            alertItemsHTML += `
              <div class="alert-log-item warning">
                <div class="alert-log-icon text-warning"><i class="fa-solid fa-triangle-exclamation"></i></div>
                <div class="alert-log-text">
                  <h5>儲槽 ${tank.name} 即將滿槽</h5>
                  <p>預估將在 ${timeStr} 內填滿。目前淨流入速率：+${netRate.toFixed(1)} t/hr。</p>
                </div>
              </div>`;
          }
        }
      } else if (netRate < 0) {
        const hoursToEmpty = currentLevel / Math.abs(netRate);
        if (hoursToEmpty <= 0.01) {
          predictionText = '儲槽已排空！';
          predictionIcon = '<i class="fa-solid fa-circle-info text-secondary"></i>';
        } else {
          const timeStr = formatHours(hoursToEmpty);
          predictionText = `預計 ${timeStr} 後排空`;
          predictionIcon = '<i class="fa-solid fa-angles-down text-warning"></i>';
          
          if (hoursToEmpty <= 8) {
            alertClass = 'alert-warning';
            systemAlertsCount++;
            alertItemsHTML += `
              <div class="alert-log-item warning">
                <div class="alert-log-icon text-warning"><i class="fa-solid fa-circle-exclamation"></i></div>
                <div class="alert-log-text">
                  <h5>儲槽 ${tank.name} 即將耗盡</h5>
                  <p>預估將在 ${timeStr} 內排空。目前淨流出速率：${netRate.toFixed(1)} t/hr。</p>
                </div>
              </div>`;
          }
        }
      }

      let trendBadgeHTML = '<span class="trend-badge text-secondary"><i class="fa-solid fa-minus"></i> 穩定</span>';
      if (netRate > 0) {
        trendBadgeHTML = `<span class="trend-badge text-danger"><i class="fa-solid fa-arrow-trend-up"></i> +${netRate.toFixed(1)} t/h</span>`;
      } else if (netRate < 0) {
        trendBadgeHTML = `<span class="trend-badge text-success"><i class="fa-solid fa-arrow-trend-down"></i> ${netRate.toFixed(1)} t/h</span>`;
      }

      const shadowColor = hexToRgba(prodColor, 0.3);

      const tankCard = document.createElement('div');
      tankCard.className = `tank-monitor-card ${alertClass}`;
      tankCard.innerHTML = `
        <div class="tank-monitor-header">
          <div class="tank-title">
            <h4>${tank.name}</h4>
            <span class="tank-prod-badge" style="background-color: ${hexToRgba(prodColor, 0.15)}; color: ${prodColor}; border: 1px solid ${hexToRgba(prodColor, 0.3)}">
              ${prodName} (${prodCode})
            </span>
          </div>
          <span class="tank-type-tag">${tank.type === 'tank' ? '儲槽' : 'Isotank'}</span>
        </div>
        
        <div class="tank-monitor-body">
          <div class="tank-visual-container" style="border-color: ${hexToRgba(prodColor, 0.4)}; box-shadow: 0 4px 15px ${shadowColor}">
            <div class="tank-water" style="height: ${percent}%; background: linear-gradient(to top, ${prodColor}, ${lightenColor(prodColor, 20)})"></div>
            <div class="tank-percent-overlay">${percent.toFixed(0)}%</div>
          </div>
          
          <div class="tank-data-details">
            <div class="tank-data-row">
              <label>當前儲量 / 上限</label>
              <div class="tank-val-big">${formatNumber(currentLevel)} <span class="tank-val-unit">t / ${formatNumber(capacity)} t</span></div>
            </div>
            <div class="tank-data-row">
              <label>淨變化率</label>
              <div>${trendBadgeHTML}</div>
            </div>
          </div>
        </div>
        
        <div class="tank-prediction-box">
          <span class="pred-title">容量趨勢預估</span>
          <div class="pred-result">
            ${predictionIcon} <span>${predictionText}</span>
          </div>
        </div>
      `;
      container.appendChild(tankCard);
    });

    if (currentProdContainer) {
      if (activeProductionHTML === '') {
        currentProdContainer.innerHTML = '<p class="text-secondary text-sm" style="padding: 10px;">目前沒有正在運行的生產排程</p>';
      } else {
        currentProdContainer.innerHTML = activeProductionHTML;
      }
    }

    if (alertLogContainer) {
      if (alertItemsHTML === '') {
        alertLogContainer.innerHTML = `
          <div class="alert-log-item text-success" style="background: rgba(16, 185, 129, 0.05); border-color: rgba(16, 185, 129, 0.15)">
            <div class="alert-log-icon"><i class="fa-solid fa-circle-check"></i></div>
            <div class="alert-log-text">
              <h5>所有儲槽容量正常</h5>
              <p>無低水位警報或超限預警。</p>
            </div>
          </div>`;
      } else {
        alertLogContainer.innerHTML = alertItemsHTML;
      }
    }

    const alertCard = document.getElementById('stat-alert-card');
    const alertIcon = document.getElementById('stat-alert-icon');
    const alertText = document.getElementById('stat-alert-text');
    
    if (alertCard && alertIcon && alertText) {
      if (systemAlertsCount > 0) {
        alertCard.classList.add('bg-danger-stripe');
        alertIcon.className = 'stat-icon bg-danger';
        alertIcon.innerHTML = '<i class="fa-solid fa-bell-ring fa-bounce"></i>';
        alertText.innerText = `${systemAlertsCount} 個容量警報`;
        alertText.className = 'stat-value text-danger';
      } else {
        alertCard.classList.remove('bg-danger-stripe');
        alertIcon.className = 'stat-icon bg-green';
        alertIcon.innerHTML = '<i class="fa-solid fa-circle-check"></i>';
        alertText.innerText = '運作正常';
        alertText.className = 'stat-value text-success';
      }
    }
    
    // 同步渲染 30 日預估表
    renderForecastTable();
  }

  // ==================== 未來 30 日進耗存動態預估模擬 ====================
  function renderForecastTable() {
    const selectTank = document.getElementById('forecast-tank-select');
    const headerRow = document.getElementById('forecast-header-row');
    const tbody = document.getElementById('forecast-body');
    
    if (!selectTank || !headerRow || !tbody) return;
    
    const selectValue = selectTank.value;
    if (!selectValue) {
      headerRow.innerHTML = '<th>項目/日期</th>';
      tbody.innerHTML = '<tr><td class="text-secondary text-center" colspan="31">請選擇監控儲槽</td></tr>';
      return;
    }
    
    let targetTanks = [];
    if (selectValue.startsWith('group_line_')) {
      const lineId = selectValue.replace('group_line_', '');
      const line = state.lines.find(l => l.id === lineId);
      if (line) {
        // Find dedicated tanks + shared tanks for the same products? 
        // Actually, shared tanks have dedicatedLineId === '' or undefined.
        // But what product? A line doesn't have a fixed product in state.
        // Let's assume shared tanks are those with dedicatedLineId === '' in the same factory.
        targetTanks = state.tanks.filter(t => t.factoryId === line.factoryId && (t.dedicatedLineId === line.id || !t.dedicatedLineId));
      }
    } else if (selectValue.startsWith('group_prod_')) {
      const parts = selectValue.split('_');
      const fId = parts[2];
      const pId = parts[3];
      targetTanks = state.tanks.filter(t => t.factoryId === fId && t.productId === pId);
    } else {
      const singleTank = state.tanks.find(t => t.id === selectValue);
      if (singleTank) targetTanks = [singleTank];
    }
    
    if (targetTanks.length === 0) {
      headerRow.innerHTML = '<th>項目/日期</th>';
      tbody.innerHTML = '<tr><td class="text-secondary text-center" colspan="31">群組內無符合條件的儲槽</td></tr>';
      return;
    }
    
    // 讀取預估開車時間 (起始日)
    const startDateInput = document.getElementById('forecast-start-date');
    let baseDate = new Date();
    if (startDateInput && startDateInput.value) {
      baseDate = new Date(startDateInput.value);
    }
    
    // 建立 30 天日期陣列
    const dates = [];
    for (let i = 0; i < 30; i++) {
      const d = new Date(baseDate.getFullYear(), baseDate.getMonth(), baseDate.getDate() + i);
      dates.push(d);
    }
    
    // 渲染表頭日期
    let headerHTML = '<th>項目 / 日期</th>';
    dates.forEach(d => {
      const mm = d.getMonth() + 1;
      const dd = d.getDate();
      const isWeekend = d.getDay() === 0 || d.getDay() === 6;
      headerHTML += `<th class="${isWeekend ? 'text-danger' : ''}">${mm}/${dd}</th>`;
    });
    headerRow.innerHTML = headerHTML;
    
    const initialStockRow = [];
    const inflowRow = [];
    const outflowRow = [];
    const endingStockRow = [];
    
    // Aggregate initial stock
    let currentSimLevel = targetTanks.reduce((sum, t) => sum + (Number(t.currentLevel) || 0), 0);
    
    dates.forEach((date, dayIdx) => {
      const dayStart = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 0, 0, 0);
      const dayEnd = new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59);
      
      const startingStock = currentSimLevel;
      initialStockRow.push(startingStock);
      
      // 計算當日排程生產進料 (加總所有目標儲槽)
      let dailyInflow = 0;
      targetTanks.forEach(t => {
        const tankSchedules = state.schedules.filter(s => s.tankId === t.id);
        tankSchedules.forEach(s => {
          const sStart = new Date(s.start);
          const sEnd = new Date(s.end);
          if (sEnd > dayStart && sStart < dayEnd) {
            const overlapStart = Math.max(sStart.getTime(), dayStart.getTime());
            const overlapEnd = Math.min(sEnd.getTime(), dayEnd.getTime());
            const overlapHours = (overlapEnd - overlapStart) / (1000 * 60 * 60);
            if (overlapHours > 0) {
              const yieldFactor = s.yield !== undefined ? (Number(s.yield) / 100) : 1;
              dailyInflow += overlapHours * Number(s.rate) * yieldFactor;
            }
          }
        });
        
        // 檢查交易紀錄中當天的登記
        const dayLogs = state.transactionLogs.filter(l => {
          if (l.tankId !== t.id) return false;
          const logDate = new Date(l.timestamp);
          return logDate.toDateString() === date.toDateString() && l.type === 'inflow';
        });
        dayLogs.forEach(l => { dailyInflow += Number(l.amount); });
      });
      inflowRow.push(dailyInflow);
      
      // 計算出庫/消耗 
      let dailyOutflow = 0;
      targetTanks.forEach(t => {
        dailyOutflow += (Number(t.outflowRate) || 0) * 24;
        
        // 加上當天因為生產排程消耗該儲槽原料的量
        const sourceSchedules = state.schedules.filter(s => s.sourceTankId === t.id);
        sourceSchedules.forEach(s => {
          const sStart = new Date(s.start);
          const sEnd = new Date(s.end);
          if (sEnd > dayStart && sStart < dayEnd) {
            const overlapStart = Math.max(sStart.getTime(), dayStart.getTime());
            const overlapEnd = Math.min(sEnd.getTime(), dayEnd.getTime());
            const overlapHours = (overlapEnd - overlapStart) / (1000 * 60 * 60);
            if (overlapHours > 0) {
              dailyOutflow += overlapHours * Number(s.rate);
            }
          }
        });

        const dayLogs = state.transactionLogs.filter(l => {
          if (l.tankId !== t.id) return false;
          const logDate = new Date(l.timestamp);
          return logDate.toDateString() === date.toDateString() && l.type === 'outflow';
        });
        dayLogs.forEach(l => { dailyOutflow += Number(l.amount); });
      });
      outflowRow.push(dailyOutflow);
      
      // 計算結算
      let endingStock = startingStock + dailyInflow - dailyOutflow;
      if (endingStock < 0) endingStock = 0; // 允許為 0，或根據需求可以為負？通常庫存不為負。
      endingStockRow.push(endingStock);
      
      currentSimLevel = endingStock;
    });
    
    // 渲染資料行
    let tbodyHTML = '';
    
    // 期初
    tbodyHTML += '<tr><td>期初庫存量</td>';
    initialStockRow.forEach(val => {
      tbodyHTML += `<td>${formatNumber(val)}</td>`;
    });
    tbodyHTML += '</tr>';
    
    // 進料
    tbodyHTML += '<tr><td class="text-success">生產進料 (+)</td>';
    inflowRow.forEach(val => {
      tbodyHTML += `<td class="text-success">${val > 0 ? '+' + formatNumber(val) : '0'}</td>`;
    });
    tbodyHTML += '</tr>';
    
    // 出庫
    tbodyHTML += '<tr><td class="text-warning">消耗出庫 (-)</td>';
    outflowRow.forEach(val => {
      tbodyHTML += `<td class="text-warning">${val > 0 ? '-' + formatNumber(val) : '0'}</td>`;
    });
    tbodyHTML += '</tr>';
    
    // 結算
    tbodyHTML += '<tr><td><b>結算剩餘量</b></td>';
    endingStockRow.forEach(val => {
      let cellStyle = 'font-weight: 700;';
      let styleClass = '';
      
      if (val < safetyLimit) {
        styleClass = 'status-tag-danger';
        cellStyle += 'color: #fff; padding: 4px 8px; border-radius: 4px; display: inline-block;';
      } else if (val > capacity) {
        styleClass = 'status-tag-warning';
        cellStyle += 'color: #fff; padding: 4px 8px; border-radius: 4px; display: inline-block;';
      } else {
        cellStyle += 'color: var(--color-accent);';
      }
      
      tbodyHTML += `<td><span class="${styleClass}" style="${cellStyle}">${formatNumber(val)}</span></td>`;
    });
    tbodyHTML += '</tr>';
    
    tbody.innerHTML = tbodyHTML;
  }

  // ==================== Excel / CSV 匯出邏輯 ====================
  function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    let csv = [];
    const rows = table.querySelectorAll('tr');
    
    for (let i = 0; i < rows.length; i++) {
      let row = [];
      const cols = rows[i].querySelectorAll('td, th');
      
      for (let j = 0; j < cols.length; j++) {
        let text = cols[j].innerText.replace(/,/g, '').replace(/\n/g, ' ').trim();
        row.push('"' + text + '"');
      }
      csv.push(row.join(','));
    }
    
    const csvContent = "\uFEFF" + csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  // ==================== 船隻位置追蹤管理 ====================
  function renderShips() {
    const tbody = document.getElementById('ship-list-body');
    if (!tbody) return;
    
    if (!state.ships || state.ships.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center text-secondary" style="padding: 30px;">
            目前無追蹤中的船隻，請點擊上方按鈕新增！
          </td>
        </tr>`;
      return;
    }
    
    tbody.innerHTML = '';
    // 按 ETA 排序
    const sorted = [...state.ships].sort((a,b) => new Date(a.eta) - new Date(b.eta));
    
    sorted.forEach(s => {
      const product = state.products.find(p => p.id === s.productId);
      const prodName = product ? product.name : '未知';
      const prodColor = product ? product.color : '#fff';
      
      let statusTag = '';
      if (s.status === 'in_transit') statusTag = '<span class="table-status-tag status-tag-pending"><i class="fa-solid fa-water"></i> 航行中</span>';
      else if (s.status === 'arriving') statusTag = '<span class="table-status-tag status-tag-active"><i class="fa-solid fa-anchor"></i> 即將靠港</span>';
      else if (s.status === 'docked') statusTag = '<span class="table-status-tag status-tag-gray"><i class="fa-solid fa-check-double"></i> 已靠港卸貨</span>';
      else if (s.status === 'delayed') statusTag = '<span class="table-status-tag status-tag-danger"><i class="fa-solid fa-clock"></i> 延誤</span>';
      else statusTag = `<span class="table-status-tag status-tag-gray">${s.status}</span>`;

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><b>${s.name}</b> <span class="text-sm text-secondary">(${s.code || '無代碼'})</span></td>
        <td>${s.location}</td>
        <td>${formatDateString(s.eta)}</td>
        <td>
          <span class="prod-table-badge">
            <span class="color-dot" style="background-color: ${prodColor}"></span>
            ${prodName}
          </span>
          <br><span class="text-sm text-secondary" style="margin-top: 4px; display:inline-block">${formatNumber(s.amount)} t</span>
        </td>
        <td>${statusTag}</td>
        <td>
          <button class="btn btn-secondary btn-icon" onclick="editShip('${s.id}')" title="修改"><i class="fa-solid fa-pen"></i></button>
          <button class="btn btn-danger btn-icon" onclick="deleteShip('${s.id}')" title="刪除"><i class="fa-solid fa-trash"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function editShip(id) {
    const s = state.ships.find(item => item.id === id);
    if (!s) return;
    
    editingShipId = id;
    document.getElementById('ship-modal-title').innerText = '修改船隻動態';
    document.getElementById('ship-id-hidden').value = id;
    document.getElementById('ship-name').value = s.name;
    document.getElementById('ship-code').value = s.code || '';
    document.getElementById('ship-location').value = s.location;
    
    const d = new Date(s.eta);
    const offset = d.getTimezoneOffset() * 60000;
    document.getElementById('ship-eta').value = new Date(d.getTime() - offset).toISOString().slice(0, 16);
    
    updateAllDropdowns(); // 確保有產品下拉選單
    document.getElementById('ship-product').value = s.productId;
    document.getElementById('ship-amount').value = s.amount;
    document.getElementById('ship-status').value = s.status;
    
    openModal('modal-ship');
  }

  function deleteShip(id) {
    if (!confirm('確定要刪除這筆船隻追蹤紀錄嗎？')) return;
    state.ships = state.ships.filter(s => s.id !== id);
    saveDataToCloud(() => {
      renderShips();
    });
  }

  
  // ==================== 廠區設定 ====================
  
  // ==================== 產線設定 ====================
  function renderLines() {
    const tbody = document.getElementById('line-list-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    state.lines.forEach(l => {
      const tr = document.createElement('tr');
      const factoryName = state.factories.find(f => f.id === l.factoryId)?.name || '未指定';
      tr.innerHTML = `
        <td><b>${l.name}</b></td>
        <td><span class="text-secondary text-sm">[${factoryName}]</span></td>
        <td style="text-align: center;">
          <button class="btn btn-secondary btn-icon" onclick="editLine('${l.id}')" title="修改"><i class="fa-solid fa-pen"></i></button>
          <button class="btn btn-danger btn-icon" onclick="deleteLine('${l.id}')" title="刪除"><i class="fa-solid fa-trash"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }
  
  function editLine(id) {
    const l = state.lines.find(item => item.id === id);
    if (!l) return;
    editingLineId = id;
    document.getElementById('line-modal-title').innerText = '修改產線資料';
    document.getElementById('line-id-hidden').value = id;
    document.getElementById('line-name').value = l.name;
    document.getElementById('line-factory').value = l.factoryId || state.factories[0]?.id;
    openModal('modal-line');
  }

  function deleteLine(id) {
    if (!confirm('您確定要刪除此產線嗎？')) return;
    state.lines = state.lines.filter(l => l.id !== id);
    saveDataToCloud(() => {
      renderLines();
      updateAllDropdowns();
    });
  }

  function renderFactories() {
    const tbody = document.getElementById('factory-list-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    state.factories.forEach(f => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><b>${f.name}</b></td>
        <td style="text-align: center;">
          <button class="btn btn-secondary btn-icon" onclick="editFactory('${f.id}')" title="修改"><i class="fa-solid fa-pen"></i></button>
          <button class="btn btn-danger btn-icon" onclick="deleteFactory('${f.id}')" title="刪除"><i class="fa-solid fa-trash"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }
  
  function editFactory(id) {
    const f = state.factories.find(item => item.id === id);
    if (!f) return;
    editingFactoryId = id;
    document.getElementById('factory-modal-title').innerText = '修改廠區資料';
    document.getElementById('factory-id-hidden').value = id;
    document.getElementById('factory-name').value = f.name;
    openModal('modal-factory');
  }

  function deleteFactory(id) {
    if (!confirm('您確定要刪除此廠區嗎？注意：有儲槽綁定在此廠區時，刪除可能導致資料異常。')) return;
    const tankInUse = state.tanks.find(t => t.factoryId === id);
    if (tankInUse) {
      alert(`刪除失敗！儲槽「${tankInUse.name}」隸屬於此廠區，請先變更儲槽廠區。`);
      return;
    }
    state.factories = state.factories.filter(f => f.id !== id);
    saveDataToCloud(() => {
      renderFactories();
          renderLines();
          renderLines();
      updateAllDropdowns();
    });
  }


  // ==================== 產品設定分頁管理 ====================
  function renderProducts() {
    const container = document.getElementById('product-list-container');
    if (!container) return;
    
    if (state.products.length === 0) {
      container.innerHTML = `
        <div class="no-data-placeholder">
          <i class="fa-solid fa-flask"></i>
          <p>目前沒有配置產品，請點擊「新增產品」</p>
        </div>`;
      return;
    }
    
    container.innerHTML = '';
    state.products.forEach(p => {
      const card = document.createElement('div');
      card.className = 'product-card';
      card.innerHTML = `
        <div class="product-card-color-stripe" style="background-color: ${p.color}"></div>
        <div class="product-card-header">
          <div class="product-card-title">
            <h4>${p.name}</h4>
            <span>代碼：${p.code}</span>
          </div>
          <div class="product-color-preview" style="width: 14px; height: 14px; border-radius: 50%; background-color: ${p.color}; box-shadow: 0 0 8px ${p.color}"></div>
        </div>
        <p class="product-card-desc">${p.desc || '無備註說明'}</p>
        <div class="product-card-actions">
          <button class="btn btn-secondary btn-icon" onclick="editProduct('${p.id}')" title="修改"><i class="fa-solid fa-pen"></i></button>
          <button class="btn btn-danger btn-icon" onclick="deleteProduct('${p.id}')" title="刪除"><i class="fa-solid fa-trash"></i></button>
        </div>
      `;
      container.appendChild(card);
    });
  }

  function editProduct(id) {
    const p = state.products.find(item => item.id === id);
    if (!p) return;
    
    editingProductId = id;
    document.getElementById('product-modal-title').innerText = '修改產品資料';
    document.getElementById('product-id-hidden').value = id;
    document.getElementById('product-name').value = p.name;
    document.getElementById('product-code').value = p.code;
    document.getElementById('product-color').value = p.color;
    document.getElementById('product-desc').value = p.desc || '';
    
    openModal('modal-product');
  }

  function deleteProduct(id) {
    if (!confirm('您確定要刪除此產品嗎？這可能會影響綁定此產品的儲槽與生產排程！')) return;
    
    const tankInUse = state.tanks.find(t => t.productId === id);
    if (tankInUse) {
      alert(`刪除失敗！儲槽「${tankInUse.name}」目前存放此產品，請先將儲槽移除或變更產品。`);
      return;
    }

    state.products = state.products.filter(p => p.id !== id);
    saveDataToCloud(() => {
      renderProducts();
          renderFactories();
          renderLines();
          renderLines();
      updateAllDropdowns();
    });
  }

  // ==================== 儲槽與容器分頁管理 ====================
  
  // ==================== 快速建置功能 ====================
  window.quickBuildDefaultTanks = function() {
    if (!confirm('這將會自動建立一廠與二廠的預設產線以及 TK604A, TK617 等儲槽。確定要執行嗎？')) return;
    
    if (!state.factories.find(f => f.id === 'factory-1')) state.factories.push({ id: "factory-1", name: "一廠" });
    if (!state.factories.find(f => f.id === 'factory-2')) state.factories.push({ id: "factory-2", name: "二廠" });

    const defaultLines = [
      { id: "line-1-1", factoryId: "factory-1", name: "一廠產線A" },
      { id: "line-2-1", factoryId: "factory-2", name: "二廠產線A" },
      { id: "line-2-2", factoryId: "factory-2", name: "二廠產線B" }
    ];
    defaultLines.forEach(dl => {
      if (!state.lines.find(l => l.id === dl.id)) state.lines.push(dl);
    });

    const defaultTanks = [
      { id: "tk-101", factoryId: "factory-1", name: "TK604A", type: "tank", productId: "", level: 0, capacity: 100, dedicatedLineId: "" },
      { id: "tk-102", factoryId: "factory-1", name: "TK604B", type: "tank", productId: "", level: 0, capacity: 100, dedicatedLineId: "" },
      { id: "tk-103", factoryId: "factory-1", name: "TK693", type: "tank", productId: "", level: 0, capacity: 100, dedicatedLineId: "" },
      { id: "tk-104", factoryId: "factory-1", name: "TK696", type: "tank", productId: "", level: 0, capacity: 100, dedicatedLineId: "" },
      { id: "tk-105", factoryId: "factory-1", name: "TK697", type: "tank", productId: "", level: 0, capacity: 100, dedicatedLineId: "" },
      { id: "tk-201", factoryId: "factory-2", name: "TK617", type: "tank", productId: "", level: 0, capacity: 150, dedicatedLineId: "line-2-1" },
      { id: "tk-202", factoryId: "factory-2", name: "TK618", type: "tank", productId: "", level: 0, capacity: 150, dedicatedLineId: "line-2-2" }
    ];
    
    defaultTanks.forEach(dt => {
      if (!state.tanks.find(t => t.id === dt.id)) state.tanks.push(dt);
    });

    saveDataToCloud(() => {
      renderTanks();
      if(typeof renderLines === 'function') renderLines();
      if(typeof renderFactories === 'function') renderFactories();
      updateAllDropdowns();
      calculateAndRenderDashboard();
      showToast('✅ 預設儲槽與產線建置完成！', 'success');
    });
  };

  
  // ==================== 儲槽專屬產線邏輯 ====================
  window.updateTankDedicatedLines = function() {
    const tankFactorySelect = document.getElementById('tank-factory');
    const tankDedicatedLine = document.getElementById('tank-dedicated-line');
    if (!tankFactorySelect || !tankDedicatedLine) return;
    
    const currentVal = tankDedicatedLine.value;
    const factoryId = tankFactorySelect.value;
    tankDedicatedLine.innerHTML = '<option value="">-- 全廠共用 (不綁定) --</option>';
    
    if (factoryId) {
      const lines = state.lines.filter(l => l.factoryId === factoryId);
      lines.forEach(l => {
        const opt = document.createElement('option');
        opt.value = l.id;
        opt.innerText = l.name;
        tankDedicatedLine.appendChild(opt);
      });
    }
    tankDedicatedLine.value = currentVal; // Restore if still valid
    if(tankDedicatedLine.selectedIndex === -1) tankDedicatedLine.value = "";
  };

  function renderTanks() {
    const tbody = document.getElementById('tank-list-body');
    if (!tbody) return;
    
    if (state.tanks.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="10" class="text-center text-secondary" style="padding: 30px;">
            目前沒有配置任何儲槽或容器。<br><br>
            <button class="btn btn-primary" onclick="window.quickBuildDefaultTanks()">
              <i class="fa-solid fa-wand-magic-sparkles"></i> 一鍵自動建置預設 TK 儲槽與產線
            </button>
          </td>
        </tr>`;
      return;
    }
    
    tbody.innerHTML = '';
    
      state.tanks.forEach(t => {
        if (state.currentFactory !== 'all' && t.factoryId !== state.currentFactory) return; // Factory Filter

      const product = state.products.find(p => p.id === t.productId);
      const prodName = product ? product.name : '未定義產品';
      const prodColor = product ? product.color : '#fff';
      
      let statusTag = '';
      if (t.status === 'normal') statusTag = '<span class="table-status-tag status-tag-active">正常</span>';
      else if (t.status === 'maintenance') statusTag = '<span class="table-status-tag status-tag-warning">保養中</span>';
      else statusTag = '<span class="table-status-tag status-tag-danger">停用</span>';

      const tr = document.createElement('tr');
      tr.innerHTML = `

        <td><b>${t.name}</b></td>
        <td><span class="text-secondary text-sm">[${state.factories.find(f => f.id === t.factoryId)?.name || '未指定'}]</span></td>
        <td>${t.type === 'tank' ? '<i class="fa-solid fa-database text-primary"></i> 儲槽' : '<i class="fa-solid fa-truck-ramp-box text-warning"></i> Isotank'}</td>

        <td>
          <span class="prod-table-badge">
            <span class="color-dot" style="background-color: ${prodColor}"></span>
            ${prodName}
          </span>
        </td>
        <td>${formatNumber(t.capacity)} t</td>
        <td>${formatNumber(t.currentLevel)} t</td>
        <td>${t.outflowRate || 0} t/hr</td>
        <td>${formatNumber(t.safetyLevel || 0)} t</td>
        <td>${statusTag}</td>
        <td>
          <button class="btn btn-secondary btn-icon" onclick="editTank('${t.id}')" title="修改"><i class="fa-solid fa-pen"></i></button>
          <button class="btn btn-danger btn-icon" onclick="deleteTank('${t.id}')" title="刪除"><i class="fa-solid fa-trash"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function editTank(id) {
    const t = state.tanks.find(item => item.id === id);
    if (!t) return;
    
    editingTankId = id;
    document.getElementById('tank-modal-title').innerText = '修改儲槽/容器資料';
    document.getElementById('tank-id-hidden').value = id;
    document.getElementById('tank-name').value = t.name;
    document.getElementById('tank-type').value = t.type;
    document.getElementById('tank-factory').value = t.factoryId || state.factories[0]?.id;
    document.getElementById('tank-product').value = t.productId;
    updateTankDedicatedLines();
    document.getElementById('tank-dedicated-line').value = t.dedicatedLineId || '';
    document.getElementById('tank-capacity').value = t.capacity;
    document.getElementById('tank-current').value = t.currentLevel;
    document.getElementById('tank-outflow').value = t.outflowRate || 0;
    document.getElementById('tank-safety').value = t.safetyLevel || 0;
    document.getElementById('tank-status').value = t.status || 'normal';
    
    toggleTankOutflowField();
    openModal('modal-tank');
  }

  function deleteTank(id) {
    if (!confirm('您確定要刪除此儲槽/容器嗎？這將刪除相關聯的所有歷史進出紀錄與排程配置！')) return;
    
    state.tanks = state.tanks.filter(t => t.id !== id);
    state.schedules = state.schedules.filter(s => s.tankId !== id);
    state.transactionLogs = state.transactionLogs.filter(l => l.tankId !== id);
    
    saveDataToCloud(() => {
      renderTanks();
      updateAllDropdowns();
    });
  }

  function toggleTankOutflowField() {
    const type = document.getElementById('tank-type').value;
      const factoryId = document.getElementById('tank-factory').value;
    const outflowWrapper = document.getElementById('tank-outflow-wrapper');
    if (type === 'isotank') {
      outflowWrapper.style.display = 'none';
      document.getElementById('tank-outflow').value = '0';
    } else {
      outflowWrapper.style.display = 'block';
    }
  }

  // ==================== 生產排程管理與甘特圖 ====================
  function renderSchedules() {
    const tbody = document.getElementById('schedule-list-body');
    const filterProduct = document.getElementById('filter-schedule-product').value;
    
    if (!tbody) return;
    
    let filtered = state.schedules;
    if (filterProduct && filterProduct !== 'all' && filterProduct !== '') {
      filtered = filtered.filter(s => s.productId === filterProduct);
    }
    
    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-secondary" style="padding: 30px;">
            目前無符合條件的排程，點擊上方按鈕新增排程！
          </td>
        </tr>`;
      return;
    }

    tbody.innerHTML = '';
    filtered.sort((a,b) => new Date(a.start) - new Date(b.start));
    
    
    filtered.forEach(s => {
      const tank = state.tanks.find(t => t.id === s.tankId);
      if (state.currentFactory !== 'all' && tank && tank.factoryId !== state.currentFactory) return;

      const product = state.products.find(p => p.id === s.productId);
      const prodName = product ? product.name : '未定義產品';
      const prodColor = product ? product.color : '#fff';
      
      let tankName = tank ? tank.name : '未定義容器';
      if (s.sourceTankId) {
        const sourceTank = state.tanks.find(t => t.id === s.sourceTankId);
        if (sourceTank) {
          tankName += ` <span class="text-secondary text-xs" style="display: block; margin-top: 2px;">(消耗：${sourceTank.name})</span>`;
        }
      }

      const start = new Date(s.start);
      const end = new Date(s.end);
      const hours = (end - start) / (1000 * 60 * 60);
      const totalVolume = Number(s.rate) * Math.max(0, hours);
      const yieldRate = s.yield !== undefined ? s.yield : 100;
      const yieldVolume = totalVolume * (yieldRate / 100);

      const now = new Date();
      let statusHTML = '';
      if (now < start) {
        statusHTML = '<span class="table-status-tag status-tag-pending">排程中</span>';
      } else if (now > end) {
        statusHTML = '<span class="table-status-tag status-tag-gray">已結束</span>';
      } else {
        statusHTML = '<span class="table-status-tag status-tag-active">生產中</span>';
      }

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>
          <span class="prod-table-badge">
            <span class="color-dot" style="background-color: ${prodColor}"></span>
            ${prodName}
          </span>
        </td>
        <td>${tankName}</td>
        <td>${s.rate} t/hr</td>
        <td>${formatDateString(s.start)}</td>
        <td>${formatDateString(s.end)}</td>
        <td>
          <b>${formatNumber(yieldVolume)} t</b>
          <span class="text-secondary text-xs" style="display: block; margin-top: 2px;">良率: ${yieldRate}% (總量: ${formatNumber(totalVolume)}t)</span>
        </td>
        <td>${statusHTML}</td>
        <td>
          <button class="btn btn-secondary btn-icon" onclick="editSchedule('${s.id}')" title="修改"><i class="fa-solid fa-pen"></i></button>
          <button class="btn btn-danger btn-icon" onclick="deleteSchedule('${s.id}')" title="刪除"><i class="fa-solid fa-trash"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  function editSchedule(id) {
    const s = state.schedules.find(item => item.id === id);
    if (!s) return;
    
    editingScheduleId = id;
    document.getElementById('schedule-modal-title').innerText = '修改生產排程';
    document.getElementById('schedule-id-hidden').value = id;
    document.getElementById('schedule-product').value = s.productId;
    document.getElementById('schedule-line').value = s.lineId;
    
    filterTanksBySelectedProduct(s.productId);
    
    document.getElementById('schedule-tank').value = s.tankId;
    document.getElementById('schedule-source-tank').value = s.sourceTankId || '';
    document.getElementById('schedule-rate').value = s.rate;
    document.getElementById('schedule-start').value = s.start;
    document.getElementById('schedule-end').value = s.end;
    
    const start = new Date(s.start);
    const end = new Date(s.end);
    const durationHours = (end - start) / (1000 * 60 * 60);
    const totalVolume = Number(s.rate) * Math.max(0, durationHours);
    
    document.getElementById('schedule-total-volume').value = totalVolume.toFixed(3);
    document.getElementById('schedule-yield').value = s.yield !== undefined ? s.yield : 100;
    updateYieldTotalDisplay();
    
    openModal('modal-schedule');
  }

  function deleteSchedule(id) {
    if (!confirm('您確定要刪除此筆排程嗎？這會讓對應儲槽的動態預測容量更新。')) return;
    state.schedules = state.schedules.filter(s => s.id !== id);
    saveDataToCloud(() => {
      renderSchedules();
      renderGanttChart();
      calculateAndRenderDashboard();
    });
  }

  function filterTanksBySelectedProduct(productId) {
    const tankSelect = document.getElementById('schedule-tank');
    if (!tankSelect) return;
    
    tankSelect.innerHTML = '';
    const filteredTanks = state.tanks.filter(t => t.productId === productId && t.status === 'normal');
    
    if (filteredTanks.length === 0) {
      const opt = document.createElement('option');
      opt.value = '';
      opt.innerText = '⚠️ 無適用此產品的正常儲槽，請先新增儲槽';
      tankSelect.appendChild(opt);
    } else {
      filteredTanks.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.innerText = `${t.name} (${t.type === 'tank' ? '固定儲槽' : 'Isotank'}) - 容量剩餘 ${formatNumber(t.capacity - t.currentLevel)} L`;
        tankSelect.appendChild(opt);
      });
    }
  }

  function calculateVolumeFromTimes() {
    const rate = Number(document.getElementById('schedule-rate').value) || 0;
    const startVal = document.getElementById('schedule-start').value;
    const endVal = document.getElementById('schedule-end').value;
    const volInput = document.getElementById('schedule-total-volume');
    
    if (!startVal || !endVal || rate <= 0) {
      if (volInput) volInput.value = '';
      updateYieldTotalDisplay();
      return;
    }
    
    const start = new Date(startVal);
    const end = new Date(volInput ? endVal : null); // Fallback safe check
    const diffHours = (new Date(endVal) - start) / (1000 * 60 * 60);
    
    if (diffHours > 0) {
      const total = rate * diffHours;
      if (volInput) volInput.value = total.toFixed(3);
    }
    updateYieldTotalDisplay();
  }

  function calculateEndTimeFromVolume() {
    const rate = Number(document.getElementById('schedule-rate').value) || 0;
    const startVal = document.getElementById('schedule-start').value;
    const totalVolume = Number(document.getElementById('schedule-total-volume').value) || 0;
    const endInput = document.getElementById('schedule-end');
    
    if (!startVal || rate <= 0 || totalVolume <= 0) {
      updateYieldTotalDisplay();
      return;
    }
    
    const start = new Date(startVal);
    const durationHours = totalVolume / rate;
    const end = new Date(start.getTime() + durationHours * 60 * 60 * 1000);
    
    const offset = end.getTimezoneOffset() * 60000;
    const localISOTime = new Date(end.getTime() - offset).toISOString().slice(0, 16);
    if (endInput) endInput.value = localISOTime;
    
    updateYieldTotalDisplay();
  }

  function updateYieldTotalDisplay() {
    const totalVolume = Number(document.getElementById('schedule-total-volume').value) || 0;
    const yieldRate = Number(document.getElementById('schedule-yield').value) || 100;
    const calcEl = document.getElementById('schedule-calc-yield-total');
    
    if (calcEl) {
      const yieldTotal = totalVolume * (yieldRate / 100);
      calcEl.innerText = formatNumber(yieldTotal);
    }
  }

  // ==================== 甘特圖繪製系統 ====================
  function renderGanttChart() {
    const container = document.getElementById('gantt-chart-container');
    const legendContainer = document.getElementById('gantt-legend-container');
    if (!container) return;
    
    const now = new Date();
    
    if (state.schedules.length === 0 || state.tanks.length === 0) {
      container.innerHTML = `
        <div class="no-data-placeholder">
          <i class="fa-solid fa-chart-gantt"></i>
          <p>目前沒有充足資料可繪製甘特圖。請確認已有儲槽與生產排程。</p>
        </div>`;
      if (legendContainer) legendContainer.innerHTML = '';
      return;
    }

    if (legendContainer) {
      legendContainer.innerHTML = '';
      state.products.forEach(p => {
        const item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = `
          <span class="legend-color" style="background-color: ${p.color}"></span>
          <span>${p.name}</span>
        `;
        legendContainer.appendChild(item);
      });
    }

    // 依據「預估開車時間（起始日）」來決定甘特圖時間軸起點
    let baseDate = new Date();
    if (state.startDateTime) {
      baseDate = new Date(state.startDateTime);
    }
    
    // 從開車起始日的前 1 天開始顯示，總共顯示 30 天，與 30 日預估表同步
    const startOfTimeline = new Date(baseDate.getFullYear(), baseDate.getMonth(), baseDate.getDate() - 1); 
    const endOfTimeline = new Date(startOfTimeline.getTime() + 30 * 24 * 60 * 60 * 1000);   
    
    const totalTimelineDuration = endOfTimeline - startOfTimeline;

    let headerCellsHTML = '';
    const dayStep = 24 * 60 * 60 * 1000;
    for (let t = startOfTimeline.getTime(); t < endOfTimeline.getTime(); t += dayStep) {
      const d = new Date(t);
      const dayName = ['日', '一', '二', '三', '四', '五', '六'][d.getDay()];
      headerCellsHTML += `<div class="gantt-header-cell">${d.getMonth()+1}/${d.getDate()} (${dayName})</div>`;
    }

    let rowsHTML = '';
    state.tanks.forEach(tank => {
      const tankSchedules = state.schedules.filter(s => s.tankId === tank.id);
      let barsHTML = '';
      
      tankSchedules.forEach(s => {
        const sStart = new Date(s.start);
        const sEnd = new Date(s.end);
        
        if (sEnd < startOfTimeline || sStart > endOfTimeline) return;
        
        const visibleStart = Math.max(sStart.getTime(), startOfTimeline.getTime());
        const visibleEnd = Math.min(sEnd.getTime(), endOfTimeline.getTime());
        
        const leftPercent = ((visibleStart - startOfTimeline.getTime()) / totalTimelineDuration) * 100;
        const widthPercent = ((visibleEnd - visibleStart) / totalTimelineDuration) * 100;
        
        const product = state.products.find(p => p.id === s.productId);
        const prodColor = product ? product.color : '#4facfe';
        const prodName = product ? product.name : '產品';

        barsHTML += `
          <div class="gantt-bar" 
               style="left: ${leftPercent}%; width: ${widthPercent}%; background: linear-gradient(135deg, ${prodColor}, ${lightenColor(prodColor, 20)}); color: #0b0f19" 
               onclick="editSchedule('${s.id}')"
               title="${prodName} 生產\n開始：${formatDateString(s.start)}\n結束：${formatDateString(s.end)}\n速率：${s.rate} t/hr">
            <span class="gantt-bar-title">${prodName} (${s.rate}t/h)</span>
          </div>`;
      });

      rowsHTML += `
        <div class="gantt-row">
          <div class="gantt-row-label" title="${tank.name}">${tank.name}</div>
          <div class="gantt-row-bars-container">
            ${barsHTML}
          </div>
        </div>`;
    });

    let redLineHTML = '';
    if (now >= startOfTimeline && now <= endOfTimeline) {
      const redLinePercent = ((now - startOfTimeline) / totalTimelineDuration) * 100;
      redLineHTML = `<div class="gantt-current-time-line" style="left: calc(120px + (100% - 120px) * ${redLinePercent / 100})"></div>`;
    }

    container.innerHTML = `
      <div class="gantt-timeline-header">
        <div style="display: flex;">
          <div style="width: 120px; flex-shrink: 0; background: var(--bg-tertiary); border-right: 1px solid var(--border-color);"></div>
          <div class="gantt-timeline-cells" style="flex-grow: 1;">
            ${headerCellsHTML}
          </div>
        </div>
      </div>
      <div style="position: relative;">
        ${redLineHTML}
        ${rowsHTML}
      </div>
    `;
  }

  // ==================== 進出料紀錄明細 ====================
  // ==================== 進出料紀錄明細 ====================
  function renderLogs() {
    const tbody = document.getElementById('log-list-body');
    const filterTank = document.getElementById('filter-log-tank').value;
    if (!tbody) return;
    
    let filtered = state.transactionLogs;
    if (filterTank && filterTank !== 'all' && filterTank !== '') {
      filtered = filtered.filter(l => l.tankId === filterTank);
    }
    
    if (filtered.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-secondary" style="padding: 30px;">
            目前無進出料登記紀錄
          </td>
        </tr>`;
      // 重設全選勾選框與批次刪除按鈕狀態
      const checkAll = document.getElementById('check-all-logs');
      if (checkAll) checkAll.checked = false;
      updateBatchDeleteButtonVisibility();
      return;
    }
    
    tbody.innerHTML = '';
    filtered.sort((a,b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    
    filtered.forEach((l, index) => {
      const tank = state.tanks.find(t => t.id === l.tankId);
      if (state.currentFactory !== 'all' && tank && tank.factoryId !== state.currentFactory) return;

      const tankName = tank ? tank.name : '未知儲槽';
      
      const product = state.products.find(p => p.id === l.productId);
      const prodName = product ? product.name : '未知產品';
      const prodColor = product ? product.color : '#fff';
      
      const typeTag = l.type === 'inflow' 
        ? '<span class="table-status-tag status-tag-active"><i class="fa-solid fa-arrow-down"></i> 進料</span>'
        : '<span class="table-status-tag status-tag-danger"><i class="fa-solid fa-arrow-up"></i> 出料</span>';

      const tr = document.createElement('tr');
      const logKey = l.id || String(index);
      tr.innerHTML = `
        <td style="text-align: center;"><input type="checkbox" class="log-checkbox" value="${logKey}"></td>
        <td>${formatDateString(l.timestamp)}</td>
        <td><span class="badge badge-warning">${state.lines.find(l => l.id === s.lineId)?.name || '未指定'}</span></td>
        <td><b>${tankName}</b></td>
        <td>
          <span class="prod-table-badge">
            <span class="color-dot" style="background-color: ${prodColor}"></span>
            ${prodName}
          </span>
        </td>
        <td>${typeTag}</td>
        <td><b class="${l.type === 'inflow' ? 'text-success' : 'text-danger'}">${l.type === 'inflow' ? '+' : '-'}${formatNumber(l.amount)} t</b></td>
        <td>${l.remark}</td>
        <td>
          <button class="btn btn-secondary btn-icon" onclick="editLog('${logKey}')" title="修改"><i class="fa-solid fa-pen"></i></button>
          <button class="btn btn-danger btn-icon" onclick="deleteLog('${logKey}')" title="刪除"><i class="fa-solid fa-trash"></i></button>
        </td>
      `;
      tbody.appendChild(tr);
    });

    // 重設全選勾選框與批次刪除按鈕狀態
    const checkAll = document.getElementById('check-all-logs');
    if (checkAll) checkAll.checked = false;
    updateBatchDeleteButtonVisibility();
  }

  let editingLogId = null;

  function editLog(idOrIndex) {
    let l = null;
    if (typeof idOrIndex === 'string' && idOrIndex.length > 5) {
      l = state.transactionLogs.find(item => item.id === idOrIndex);
    } else {
      l = state.transactionLogs[Number(idOrIndex)];
    }
    if (!l) return;

    editingLogId = l.id || idOrIndex;
    
    document.getElementById('log-modal-title').innerText = '修改進出料紀錄';
    document.getElementById('log-id-hidden').value = editingLogId;
    
    updateAllDropdowns();
    document.getElementById('log-tank').value = l.tankId;
    document.getElementById('log-type').value = l.type;
    document.getElementById('log-amount').value = l.amount;
    document.getElementById('log-remark').value = l.remark;
    
    // 轉換 ISO 時間為本地 datetime-local 格式
    const d = new Date(l.timestamp);
    const offset = d.getTimezoneOffset() * 60000;
    const localISOTime = new Date(d.getTime() - offset).toISOString().slice(0, 16);
    document.getElementById('log-timestamp').value = localISOTime;
    
    // 修改時預設不勾選「同步更新儲槽當前庫存量」
    document.getElementById('log-sync-tank').checked = false;
    
    updateLogFormStatusPreview();
    openModal('modal-log');
  }

  function updateBatchDeleteButtonVisibility() {
    const checkboxes = document.querySelectorAll('.log-checkbox');
    const checked = document.querySelectorAll('.log-checkbox:checked');
    const btnBatchDel = document.getElementById('btn-batch-delete-logs');
    const countEl = document.getElementById('selected-logs-count');
    
    if (btnBatchDel && countEl) {
      if (checked.length > 0) {
        btnBatchDel.style.display = 'inline-flex';
        countEl.innerText = checked.length;
      } else {
        btnBatchDel.style.display = 'none';
      }
    }
  }

  // ==================== 批次登載進出料管理 ====================
  function initBatchGrid() {
    const tbody = document.getElementById('batch-entry-body');
    if (!tbody) return;
    tbody.innerHTML = '';
    for (let i = 0; i < 5; i++) {
      const tr = document.createElement('tr');
      tr.innerHTML = generateBatchRowHTML();
      tbody.appendChild(tr);
    }
  }

  function generateBatchRowHTML(data = {}) {
    const now = new Date();
    const offset = now.getTimezoneOffset() * 60000;
    const defaultTime = new Date(now.getTime() - offset).toISOString().slice(0, 16);
    
    const timestamp = data.timestamp || defaultTime;
    const tankId = data.tankId || "";
    const type = data.type || "outflow";
    const amount = data.amount || "";
    const remark = data.remark || "";
    
    // 生成儲槽選項
    let tankOptionsHTML = '<option value="">-- 選擇儲槽 --</option>';
    state.tanks.forEach(t => {
      const prod = state.products.find(p => p.id === t.productId);
      const prodName = prod ? prod.name : '未知';
      const selected = t.id === tankId ? 'selected' : '';
      tankOptionsHTML += `<option value="${t.id}" ${selected}>${t.name} (${prodName})</option>`;
    });
    
    return `
      <td><input type="datetime-local" class="form-control batch-time" value="${timestamp}"></td>
      <td><select class="form-control batch-tank">${tankOptionsHTML}</select></td>
      <td>
        <select class="form-control batch-type">
          <option value="outflow" ${type === 'outflow' ? 'selected' : ''}>出料 (庫存減少)</option>
          <option value="inflow" ${type === 'inflow' ? 'selected' : ''}>進料 (庫存增加)</option>
        </select>
      </td>
      <td><input type="number" class="form-control batch-amount" value="${amount}" min="0.01" step="any" placeholder="例如：2000"></td>
      <td><input type="text" class="form-control batch-remark" value="${remark}" placeholder="如：裝載槽車 ISO-02 / 王小明"></td>
      <td style="text-align: center;">
        <button type="button" class="btn btn-danger btn-icon" onclick="this.closest('tr').remove()" title="移除此行">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </td>
    `;
  }

  function addBatchRow() {
    const tbody = document.getElementById('batch-entry-body');
    if (!tbody) return;
    const tr = document.createElement('tr');
    tr.innerHTML = generateBatchRowHTML();
    tbody.appendChild(tr);
  }

  function saveBatchEntries() {
    const tbody = document.getElementById('batch-entry-body');
    if (!tbody) return;
    
    const rows = tbody.querySelectorAll('tr');
    const newLogs = [];
    const tankUpdates = {};
    
    let hasError = false;
    let validCount = 0;
    
    rows.forEach((row, index) => {
      const timestamp = row.querySelector('.batch-time').value;
      const tankId = row.querySelector('.batch-tank').value;
      const type = row.querySelector('.batch-type').value;
      const amountVal = row.querySelector('.batch-amount').value;
      const remark = row.querySelector('.batch-remark').value;
      
      // 若整行完全沒有填，略過
      if (!tankId && !amountVal && !remark) {
        return;
      }
      
      if (!tankId || !amountVal) {
        alert(`第 ${index + 1} 行資料填寫不完整（必須選擇儲槽並輸入數量）！`);
        hasError = true;
        return;
      }
      
      const amount = Number(amountVal);
      if (amount <= 0 || isNaN(amount)) {
        alert(`第 ${index + 1} 行輸入的數量必須大於 0！`);
        hasError = true;
        return;
      }
      
      const tank = state.tanks.find(t => t.id === tankId);
      if (!tank) {
        alert(`第 ${index + 1} 行儲槽不存在！`);
        hasError = true;
        return;
      }
      
      newLogs.push({
        id: generateUUID(),
        timestamp: new Date(timestamp).toISOString(),
        tankId: tankId,
        productId: tank.productId,
        type: type,
        amount: amount,
        remark: remark || "批次登打載入"
      });
      
      if (!tankUpdates[tankId]) {
        tankUpdates[tankId] = Number(tank.currentLevel) || 0;
      }
      
      if (type === 'inflow') {
        tankUpdates[tankId] += amount;
      } else {
        tankUpdates[tankId] -= amount;
      }
      
      if (tankUpdates[tankId] > Number(tank.capacity)) {
        alert(`警告：第 ${index + 1} 行交易將使儲槽 ${tank.name} 儲量超過上限！`);
        hasError = true;
        return;
      }
      
      if (tankUpdates[tankId] < 0) {
        alert(`警告：第 ${index + 1} 行交易將使儲槽 ${tank.name} 餘額為負數！`);
        hasError = true;
        return;
      }
      
      validCount++;
    });
    
    if (hasError) return;
    
    if (validCount === 0) {
      alert('請填寫至少一行有效的進出料紀錄！');
      return;
    }
    
    // 寫入 state
    state.transactionLogs = state.transactionLogs.concat(newLogs);
    
    // 更新儲槽儲量
    for (const tankId in tankUpdates) {
      const tank = state.tanks.find(t => t.id === tankId);
      if (tank) {
        tank.currentLevel = tankUpdates[tankId];
      }
    }
    
    saveDataToCloud(() => {
      showToast(`成功批次登記 ${validCount} 筆交易！`, "success");
      initBatchGrid();
      renderLogs();
      calculateAndRenderDashboard();
    });
  }

  function deleteLog(idOrIndex) {
    if (!confirm('您確定要刪除此筆進出料紀錄嗎？（注意：此刪除不會還原儲槽庫存量，若需修正庫存，請至儲槽分頁直接修改當前儲量）')) return;
    
    if (typeof idOrIndex === 'string' && idOrIndex.length > 5) {
      state.transactionLogs = state.transactionLogs.filter(l => l.id !== idOrIndex);
    } else {
      state.transactionLogs.splice(Number(idOrIndex), 1);
    }
    
    saveDataToCloud(() => {
      renderLogs();
      calculateAndRenderDashboard();
    });
  }

  function updateLogFormStatusPreview() {
    const tankId = document.getElementById('log-tank').value;
    const previewEl = document.getElementById('log-tank-status-preview');
    if (!tankId) {
      previewEl.innerText = '尚未選擇儲槽';
      return;
    }
    const tank = state.tanks.find(t => t.id === tankId);
    if (!tank) {
      previewEl.innerText = '未知儲槽';
      return;
    }
    const product = state.products.find(p => p.id === tank.productId);
    const prodName = product ? product.name : '未知';
    previewEl.innerHTML = `當前產品：<b>${prodName}</b> | 當前儲量：<b>${formatNumber(tank.currentLevel)} t</b> / 最大容量：${formatNumber(tank.capacity)} L`;
  }

  // ==================== 備份與還原功能 ====================
  function loadArchiveList() {
    const container = document.getElementById('archive-list-container');
    if (!container) return;
    
    container.innerHTML = '<li style="padding: 16px;" class="text-secondary text-sm">正在載入雲端備份庫清單...</li>';
    
    if (typeof google === 'undefined' || !google.script || !google.script.run) {
      container.innerHTML = '<li style="padding: 24px;" class="text-center text-secondary text-sm">本地偵測模式下，無法載入雲端歷史備份</li>';
      return;
    }
    
    google.script.run
      .withSuccessHandler(list => {
        if (list.length === 0) {
          container.innerHTML = '<li style="padding: 24px;" class="text-center text-secondary text-sm">目前無任何歷史備份存檔</li>';
          return;
        }
        container.innerHTML = '';
        list.forEach(archive => {
          const li = document.createElement('li');
          li.className = 'archive-item';
          li.innerHTML = `
            <div class="archive-info">
              <h4>${archive.id}</h4>
              <span>備份時間：${archive.time}</span>
            </div>
            <div class="archive-actions">
              <button class="btn btn-secondary" onclick="restoreArchive('${archive.id}', '${encodeURIComponent(archive.dataStr)}')">
                <i class="fa-solid fa-trash-arrow-up text-warning"></i> 還原此版本
              </button>
            </div>
          `;
          container.appendChild(li);
        });
      })
      .withFailureHandler(err => {
        container.innerHTML = '<li style="padding: 16px;" class="text-danger text-sm">載入備份清單失敗</li>';
      })
      .getArchiveList();
  }

  function restoreArchive(name, encodedDataStr) {
    if (!confirm(`⚠️ 警告：您確定要還原備份「${name}」嗎？這會覆蓋目前的全部資料（包含產品、儲槽與排程）。建議您先為目前資料建立一個新備份以防萬一。`)) return;
    
    try {
      const dataStr = decodeURIComponent(encodedDataStr);
      const restoredState = JSON.parse(dataStr);
      
      state.products = restoredState.products || [];
      state.tanks = restoredState.tanks || [];
      state.lines = restoredState.lines || [];
      state.schedules = restoredState.schedules || [];
      state.transactionLogs = restoredState.transactionLogs || [];
      state.startDateTime = restoredState.startDateTime || "";
      state.ships = restoredState.ships || [];
      state.factories = restoredState.factories || [];
      
      saveDataToCloud(() => {
        showToast(`已成功還原至備份版本 [${name}]`, "success");
        calculateAndRenderDashboard();
        updateStats();
        updateAllDropdowns();
        document.querySelector('.nav-btn[data-tab="dashboard"]').click();
      });
    } catch (e) {
      showToast("還原失敗，資料格式損毀：" + e.toString(), "error");
    }
  }

  // ==================== 頁面事件監聽設定 ====================
  function setupEventListeners() {
    document.getElementById('btn-sync').addEventListener('click', loadDataFromCloud);

    // --- 匯出 Excel 按鈕事件綁定 ---
    document.getElementById('btn-export-forecast').addEventListener('click', () => {
      const tankSelect = document.getElementById('forecast-tank-select');
      const tankId = tankSelect.value;
      if (!tankId) {
        alert('請先選擇監控儲槽！');
        return;
      }
      const tank = state.tanks.find(t => t.id === tankId);
      const name = tank ? tank.name : '儲槽';
      exportTableToCSV('forecast-table', `${name}_未來30日進耗存預估表.csv`);
    });

    document.getElementById('btn-export-schedules').addEventListener('click', () => {
      exportTableToCSV('schedule-table', '生產排程明細表.csv');
    });

    document.getElementById('btn-export-tanks').addEventListener('click', () => {
      exportTableToCSV('tank-table', '儲槽與容器列表.csv');
    });

    document.getElementById('btn-export-logs').addEventListener('click', () => {
      exportTableToCSV('log-table', '儲槽進出料與交易明細.csv');
    });

    // 預估表儲槽切換事件
    document.getElementById('forecast-tank-select').addEventListener('change', renderForecastTable);

    // 預估表日期切換事件
    const startDateInput = document.getElementById('forecast-start-date');
    const chkContinuous = document.getElementById('chk-continuous-start');
    
    if (startDateInput) {
      startDateInput.addEventListener('change', (e) => {
        state.startDateTime = e.target.value;
        saveDataToCloud(() => {
          renderForecastTable();
        });
      });
    }
    
    if (chkContinuous) {
      chkContinuous.addEventListener('change', (e) => {
        state.continuousStart = e.target.checked;
        startDateInput.disabled = e.target.checked;
        if (state.continuousStart) {
          const today = new Date();
          const yyyy = today.getFullYear();
          const mm = String(today.getMonth() + 1).padStart(2, '0');
          const dd = String(today.getDate()).padStart(2, '0');
          startDateInput.value = `${yyyy}-${mm}-${dd}`;
          state.startDateTime = startDateInput.value;
        }
        saveDataToCloud(() => {
          renderForecastTable();
        });
      });
    }

    document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
      btn.addEventListener('click', () => {
        closeAllModals();
      });
    });

    // --- 船隻 Form 提交 ---
    const btnAddShip = document.getElementById('btn-add-ship');
    if (btnAddShip) {
      btnAddShip.addEventListener('click', () => {
        if (state.products.length === 0) {
          alert('請先設定產品品項！');
          return;
        }
        editingShipId = null;
        document.getElementById('ship-modal-title').innerText = '新增船隻動態';
        document.getElementById('form-ship').reset();
        document.getElementById('ship-id-hidden').value = '';
        
        const now = new Date();
        const offset = now.getTimezoneOffset() * 60000;
        document.getElementById('ship-eta').value = new Date(now.getTime() - offset + 72 * 3600000).toISOString().slice(0, 16); 
        
        updateAllDropdowns();
        openModal('modal-ship');
      });
    }

    const formShip = document.getElementById('form-ship');
    if (formShip) {
      formShip.addEventListener('submit', (e) => {
        e.preventDefault();
        const id = document.getElementById('ship-id-hidden').value || generateUUID();
        const name = document.getElementById('ship-name').value;
        const code = document.getElementById('ship-code').value;
        const location = document.getElementById('ship-location').value;
        const eta = document.getElementById('ship-eta').value;
        const productId = document.getElementById('ship-product').value;
        const amount = Number(document.getElementById('ship-amount').value);
        const status = document.getElementById('ship-status').value;

        if (!state.ships) state.ships = [];

        if (editingShipId) {
          const s = state.ships.find(item => item.id === editingShipId);
          if (s) {
            s.name = name;
            s.code = code;
            s.location = location;
            s.eta = new Date(eta).toISOString();
            s.productId = productId;
          s.lineId = lineId;
            s.amount = amount;
            s.status = status;
          }
        } else {
          state.ships.push({ id, name, code, location, eta: new Date(eta).toISOString(), productId, amount, status });
        }

        saveDataToCloud(() => {
          closeAllModals();
          renderShips();
        });
      });
    }

    
    // --- 廠區 Form 提交 ---
    const btnAddFactory = document.getElementById('btn-add-factory');
    if (btnAddFactory) {
      btnAddFactory.addEventListener('click', () => {
        editingFactoryId = null;
        document.getElementById('factory-modal-title').innerText = '新增廠區';
        document.getElementById('form-factory').reset();
        document.getElementById('factory-id-hidden').value = '';
        openModal('modal-factory');
      });
    }

    const formFactory = document.getElementById('form-factory');
    if (formFactory) {
      formFactory.addEventListener('submit', (e) => {
        e.preventDefault();
        const id = document.getElementById('factory-id-hidden').value || generateUUID();
        const name = document.getElementById('factory-name').value;
        if (editingFactoryId) {
          const f = state.factories.find(item => item.id === editingFactoryId);
          if (f) f.name = name;
        } else {
          state.factories.push({ id, name });
        }
        saveDataToCloud(() => {
          closeAllModals();
          renderFactories();
          renderLines();
          renderLines();
          updateAllDropdowns();
        });
      });
    }
    
    // --- Global Factory Select ---
    const globalSelectEvt = document.getElementById('global-factory-select');
    if (globalSelectEvt) {
      globalSelectEvt.addEventListener('change', (e) => {
        state.currentFactory = e.target.value;
        // Re-render everything
        calculateAndRenderDashboard();
        renderTanks();
        renderSchedules();
        renderGanttChart();
        renderLogs();
        updateAllDropdowns();
      });
    }

    // --- 產品 Form 提交 ---
    document.getElementById('btn-add-product').addEventListener('click', () => {
      editingProductId = null;
      document.getElementById('product-modal-title').innerText = '新增產品設定';
      document.getElementById('form-product').reset();
      document.getElementById('product-id-hidden').value = '';
      openModal('modal-product');
    });
    
    document.getElementById('form-product').addEventListener('submit', (e) => {
      e.preventDefault();
      const id = document.getElementById('product-id-hidden').value || generateUUID();
      const name = document.getElementById('product-name').value;
      const code = document.getElementById('product-code').value;
      const color = document.getElementById('product-color').value;
      const desc = document.getElementById('product-desc').value;
      
      if (editingProductId) {
        const p = state.products.find(item => item.id === editingProductId);
        if (p) {
          p.name = name;
          p.code = code;
          p.color = color;
          p.desc = desc;
        }
      } else {
        state.products.push({ id, name, code, color, desc });
      }
      
      saveDataToCloud(() => {
        closeAllModals();
        renderProducts();
          renderFactories();
          renderLines();
          renderLines();
        updateAllDropdowns();
      });
    });

    
    // --- 產線 Form 提交 ---
    const btnAddLine = document.getElementById('btn-add-line');
    if (btnAddLine) {
      btnAddLine.addEventListener('click', () => {
        editingLineId = null;
        document.getElementById('line-modal-title').innerText = '新增產線';
        document.getElementById('form-line').reset();
        document.getElementById('line-id-hidden').value = '';
        document.getElementById('line-factory').value = state.currentFactory !== 'all' ? state.currentFactory : (state.factories[0]?.id || '');
        openModal('modal-line');
      });
    }

    const formLine = document.getElementById('form-line');
    if (formLine) {
      formLine.addEventListener('submit', (e) => {
        e.preventDefault();
        const id = document.getElementById('line-id-hidden').value || generateUUID();
        const name = document.getElementById('line-name').value;
        const factoryId = document.getElementById('line-factory').value;
        if (editingLineId) {
          const l = state.lines.find(item => item.id === editingLineId);
          if (l) {
            l.name = name;
            l.factoryId = factoryId;
          }
        } else {
          state.lines.push({ id, name, factoryId });
        }
        saveDataToCloud(() => {
          closeAllModals();
          renderLines();
          updateAllDropdowns();
        });
      });
    }

    // --- 儲槽 Form 提交 ---
    document.getElementById('btn-add-tank').addEventListener('click', () => {
      if (state.products.length === 0) {
        alert('請先新增至少一項「產品設定」，才能建立儲槽。');
        return;
      }
      editingTankId = null;
      document.getElementById('tank-modal-title').innerText = '新增儲槽/容器';
      document.getElementById('form-tank').reset();
      document.getElementById('tank-id-hidden').value = '';
      document.getElementById('tank-factory').value = state.factories[0]?.id || '';
      updateTankDedicatedLines();
      updateAllDropdowns();
      toggleTankOutflowField();
      openModal('modal-tank');
    });

    document.getElementById('tank-type').addEventListener('change', toggleTankOutflowField);

    document.getElementById('form-tank').addEventListener('submit', (e) => {
      e.preventDefault();
      const id = document.getElementById('tank-id-hidden').value || generateUUID();
      const name = document.getElementById('tank-name').value;
      const type = document.getElementById('tank-type').value;
      const factoryId = document.getElementById('tank-factory').value;
      const productId = document.getElementById('tank-product').value;
        const dedicatedLineId = document.getElementById('tank-dedicated-line').value;
      const capacity = Number(document.getElementById('tank-capacity').value);
      const currentLevel = Number(document.getElementById('tank-current').value);
      const outflowRate = Number(document.getElementById('tank-outflow').value) || 0;
      const safetyLevel = Number(document.getElementById('tank-safety').value) || 0;
      const status = document.getElementById('tank-status').value;

      if (currentLevel > capacity) {
        alert('錯誤：當前儲量不能大於容量上限！');
        return;
      }

      if (editingTankId) {
        const t = state.tanks.find(item => item.id === editingTankId);
        if (t) {
          t.name = name;
          t.type = type;
          t.factoryId = factoryId;
          t.dedicatedLineId = dedicatedLineId;
          t.productId = productId;
          t.capacity = capacity;
          t.currentLevel = currentLevel;
          t.outflowRate = outflowRate;
          t.safetyLevel = safetyLevel;
          t.status = status;
        }
      } else {
        state.tanks.push({ id, factoryId, dedicatedLineId, name, type, productId, capacity, currentLevel, outflowRate, safetyLevel, status });
      }

      saveDataToCloud(() => {
        closeAllModals();
        renderTanks();
        updateAllDropdowns();
      });
    });

    // --- 生產排程 Form 提交 ---
    document.getElementById('btn-add-schedule').addEventListener('click', () => {
      if (state.tanks.length === 0) {
        alert('請先建立至少一個儲槽/容器，才能規劃生產排程！');
        return;
      }
      
      editingScheduleId = null;
      document.getElementById('schedule-modal-title').innerText = '新增生產排程';
      document.getElementById('form-schedule').reset();
      document.getElementById('schedule-id-hidden').value = '';
      const firstLine = document.getElementById('schedule-line').options[0];
      if(firstLine) document.getElementById('schedule-line').value = firstLine.value;
      
      const now = new Date();
      const offset = now.getTimezoneOffset() * 60000;
      const localISOTime = new Date(now.getTime() - offset).toISOString().slice(0, 16);
      const localISOTimeEnd = new Date(now.getTime() - offset + 8 * 3600000).toISOString().slice(0, 16); 
      document.getElementById('schedule-start').value = localISOTime;
      document.getElementById('schedule-end').value = localISOTimeEnd;
      
      const firstProd = state.products[0].id;
      document.getElementById('schedule-product').value = firstProd;
      filterTanksBySelectedProduct(firstProd);
      
      calculateVolumeFromTimes();
      document.getElementById('schedule-yield').value = 100;
      updateYieldTotalDisplay();
      openModal('modal-schedule');
    });

    document.getElementById('schedule-product').addEventListener('change', (e) => {
      filterTanksBySelectedProduct(e.target.value);
      calculateVolumeFromTimes();
    });

    document.getElementById('schedule-rate').addEventListener('input', calculateVolumeFromTimes);
    document.getElementById('schedule-start').addEventListener('change', calculateVolumeFromTimes);
    document.getElementById('schedule-end').addEventListener('change', calculateVolumeFromTimes);
    document.getElementById('schedule-total-volume').addEventListener('input', calculateEndTimeFromVolume);
    document.getElementById('schedule-yield').addEventListener('input', updateYieldTotalDisplay);

    document.getElementById('form-schedule').addEventListener('submit', (e) => {
      e.preventDefault();
      const id = document.getElementById('schedule-id-hidden').value || generateUUID();
      const productId = document.getElementById('schedule-product').value;
        const lineId = document.getElementById('schedule-line').value;
      const tankId = document.getElementById('schedule-tank').value;
      const sourceTankId = document.getElementById('schedule-source-tank').value || '';
      const rate = Number(document.getElementById('schedule-rate').value);
      const start = document.getElementById('schedule-start').value;
      const end = document.getElementById('schedule-end').value;
      const yieldVal = Number(document.getElementById('schedule-yield').value) || 100;

      if (!tankId) {
        alert('請選擇目標儲料容器！');
        return;
      }
      
      if (sourceTankId && sourceTankId === tankId) {
        alert('錯誤：原料來源儲槽與目標儲槽不能為同一個！');
        return;
      }

      if (new Date(end) <= new Date(start)) {
        alert('結束時間必須晚於開始時間！');
        return;
      }

      if (editingScheduleId) {
        const s = state.schedules.find(item => item.id === editingScheduleId);
        if (s) {
          s.productId = productId;
          s.lineId = lineId;
          s.tankId = tankId;
          s.sourceTankId = sourceTankId;
          s.rate = rate;
          s.start = start;
          s.end = end;
          s.yield = yieldVal;
        }
      } else {
        state.schedules.push({ id, productId, lineId, tankId, sourceTankId, rate, start, end, yield: yieldVal });
      }

      saveDataToCloud(() => {
        closeAllModals();
        renderSchedules();
        renderGanttChart();
        calculateAndRenderDashboard();
      });
    });

    document.getElementById('filter-schedule-product'),
      document.getElementById('ship-product').addEventListener('change', () => {
      renderSchedules();
    });

    // --- 進出料紀錄 Form 提交 ---
    document.getElementById('btn-add-log').addEventListener('click', () => {
      if (state.tanks.length === 0) {
        alert('請先建立儲槽！');
        return;
      }
      editingLogId = null;
      document.getElementById('log-modal-title').innerText = '手動登記儲槽進出料';
      document.getElementById('form-log').reset();
      document.getElementById('log-id-hidden').value = '';
      
      const now = new Date();
      const offset = now.getTimezoneOffset() * 60000;
      const localISOTime = new Date(now.getTime() - offset).toISOString().slice(0, 16);
      document.getElementById('log-timestamp').value = localISOTime;
      
      document.getElementById('log-sync-tank').checked = true;
      
      updateAllDropdowns();
      updateLogFormStatusPreview();
      openModal('modal-log');
    });

    document.getElementById('log-tank').addEventListener('change', updateLogFormStatusPreview);
    document.getElementById('filter-log-tank').addEventListener('change', renderLogs);

    document.getElementById('form-log').addEventListener('submit', (e) => {
      e.preventDefault();
      const id = document.getElementById('log-id-hidden').value;
      const tankId = document.getElementById('log-tank').value;
      const type = document.getElementById('log-type').value;
      const amount = Number(document.getElementById('log-amount').value);
      const remark = document.getElementById('log-remark').value;
      const syncTank = document.getElementById('log-sync-tank').checked;
      const timestampVal = document.getElementById('log-timestamp').value;

      const tank = state.tanks.find(t => t.id === tankId);
      if (!tank) return;

      // 如果有勾選「同步更新儲槽當前庫存」
      if (syncTank) {
        // 如果是修改，先「回退」舊記錄對水位的影響
        if (id) {
          let oldLog = null;
          if (typeof id === 'string' && id.length > 5) {
            oldLog = state.transactionLogs.find(item => item.id === id);
          } else {
            oldLog = state.transactionLogs[Number(id)];
          }
          if (oldLog) {
            const oldTank = state.tanks.find(t => t.id === oldLog.tankId);
            if (oldTank) {
              if (oldLog.type === 'inflow') {
                oldTank.currentLevel = Math.max(0, oldTank.currentLevel - Number(oldLog.amount));
              } else {
                oldTank.currentLevel = oldTank.currentLevel + Number(oldLog.amount);
              }
            }
          }
        }
        
        // 再套用新記錄的影響
        if (type === 'outflow') {
          if (tank.currentLevel < amount) {
            if (!confirm(`⚠️ 警告：目前儲槽餘量 (${formatNumber(tank.currentLevel)} t) 小於出庫量 (${formatNumber(amount)} t)，強行出庫將導致庫存變為負數！是否繼續？`)) {
              return;
            }
          }
          tank.currentLevel = Math.max(0, tank.currentLevel - amount);
        } else {
          if (tank.currentLevel + amount > tank.capacity) {
            if (!confirm(`⚠️ 警告：進料後容量 (${formatNumber(tank.currentLevel + amount)} t) 將超出儲槽上限 (${formatNumber(tank.capacity)} t)！是否繼續？`)) {
              return;
            }
          }
          tank.currentLevel = tank.currentLevel + amount;
        }
      }

      const timestamp = timestampVal ? new Date(timestampVal).toISOString() : new Date().toISOString();

      if (id) {
        // 修改歷史記錄
        let l = null;
        if (typeof id === 'string' && id.length > 5) {
          l = state.transactionLogs.find(item => item.id === id);
        } else {
          l = state.transactionLogs[Number(id)];
        }
        if (l) {
          l.timestamp = timestamp;
          l.tankId = tankId;
          l.productId = tank.productId;
          l.type = type;
          l.amount = amount;
          l.remark = remark;
        }
      } else {
        // 新增記錄
        state.transactionLogs.push({
          id: generateUUID(),
          timestamp,
          tankId,
          productId: tank.productId,
          type,
          amount,
          remark
        });
      }

      saveDataToCloud(() => {
        closeAllModals();
        renderLogs();
        calculateAndRenderDashboard();
        renderTanks(); 
      });
    });

    // --- 進出料多選與批次刪除監聽 ---
    const logListBody = document.getElementById('log-list-body');
    if (logListBody) {
      logListBody.addEventListener('change', (e) => {
        if (e.target.classList.contains('log-checkbox')) {
          updateBatchDeleteButtonVisibility();
        }
      });
    }

    const checkAllLogs = document.getElementById('check-all-logs');
    if (checkAllLogs) {
      checkAllLogs.addEventListener('change', (e) => {
        const checked = e.target.checked;
        document.querySelectorAll('.log-checkbox').forEach(cb => {
          cb.checked = checked;
        });
        updateBatchDeleteButtonVisibility();
      });
    }

    document.getElementById('btn-batch-delete-logs').addEventListener('click', () => {
      const checkedBoxes = document.querySelectorAll('.log-checkbox:checked');
      if (checkedBoxes.length === 0) return;
      
      if (!confirm(`⚠️ 您確定要批次刪除這 ${checkedBoxes.length} 筆進出料紀錄嗎？（注意：此動作不會還原儲槽水位，若需修改水位請至儲槽分頁直接變更）`)) {
        return;
      }
      
      const idsToDelete = Array.from(checkedBoxes).map(cb => cb.value);
      
      state.transactionLogs = state.transactionLogs.filter((l, index) => {
        const key = l.id || String(index);
        return !idsToDelete.includes(key);
      });
      
      saveDataToCloud(() => {
        showToast(`已成功批次刪除 ${idsToDelete.length} 筆紀錄！`, "success");
        renderLogs();
        calculateAndRenderDashboard();
      });
    });

    // --- 備份按鈕 ---
    document.getElementById('btn-backup').addEventListener('click', () => {
      const archiveNameInput = document.getElementById('archive-name');
      const archiveName = archiveNameInput.value.trim();
      if (!archiveName) {
        alert('請輸入備份名稱或備註以作識別！');
        return;
      }

      showLoading(true, "正在建立雲端備份存檔...");
      if (typeof google === 'undefined' || !google.script || !google.script.run) {
        showLoading(false);
        showToast("本地模式下無法建立雲端備份！", "error");
        return;
      }
      google.script.run
        .withSuccessHandler(result => {
          showLoading(false);
          if (result === "SUCCESS") {
            showToast(`已建立備份「${archiveName}」！`, "success");
            archiveNameInput.value = '';
            loadArchiveList(); 
          } else {
            showToast("備份失敗: " + result, "error");
          }
        })
        .withFailureHandler(err => {
          showLoading(false);
          showToast("備份時發生系統錯誤", "error");
        })
        .archiveData(state, archiveName);
    });

    // --- 全清空按鈕 ---
    document.getElementById('btn-clear-all').addEventListener('click', () => {
      if (!confirm('⚠️ 警告：您確定要清空整套系統的所有資料嗎？這將刪除所有產品、儲槽、生產排程與交易紀錄！此動作無法復原！')) return;
      if (!confirm('請再次確認是否真的要清空？所有現存資料將被抹除。')) return;
      
      state.factories = [
      { id: "factory-1", name: "一廠" },
      { id: "factory-2", name: "二廠" }
    ];
    state.products = [];
      state.tanks = [];
      state.schedules = [];
      state.ships = [
      { id: "ship-01", name: "Ever Green", code: "9811000", location: "南海 (航向高雄港)", eta: formatTime(new Date(now.getTime() + 48 * 3600000)), productId: "p-01", amount: 15000, status: "in_transit" }
    ];
    state.transactionLogs = [];
      state.startDateTime = "";
      state.ships = [];
      
      saveDataToCloud(() => {
        showToast("系統資料已全部清空！", "success");
        calculateAndRenderDashboard();
        updateStats();
        updateAllDropdowns();
        document.querySelector('.nav-btn[data-tab="dashboard"]').click();
      });
    });

    // --- 批次快速登打按鈕事件 ---
    const btnBatchAdd = document.getElementById('btn-batch-add-row');
    if (btnBatchAdd) {
      btnBatchAdd.addEventListener('click', addBatchRow);
    }
    const btnBatchSave = document.getElementById('btn-batch-save');
    if (btnBatchSave) {
      btnBatchSave.addEventListener('click', saveBatchEntries);
    }
  }

  // ==================== 輔助工具函數 ====================
  function formatHours(h) {
    if (h > 48) {
      const days = Math.floor(h / 24);
      const remainHours = Math.round(h % 24);
      return `${days} 天 ${remainHours} 小時`;
    }
    return `${h.toFixed(1)} 小時`;
  }

  function formatDateString(isoStr) {
    if (!isoStr) return '';
    const d = new Date(isoStr);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}/${pad(d.getMonth()+1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  function formatNumber(num) {
    if (num === undefined || num === null) return '0';
    const n = Number(num);
    // 如果小於 100 且有小數點，保留一位小數；大數則四捨五入為整數，避免顯示過細
    if (Math.abs(n) < 100 && n % 1 !== 0) {
      return n.toLocaleString('zh-TW', { maximumFractionDigits: 1 });
    }
    return Math.round(n).toLocaleString('zh-TW', { maximumFractionDigits: 0 });
  }

  function lightenColor(col, amt) {
    col = col.replace('#', '');
    var num = parseInt(col, 16);
    var r = (num >> 16) + amt;
    var g = ((num >> 8) & 0x00FF) + amt;
    var b = (col.length === 3 ? (num & 0x000F) : (num & 0x0000FF)) + amt;
    r = Math.min(255, Math.max(0, r));
    g = Math.min(255, Math.max(0, g));
    b = Math.min(255, Math.max(0, b));
    return '#' + (g | (b << 8) | (r << 16)).toString(16).padStart(6, '0');
  }

  function hexToRgba(hex, alpha) {
    hex = hex.replace('#', '');
    let r = parseInt(hex.substring(0, 2), 16);
    let g = parseInt(hex.substring(2, 4), 16);
    let b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function generateUUID() {
    return 'uuid-' + Math.random().toString(36).substring(2, 9) + '-' + Date.now().toString(36);
  }

  // ==================== Modal 與 UI 控制 ====================
  function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
      modal.classList.add('open');
    }
  }

  function closeAllModals() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
      modal.classList.remove('open');
    });
  }

  function showLoading(show, message = "載入中...") {
    const overlay = document.getElementById('loading-screen');
    const textEl = overlay.querySelector('.loading-text');
    if (overlay) {
      if (show) {
        textEl.innerText = message;
        overlay.style.display = 'flex';
        overlay.style.opacity = '1';
      } else {
        overlay.style.opacity = '0';
        setTimeout(() => {
          overlay.style.display = 'none';
        }, 250);
      }
    }
  }

  function showToast(message, type = "info") {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let iconHTML = '<i class="fa-solid fa-circle-info toast-icon"></i>';
    if (type === 'success') iconHTML = '<i class="fa-solid fa-circle-check toast-icon"></i>';
    else if (type === 'warning') iconHTML = '<i class="fa-solid fa-triangle-exclamation toast-icon"></i>';
    else if (type === 'error') iconHTML = '<i class="fa-solid fa-circle-xmark toast-icon"></i>';
    
    toast.innerHTML = `
      ${iconHTML}
      <div class="toast-content">${message}</div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
      toast.classList.add('fade-out');
      setTimeout(() => {
        toast.remove();
      }, 400);
    }, 5000);
  }
  
  // ==================== Excel 匯入解析 ====================
  function handleExcelUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    showToast('info', '解析中...', '正在讀取 Excel 檔案。');
    
    const reader = new FileReader();
    reader.onload = function(e) {
      try {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, {type: 'array'});
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];
        
        // Convert to 2D array
        const json = XLSX.utils.sheet_to_json(worksheet, {header: 1});
        
        // Find all header rows
        const headerRows = [];
        for (let i = 0; i < json.length; i++) {
          const row = json[i];
          if (!row) continue;
          for (let j = 0; j < row.length; j++) {
            if (typeof row[j] === 'string' && row[j].includes('槽別')) {
              headerRows.push(i);
              break;
            }
          }
        }
        
        if (headerRows.length === 0) {
          alert('無法在 Excel 中找到包含「槽別」的列，請確認格式。');
          return;
        }
        
        const updates = [];
        const updateText = [];
        
        // Process each block
        for (let b = 0; b < headerRows.length; b++) {
           const startIdx = headerRows[b];
           const endIdx = (b + 1 < headerRows.length) ? headerRows[b+1] : json.length;
           
           const headerRow = json[startIdx];
           const tankNames = [];
           const tankColIndices = [];
           
           // Find product row (usually right below '槽別' row)
           const prodRow = startIdx + 1 < json.length ? json[startIdx + 1] : [];
           const tankProducts = []; // To store product names for each tank

           for (let j = 0; j < headerRow.length; j++) {
              if (typeof headerRow[j] === 'string' && headerRow[j].includes('槽別')) {
                 for (let k = j + 1; k < headerRow.length; k++) {
                    if (headerRow[k]) {
                       const cleanedName = String(headerRow[k]).toUpperCase().replace(/[- ]/g, '');
                       tankNames.push(cleanedName);
                       tankColIndices.push(k);
                       // Get product name from the row below
                       const prodName = prodRow[k] ? String(prodRow[k]).toUpperCase().replace(/[- ]/g, '') : '';
                       tankProducts.push(prodName);
                    }
                 }
                 break;
              }
           }
           
           // Find amount rows in this block
           const amountRowIndices = [];
           for (let i = startIdx + 1; i < endIdx; i++) {
              const row = json[i];
              if (!row) continue;
              const rowStr = row.join('');
              if (rowStr.includes('數量') || rowStr.includes('重量')) {
                 amountRowIndices.push(i);
              }
           }
           
           // Extract latest valid weight for each tank
           for (let idx = 0; idx < tankColIndices.length; idx++) {
              const col = tankColIndices[idx];
              let finalWeight = null;
              
              for (let r = amountRowIndices.length - 1; r >= 0; r--) {
                 const rowIdx = amountRowIndices[r];
                 const val = json[rowIdx][col];
                 if (val !== undefined && val !== null && val !== '') {
                    // Extract number from string, ignore commas
                    const weightStr = String(val).replace(/,/g, '').trim();
                    if (weightStr !== '' && !isNaN(Number(weightStr))) {
                       const weight = Number(weightStr);
                       if (weight >= 0) {
                          finalWeight = weight;
                          break;
                       }
                    }
                 }
              }
              
              if (finalWeight !== null) {
                 const tankNameCleaned = tankNames[idx];
                 const prodNameCleaned = tankProducts[idx];
                 
                 // Find tank matching BOTH name and (if possible) product
                 let systemTank = state.tanks.find(t => {
                     if (t.name.toUpperCase().replace(/[- ]/g, '') !== tankNameCleaned) return false;
                     // If Excel has a product name, try to match it with the tank's product
                     if (prodNameCleaned) {
                         const tProd = state.products.find(p => p.id === t.productId);
                         if (tProd) {
                             const sysProdName = tProd.name.toUpperCase().replace(/[- ]/g, '');
                             // Fuzzy match: if one contains the other
                             if (sysProdName.includes(prodNameCleaned) || prodNameCleaned.includes(sysProdName)) {
                                 return true;
                             }
                             return false; // Name matches but product completely differs
                         }
                     }
                     return true; // Fallback if no product info available
                 });
                 
                 if (!systemTank) {
                     // Fallback to just name matching if strict product matching failed
                     systemTank = state.tanks.find(t => t.name.toUpperCase().replace(/[- ]/g, '') === tankNameCleaned);
                 }
                 
                 if (systemTank) {
                    updates.push({ tank: systemTank, weight: finalWeight });
                    updateText.push(`${systemTank.name}: ${finalWeight} kg`);
                 }
              }
           }
        }
        
        if (updates.length === 0) {
           alert('成功解析檔案，但未找到系統中對應的儲槽或有效的數值。');
           return;
        }
        
        if (confirm(`✅ 準備更新以下 ${updates.length} 顆儲槽的庫存量 (自動採計最新數值)：\n\n${updateText.slice(0, 15).join('\n')}${updateText.length > 15 ? '\n...等' : ''}\n\n是否確定寫入？`)) {
           updates.forEach(u => {
              u.tank.currentLevel = u.weight;
           });
           saveDataToCloud(() => {
              renderTanks();
              updateAllDropdowns();
              calculateAndRenderDashboard();
              alert(`🎉 成功更新 ${updates.length} 筆儲槽庫存！`);
           });
        }
        
      } catch (err) {
         console.error(err);
         alert('檔案解析失敗，請確保上傳的是正確的 Excel 格式。');
      } finally {
         event.target.value = ''; // reset input
      }
    };
    reader.readAsArrayBuffer(file);
  }
