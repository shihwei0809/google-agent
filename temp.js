
  // 動態提示字跑馬燈
  function startPlaceholderMarquee(elementId, originalText) {
    const el = document.getElementById(elementId);
    if (!el) return;
    let text = originalText + '   '; 
    setInterval(() => {
      text = text.substring(1) + text[0];
      el.setAttribute('placeholder', text);
    }, 400); 
  }
  document.addEventListener('DOMContentLoaded', () => {
    startPlaceholderMarquee('empIdInput', '掃描或輸入工號... ');
    startPlaceholderMarquee('requester', '姓名（工號查到後會自動填入）... ');
  });



  // 1. 完整預載明天槽車排程（共 20 筆：10 筆出貨 + 10 筆進料，預設日期為報表日 2026-09-06）
  let t100Orders = [
    // --- 【出貨槽車 (10 筆)】 ---
    { "doc_no": "ESXM101-20260901013", "date": "2026-09-06", "time": "08:00", "flowType": "出貨", "grade": "UPS", "productName": "IPAUPS", "tankNo": "TK624", "customer": "關東鑫林", "container": "PPCU7019228", "quantity": "5000 KG", "note": "L2 08:00 槽號:PPCU7019228 隨貨附樣" },
    { "doc_no": "ESXM101-20260901020", "date": "2026-09-06", "time": "08:00", "flowType": "出貨", "grade": "UPS", "productName": "IPAUPS", "tankNo": "TK605", "customer": "關東鑫林", "container": "PPCU7020018", "quantity": "5000 KG", "note": "L3崙尾 08:00 槽號:PPCU7020018 隨貨附樣" },
    { "doc_no": "ESXM101-20260901021", "date": "2026-09-06", "time": "08:00", "flowType": "出貨", "grade": "UPS", "productName": "IPAUPS", "tankNo": "TK605", "customer": "關東鑫林", "container": "PPCU7019193", "quantity": "5000 KG", "note": "L3崙尾 08:00 槽號:PPCU7019193 隨貨附樣" },
    { "doc_no": "ESXM101-20260902005", "date": "2026-09-06", "time": "09:00", "flowType": "出貨", "grade": "工業級", "productName": "CPNE3(T)", "tankNo": "S223", "customer": "勝一化工", "container": "S223", "quantity": "15000 KG", "note": "出TK-683,提貨槽車S223 (FOR TSMC),當天拉回永安二廠" },
    { "doc_no": "ESXM101-20260901022", "date": "2026-09-06", "time": "13:00", "flowType": "出貨", "grade": "UPS", "productName": "IPAUPS", "tankNo": "TK605", "customer": "關東鑫林", "container": "PPCU7019212", "quantity": "5000 KG", "note": "L3崙尾 13:00 槽號:PPCU7019212 隨貨附樣" },
    { "doc_no": "ESXM109-20260902011", "date": "2026-09-06", "time": "13:00", "flowType": "出貨", "grade": "工業級", "productName": "CPNE4", "tankNo": "S224", "customer": "勝一化工", "container": "S224", "quantity": "15000 KG", "note": "PM13:00 槽號：S224，充15噸" },
    { "doc_no": "ESXM101-20260831012", "date": "2026-09-06", "time": "排程", "flowType": "出貨", "grade": "工業級", "productName": "IPAHQ", "tankNo": "", "customer": "勝一化工", "container": "勝一槽車", "quantity": "4300 KG", "note": "勝一派技服，隨COA+三合一單" },
    { "doc_no": "ESXM101-20260831027", "date": "2026-09-06", "time": "排程", "flowType": "出貨", "grade": "工業級", "productName": "IPAHQ", "tankNo": "", "customer": "勝一化工", "container": "勝一槽車", "quantity": "4300 KG", "note": "勝一派技服" },
    { "doc_no": "ESXM101-20260831028", "date": "2026-09-06", "time": "排程", "flowType": "出貨", "grade": "工業級", "productName": "IPAHQ", "tankNo": "", "customer": "勝一化工", "container": "勝一槽車", "quantity": "4300 KG", "note": "勝一派技服" },
    { "doc_no": "ESXM101-20260903004", "date": "2026-09-06", "time": "排程", "flowType": "出貨", "grade": "工業級", "productName": "IPAHQ", "tankNo": "", "customer": "勝一化工", "container": "勝一槽車", "quantity": "4300 KG", "note": "勝一派技服" },
    // --- 【進料槽車 (10 筆)】 ---
    { "doc_no": "ESPM411-20260906001", "date": "2026-09-06", "time": "09:00", "flowType": "進料", "grade": "工業級", "productName": "EBR-P1R", "tankNo": "TKC05", "customer": "台積電 (南科18廠P5)", "container": "KEQ-3506 (櫃:6108)", "quantity": "8000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906002", "date": "2026-09-06", "time": "09:00", "flowType": "進料", "grade": "工業級", "productName": "EBR-P1R", "tankNo": "TKC01", "customer": "台積電 (南科18廠P7)", "container": "KEQ-3506 (櫃:6108)", "quantity": "8000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906003", "date": "2026-09-06", "time": "18:00", "flowType": "進料", "grade": "工業級", "productName": "EBR-P1R", "tankNo": "TKC04", "customer": "台積電 (南科18廠P4)", "container": "AAG-678 (櫃:2597)", "quantity": "8000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906004", "date": "2026-09-06", "time": "18:00", "flowType": "進料", "grade": "工業級", "productName": "EBR-P1R", "tankNo": "TKC04", "customer": "台積電 (南科18廠P6)", "container": "AAG-678 (櫃:2597)", "quantity": "8000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906005", "date": "2026-09-06", "time": "18:00", "flowType": "進料", "grade": "工業級", "productName": "NBAC-P1R", "tankNo": "TK659", "customer": "台積電 (南科18廠P4)", "container": "KEQ-3510 (櫃:3977)", "quantity": "2000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906006", "date": "2026-09-06", "time": "18:00", "flowType": "進料", "grade": "工業級", "productName": "NBAC-P1R", "tankNo": "TK659", "customer": "台積電 (高雄廠F22P1)", "container": "KEQ-3510 (櫃:3977)", "quantity": "2000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906007", "date": "2026-09-06", "time": "18:00", "flowType": "進料", "grade": "工業級", "productName": "NBAC-P1R", "tankNo": "TK659", "customer": "台積電 (高雄廠F22P2)", "container": "KEQ-3510 (櫃:3977)", "quantity": "2000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906008", "date": "2026-09-06", "time": "18:00", "flowType": "進料", "grade": "工業級", "productName": "NBAC-P1R", "tankNo": "TK659", "customer": "台積電 (高雄廠F22P3)", "container": "KEQ-3510 (櫃:3977)", "quantity": "2000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906010", "date": "2026-09-06", "time": "10:00", "flowType": "進料", "grade": "工業級", "productName": "CPN-P1R", "tankNo": "TK643", "customer": "台積電 (先進封測7廠)", "container": "AAG-775 (櫃:38)", "quantity": "5000 KG", "note": "" },
    { "doc_no": "ESPM411-20260906011", "date": "2026-09-06", "time": "10:00", "flowType": "進料", "grade": "工業級", "productName": "CPN-P1R", "tankNo": "TK643", "customer": "台積電 (先進封測8廠)", "container": "AAG-775 (櫃:38)", "quantity": "5000 KG", "note": "" }
  ];

  let t100FilterMode = 'today'; // 'today' | 'date' | 'pending' | 'all'

  function getLocalDateString(d = new Date()) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  
  // 自動套用產品等級
  function autoSelectGrade(prodName) {
    if(!prodName) return;
    const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
    if(!cfgStr) return;
    try {
      const cfg = JSON.parse(cfgStr);
      const mapStr = cfg.OPTIONS_PRODUCT_GRADES_MAP || cfg.productGradesMap || '';
      if(!mapStr) return;
      const pairs = mapStr.split(',').map(s => s.trim()).filter(Boolean);
      const mapping = {};
      pairs.forEach(p => {
        const parts = p.split(':').map(s => s.trim());
        if(parts.length >= 2) mapping[parts[0]] = parts[1];
      });
      if(mapping[prodName]) {
        const gradeSelect = document.getElementById('grade');
        if (gradeSelect) gradeSelect.value = mapping[prodName];
      }
    } catch(e) { console.warn(e); }
  }

  let allData = [];
  const IS_GAS = (typeof google !== 'undefined' && google.script && google.script.run);
  const DEFAULT_GAS_API_URL = '/api';
  let GAS_API_URL = localStorage.getItem('HS_QC_GAS_API_URL') || DEFAULT_GAS_API_URL;

  // 優先讀取曾匯入過的排程快取
  const cachedOrders = localStorage.getItem('HS_QC_T100_ORDERS');
  if (cachedOrders) {
    try { t100Orders = JSON.parse(cachedOrders); } catch(e){}
  }

  // Teams 頻道 Webhook 本機快取設定
  let localTeamsConfig = {
    managerWebhook: '',
    depts: {
      '資材課': '',
      '現場一課': '',
      '現場二課': '',
      '回收處理課': ''
    },
    enableRealSend: false
  };

  function loadTeamsConfig() {
    const saved = localStorage.getItem('HS_QC_TEAMS_CONFIG');
    if (saved) {
      try { 
        const parsed = JSON.parse(saved);
        localTeamsConfig = { ...localTeamsConfig, ...parsed };
        if (!localTeamsConfig.depts) localTeamsConfig.depts = {}; // 防呆：舊版紀錄沒有 depts 的情況
      } catch(e) {}
    }
  }

  function saveTeamsConfig() {
    if (!localTeamsConfig.depts) localTeamsConfig.depts = {};
    localTeamsConfig.managerWebhook = document.getElementById('teamsManagerWebhook').value.trim();
    localTeamsConfig.depts['資材課'] = document.getElementById('teamsWebhook_資材課').value.trim();
    localTeamsConfig.depts['現場一課'] = document.getElementById('teamsWebhook_現場一課').value.trim();
    localTeamsConfig.depts['現場二課'] = document.getElementById('teamsWebhook_現場二課').value.trim();
    localTeamsConfig.depts['回收處理課'] = document.getElementById('teamsWebhook_回收處理課').value.trim();
    localTeamsConfig.enableRealSend = document.getElementById('teamsEnableRealSend').checked;

    localStorage.setItem('HS_QC_TEAMS_CONFIG', JSON.stringify(localTeamsConfig));
    closeTeamsConfigModal();
    showToast("💾 Teams Webhook 設定已成功保存！");
  }

  function openTeamsConfigModal() {
    loadTeamsConfig();
    document.getElementById('teamsManagerWebhook').value = localTeamsConfig.managerWebhook || '';
    document.getElementById('teamsWebhook_資材課').value = localTeamsConfig.depts['資材課'] || '';
    document.getElementById('teamsWebhook_現場一課').value = localTeamsConfig.depts['現場一課'] || '';
    document.getElementById('teamsWebhook_現場二課').value = localTeamsConfig.depts['現場二課'] || '';
    document.getElementById('teamsWebhook_回收處理課').value = localTeamsConfig.depts['回收處理課'] || '';
    document.getElementById('teamsEnableRealSend').checked = !!localTeamsConfig.enableRealSend;
    document.getElementById('teamsConfigModal').style.display = 'flex';
  }

  function closeTeamsConfigModal() {
    document.getElementById('teamsConfigModal').style.display = 'none';
  }

  function closeTeamsCardModal() {
    document.getElementById('teamsCardModal').style.display = 'none';
  }

  // 顯示 Teams 訊息卡片預覽
  function showTeamsPreviewModal(targetDept, cardData) {
    const channelTag = document.getElementById('teamsPreviewChannelTag');
    channelTag.innerHTML = `📢 訊息分流目標：<b>【品管主管頻道】</b> + <b>【${targetDept}頻道】</b> <span style="margin-left:auto; font-size:0.75rem; color:#6b7280;">(其他課室完全不受干擾)</span>`;

    const bar = document.getElementById('teamsPreviewBar');
    bar.className = 'teams-card-bar ' + (cardData.color || 'green');

    document.getElementById('teamsPreviewTitle').innerText = cardData.title;
    document.getElementById('teamsPreviewSubtitle').innerText = cardData.subtitle;

    const factsContainer = document.getElementById('teamsPreviewFacts');
    factsContainer.innerHTML = cardData.facts.map(f => `
      <div class="teams-fact-row">
        <div class="teams-fact-name">${f.name}</div>
        <div class="teams-fact-value">${f.value}</div>
      </div>
    `).join('');

    document.getElementById('teamsCardModal').style.display = 'flex';
  }

  // 本機執行 Teams 發送或彈出卡片預覽
  function dispatchTeamsCard(targetDept, cardPayload, previewData) {
    loadTeamsConfig();
    
    // 如果有設定真實 Webhook 且開啟發送
    if (localTeamsConfig.enableRealSend) {
      const urls = [];
      if (localTeamsConfig.managerWebhook) urls.push(localTeamsConfig.managerWebhook);
      if (localTeamsConfig.depts[targetDept]) urls.push(localTeamsConfig.depts[targetDept]);

      urls.forEach(url => {
        try {
          fetch(url, {
            method: 'POST',
            mode: 'no-cors',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(cardPayload)
          }).then(() => console.log('Teams POST dispatched:', url));
        } catch(e) {
          console.warn('Teams fetch error:', e);
        }
      });
      showToast(`📢 Teams 卡片已推播至【主管頻道】+【${targetDept}頻道】！`);
    }

    // 無論是否真實發送，都在本機跳出卡片預覽，讓測試人員一目了然！
    showTeamsPreviewModal(targetDept, previewData);
  }

  // 測試模擬卡片
  function testTeamsPreviewCard() {
    const dummyData = {
      title: "✅【QC 檢驗完成 - 判定合格放行】",
      subtitle: "檢驗結果已判定，請一部一課進行後續作業",
      color: "green",
      facts: [
        { name: "🏢 送樣單位", value: "一部一課（送樣人：陳明哲）" },
        { name: "🧪 檢驗品名", value: "IPAUPS" },
        { name: "🛢️ 槽號 / 車牌", value: "TK624 / PPCU7019228" },
        { name: "📋 檢驗單號", value: "ESXM101-20260901013" },
        { name: "🎯 判定結果", value: "PASS (合格放行)" },
        { name: "📝 判定備註", value: "水分與金屬離子檢驗合規" },
        { name: "⏱️ 完成時間", value: new Date().toLocaleString() }
      ]
    };
    closeTeamsConfigModal();
    showTeamsPreviewModal("一部一課", dummyData);
  }

  // 本機測試：一鍵注入一筆 2.5 小時前的超時樣品
  function injectOverdueTestSample() {
    const twoAndHalfHoursAgo = new Date(Date.now() - 2.5 * 60 * 60 * 1000).toISOString();
    const testSample = {
      id: "sample-overdue-" + Date.now(),
      barcode: "ESXM101-超時測試單",
      flowType: "出貨",
      grade: "UPS",
      productName: "IPAUPS",
      tankNo: "TK605",
      customer: "PPCU7020018",
      quantity: "5000 KG",
      dept: "一部一課",
      requester: "王大同",
      status: "pending",
      createdAt: twoAndHalfHoursAgo,
      isAlerted: false
    };

    allData.unshift(testSample);
    if (!IS_GAS) {
      localStorage.setItem('HS_QC_SAMPLES', JSON.stringify(allData));
    }
    render();
    showToast("⚠️ 已注入等候 2.5 小時的測試樣品！看板已呈現紅字警報。");
  }

  // 本機測試：手動觸發 2 小時巡檢警報
  function triggerOverdueCheckLocal() {
    const overdueList = allData.filter(s => {
      if (s.status !== 'pending' || !s.createdAt) return false;
      const diffMs = Date.now() - new Date(s.createdAt).getTime();
      return diffMs >= (2 * 60 * 60 * 1000);
    });

    if (overdueList.length === 0) {
      alert("目前沒有等候超過 2 小時的待驗樣品！\n\n您可以先點擊「⏱️ 注入逾期樣品 (>2小時)」進行模擬。");
      return;
    }

    const target = overdueList[0];
    const diffHours = ((Date.now() - new Date(target.createdAt).getTime()) / (1000 * 60 * 60)).toFixed(1);

    const overdueCardPayload = {
      "@type": "MessageCard",
      "@context": "http://schema.org/extensions",
      "themeColor": "D9381E",
      "summary": `🚨【QC 檢驗超時警報】${target.productName} 等候已達 ${diffHours} 小時`,
      "sections": [{
        "activityTitle": `🚨【QC 檢驗超時警報】等候已達 ${diffHours} 小時`,
        "activitySubtitle": `樣品檢驗已逾 2 小時未判定，請品管與 ${target.dept} 儘速處理`,
        "facts": [
          { "name": "🏢 送樣單位", "value": `${target.dept}（送樣人：${target.requester || '無'}）` },
          { "name": "🧪 檢驗品名", "value": target.productName },
          { "name": "🛢️ 槽號 / 車牌", "value": `${target.tankNo || '-'} / ${target.customer || '-'}` },
          { "name": "📋 單號編號", "value": target.barcode },
          { "name": "⏰ 送樣時間", "value": formatSimpleDate(target.createdAt) }
        ],
        "markdown": true
      }]
    };

    const previewData = {
      title: `🚨【QC 檢驗超時警報】等候已達 ${diffHours} 小時`,
      subtitle: `樣品檢驗已逾 2 小時未判定，請品管與 ${target.dept} 儘速處理`,
      color: "red",
      facts: [
        { name: "🏢 送樣單位", value: `${target.dept}（送樣人：${target.requester || '無'}）` },
        { name: "🧪 檢驗品名", value: target.productName },
        { name: "🛢️ 槽號 / 車牌", value: `${target.tankNo || '-'} / ${target.customer || '-'}` },
        { name: "📋 單號編號", value: target.barcode },
        { name: "⏰ 送樣時間", value: formatSimpleDate(target.createdAt) }
      ]
    };

    dispatchTeamsCard(target.dept, overdueCardPayload, previewData);
  }

  // 檢查某筆排程是否已在看板/系統中送樣過 (支援單號比對與槽號+車櫃比對)
  function getOrderSubmissionInfo(order) {
    if (!allData || allData.length === 0 || !order) return null;
    
    // 1. 單號精準比對 (最優先且最精確)
    if (order.doc_no && String(order.doc_no).trim()) {
      const targetDoc = String(order.doc_no).trim().toLowerCase();
      const matchDoc = allData.find(s => s.barcode && String(s.barcode).toLowerCase().includes(targetDoc));
      if (matchDoc) return matchDoc;
    }
    
    // 2. 槽號 + 品名 + 客戶/車號/櫃號比對 (針對無單號或預先充填送樣)
    const matchDetails = allData.find(s => {
      const sameProd = order.productName && s.productName && (String(s.productName).trim().toLowerCase() === String(order.productName).trim().toLowerCase());
      if (!sameProd) return false;

      // 若同一台車每天都來，僅憑槽號或車號會重複判定為「已送樣」。因此必須比對「排程日期」是否與「送樣日期」吻合
      if (order.date && s.createdAt) {
        const sampleDateStr = getLocalDateString(new Date(s.createdAt));
        if (sampleDateStr !== order.date) return false;
      }

      let tankMatch = false;
      let contMatch = false;
      let hasTankData = order.tankNo && s.tankNo;
      let hasContData = order.container && s.customer;

      if (hasTankData) {
        tankMatch = String(s.tankNo).trim().toLowerCase() === String(order.tankNo).trim().toLowerCase();
      }
      if (hasContData) {
        contMatch = String(s.customer).trim().toLowerCase().includes(String(order.container).trim().toLowerCase()) ||
                    String(order.container).trim().toLowerCase().includes(String(s.customer).trim().toLowerCase());
      }

      if (hasTankData && hasContData) return tankMatch && contMatch;
      if (hasTankData) return tankMatch;
      if (hasContData) return contMatch;
      return false;
    });
    return matchDetails || null;
  }

  // 切換 T100 篩選模式 ('today': 今日排程, 'date': 指定日期, 'pending': 待送樣放櫃, 'all': 全部)
  function setT100FilterMode(mode) {
    t100FilterMode = mode;
    const todayStr = getLocalDateString();
    const dateInput = document.getElementById('t100DateFilter');
    
    if (mode === 'today' && dateInput) {
      dateInput.value = todayStr;
    }
    
    // 更新按鈕 active 狀態
    const btnToday = document.getElementById('btnFilterToday');
    const btnPending = document.getElementById('btnFilterPending');
    const btnAll = document.getElementById('btnFilterAll');
    if (btnToday) btnToday.className = 'btn-t100-filter' + (mode === 'today' ? ' active' : '');
    if (btnPending) btnPending.className = 'btn-t100-filter' + (mode === 'pending' ? ' active' : '');
    if (btnAll) btnAll.className = 'btn-t100-filter' + (mode === 'all' ? ' active' : '');
    const btnYesterday = document.getElementById('btnFilterYesterday');
    if (btnYesterday) btnYesterday.className = 'btn-t100-filter' + (mode === 'yesterday' ? ' active' : '');
    const btnResample = document.getElementById('btnFilterResample');
    if (btnResample) btnResample.className = 'btn-t100-filter' + (mode === 'resample' ? ' active' : '');
    
    renderT100Dropdown();
  }

  // 更新 T100 篩選按鈕上的數量徽章
  function updateT100ButtonCounts() {
    if (!t100Orders || !Array.isArray(t100Orders)) return;
    const todayStr = getLocalDateString();

    // 今日排程數量
    const todayCount = t100Orders.filter(o => o.date === todayStr).length;
    const btnToday = document.getElementById('btnFilterToday');
    if (btnToday) btnToday.innerHTML = `📅 今日排程 <span style="background:rgba(255,255,255,0.35);border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">${todayCount}</span>`;

    // 昨天排程數量
    const yesterday = new Date(); yesterday.setDate(yesterday.getDate() - 1);
    const yesterdayStr = getLocalDateString(yesterday);
    const yesterdayCount = t100Orders.filter(o => o.date === yesterdayStr).length;
    const btnYest = document.getElementById('btnFilterYesterday');
    if (btnYest) btnYest.innerHTML = `📆 昨天排程 <span style="background:rgba(255,255,255,0.35);border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">${yesterdayCount}</span>`;

    // 待送樣放櫃數量（未送或退回件）
    const pendingCount = t100Orders.filter(o => {
      const sub = getOrderSubmissionInfo(o);
      if (!sub) return true;
      if (sub.status === 'failed') return true;
      if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) return true;
      return false;
    }).length;
    const btnPending = document.getElementById('btnFilterPending');
    if (btnPending) btnPending.innerHTML = `📦 待送樣放櫃 <span style="background:rgba(255,255,255,0.35);border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">${pendingCount}</span>`;

    // 取樣重送數量 - 直接從 t100Orders 的送樣狀態計算（不依賴 render() 的局部變數）
    const resampleCount = (!t100Orders || !Array.isArray(t100Orders)) ? 0 : t100Orders.filter(o => {
      const sub = getOrderSubmissionInfo(o);
      return sub && (sub.status === 'failed' || (sub.status === 'pending' && (parseInt(sub.round || 1) > 1 || sub.parentId)));
    }).length;
    const btnResample = document.getElementById('btnFilterResample');
    if (btnResample) {
      const badge = resampleCount > 0
        ? `<span style="background:#dc2626;color:white;border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">${resampleCount}</span>`
        : `<span style="background:rgba(255,255,255,0.35);border-radius:10px;padding:1px 7px;font-size:0.8em;margin-left:3px;">0</span>`;
      btnResample.innerHTML = `🔄 取樣重送 ${badge}`;
    }
  }

  // 日期選取器變更事件
  function onT100DateFilterChange(val) {
    if (!val) return;
    t100FilterMode = 'date';
    const btnToday = document.getElementById('btnFilterToday');
    const btnPending = document.getElementById('btnFilterPending');
    const btnAll = document.getElementById('btnFilterAll');
    if (btnToday) btnToday.className = 'btn-t100-filter' + (val === getLocalDateString() ? ' active' : '');
    if (btnPending) btnPending.className = 'btn-t100-filter';
    if (btnAll) btnAll.className = 'btn-t100-filter';
    renderT100Dropdown();
  }

  // 初始化與動態渲染 T100 下拉選單（依日期過濾、標記已送樣/待送樣）
  function renderT100Dropdown() {
    const sel = document.getElementById('t100Select');
    if (!sel) return;

    const todayStr = getLocalDateString();
    const dateInput = document.getElementById('t100DateFilter');
    if (dateInput && !dateInput.value) {
      dateInput.value = todayStr;
    }
    const selectedDate = (dateInput && dateInput.value) ? dateInput.value : todayStr;

    // 依模式過濾出符合條件的排程
    let filteredOrders = [];
    let filterDescription = '';

    if (t100FilterMode === 'today') {
      filteredOrders = t100Orders.filter(o => o.date === todayStr);
      filterDescription = `今日 (${todayStr})`;
    } else if (t100FilterMode === 'yesterday') {
      const yesterday = new Date(); yesterday.setDate(yesterday.getDate() - 1);
      const yStr = getLocalDateString(yesterday);
      filteredOrders = t100Orders.filter(o => o.date === yStr);
      filterDescription = `昨日 (${yStr})`;
    } else if (t100FilterMode === 'date') {
      filteredOrders = t100Orders.filter(o => o.date === selectedDate);
      filterDescription = `${selectedDate}`;
    } else if (t100FilterMode === 'pending') {
      filteredOrders = t100Orders.filter(o => {
        const sub = getOrderSubmissionInfo(o);
        if (!sub) return true;
        if (sub.status === 'failed') return true;
        if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) return true;
        return false;
      });
      filterDescription = `待送樣放櫃/排程`;
    } else if (t100FilterMode === 'resample') {
      // 品質不合格重取 / 需特採 - 從 t100Orders 的送樣狀態計算（不依賴 render() 局部變數）
      filteredOrders = t100Orders.filter(o => {
        const sub = getOrderSubmissionInfo(o);
        return sub && (sub.status === 'failed' || (sub.status === 'pending' && (parseInt(sub.round || 1) > 1 || sub.parentId)));
      });
      filterDescription = '品質不合格重取 / 需特採';
    } else if (t100FilterMode === 'all') {
      filteredOrders = [...t100Orders];
      filterDescription = `全部匯入排程`;
    }

    // 計算狀態統計
    const totalCount = t100Orders.length;
    const submittedInTotal = t100Orders.filter(o => getOrderSubmissionInfo(o)).length;
    const submittedInView = filteredOrders.filter(o => getOrderSubmissionInfo(o)).length;
    const pendingInView = filteredOrders.length - submittedInView;

    const pendingInTotal = totalCount - submittedInTotal;
    const statsBadge = document.getElementById('t100StatsBadge');
    if (statsBadge) {
      if (t100FilterMode === 'today') {
        statsBadge.innerHTML = `今日排程: <b>${filteredOrders.length}</b> 車 (✅已送: ${submittedInView} | ⏳待送: ${pendingInView}) · 系統尚有 ${pendingInTotal} 車未送樣`;
      } else if (t100FilterMode === 'pending') {
        statsBadge.innerHTML = `📦 待送樣放櫃: <b>${filteredOrders.length}</b> 車未送樣 (已完成 ${submittedInTotal} 車)`;
      } else {
        statsBadge.innerHTML = `${filterDescription}: <b>${filteredOrders.length}</b> 車 (✅已送: ${submittedInView} | ⏳待送: ${pendingInView})`;
      }
    }

    let html = '';
    const outOrders = filteredOrders.filter(o => o.flowType === '出貨');
    const inOrders = filteredOrders.filter(o => o.flowType === '進料');

    if (filteredOrders.length === 0) {
      if (t100FilterMode === 'today') {
        const hintText = pendingInTotal > 0 ? `系統內還有 ${pendingInTotal} 筆待送樣車次，可點擊「待送樣放櫃」查詢` : '所有排程皆已完成送樣';
        html += `<option value="">-- 📅 今日 (${todayStr}) 尚無排程 (${hintText}) --</option>`;
      } else if (t100FilterMode === 'pending') {
        html += `<option value="">-- 🎉 太棒了！所有放櫃與排程車次皆已完成送樣 --</option>`;
      } else {
        const hintText = pendingInTotal > 0 ? `尚有 ${pendingInTotal} 筆待送樣，可點擊「待送樣放櫃」查詢` : '所有排程皆已完成送樣';
        html += `<option value="">-- 📅 日期 [${selectedDate}] 無排程 (${hintText}) --</option>`;
      }
    } else {
      html += `<option value="">-- 點此選擇 ${filterDescription} (共 ${filteredOrders.length} 車次：${outOrders.length} 出貨 + ${inOrders.length} 進料) --</option>`;

      if (outOrders.length > 0) {
        html += `<optgroup label="🚚 【出貨槽車排程】(${outOrders.length} 車次)">`;
        outOrders.forEach(o => {
          const globalIdx = t100Orders.indexOf(o);
          const sub = getOrderSubmissionInfo(o);
          let mark = '⏳[待送樣] ';
          if (sub) {
            if (sub.status === 'completed') mark = '✅[已驗合格] ';
            else if (sub.status === 'failed' && sub.qcResult === '需特採') mark = '⚠️[不符內控需特採] ';
            else if (sub.status === 'failed') mark = '⛔[品質不合格重取] ';
            else if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) mark = '🔄[已自動重送待驗] ';
            else mark = '✅[已送樣待驗] ';
          }
          
          let dtStr = o.date || '';
          if (o.time && o.time !== '排程') {
            dtStr = dtStr ? `${dtStr} ${o.time}` : o.time;
          } else if (o.time === '排程') {
            dtStr = dtStr ? `${dtStr} 排程` : '排程';
          }
          const dtBadge = dtStr ? `[${dtStr}] ` : '';

          const tankBadge = o.tankNo ? ` [槽:${o.tankNo}]` : '';
          const boxBadge = o.container ? ` [車/櫃:${o.container}]` : '';
          html += `<option value="${globalIdx}">${mark}${dtBadge}${o.doc_no} | ${o.productName}${tankBadge}${boxBadge} (${o.customer} ${o.quantity})</option>`;
        });
        html += `</optgroup>`;
      }

      if (inOrders.length > 0) {
        html += `<optgroup label="📥 【進料/入庫槽車排程】(${inOrders.length} 車次)">`;
        inOrders.forEach(o => {
          const globalIdx = t100Orders.indexOf(o);
          const sub = getOrderSubmissionInfo(o);
          let mark = '⏳[待送樣] ';
          if (sub) {
            if (sub.status === 'completed') mark = '✅[已驗合格] ';
            else if (sub.status === 'failed') mark = '⛔[品質不合格重取] ';
            else mark = '✅[已送樣待驗] ';
          }
          
          let dtStr = o.date || '';
          if (o.time && o.time !== '排程') {
            dtStr = dtStr ? `${dtStr} ${o.time}` : o.time;
          } else if (o.time === '排程') {
            dtStr = dtStr ? `${dtStr} 排程` : '排程';
          }
          const dtBadge = dtStr ? `[${dtStr}] ` : '';

          const tankBadge = o.tankNo ? ` [槽:${o.tankNo}]` : '';
          const boxBadge = o.container ? ` [車:${o.container}]` : '';
          html += `<option value="${globalIdx}">${mark}${dtBadge}${o.doc_no} | ${o.productName}${tankBadge}${boxBadge} (${o.customer} ${o.quantity})</option>`;
        });
        html += `</optgroup>`;
      }
    }

    sel.innerHTML = html;
  }

  // 當使用者在下拉選單選取某車次時，自動帶入表單並偵測重複送樣
  function onT100SelectChange(val) {
    const alertBox = document.getElementById('t100AlreadySubmittedAlert');
    const alertText = document.getElementById('t100AlertText');

    if (val === "") {
      if (alertBox) alertBox.style.display = 'none';
      return;
    }
    const item = t100Orders[parseInt(val)];
    if (!item) return;

    
    // 自動尋找同車次的進出貨單 (同車牌/同動向)
    let combinedDocs = item.doc_no || '';
    if (item.container && item.container.trim() !== '' && item.flowType === '進料') {
        const sameTruckItems = t100Orders.filter(o => o !== item && o.container === item.container && o.flowType === item.flowType);
        if (sameTruckItems.length > 0) {
            const extraDocs = sameTruckItems.map(o => o.doc_no).filter(Boolean);
            if (extraDocs.length > 0) {
                const combined = [item.doc_no, ...extraDocs].join(', ');
                if (confirm(`發現此車次 (${item.container}) 共有 ${extraDocs.length + 1} 筆排程單號：\n${combined}\n\n是否要自動合併成同一張檢驗單？`)) {
                    combinedDocs = combined;
                }
            }
        }
    }

    document.getElementById('barcode').value = combinedDocs;

    document.getElementById('flowType').value = item.flowType || '出貨';
    document.getElementById('grade').value = item.grade || '工業級';
    document.getElementById('productName').value = item.productName || '';
    autoSelectGrade(item.productName);
    document.getElementById('tankNo').value = item.tankNo || '';
    document.getElementById('customer').value = item.container || item.customer || '';
    document.getElementById('quantity').value = item.quantity || '';

    // 檢查該訂單是否已送過樣
    const sub = getOrderSubmissionInfo(item);
    if (sub && alertBox && alertText) {
      alertBox.style.display = 'flex';
      const timeStr = formatSimpleDate(sub.createdAt);
      const statusDesc = (sub.status === 'completed') ? '已完成檢驗 (放行)' : '檢驗中 (等候結果)';
      alertText.innerHTML = `<strong>⚠️ 重複送樣警示：</strong>此車次單號 <code>${item.doc_no}</code> 已於 <strong>${timeStr}</strong> 提交送樣！目前狀態為 <strong>【${statusDesc}】</strong>。<br>若此車次需重新抽樣或進行二次複驗，請確認後再提交。`;
      showToast(`⚠️ 注意：此車次已於 ${timeStr} 送樣過 (${statusDesc})！`, 4500);
    } else if (alertBox) {
      alertBox.style.display = 'none';
      showToast(`✅ 已自動帶入 [${item.flowType}] 排程：${item.productName} (${item.container || item.tankNo})`);
    }

    document.getElementById('requester').focus();
  }

  // 前端即時解析上傳的 Excel（智慧自動搜尋「槽車」分頁，並支援多重備援分頁自動掃描）
  function handleExcelUpload(e) {
    const file = e.target.files[0];
    if(!file) return;

    showToast("正在解析 Excel 槽車分頁(出貨與進料)...");
    const reader = new FileReader();
    reader.onload = function(evt) {
      try {
        const data = new Uint8Array(evt.target.result);
        const workbook = XLSX.read(data, { type: 'array', cellDates: true });

        // 核心單一工作表解析器
        function parseSheet(sheetName) {
          const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
          const ignoredConfig = cfgStr ? JSON.parse(cfgStr)['T100_IGNORE_PRODUCTS'] : 'IPAHQ';
          const ignoredList = (ignoredConfig || 'IPAHQ').split(',').map(s => s.trim().toUpperCase());

          const worksheet = workbook.Sheets[sheetName];
          if (!worksheet) return [];
          const rows = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
          if (!rows || rows.length < 4) return [];

          let currentMode = null;
          let colMap = {};
          const parsedOrders = [];
          let lastOutDate = '';
          let lastInDate = '';

          function parseCellDate(v) {
            if(!v) return '';
            if(v instanceof Date && !isNaN(v.getTime())) {
              const y = v.getFullYear();
              const m = String(v.getMonth() + 1).padStart(2, '0');
              const d = String(v.getDate()).padStart(2, '0');
              return `${y}-${m}-${d}`;
            }
            const s = String(v).trim();
            const match = s.match(/(202\d)[-/.](\d{1,2})[-/.](\d{1,2})/);
            if(match) {
              return `${match[1]}-${match[2].padStart(2, '0')}-${match[3].padStart(2, '0')}`;
            }
            return '';
          }

          for(let r = 0; r < rows.length; r++) {
            const row = rows[r];
            if(!row || row.length === 0) continue;

            const rowStr = row.map(v => String(v || '')).join(' ');
            if(rowStr.includes('出貨通知單') || rowStr.includes('出通單')) {
              currentMode = '出貨';
              colMap = {};
              for(let c = 0; c < row.length; c++) {
                const h = String(row[c] || '').trim();
                if(h) colMap[h] = c;
              }
              continue;
            } else if(rowStr.includes('入庫單') || rowStr.includes('進貨單')) {
              currentMode = '進料';
              colMap = {};
              for(let c = 0; c < row.length; c++) {
                const h = String(row[c] || '').trim();
                if(h) colMap[h] = c;
              }
              continue;
            }

            if(!currentMode || Object.keys(colMap).length === 0) continue;

            const gv = (keys) => {
              if(typeof keys === 'string') keys = [keys];
              for(const k of keys) {
                if(colMap[k] !== undefined && row[colMap[k]] !== undefined && row[colMap[k]] !== null) {
                  return row[colMap[k]];
                }
              }
              return '';
            };

            if(currentMode === '出貨') {
              const docNo = gv(['出貨通知單', '出通單', '出貨單']);
              const prod = gv(['品名', '物料名稱']);
              if(!docNo || !prod) continue;
              if(ignoredList.includes(String(prod).trim().toUpperCase())) continue;

              // 嚴格只從「預計出貨日期」欄位抓取，若為合併儲存格向下繼承！
              const rawDate = gv(['預計出貨日期', '預計出貨日', '出貨日期', '出貨日', '預計到貨日期']);
              const cellDate = parseCellDate(rawDate);
              if(cellDate) {
                lastOutDate = cellDate;
              }

              const timeStr = gv(['預計出貨時間', '出貨時間']);
              const tank = gv(['儲位名稱', '出貨槽號', '槽號', '儲位', '槽別', '槽别']);
              const cust = gv(['交易對象簡稱', '客戶名稱', '客戶', '送貨地址簡稱']);
              const truck = gv(['出通單單頭.車牌號碼', '車牌號碼', '車牌號碼(磅)', '車牌', '車號']);
              const qty = gv(['換算數量', '預計出貨數量(KG)', '出貨數量(KG)', '數量']);
              const spec = gv(['規格說明', '規格']);
              const note = gv(['注意事項', '備註']);

              let container = String(truck || '').trim();
              if(!container && note) {
                const m = String(note).match(/槽號[:：]?\s*([A-Za-z0-9\-]+)/);
                if(m) container = m[1];
                else {
                  const m2 = String(note).match(/提貨槽車\s*([A-Za-z0-9\-]+)/);
                  if(m2) container = m2[1];
                }
              }

              let grade = '工業級';
              if(String(prod).toUpperCase().includes('UPS')) grade = 'UPS';
              else if(String(prod).toUpperCase().includes('IF')) grade = 'IF';

              let orderDate = lastOutDate;
              if(!orderDate && docNo) {
                const mDoc = String(docNo).match(/(202\d)([01]\d)([0-3]\d)/);
                if(mDoc) orderDate = `${mDoc[1]}-${mDoc[2]}-${mDoc[3]}`;
              }

              parsedOrders.push({
                doc_no: String(docNo).trim(),
                date: orderDate || getLocalDateString(),
                time: String(timeStr || '').trim(),
                flowType: '出貨',
                grade: grade,
                productName: String(prod).trim(),
                tankNo: String(tank || '').trim(),
                customer: String(cust || '').trim(),
                container: container ? container : String(cust || '').trim(),
                quantity: qty ? `${qty} KG` : String(spec || '').trim(),
                note: String(note || '').trim()
              });
            } else if(currentMode === '進料') {
              const docNo = gv(['入庫單', '進貨單', '入庫單號', '進貨單號']);
              const prod = gv(['品名', '物料名稱']);
              if(!docNo || !prod) continue;
              if(ignoredList.includes(String(prod).trim().toUpperCase())) continue;

              // 嚴格只從「預計進貨日」欄位抓取，若為合併儲存格向下繼承！絕對不讀取「單據日期」與「採購單號」！
              const rawDate = gv(['預計進貨日', '預計進貨日期', '預計到貨日期', '進貨日', '進貨日期']);
              const cellDate = parseCellDate(rawDate);
              if(cellDate) {
                lastInDate = cellDate;
              }

              const timeStr = gv(['預計進貨時間', '進貨時間', '預計到貨時間']);
              const tank = gv(['槽别', '槽別', '儲位', '儲位名稱', '槽號']);
              const spec = gv(['規格', '規格說明']);
              const vendor = gv(['供應商簡稱', '廠商簡稱', '供應商', '交易對象簡稱', '廠商']);
              const origin = gv(['出貨廠別(廠商)', '出貨廠別(備用)', '廠別', '來源廠別', '出貨廠別']);
              const truck = gv(['車牌號碼', '車號', '車號/櫃號', '車牌/櫃號', '車牌', '出通單單頭.車牌號碼']);
              const box = gv(['櫃號', '貨櫃號碼', '貨櫃編號']);
              const qty = gv(['預計進貨數量(KG)', '進貨數量(KG)', '預計進貨數量', '換算數量', '數量']);
              const note = gv(['備註', '注意事項']);

              let container = String(truck || '').trim();
              if(box && String(box).trim()) {
                container = container ? `${container} (櫃:${box})` : String(box).trim();
              }

              const custStr = (vendor && origin) ? `${vendor} (${origin})` : (origin || vendor || '');

              let grade = '工業級';
              if(String(prod).toUpperCase().includes('UPS')) grade = 'UPS';
              else if(String(prod).toUpperCase().includes('IF')) grade = 'IF';

              let orderDate = lastInDate;
              if(!orderDate && docNo) {
                const mDoc = String(docNo).match(/(202\d)([01]\d)([0-3]\d)/);
                if(mDoc) orderDate = `${mDoc[1]}-${mDoc[2]}-${mDoc[3]}`;
              }

              parsedOrders.push({
                doc_no: String(docNo).trim(),
                date: orderDate || getLocalDateString(),
                time: String(timeStr || '').trim(),
                flowType: '進料',
                grade: grade,
                productName: String(prod).trim(),
                tankNo: String(tank || '').trim(),
                customer: custStr.trim(),
                container: container ? container : custStr.trim(),
                quantity: qty ? `${qty} KG` : String(spec || '').trim(),
                note: String(note || '').trim()
              });
            }
          }
          return parsedOrders;
        }

        // 1. 優先鎖定含「槽車」之分頁
        let targetSheetName = workbook.SheetNames.find(n => n.includes('槽車'));
        let finalOrders = [];
        let actualSheetUsed = '';

        if (targetSheetName) {
          finalOrders = parseSheet(targetSheetName);
          if (finalOrders.length > 0) actualSheetUsed = targetSheetName;
        }

        // 2. 若「槽車」分頁未找到或解析出 0 筆，自動遍歷其餘所有分頁進行備援解析
        if (finalOrders.length === 0) {
          for(const sName of workbook.SheetNames) {
            if(sName === targetSheetName) continue;
            const res = parseSheet(sName);
            if(res.length > 0) {
              finalOrders = res;
              actualSheetUsed = sName;
              break;
            }
          }
        }

        if(finalOrders.length === 0) {
          alert(`⚠️ 未能自此試算表解析出任何有效的槽車排程！\n\n已檢查的活頁簿分頁：\n${workbook.SheetNames.map((s, idx) => `  [${idx+1}] ${s}`).join('\n')}\n\n請確認分頁內是否含有「出貨通知單」或「入庫單」之資料列。`);
          return;
        }

        t100Orders = finalOrders;
        localStorage.setItem('HS_QC_T100_ORDERS', JSON.stringify(t100Orders));

        // 自動同步日期過濾器
        const todayStr = getLocalDateString();
        const hasToday = finalOrders.some(o => o.date === todayStr);
        const dateInput = document.getElementById('t100DateFilter');
        if(hasToday) {
          setT100FilterMode('today');
        } else {
          const dates = [...new Set(finalOrders.map(o => o.date).filter(Boolean))].sort();
          const targetDate = dates.length ? dates[dates.length - 1] : todayStr;
          if(dateInput) dateInput.value = targetDate;
          setT100FilterMode('date');
        }

        const outCount = finalOrders.filter(o => o.flowType === '出貨').length;
        const inCount = finalOrders.filter(o => o.flowType === '進料').length;
        showToast(`🎉 成功鎖定「${actualSheetUsed}」分頁，匯入 ${finalOrders.length} 筆槽車排程 (${outCount} 出貨 + ${inCount} 進料)！`, 5000);

        // ☁️ 雲端同步：將排程上傳至 Google Sheets（若已設定 GAS API）
        uploadOrdersToCloud(finalOrders);
      } catch(err) {
        console.error(err);
        alert("解析 Excel 失敗：" + err.message);
      }
    };
    reader.readAsArrayBuffer(file);
  }
  // ☁️ 排程上傳：匯入 Excel 後自動同步至 Google Sheets（覆蓋模式）
  async function uploadOrdersToCloud(orders) {
    if (!GAS_API_URL) return; // 未設定 GAS 則略過
    showToast('⬆️ 正在將排程同步至雲端...', 3000);
    try {
      const resp = await fetch(GAS_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({ action: 'saveOrders', orders: orders })
      });
      const result = await resp.json();
      if (result.success) {
        showToast(`☁️ 雲端同步完成！共 ${result.count} 筆排程已上傳 (${result.importedAt})`, 6000);
      } else {
        showToast(`⚠️ 雲端同步失敗：${result.error || '未知錯誤'}（資料已保存於本機）`, 6000);
      }
    } catch(err) {
      console.warn('雲端排程上傳失敗（僅影響跨裝置同步）：', err);
      showToast('⚠️ 雲端連線逾時，排程僅保存於本機', 4000);
    }
  }

  // ☁️ 排程下載：頁面載入時從 Google Sheets 拉取排程（供所有設備共用）
  async function loadOrdersFromCloud() {
    if (!GAS_API_URL) return; // 未設定 GAS 則略過
    try {
      const resp = await fetch(`${GAS_API_URL}?action=getOrders`);
      const result = await resp.json();
      if (result.success && Array.isArray(result.orders)) {
        // 合併：以雲端為主（覆蓋 localStorage），但保留 localStorage 若雲端為空
        t100Orders = result.orders;
        localStorage.setItem('HS_QC_T100_ORDERS', JSON.stringify(t100Orders));
        renderT100Dropdown();
        const outCount = result.orders.filter(o => o.flowType === '出貨').length;
        const inCount = result.orders.filter(o => o.flowType === '進料').length;
        showToast(`☁️ 已從雲端載入 ${result.count} 筆排程 (${outCount} 出貨 + ${inCount} 進料)`, 5000);
        // 自動過濾今天
        const todayStr = getLocalDateString();
        const hasToday = t100Orders.some(o => o.date === todayStr);
        if (hasToday) setT100FilterMode('today');
      }
    } catch(err) {
      console.info('雲端排程讀取失敗（使用本機快取）：', err);
    }
  }

  function getFlowTag(type) {
    if(type === '進料') return `<span class="tag-flow tag-in">進料</span>`;
    if(type === '出貨') return `<span class="tag-flow tag-out">出貨</span>`;
    if(type === '補料') return `<span class="tag-flow tag-replenish">補料</span>`;
    if(type === '委託') return `<span class="tag-flow tag-commission">委託</span>`;
    return `<span class="tag-flow tag-in">${type || '-'}</span>`;
  }

  function formatSimpleDate(isoString) {
    if(!isoString) return '-';
    const d = new Date(isoString);
    if(isNaN(d.getTime())) return isoString;
    const pad = n => n.toString().padStart(2, '0');
    return `${pad(d.getMonth()+1)}/${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  }

  // 計算等候時間並產生紅/藍狀態徽章

  function skipSample() {
    let barcode = document.getElementById('barcode').value.trim();
    const productName = document.getElementById('productName').value.trim();
    const tankNo = document.getElementById('tankNo').value.trim();
    const customer = document.getElementById('customer').value.trim();
    const requester = document.getElementById('requester').value.trim();
    const dept = document.getElementById('dept').value;
    const remark = document.getElementById('remark')?.value?.trim() || '';

    if (!productName || !tankNo || !customer || !requester) {
      alert("⚠️ 請先將上方的基本資料填妥！");
      return; 
    }

    if (!barcode) {
      const todayStr = new Date().toISOString().split('T')[0].replace(/-/g, '');
      barcode = `${todayStr}-庫存`;
    }

    if(!confirm("確定要將此筆排程標記為「免送樣」直接結案嗎？\n(結案後將不會出現在待檢驗清單)")) return;

    const btn = document.getElementById('skipBtn'); 
    btn.disabled = true; 
    btn.innerText = "寫入結案紀錄中...";
    
    const payload = { 
      id: 'ID-' + Date.now(),
      barcode: barcode, 
      flowType: document.getElementById('flowType').value, 
      grade: document.getElementById('grade').value,
      productName: productName, 
      tankNo: tankNo, 
      customer: customer, 
      quantity: document.getElementById('quantity').value, 
      dept: dept, 
      requester: requester,
      remark: remark,
      status: 'completed',
      qcResult: '免送樣',
      qcNote: '預先充填出貨，免送樣結案',
      qcApprover: '系統自動',
      createdAt: new Date().toISOString(),
      completedAt: new Date(new Date().getTime() + 8*60*60*1000).toISOString().replace('T', ' ').substring(0, 19)
    };

    fetch(GAS_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ action: 'createSample', payload: payload })
    })
    .then(res => res.json())
    .then(res => {
      resetForm();
      btn.disabled = false;
      btn.innerText = "直接結案 (免送樣)";
      if(res.success) {
        showToast("✅ 免送樣結案成功！已從排程中移除。");
        load();
      } else {
        alert("失敗：" + res.error);
      }
    })
    .catch(err => {
      btn.disabled = false;
      btn.innerText = "直接結案 (免送樣)";
      alert("雲端連線失敗：" + err.message);
    });
  }

  function getWaitTimeBadge(createdAt) {
    if(!createdAt) return '-';
    const createdTime = new Date(createdAt).getTime();
    if(isNaN(createdTime)) return '-';

    const diffMs = Date.now() - createdTime;
    const diffHours = (diffMs / (1000 * 60 * 60)).toFixed(1);

    if (diffMs >= (2 * 60 * 60 * 1000)) {
      return `<div class="badge-overdue">⚠️ 等候 ${diffHours} 小時 (逾期)</div>`;
    }
    return `<div class="badge-ontime">⏱️ 等候 ${diffHours} 小時</div>`;
  }

  // 動態套用雲端/本機自訂下拉選單選項 (動向、等級、品名)
  function applyDynamicDropdownOptions(cfg) {
    if(!cfg) return;

    function parseCommaSeparated(str) {
      if (!str) return [];
      return str.split(',').map(s => s.trim()).filter(s => s);
    }

    const flowTypes = parseCommaSeparated(cfg.OPTIONS_FLOW_TYPES || cfg.flowTypes);
    const grades = parseCommaSeparated(cfg.OPTIONS_GRADES || cfg.grades);
    const products = parseCommaSeparated(cfg.OPTIONS_PRODUCTS || cfg.products);
    const depts = parseCommaSeparated(cfg.OPTIONS_DEPTS || cfg.depts);

    // 1. 動態填充「動向」
    if(flowTypes.length) {
      const selFlow = document.getElementById('flowType');
      if(selFlow) {
        selFlow.innerHTML = flowTypes.map(f => `<option value="${f}">${f}</option>`).join('');
        }
    }

    // 2. 動態填充「等級」
    if(grades.length) {
      const selGrade = document.getElementById('grade');
      if(selGrade) {
        selGrade.innerHTML = grades.map(g => `<option value="${g}">${g}</option>`).join('');
        }
    }

    // 3. 動態填充「品名」datalist
    if(products.length) {
      const dl = document.getElementById('productList');
      if(dl) {
        dl.innerHTML = products.map(p => `<option value="${p}">`).join('');
      }
    }

    // 4. 動態填充「送樣單位」
    if(depts.length) {
      const selDept = document.getElementById('dept');
      if(selDept) {
        selDept.innerHTML = depts.map(d => `<option value="${d}">${d}</option>`).join('');
        }
    }
  }

  function getLocalDynamicOptions() {
    const raw = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
    if(raw) {
      try { return JSON.parse(raw); } catch(e){}
    }
    return {
      flowTypes: ['出貨', '進料', '補料', '委託'],
      grades: ['工業級', 'UPS', 'IF'],
      depts: ['資材課', '二部一課', '二部二課', '一部一課', '一部二課'],
      products: [
        'IPA', 'IPAUPS', 'IPAHQ', 'CPNE3(T)', 'CPNE4', 'CPN-P1R',
        'EBR', 'EBR-P1R', 'NBAC', 'NBAC-P1R', 'CPN', 'EG',
        'NMP', 'GAA', 'ACT', 'PM', 'PMA98', 'heavy-R',
        'DPM', 'DPM-B1', 'SEP73', 'Anone', 'GBL', 'PG', 'EBRR'
      ]
    };
  }

  // 雙模數據載入（GAS 模式 / Cloudflare Pages PWA API 連線 / 離線快取模式）
  function load() {
    loadTeamsConfig();
    if(IS_GAS) {
      document.getElementById('envBadge').innerText = "☁️ GAS 雲端連線中";
      google.script.run.withSuccessHandler(data => { allData = data; render(); }).getSamples();
      google.script.run.withSuccessHandler(cfg => {
        if(cfg) {
          applyDynamicDropdownOptions(cfg);
          localStorage.setItem('HS_QC_DYNAMIC_OPTIONS', JSON.stringify(cfg));
            if(cfg.QC_PIN) localStorage.setItem('HS_QC_ADMIN_PIN', cfg.QC_PIN);
          if(cfg.pin) localStorage.setItem('HS_QC_ADMIN_PIN', cfg.pin);
        }
      }).getSystemConfig();
      google.script.run.withSuccessHandler(res => {
        if (res && res.success && res.data) {
          localStorage.setItem('HS_QC_EMP_MAP', JSON.stringify(res.data));
        }
      }).getEmployeesFromSheet();
    } else if (GAS_API_URL) {
      document.getElementById('envBadge').innerText = "☁️ 雲端 API 同步中";
      // 1. 抓取試算表樣品
      fetch(`${GAS_API_URL}?action=getSamples&_t=${Date.now()}`, { cache: "no-store" })
        .then(res => res.json())
        .then(data => {
          // 相容舊版中文狀態
          data.forEach(s => {
            if (s.status === "待檢驗") s.status = "pending";
            else if (s.status === "已檢驗") s.status = "completed";
            else if (s.status === "退件" || s.status === "重取樣") s.status = "failed";
          });
          allData = data;
          localStorage.setItem('HS_QC_SAMPLES', JSON.stringify(allData));
          render();
        })
        .catch(err => {
          console.warn("API 取得樣品失敗，使用離線資料", err);
          document.getElementById('envBadge').innerText = "💻 離線模式";
          const stored = localStorage.getItem('HS_QC_SAMPLES');
          if(stored) { try { allData = JSON.parse(stored); } catch(e){} }
          render();
        });

      // 2. 抓取試算表系統配置 (選單與 PIN 碼)
      fetch(`${GAS_API_URL}?action=getConfig&_t=${Date.now()}`, { cache: "no-store" })
        .then(res => res.json())
        .then(cfg => {
          if(cfg) {
            applyDynamicDropdownOptions(cfg);
            localStorage.setItem('HS_QC_DYNAMIC_OPTIONS', JSON.stringify(cfg));
            if(cfg.QC_PIN) localStorage.setItem('HS_QC_ADMIN_PIN', cfg.QC_PIN);
            if(cfg.pin) localStorage.setItem('HS_QC_ADMIN_PIN', cfg.pin);
          }
        })
        .catch(err => {
          console.warn("API 取得選單失敗，使用快取", err);
          applyDynamicDropdownOptions(getLocalDynamicOptions());
        });

      // 3. 從 Google Sheets 載入排程（供所有設備共享下拉選單）
      loadOrdersFromCloud();

      // 4. 抓取雲端員工名單
      fetch(`${GAS_API_URL}?action=getEmployees&_t=${Date.now()}`, { cache: "no-store" })
        .then(res => res.json())
        .then(res => {
          if (res && res.success && res.data) {
            let empDict = {};
            if (Array.isArray(res.data)) {
              res.data.forEach(r => { if (r.emp_id) empDict[r.emp_id] = r.name; });
            } else {
              empDict = res.data;
            }
            localStorage.setItem('HS_QC_EMP_MAP', JSON.stringify(empDict));
          }
        })
        .catch(err => console.warn("API 取得員工名單失敗", err));

    } else {
      document.getElementById('envBadge').innerText = "💻 獨立 PWA 運作模式";
      applyDynamicDropdownOptions(getLocalDynamicOptions());
      const stored = localStorage.getItem('HS_QC_SAMPLES');
      if(stored) {
        try { allData = JSON.parse(stored); } catch(e) { allData = []; }
      } else {
        allData = [
          { id: "sample-1", barcode: "ESXM101-20260901013", flowType: "出貨", grade: "UPS", productName: "IPAUPS", tankNo: "TK624", customer: "PPCU7019228", quantity: "5000 KG", dept: "資材課", requester: "陳明哲", status: "pending", createdAt: new Date(Date.now() - 2.5 * 3600 * 1000).toISOString() },
          { id: "sample-2", barcode: "ESPM411-20260906001", flowType: "進料", grade: "工業級", productName: "EBR-P1R", tankNo: "TKC05", customer: "KEQ-3506 (櫃:6108)", quantity: "8000 KG", dept: "回收處理課", requester: "張建國", status: "pending", createdAt: new Date(Date.now() - 45 * 60 * 1000).toISOString() },
          { id: "sample-3", barcode: "ESXM101-20260901020", flowType: "出貨", grade: "UPS", productName: "IPAUPS", tankNo: "TK605", customer: "PPCU7020018", quantity: "5000 KG", dept: "一部一課", requester: "林大為", status: "completed", qcResult: "PASS", qcNote: "品質合格放行", createdAt: new Date(Date.now()-3600000).toISOString(), completedAt: new Date().toISOString() }
        ];
        localStorage.setItem('HS_QC_SAMPLES', JSON.stringify(allData));
      }
      render();
    }
  }

  function render() {
    const loggedInUser = sessionStorage.getItem('QC_LOGGED_IN_USER');
    const kw = (document.getElementById('kwInput').value || '').toLowerCase();
    const start = document.getElementById('dateStart').value;
    const end = document.getElementById('dateEnd').value;
    const pHead = document.querySelector("#table-pending thead");
    const cHead = document.querySelector("#table-completed thead");
    const pBody = document.querySelector("#table-pending tbody");
    const cBody = document.querySelector("#table-completed tbody");
    const isAdaptive = (localStorage.getItem('HS_QC_TABLE_MODE') || 'adaptive') === 'adaptive';

    const filtered = allData.filter(s => {
      const matchKw = String(s.barcode || '').toLowerCase().includes(kw) || 
                      String(s.productName || '').toLowerCase().includes(kw) || 
                      String(s.tankNo || '').toLowerCase().includes(kw) ||
                      String(s.customer || '').toLowerCase().includes(kw) ||
                      String(s.dept || '').toLowerCase().includes(kw);
      const sDate = s.createdAt ? new Date(s.createdAt).toISOString().split('T')[0] : '';
      const matchDate = (!start || sDate >= start) && (!end || sDate <= end);
      return matchKw && matchDate;
    });

    const pData = filtered.filter(s => s.status === 'pending');
    let cData = filtered.filter(s => s.status === 'completed' || s.status === 'failed');
    updateT100ButtonCounts();

    // 如果使用者沒有輸入明確的起迄日期，則「已檢驗完成」預設只顯示近3天 (今天、昨天、前天)
    if (!start && !end) {
      const d = new Date();
      d.setDate(d.getDate() - 2); // 往前推2天 = 包含今天共3天
      const minDateStr = d.toISOString().split('T')[0];
      cData = cData.filter(s => {
        if (s.qcResult === 'FAIL') return true; // FAIL 案件不隱藏，保留以供特採評估
        const sDate = s.createdAt ? new Date(s.createdAt).toISOString().split('T')[0] : '';
        return sDate >= minDateStr;
      });
    }

    // 計算逾期件數
    const overdueCount = pData.filter(s => {
      if (!s.createdAt) return false;
      return (Date.now() - new Date(s.createdAt).getTime()) >= (2 * 60 * 60 * 1000);
    }).length;

    document.getElementById('kpi-pending').innerText = pData.length;
    document.getElementById('kpi-overdue').innerText = overdueCount;
    document.getElementById('kpi-completed').innerText = cData.length;
    document.getElementById('pendingCountBadge').innerText = `${pData.length} 件 (逾期 ${overdueCount})`;
    document.getElementById('completedCountBadge').innerText = `${cData.length} 件`;
    const tabP = document.getElementById('tabCountPending');
    if(tabP) tabP.innerText = `${pData.length} (逾期 ${overdueCount})`;
    const tabC = document.getElementById('tabCountCompleted');
    if(tabC) tabC.innerText = `${cData.length}`;

    const todayStr = new Date().toISOString().split('T')[0];
    document.getElementById('kpi-today').innerText = allData.filter(s => s.createdAt && s.createdAt.startsWith(todayStr)).length;

    // 動態切換表頭 Thead
    if (isAdaptive) {
      if (pHead) {
        pHead.innerHTML = `<tr>
          <th style="width: 30%;">品項 / 單號</th>
          <th style="width: 23%;">槽號 / 車牌</th>
          <th style="width: 28%;">送樣單位 / 等候時長</th>
          <th style="width: 19%; text-align:center;">操作</th>
        </tr>`;
      }
      if (cHead) {
        cHead.innerHTML = `<tr>
          <th style="width: 30%;">品項 / 單號</th>
          <th style="width: 23%;">槽號 / 車牌</th>
          <th style="width: 26%;">送樣單位 / 判定</th>
          <th style="width: 21%;">判定備註</th>
        </tr>`;
      }

      // 自適應 4 欄內容（零水平捲軸）
      pBody.innerHTML = pData.length ? pData.map(s => `<tr style="${(parseInt(s.round)||1) >= 2 ? 'background:#fff7ed;' : ''}">
        <td>
          <div style="display:flex; align-items:center; gap:4px; flex-wrap:wrap; margin-bottom:2px;">
            <b style="font-size:0.88rem; color:#0f172a;">${s.productName}</b>
            ${getFlowTag(s.flowType)}
            <span style="font-size:0.72rem; font-weight:bold; color:#1e40af; background:#eff6ff; padding:1px 4px; border-radius:3px;">${s.grade || '-'}</span>
            ${(parseInt(s.round)||1) >= 2 ? `<span style="font-size:0.72rem; font-weight:bold; color:#ea580c; background:#fed7aa; padding:1px 6px; border-radius:10px;">⚠️ 第${s.round}次送樣</span>` : ''}
          </div>
          <div style="font-size:0.75rem; color:#64748b; font-family:monospace; word-break:break-all;">單: <b>${s.barcode}</b></div>
        </td>
        <td>
          <div style="margin-bottom:2px;">
            <span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:0.78rem;">${s.tankNo || '-'}</span>
          </div>
          <div style="font-size:0.76rem; color:#334155; word-break:break-all;">車: <b>${s.customer || '-'}</b></div>
        </td>
        <td>
          <div style="font-weight:600; color:#1e293b; font-size:0.8rem; margin-bottom:2px;">
            ${s.dept} ${s.requester ? `<span style="font-size:0.72rem; color:#64748b;">(${s.requester})</span>` : ''}
          </div>
          <div style="font-size:0.72rem; color:#64748b;">${formatSimpleDate(s.createdAt)}</div>
          <div style="margin-top:2px;">${getWaitTimeBadge(s.createdAt)}</div>
        </td>
        <td style="text-align:center;">
          <div style="display:flex; flex-direction:column; gap:4px; align-items:center;">
            <button class="btn-action btn-print" onclick="printLabelById('${s.id}')" style="width:100%; padding:4px 0; font-size:0.75rem; margin:0;">列印</button>
            <button class="btn-action btn-judge" onclick="openJudge('${s.id}')" style="width:100%; padding:4px 0; font-size:0.75rem; margin:0;">判定</button>
          </div>
        </td>
      </tr>`).join('') : `<tr><td colspan="4" style="text-align:center; color:#94a3b8; padding:30px;">目前無待檢驗樣品</td></tr>`;
      console.log('pData:', pData);
      console.log('pBody.innerHTML length:', pBody.innerHTML.length);
      console.log('pData:', pData);
      console.log('pBody.innerHTML length:', pBody.innerHTML.length);

      cBody.innerHTML = cData.length ? cData.slice(0, 30).map(s => `<tr>
        <td>
          <div style="display:flex; align-items:center; gap:4px; flex-wrap:wrap; margin-bottom:2px;">
            <b style="font-size:0.88rem; color:#0f172a;">${s.productName}</b>
            ${getFlowTag(s.flowType)}
            <span style="font-size:0.72rem; font-weight:bold; color:#1e40af; background:#eff6ff; padding:1px 4px; border-radius:3px;">${s.grade || '-'}</span>
            ${(parseInt(s.round)||1) >= 2 ? `<span style="font-size:0.72rem; font-weight:bold; color:#ea580c; background:#fed7aa; padding:1px 6px; border-radius:10px;">第${s.round}次</span>` : ''}
          </div>
          <div style="font-size:0.75rem; color:#64748b; font-family:monospace; word-break:break-all;">單: <b>${s.barcode}</b></div>
        </td>
        <td>
          <div style="margin-bottom:2px;">
            <span style="background:#f1f5f9; color:#475569; padding:2px 6px; border-radius:4px; font-weight:bold; font-size:0.78rem;">${s.tankNo || '-'}</span>
          </div>
          <div style="font-size:0.76rem; color:#334155; word-break:break-all;">車: <b>${s.customer || '-'}</b></div>
        </td>
        <td>
          <div style="display:flex; align-items:center; gap:4px; margin-bottom:2px; flex-wrap:wrap;">
            <span style="font-weight:600; color:#1e293b; font-size:0.8rem;">${s.dept || '-'}</span>
            <b style="color:${s.qcResult==='PASS'?'#059669':(s.qcResult==='特採'?'#7c3aed':(s.qcResult==='需特採'?'#d97706':'#dc2626'))}; background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':(s.qcResult==='需特採'?'#fef3c7':'#fee2e2'))}; padding:1px 5px; border-radius:4px; font-size:0.74rem;">${s.qcResult}</b>
          </div>
          <div style="font-size:0.72rem; color:#64748b;">完成: ${formatSimpleDate(s.completedAt)}</div>
        </td>
        <td>
          <div style="font-size:0.76rem; color:#475569; line-height:1.3; max-height:36px; overflow-y:auto; word-break:break-word; margin-bottom:4px;">
            ${s.qcNote || '<span style="color:#94a3b8;">無備註</span>'}
          </div>
          ${s.qcResult === '需特採' ? `<button onclick="openJudge('${s.id}')" style="font-size:0.7rem; background:#8b5cf6; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%; margin-top:3px; animation: pulse 2s infinite;">🚨 主管審核特採</button>` : ''}
          ${s.qcResult === 'FAIL' ? `<div style="font-size:0.7rem; color:#b91c1c; font-weight:bold; background:#fee2e2; padding:3px; border-radius:4px; text-align:center;">已自動產生重送單</div>` : ''}
          ${(s.parentId || s.round > 1) ? `<button onclick="showSampleHistory('${s.parentId || s.id}')" style="font-size:0.7rem; background:#e0f2fe; color:#0369a1; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%; margin-top:3px;">📋 查看送樣歷史</button>` : ''}
        </td>
      </tr>`).join('') : `<tr><td colspan="4" style="text-align:center; color:#94a3b8; padding:30px;">尚無檢驗完成紀錄</td></tr>`;
    } else {
      // 傳統完整九欄展開模式
      if (pHead) {
        pHead.innerHTML = `<tr>
          <th>單號</th>
          <th>動向</th>
          <th>等級</th>
          <th>品名</th>
          <th>槽號</th>
          <th>車牌/櫃號</th>
          <th>送樣單位</th>
          <th>送樣時間 / 等候時長</th>
          <th class="col-action">操作</th>
        </tr>`;
      }
      if (cHead) {
        cHead.innerHTML = `<tr>
          <th>單號</th>
          <th>動向</th>
          <th>等級</th>
          <th>品名</th>
          <th>槽號</th>
          <th>車牌/櫃號</th>
          <th>送樣單位</th>
          <th>判定結果</th>
          <th>完成時間</th>
          <th>判定備註</th>
        </tr>`;
      }

      pBody.innerHTML = pData.length ? pData.map(s => `<tr style="${(parseInt(s.round)||1) >= 2 ? 'background:#fff7ed;' : ''}">
        <td><b>${s.barcode}</b>${(parseInt(s.round)||1) >= 2 ? ` <span style="font-size:0.7rem;font-weight:bold;color:#ea580c;background:#fed7aa;padding:1px 5px;border-radius:8px;">第${s.round}次</span>` : ''}</td>
        <td>${getFlowTag(s.flowType)}</td>
        <td><span style="font-weight:bold; color:#1e40af;">${s.grade || '-'}</span></td>
        <td><b>${s.productName}</b></td>
        <td><span style="background:#e0f2fe; color:#0369a1; padding:2px 6px; border-radius:4px; font-weight:bold;">${s.tankNo || '-'}</span></td>
        <td>${s.customer || '-'}</td>
        <td><span style="font-weight:bold; color:#475569;">${s.dept}</span></td>
        <td>
          <div style="color:#64748b; font-size:0.8rem; font-weight:bold;">${formatSimpleDate(s.createdAt)}</div>
          <div style="margin-top:3px;">${getWaitTimeBadge(s.createdAt)}</div>
        </td>
        <td class="col-action" style="white-space: nowrap; text-align:center;">
          <button class="btn-action btn-print" onclick="printLabelById('${s.id}')">列印</button>
          <button class="btn-action btn-judge" onclick="openJudge('${s.id}')">判定</button>
        </td>
      </tr>`).join('') : `<tr><td colspan="9" style="text-align:center; color:#94a3b8; padding:30px;">目前無待檢驗樣品</td></tr>`;
      
      cBody.innerHTML = cData.length ? cData.slice(0, 30).map(s => `<tr>
        <td><b>${s.barcode}</b>${(parseInt(s.round)||1) >= 2 ? ` <span style="font-size:0.7rem;font-weight:bold;color:#ea580c;background:#fed7aa;padding:1px 5px;border-radius:8px;">第${s.round}次</span>` : ''}</td>
        <td>${getFlowTag(s.flowType)}</td>
        <td><b>${s.grade || '-'}</b></td>
        <td><b>${s.productName}</b></td>
        <td>${s.tankNo || '-'}</td>
        <td>${s.customer || '-'}</td>
        <td><span style="font-weight:600; color:#475569;">${s.dept || '-'}</span></td>
        <td><b style="color:${s.qcResult==='PASS'?'#059669':'#dc2626'}; background:${s.qcResult==='PASS'?'#d1fae5':'#fee2e2'}; padding:3px 8px; border-radius:4px;">${s.qcResult}</b></td>
        <td style="color:#4b5563;">${formatSimpleDate(s.completedAt)}</td>
        <td style="font-size:0.8rem; color:#64748b;">
          ${s.qcNote || '-'}
          ${s.qcResult === '需特採' ? `<br><button onclick="openJudge('${s.id}')" style="font-size:0.7rem; background:#8b5cf6; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;">🚨 審核特採</button>` : ''}
            ${s.qcResult === 'FAIL' ? `<br><div style="font-size:0.7rem; color:#b91c1c; font-weight:bold;">已自動重送</div>` : ''}
          ${(s.parentId || s.round > 1) ? `<br><button onclick="showSampleHistory('${s.parentId || s.id}')" style="font-size:0.7rem; background:#e0f2fe; color:#0369a1; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:2px;">📋 送樣歷史</button>` : ''}
        </td>
      </tr>`).join('') : `<tr><td colspan="10" style="text-align:center; color:#94a3b8; padding:30px;">尚無檢驗完成紀錄</td></tr>`;
    }

    // 當樣品列表更新時，同步刷新 T100 排程選單的送樣狀態記號
    renderT100Dropdown();
  }

  function resetFilters() {
    document.getElementById('kwInput').value = '';
    document.getElementById('dateStart').value = '';
    document.getElementById('dateEnd').value = '';
    render();
  }

  function resetForm() {
    document.getElementById('qcForm').reset();
    document.getElementById('t100Select').value = '';
    const alertBox = document.getElementById('t100AlreadySubmittedAlert');
    if (alertBox) alertBox.style.display = 'none';
    const empId = document.getElementById('empIdInput');
    if (empId) empId.value = '';
    const empMsg = document.getElementById('empLookupMsg');
    if (empMsg) empMsg.innerText = '';
    setBarcodePlaceholder();
  }

  // =========================================================
  // 工號查詢模組：掃描或輸入工號自動帶出姓名
  // =========================================================

  function getEmployeeMap() {
    try {
      return JSON.parse(localStorage.getItem('HS_QC_EMP_MAP') || '{}');
    } catch(e) { return {}; }
  }

  function lookupEmployeeId(empId) {
    const id = String(empId || '').trim();
    const msg = document.getElementById('empLookupMsg');
    const nameInput = document.getElementById('requester');
    if (!id) { if (msg) msg.innerText = ''; return; }
    const map = getEmployeeMap();
    if (map[id]) {
      nameInput.value = map[id];
      if (msg) { msg.innerText = `✅ ${id} → ${map[id]}`; msg.style.color = '#059669'; }
    } else {
      if (msg) { msg.innerText = `⚠️ 未找到工號 ${id}，請直接在姓名欄輸入`; msg.style.color = '#d97706'; }
    }
  }

  function openEmpMapModal() {
    const map = getEmployeeMap();
    const lines = Object.entries(map).map(([k,v]) => `${k}:${v}`).join('\n');
    document.getElementById('empMapTextarea').value = lines;
    document.getElementById('empMapModal').style.display = 'flex';
  }

  function closeEmpMapModal() {
    document.getElementById('empMapModal').style.display = 'none';
  }

  function saveEmpMap() {
    const raw = document.getElementById('empMapTextarea').value;
    const map = {};
    raw.split('\n').forEach(line => {
      const [id, ...rest] = line.split(':');
      if (id && rest.length) map[id.trim()] = rest.join(':').trim();
    });
    localStorage.setItem('HS_QC_EMP_MAP', JSON.stringify(map));
    closeEmpMapModal();
    showToast(`✅ 已儲存 ${Object.keys(map).length} 筆員工資料！`);
  }

  function submitForm() {
    let barcode = document.getElementById('barcode').value.trim();
    const productName = document.getElementById('productName').value.trim();
    const tankNo = document.getElementById('tankNo').value.trim();
    const customer = document.getElementById('customer').value.trim();
    const requester = document.getElementById('requester').value.trim();
    const dept = document.getElementById('dept').value;
    const remark = document.getElementById('remark')?.value?.trim() || '';

    if (!productName || !tankNo || !customer || !requester) {
      alert("⚠️ 提交失敗！\n\n「品名、進出貨槽號、車牌/櫃號、送樣人員」皆為必填項目，請確認填妥後再送出。");
      return; 
    }

    if (!barcode) {
      const todayStr = new Date().toISOString().split('T')[0].replace(/-/g, '');
      barcode = `${todayStr}-庫存`;
    }

    const btn = document.getElementById('submitBtn'); 
    btn.disabled = true; 
    btn.innerText = "寫入送樣紀錄中...";
    
    const payload = { 
      id: 'ID-' + Date.now(),
      barcode: barcode, 
      flowType: document.getElementById('flowType').value, 
      grade: document.getElementById('grade').value,
      productName: productName, 
      tankNo: tankNo, 
      customer: customer, 
      quantity: document.getElementById('quantity').value, 
      dept: dept, 
      requester: requester,
      remark: remark,
      status: 'pending',
      createdAt: new Date().toISOString()
    };

    if(IS_GAS) {


      google.script.run.withSuccessHandler(() => { 
        resetForm();
        btn.disabled = false; 
        btn.innerText = "確認提交送樣 🚀"; 
        showToast("✅ 送樣成功已寫入 Google 試算表！");
        load(); 
      }).createSample(payload);
    } else if(GAS_API_URL) {
      fetch(GAS_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({ action: 'createSample', payload: payload })
      })
      .then(res => res.json())
      .then(res => {
        resetForm();
        btn.disabled = false;
        btn.innerText = "確認提交送樣 🚀";
        if(res.success) {
          showToast("✅ 送樣成功已即時寫入 Google 試算表！");
          load();
        } else {
          alert("送樣失敗：" + (res.error || "未知錯誤"));
        }
      })
      .catch(err => {
        console.warn("API 送樣異常，暫存本機", err);
        allData.unshift(payload);
        localStorage.setItem('HS_QC_SAMPLES', JSON.stringify(allData));
        resetForm();
        btn.disabled = false;
        btn.innerText = "確認提交送樣 🚀";
        showToast("⚠️ 雲端連線失敗，已先暫存於本機！");
        render();
      });
    } else {
      setTimeout(() => {
        allData.unshift(payload);
        localStorage.setItem('HS_QC_SAMPLES', JSON.stringify(allData));
        resetForm();
        btn.disabled = false; 
        btn.innerText = "確認提交送樣 🚀"; 
        showToast("✅ 送樣成功（本機/離線紀錄已更新）！");
        render();
      }, 300);
    }
  }

  function printLabelById(id) { 
    const targetData = allData.find(d => d.id === id); 
    if(!targetData) return;

    // 若曾記住偏好設定，直接快速列印 (水分/GC 1張 + Metal 2張)
    const remember = localStorage.getItem('HS_QC_REMEMBER_PRINT');
    if(remember === 'true') {
      const wQty = parseInt(localStorage.getItem('HS_QC_PRINT_WATER') || '1', 10);
      let mQty = parseInt(localStorage.getItem('HS_QC_PRINT_METAL') || '2', 10);
      if (targetData.grade === '回收液') mQty = 0;
      const rotateMode = localStorage.getItem('HS_QC_PRINT_ROTATE') || 'none';
      doPrintLabels(targetData, wQty, mQty, rotateMode);
      return;
    }

    openPrintModal(targetData);
  }

  // 工具箱點擊：隨時開啟設定修改貼紙規格或張數
  function openPrintSettingsGlobal() {
    const dummy = allData[0] || {
      id: "dummy",
      barcode: "ESXM101-設定預覽單",
      productName: "IPAUPS",
      grade: "UPS",
      tankNo: "TK624",
      customer: "PPCU7019228",
      flowType: "出貨",
      quantity: "5000 KG",
      dept: "資材課",
      requester: "品管測試員",
      createdAt: new Date().toISOString()
    };
    openPrintModal(dummy);
  }

  function openPrintModal(data) {
    document.getElementById('printTargetId').value = data.id;
    document.getElementById('printPreviewBarcode').innerText = data.barcode;
    document.getElementById('printPreviewProduct').innerText = data.productName + ' (' + (data.grade || '-') + ')';
    document.getElementById('printPreviewTank').innerText = data.tankNo || '-';
    document.getElementById('printPreviewTruck').innerText = data.customer || '-';
    document.getElementById('printPreviewDept').innerText = data.dept;
    document.getElementById('printPreviewRequester').innerText = data.requester;

    const savedW = localStorage.getItem('HS_QC_PRINT_WATER') || '1';
    let savedM = localStorage.getItem('HS_QC_PRINT_METAL') || '2';
    const savedWidth = localStorage.getItem('HS_QC_PRINT_WIDTH') || '90';
    const savedHeight = localStorage.getItem('HS_QC_PRINT_HEIGHT') || '50';
    const savedFix = localStorage.getItem('HS_QC_PRINT_FIX') === 'true';
    const savedRotateMode = localStorage.getItem('HS_QC_PRINT_ROTATE') || 'none';

    if (data.grade === '回收液') savedM = '0';

    document.getElementById('printQtyWaterGC').value = savedW;
    document.getElementById('printQtyMetal').value = savedM;
    document.getElementById('printLabelWidth').value = savedWidth;
    document.getElementById('printLabelHeight').value = savedHeight;
    if(document.getElementById('printFixOrientation')) document.getElementById('printFixOrientation').checked = savedFix;
    if(document.getElementById('printRotateMode')) document.getElementById('printRotateMode').value = savedRotateMode;
    document.getElementById('rememberPrintSettings').checked = (localStorage.getItem('HS_QC_REMEMBER_PRINT') === 'true');

    updateTotalLabelCount();
    
    // 切換按鈕顯示狀態：如果是純設定模式 (dummy)，則顯示「儲存設定」，隱藏「送出列印」
    if (data.id === "dummy") {
      document.getElementById('btnPrintLabels').style.display = 'none';
      document.getElementById('btnSavePrintSettingsOnly').style.display = 'block';
    } else {
      document.getElementById('btnPrintLabels').style.display = 'block';
      document.getElementById('btnSavePrintSettingsOnly').style.display = 'none';
    }

    document.getElementById('printModal').style.display = 'flex';
  }

  function savePrintSettingsOnly() {
    const wQty = document.getElementById('printQtyWaterGC').value;
    const mQty = document.getElementById('printQtyMetal').value;
    const width = document.getElementById('printLabelWidth').value;
    const height = document.getElementById('printLabelHeight').value;
    const rotateMode = document.getElementById('printRotateMode') ? document.getElementById('printRotateMode').value : 'none';
    
    localStorage.setItem('HS_QC_PRINT_WATER', wQty);
    localStorage.setItem('HS_QC_PRINT_METAL', mQty);
    localStorage.setItem('HS_QC_PRINT_WIDTH', width);
    localStorage.setItem('HS_QC_PRINT_HEIGHT', height);
    if(document.getElementById('printFixOrientation')) localStorage.setItem('HS_QC_PRINT_FIX', document.getElementById('printFixOrientation').checked);
    localStorage.setItem('HS_QC_PRINT_ROTATE', rotateMode);

    if(document.getElementById('rememberPrintSettings').checked) {
      localStorage.setItem('HS_QC_REMEMBER_PRINT', 'true');
    } else {
      localStorage.removeItem('HS_QC_REMEMBER_PRINT');
    }
    closePrintModal();
    showToast("✅ 列印設定已更新");
  }

  function closePrintModal() {
    document.getElementById('printModal').style.display = 'none';
  }

  function updateTotalLabelCount() {
    const w = parseInt(document.getElementById('printQtyWaterGC').value || '0', 10);
    const m = parseInt(document.getElementById('printQtyMetal').value || '0', 10);
    const width = parseInt(document.getElementById('printLabelWidth').value || '90', 10);
    const height = parseInt(document.getElementById('printLabelHeight').value || '50', 10);
    const total = w + m;
    document.getElementById('printTotalLabelCount').innerText = `${total} 張 (${width}mm × ${height}mm)`;
  }

  function resetPrintSettingsToDefault() {
    localStorage.removeItem('HS_QC_REMEMBER_PRINT');
    localStorage.removeItem('HS_QC_PRINT_WATER');
    localStorage.removeItem('HS_QC_PRINT_METAL');
    localStorage.removeItem('HS_QC_PRINT_WIDTH');
    localStorage.removeItem('HS_QC_PRINT_HEIGHT');
    localStorage.removeItem('HS_QC_PRINT_FIX');
    localStorage.removeItem('HS_QC_PRINT_ROTATE');
    if(document.getElementById('printFixOrientation')) document.getElementById('printFixOrientation').checked = false;
    if(document.getElementById('printRotateMode')) document.getElementById('printRotateMode').value = 'none';
    document.getElementById('printQtyWaterGC').value = '1';
    document.getElementById('printQtyMetal').value = '2';
    document.getElementById('printLabelWidth').value = '90';
    document.getElementById('printLabelHeight').value = '50';
    document.getElementById('rememberPrintSettings').checked = false;
    updateTotalLabelCount();
    showToast("🔄 已恢復預設規格：90mm × 50mm，水分/GC 1張 + Metal 2張！");
  }

  function confirmPrintLabels() {
    const id = document.getElementById('printTargetId').value;
    const targetData = allData.find(d => d.id === id);
    if(!targetData) return;

    const wQty = parseInt(document.getElementById('printQtyWaterGC').value || '0', 10);
    const mQty = parseInt(document.getElementById('printQtyMetal').value || '0', 10);
    const width = parseInt(document.getElementById('printLabelWidth').value || '90', 10);
    const height = parseInt(document.getElementById('printLabelHeight').value || '50', 10);

    if(wQty + mQty <= 0) {
      alert("請至少選擇列印 1 張標籤！");
      return;
    }

    const rotateMode = document.getElementById('printRotateMode') ? document.getElementById('printRotateMode').value : 'none';
    localStorage.setItem('HS_QC_PRINT_WATER', String(wQty));
    localStorage.setItem('HS_QC_PRINT_METAL', String(mQty));
    localStorage.setItem('HS_QC_PRINT_WIDTH', String(width));
    localStorage.setItem('HS_QC_PRINT_HEIGHT', String(height));
    localStorage.setItem('HS_QC_PRINT_ROTATE', rotateMode);

    if(document.getElementById('rememberPrintSettings').checked) {
      localStorage.setItem('HS_QC_REMEMBER_PRINT', 'true');
    } else {
      localStorage.removeItem('HS_QC_REMEMBER_PRINT');
    }

    closePrintModal();
    doPrintLabels(targetData, wQty, mQty, rotateMode);
  }

  // 讀取並正規化標籤尺寸。TSC 直式標籤以「窄寬 × 長高」送紙，避免只旋轉畫面而沒有同步旋轉紙張尺寸。
  function getPrintDimensions(rotateMode = 'none') {
    const configuredWidth = parseInt(localStorage.getItem('HS_QC_PRINT_WIDTH') || '90', 10);
    const configuredHeight = parseInt(localStorage.getItem('HS_QC_PRINT_HEIGHT') || '50', 10);
    const labelWidth = (Number.isFinite(configuredWidth) && configuredWidth > 0) ? configuredWidth : 90;
    const labelHeight = (Number.isFinite(configuredHeight) && configuredHeight > 0) ? configuredHeight : 50;

    const fixOrientation = localStorage.getItem('HS_QC_PRINT_FIX') === 'true';
    const needsRotate = rotateMode === '90' || rotateMode === '-90';
    const swapPageAxes = needsRotate || (fixOrientation && labelWidth > labelHeight);

    return {
      labelWidth,
      labelHeight,
      pageWidth: swapPageAxes ? labelHeight : labelWidth,
      pageHeight: swapPageAxes ? labelWidth : labelHeight,
      autoRotate: (fixOrientation && labelWidth > labelHeight && !needsRotate)
    };
  }

  // 標籤機專用連續列印輸出核心 (支援 TSC 直式與自訂貼紙尺寸)
  function doPrintLabels(data, waterCount, metalCount, rotateMode = 'none') {
    const totalLabels = waterCount + metalCount;
    const { labelWidth, labelHeight, pageWidth, pageHeight, autoRotate } = getPrintDimensions(rotateMode);
    let labelPagesHtml = '';
    let currentIdx = 1;

    const isCompact = labelHeight <= 60;
    const compactClass = isCompact ? ' compact' : '';
                const rotationTransform = rotateMode === '90' 
      ? `transform: rotate(90deg) translateY(-100%); transform-origin: top left;` 
      : rotateMode === '-90'
      ? `transform: rotate(-90deg) translateX(-100%); transform-origin: top left;`
      : rotateMode === '180'
      ? `transform: rotate(180deg); transform-origin: center center;`
      : autoRotate
      ? `transform: rotate(90deg) translateY(-100%); transform-origin: top left;`
      : '';
    const orientationClass = '';

    // 1. 水分 & GC 檢驗標籤 (共 waterCount 張)
    for(let i = 1; i <= waterCount; i++) {
      labelPagesHtml += `
        <div class="label-page${compactClass}${orientationClass}">
          <div class="rotatable-container" style="${rotationTransform}">
            <div class="label-border">
              <div class="label-header">
                <div class="corp-title">鴻勝化學品管檢驗中心 (QC LAB)</div>
                <div class="badge-cat water">💧【水分 & GC】檢驗樣品 (${currentIdx}/${totalLabels})</div>
              </div>
              
              <div class="barcode-banner">
                <div class="barcode-num" style="${data.barcode && data.barcode.length > 25 ? 'font-size:10.5px; line-height:1.25; letter-spacing:0;' : ''}">${data.barcode}</div>
              </div>

              <div class="content-wrapper">
                <table class="info-table">
                  <tr><td class="f-name">品名：</td><td class="f-val"><b>${data.productName}</b> <span class="tag-grade">${data.grade || '-'}</span></td></tr>
                  <tr><td class="f-name">儲位：</td><td class="f-val"><span class="tag-tank">${data.tankNo || '-'}</span></td></tr>
                  <tr><td class="f-name">車牌：</td><td class="f-val">${data.customer || '-'}</td></tr>
                  <tr><td class="f-name">數量：</td><td class="f-val">${data.flowType} / ${data.quantity || '-'}</td></tr>
                  <tr><td class="f-name">送樣：</td><td class="f-val">${data.dept} (<b>${data.requester}</b>)</td></tr>
                  <tr><td class="f-name">時間：</td><td class="f-val">${formatSimpleDate(data.createdAt)}</td></tr>
                </table>

                <div class="lab-record-box">
                  <div class="lab-title">🧪 實驗室記錄：</div>
                  <div class="lab-row"><span>• 水分：</span><span class="fill-line">________ ppm</span></div>
                  <div class="lab-row"><span>• GC：</span><span class="fill-line">________ %</span></div>
                  <div class="lab-row sign-row"><span>簽章：____</span><span>日期：______</span></div>
                </div>
              </div>

              <div class="label-footer">
                <span>貼紙: ${labelWidth}x${labelHeight}mm</span>
                <span>頁次: ${currentIdx}/${totalLabels}</span>
              </div>
            </div>
          </div>
        </div>
        </div>
      `;
      currentIdx++;
    }

    // 2. Metal 金屬離子 ICP-MS 標籤 (共 metalCount 張)
    for(let i = 1; i <= metalCount; i++) {
      const isSecondSample = (i >= 2);
      const bottleTitle = isSecondSample ? "瓶 2 (留樣)" : "瓶 1 (正樣)";
      const bottleBadgeClass = isSecondSample ? "metal-retention" : "metal-main";

      labelPagesHtml += `
        <div class="label-page${compactClass}${orientationClass}">
          <div class="rotatable-container" style="${rotationTransform}">
            <div class="label-border">
              <div class="label-header">
                <div class="corp-title">鴻勝化學品管檢驗中心 (QC LAB)</div>
                <div class="badge-cat ${bottleBadgeClass}">🔬【Metal ICP-MS】${bottleTitle} (${currentIdx}/${totalLabels})</div>
              </div>
              
              <div class="barcode-banner">
                <div class="barcode-num" style="${data.barcode && data.barcode.length > 25 ? 'font-size:10.5px; line-height:1.25; letter-spacing:0;' : ''}">${data.barcode}</div>
              </div>

              <div class="content-wrapper">
                <table class="info-table">
                  <tr><td class="f-name">品名：</td><td class="f-val"><b>${data.productName}</b> <span class="tag-grade">${data.grade || '-'}</span></td></tr>
                  <tr><td class="f-name">儲位：</td><td class="f-val"><span class="tag-tank">${data.tankNo || '-'}</span></td></tr>
                  <tr><td class="f-name">車牌：</td><td class="f-val">${data.customer || '-'}</td></tr>
                  <tr><td class="f-name">數量：</td><td class="f-val">${data.flowType} / ${data.quantity || '-'}</td></tr>
                  <tr><td class="f-name">送樣：</td><td class="f-val">${data.dept} (<b>${data.requester}</b>)</td></tr>
                  <tr><td class="f-name">時間：</td><td class="f-val">${formatSimpleDate(data.createdAt)}</td></tr>
                </table>

                <div class="lab-record-box">
                  <div class="lab-title">🔬 ICP-MS 記錄：</div>
                  <div class="lab-row"><span>• 案號：</span><span class="fill-line">____________</span></div>
                  <div class="lab-row type-row"><span>${isSecondSample ? '☑留樣 □複測' : '☑正樣 □急件'}</span></div>
                  <div class="lab-row sign-row"><span>簽章：____</span><span>日期：______</span></div>
                </div>
              </div>

              <div class="label-footer">
                <span>貼紙: ${labelWidth}x${labelHeight}mm</span>
                <span>頁次: ${currentIdx}/${totalLabels}</span>
              </div>
            </div>
          </div>
        </div>
        </div>
      `;
      currentIdx++;
    }

    const printWindow = window.open('', '_blank', 'width=750,height=800');
    printWindow.document.write(`
      <!doctype html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>檢驗送樣標籤 - ${data.barcode}</title>
        <style>
          @page {
            size: ${pageWidth}mm ${pageHeight}mm;
            margin: 0;
          }
          * { box-sizing: border-box; }
          html, body {
            width: ${pageWidth}mm;
            height: ${pageHeight}mm;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Microsoft JhengHei", sans-serif;
            background: #fff;
            color: #000;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .rotatable-container {
            width: ${labelWidth}mm;
            height: ${labelHeight}mm;
            position: absolute;
            left: 0;
            top: 0;
            padding: 2mm;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
          }
          .label-page {
            width: ${pageWidth}mm;
            height: ${pageHeight}mm;
            position: relative;
            page-break-after: always;
            page-break-inside: avoid;
          }
          .label-page:last-child {
            page-break-after: auto;
          }
          
          
          /* 緊湊模式 (高度 <= 60mm) 專用排版 */
          .label-page.compact .rotatable-container {
            padding: 1mm;
          }
          .label-page.compact .label-border {
            padding: 1mm 1.5mm;
          }
          .label-page.compact .corp-title {
            display: none; /* 隱藏公司抬頭 */
          }
          .label-page.compact .badge-cat {
            margin-top: 0;
            padding: 0.5mm;
            font-size: 11px;
          }
          .label-page.compact .barcode-banner {
            margin: 0.5mm 0;
            padding: 0.5mm;
          }
          .label-page.compact .barcode-num {
            font-size: 12px;
          }
          .label-page.compact .content-wrapper {
            display: flex;
            gap: 1.5mm;
            align-items: stretch;
            height: 100%;
            overflow: hidden;
          }
          .label-page.compact .info-table {
            width: 55%;
            margin: 0;
            font-size: 9.5px;
          }
          .label-page.compact .info-table td {
            padding: 0.5mm 0;
          }
          .label-page.compact .f-name {
            width: 9mm; /* 縮短標題寬度 */
          }
          .label-page.compact .lab-record-box {
            width: 45%;
            margin: 0;
            padding: 1mm;
            font-size: 9.5px;
            display: flex;
            flex-direction: column;
            justify-content: space-evenly;
          }
          .label-page.compact .lab-title {
            margin-bottom: 0;
          }
          .label-page.compact .lab-row {
            margin-bottom: 0;
            flex-direction: column; /* 簽章和線條排上下 */
          }
          .label-page.compact .sign-row {
            flex-direction: row; /* 簽章日期排左右 */
            font-size: 8px;
          }
          .label-page.compact .label-footer {
            margin-top: 0.5mm;
            padding-top: 0.5mm;
            font-size: 8px;
          }
          .label-border {
            border: 2.5px solid #000;
            border-radius: 6px;
            height: 100%;
            padding: 2.5mm 3mm;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
          }
          .label-header {
            text-align: center;
            border-bottom: 1.5px solid #000;
            padding-bottom: 2mm;
          }
          .corp-title {
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.5px;
            color: #333;
          }
          .badge-cat {
            margin-top: 1.5mm;
            padding: 2mm 1mm;
            font-size: 13px;
            font-weight: 900;
            color: #fff;
            border-radius: 4px;
            text-align: center;
          }
          .badge-cat.water {
            background: #1e3a8a;
          }
          .badge-cat.metal-main {
            background: #0f172a;
          }
          .badge-cat.metal-retention {
            background: #334155;
          }
          .barcode-banner {
            margin: 1.5mm 0;
            text-align: center;
            background: #f1f5f9;
            border: 1px dashed #475569;
            border-radius: 4px;
            padding: 1mm 2mm;
          }
          .barcode-num {
            font-size: 15px;
            font-weight: 900;
            letter-spacing: 1px;
            color: #000;
          }
          .info-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11.5px;
            margin: 1mm 0;
          }
          .info-table td {
            padding: 1.2mm 0.5mm;
            vertical-align: middle;
            border-bottom: 0.5px solid #e2e8f0;
          }
          .info-table tr:last-child td {
            border-bottom: none;
          }
          .f-name {
            width: 23mm;
            font-weight: 700;
            color: #334155;
            white-space: nowrap;
          }
          .f-val {
            font-weight: 800;
            color: #0f172a;
          }
          .tag-grade {
            background: #dbeafe;
            color: #1e40af;
            font-size: 10px;
            padding: 1px 4px;
            border-radius: 3px;
            margin-left: 2px;
          }
          .tag-tank {
            background: #e0f2fe;
            color: #0369a1;
            padding: 1px 5px;
            border-radius: 3px;
          }
          .lab-record-box {
            border: 1.5px dashed #000;
            border-radius: 4px;
            padding: 1.5mm 2mm;
            background: #fafafa;
            font-size: 10.5px;
            margin: 1mm 0;
          }
          .lab-title {
            font-weight: 900;
            color: #000;
            margin-bottom: 1mm;
          }
          .lab-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 1mm;
          }
          .lab-row:last-child {
            margin-bottom: 0;
          }
          .fill-line {
            font-weight: bold;
            color: #444;
          }
          .label-footer {
            display: flex;
            justify-content: space-between;
            font-size: 9px;
            color: #64748b;
            border-top: 1px solid #cbd5e1;
            padding-top: 1mm;
            margin-top: 0.5mm;
          }
        
    .phrase-tag {
      background: #f1f5f9;
      color: #475569;
      padding: 4px 10px;
      border-radius: 12px;
      font-size: 0.75rem;
      cursor: pointer;
      border: 1px solid #cbd5e1;
      transition: all 0.2s;
      user-select: none;
    }
    .phrase-tag:hover {
      background: #e2e8f0;
      color: #0f172a;
      border-color: #94a3b8;
    }

    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.7); }
      70% { box-shadow: 0 0 0 6px rgba(139, 92, 246, 0); }
      100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
    }
  </style>
      </head>
      <body>
        ${labelPagesHtml}
        <script>
          window.onload = function() {
            setTimeout(function() {
              window.print();
              window.onafterprint = function(){ window.close(); };
            }, 250);
          };
        <\/script>
      </body>
      </html>
    `);
    printWindow.document.close();
  }

  let pendingActionId = null;
  let pendingActionType = null;

  function openJudge(id) {
    if (!sessionStorage.getItem('QC_LOGGED_IN_USER')) {
      pendingActionId = id;
      pendingActionType = 'judge';
      openAdminUnlockModal();
      return;
    }
    const sample = allData.find(s => s.id === id);
    const sel = document.getElementById('modalResult');
    if (sample && sample.qcResult === '需特採') {
      sel.innerHTML = `
        <option value="特採">PASS (特採放行)</option>
        <option value="FAIL">FAIL (駁回特採並自動重送)</option>
      `;
      sel.value = '特採';
    } else {
      sel.innerHTML = `
        <option value="PASS">PASS (合格放行)</option>
        <option value="FAIL">FAIL (不合格自動重送)</option>
        <option value="需特採">不符合內控 (需特採)</option>
      `;
      sel.value = 'PASS';
    }
    document.getElementById('currentId').value = id; 
    document.getElementById('modalNote').value = '合格放行'; 
    document.getElementById('modalResult').value = 'PASS';
    handleResultChange(); 
    
    const approverText = document.getElementById('judgeApproverText');
    if (approverText) {
      approverText.innerText = '👤 放行核准人：' + sessionStorage.getItem('QC_LOGGED_IN_USER');
    }
    
    const pinBox = document.getElementById('modalPin');
    if(pinBox && pinBox.parentElement) {
      pinBox.parentElement.style.display = 'none';
      pinBox.value = '8888'; // fallback
    }

    
    const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
    const phrasesStr = cfgStr ? (JSON.parse(cfgStr)['OPTIONS_PHRASES'] || '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他') : '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他';
    const phrases = phrasesStr.split(',').map(s=>s.trim()).filter(Boolean);
    const container = document.getElementById('modalPhraseContainer');
    if (container) {
      container.innerHTML = phrases.map(p => `<span class="phrase-tag" onclick="document.getElementById('modalNote').value = this.innerText">${p}</span>`).join('');
    }
    
    document.getElementById('judgeModal').style.display = 'flex'; 
  }
  function closeModal() { document.getElementById('judgeModal').style.display = 'none'; }

  
  function handleResultChange() {
    const sel = document.getElementById('modalResult');
    const note = document.getElementById('modalNote');
    if (sel.value === 'FAIL') {
      sel.style.color = '#dc2626'; // Red
      if (note.value === '合格放行' || note.value === '特採放行') note.value = '';
    } else if (sel.value === '需特採') {
      sel.style.color = '#d97706'; // Orange
      if (note.value === '合格放行' || note.value === '特採放行') note.value = '';
    } else if (sel.value === '特採') {
      sel.style.color = '#7c3aed'; // Purple
      if (note.value === '合格放行' || note.value === '') note.value = '特採放行';
    } else {
      sel.style.color = '#059669'; // Green
      if (note.value === '' || note.value === '特採放行') note.value = '合格放行';
    }
  }
  function submitJudge() {
    const approver = sessionStorage.getItem('QC_LOGGED_IN_USER');
    const pin = document.getElementById('modalPin').value;
    
    const btn = document.getElementById('modalBtn'); 
    btn.disabled = true; 
    btn.innerText = "驗證授權中...";
    
    const id = document.getElementById('currentId').value;
    const result = document.getElementById('modalResult').value;
    const note = document.getElementById('modalNote').value;
    const targetItem = allData.find(d => d.id === id);

    if(IS_GAS) {
      google.script.run.withSuccessHandler((res) => { 
        btn.disabled = false; btn.innerText = "確認判定並通知 Teams";
        if(res.success) { 
          closeModal(); 
          showToast("✅ 判定放行完成！Teams 卡片已精準通報主管與該單位。");
          load(); 
        } else { 
          alert(res.error); 
          document.getElementById('judgeApproverText').innerText = '👤 放行核准人：' + (sessionStorage.getItem('QC_LOGGED_IN_USER') || '未登入'); 
        }
      }).completeSample(id, result, note, pin);
    } else if(GAS_API_URL) {
      fetch(GAS_API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify({
          action: 'completeSample',
          id: id,
          result: result,
          note: note,
          pin: pin,
          approver: approver
        })
      })
      .then(res => res.json())
      .then(res => {
        btn.disabled = false; btn.innerText = "確認判定並通知 Teams";
        if(res.success) {
          closeModal();
          showToast("✅ 判定放行完成！試算表已更新，Teams 卡片已發送。");
          load();
        } else {
          alert(res.error || "判定失敗");
          document.getElementById('judgeApproverText').innerText = '👤 放行核准人：' + (sessionStorage.getItem('QC_LOGGED_IN_USER') || '未登入');
        }
      })
      .catch(err => {
        btn.disabled = false; btn.innerText = "確認判定並通知 Teams";
        alert("雲端 API 連線異常：" + err.message);
      });
    } else {
      setTimeout(() => {
        btn.disabled = false; btn.innerText = "確認判定並通知 Teams";
        if(pin !== '8888') {
          alert("⛔ 授權失敗：品管專屬密碼錯誤！(預設為 8888)");
          document.getElementById('judgeApproverText').innerText = '👤 放行核准人：' + (sessionStorage.getItem('QC_LOGGED_IN_USER') || '未登入');
          return;
        }
        if(targetItem) {
          targetItem.status = 'completed';
          targetItem.qcResult = result;
          targetItem.qcNote = note;
          targetItem.completedAt = new Date().toISOString();
          localStorage.setItem('HS_QC_SAMPLES', JSON.stringify(allData));

          // 本機模擬 Teams 判定完成發送與彈窗預覽
          const isPass = (result === 'PASS');
          const themeColor = isPass ? "107C41" : "D9381E";
          const statusTitle = isPass ? "✅【QC 檢驗完成 - 判定合格放行】" : "❌【QC 檢驗完成 - 判定不合格】";

          const teamsPayload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": themeColor,
            "summary": statusTitle,
            "sections": [{
              "activityTitle": statusTitle,
              "activitySubtitle": `檢驗結果已判定，請 ${targetItem.dept} 進行後續作業`,
              "facts": [
                { "name": "🏢 送樣單位", "value": `${targetItem.dept}（送樣人：${targetItem.requester || '無'}）` },
                { "name": "🧪 檢驗品名", "value": targetItem.productName },
                { "name": "🛢️ 槽號 / 車牌", "value": `${targetItem.tankNo || '-'} / ${targetItem.customer || '-'}` },
                { "name": "📋 檢驗單號", "value": targetItem.barcode },
                { "name": "🎯 判定結果", "value": result },
                { "name": "📝 判定備註", "value": note || "無" },
                { "name": "⏱️ 完成時間", "value": new Date().toLocaleString() }
              ],
              "markdown": true
            }]
          };

          const previewData = {
            title: statusTitle,
            subtitle: `檢驗結果已判定，請 ${targetItem.dept} 進行後續作業`,
            color: isPass ? "green" : "red",
            facts: [
              { name: "🏢 送樣單位", value: `${targetItem.dept}（送樣人：${targetItem.requester || '無'}）` },
              { name: "🧪 檢驗品名", value: targetItem.productName },
              { name: "🛢️ 槽號 / 車牌", value: `${targetItem.tankNo || '-'} / ${targetItem.customer || '-'}` },
              { name: "📋 檢驗單號", value: targetItem.barcode },
              { name: "🎯 判定結果", value: result },
              { name: "📝 判定備註", value: note || "無" },
              { name: "⏱️ 完成時間", value: new Date().toLocaleString() }
            ]
          };

          dispatchTeamsCard(targetItem.dept, teamsPayload, previewData);
        }
        closeModal();
        showToast("✅ 判定成功（本機紀錄已更新）！Teams 卡片已產生。");
        render();
      }, 300);
    }
  }

  // =========================================================
  // 退回重新送樣模組
  // =========================================================

  
  function openConcession(id) {
    if (!sessionStorage.getItem('QC_LOGGED_IN_USER')) {
      pendingActionId = id;
      pendingActionType = 'concession';
      openAdminUnlockModal();
      return;
    }
    openJudge(id);
    setTimeout(() => {
      const sel = document.getElementById('modalResult');
      if(sel) { sel.value = '特採'; handleResultChange(); }
    }, 50);
  }

  function openReturnResample(id) {
    if (!sessionStorage.getItem('QC_LOGGED_IN_USER')) {
      pendingActionId = id;
      pendingActionType = 'resample';
      openAdminUnlockModal();
      return;
    }
    document.getElementById('returnResampleId').value = id;
    document.getElementById('returnResampleNote').value = '';
    const pinBox = document.getElementById('returnResamplePin');
    if(pinBox && pinBox.parentElement) {
      pinBox.parentElement.style.display = 'none';
      pinBox.value = '8888'; // fallback
    }
    
    const cfgStr = localStorage.getItem('HS_QC_DYNAMIC_OPTIONS');
    const phrasesStr = cfgStr ? (JSON.parse(cfgStr)['OPTIONS_PHRASES'] || '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他') : '合格放行, 水分偏高, 金屬異常, 微粒超標, 外觀異常, 其他';
    const phrases = phrasesStr.split(',').map(s=>s.trim()).filter(Boolean).filter(p => p !== '合格放行');
    const container = document.getElementById('returnResamplePhraseContainer');
    if (container) {
      container.innerHTML = phrases.map(p => `<span class="phrase-tag" onclick="document.getElementById('returnResampleNote').value = this.innerText">${p}</span>`).join('');
    }
    
    document.getElementById('returnResampleModal').style.display = 'flex';
  }
  function closeReturnResampleModal() {
    document.getElementById('returnResampleModal').style.display = 'none';
  }

  async function submitReturnResample() {
    const id = document.getElementById('returnResampleId').value;
    const note = document.getElementById('returnResampleNote').value.trim();
    const pin = document.getElementById('returnResamplePin').value.trim();
    if (!note) { alert('請輸入退回原因！'); return; }
    

    const btn = document.getElementById('returnResampleBtn');
    btn.disabled = true;
    btn.innerText = '處理中...';

    const handleSuccess = (res) => {
      btn.disabled = false;
      btn.innerText = '確認退回並建立重送記錄';
      if (res && res.success) {
        closeReturnResampleModal();
        showToast(`↩️ 已退回！系統已自動建立第 ${res.round} 次送樣記錄，請通知課室重新送樣。`);
        // 更新本機資料
        const item = allData.find(d => d.id === id);
        if (item) { item.status = 'failed'; item.qcResult = 'FAIL'; item.qcNote = note; }
        if (res.newId) {
          const newItem = item ? { ...item, id: res.newId, status: 'pending', round: res.round, parentId: item.parentId || id, qcResult: '', qcNote: '', completedAt: '', createdAt: new Date().toISOString() } : null;
          if (newItem) allData.push(newItem);
        }
        localStorage.setItem('HS_QC_SAMPLES', JSON.stringify(allData));
        load();
      } else {
        alert((res && res.error) || '退回失敗，請再試一次');
        document.getElementById('returnResamplePin').value = '';
      }
    };

    if (IS_GAS) {
      google.script.run.withSuccessHandler(handleSuccess).returnForResample(id, note, pin);
    } else if (GAS_API_URL) {
      try {
        const resp = await fetch(GAS_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'text/plain;charset=utf-8' },
          body: JSON.stringify({ action: 'returnForResample', id, note, pin })
        });
        handleSuccess(await resp.json());
      } catch(err) {
        btn.disabled = false;
        btn.innerText = '確認退回並建立重送記錄';
        alert('API 連線異常：' + err.message);
      }
    } else {
      // 本機離線模式
      const sysPin = localStorage.getItem('HS_QC_ADMIN_PIN') || '8888';
      if (pin !== sysPin) { btn.disabled = false; btn.innerText = '確認退回並建立重送記錄'; alert('⛔ 授權失敗：PIN 碼錯誤！'); document.getElementById('returnResamplePin').value = ''; return; }
      const item = allData.find(d => d.id === id);
      const oldRound = parseInt(item?.round) || 1;
      const rootId = item?.parentId || id;
      const newId = 'RR-' + Date.now();
      const newItem = { ...item, id: newId, status: 'pending', round: oldRound + 1, parentId: rootId, qcResult: '', qcNote: '', completedAt: '', isAlerted: '', createdAt: new Date().toISOString() };
      if (item) { item.status = 'failed'; item.qcResult = 'FAIL'; item.qcNote = note; item.completedAt = new Date().toISOString(); }
      allData.push(newItem);
      handleSuccess({ success: true, newId, round: oldRound + 1 });
    }
  }

  // =========================================================
  // 送樣歷史記錄檢視
  // =========================================================

  function showSampleHistory(rootId) {
    // 找出同一批次的所有紀錄（自己是根或 parentId 等於根）
    const history = allData.filter(d => d.id === rootId || d.parentId === rootId)
      .sort((a, b) => (parseInt(a.round)||1) - (parseInt(b.round)||1));

    const statusLabel = { pending: '⏳ 待檢驗', completed: '✅ 完成', failed: '❌ 不合格退回' };
    const statusColor = { pending: '#0369a1', completed: '#059669', failed: '#dc2626' };

    document.getElementById('sampleHistoryContent').innerHTML = history.length
      ? history.map(s => `
        <div style="border:1px solid #e2e8f0; border-radius:8px; padding:12px; margin-bottom:10px; background:${s.status==='completed'?'#f0fdf4':s.status==='failed'?'#fff1f2':'#f8fafc'};">
          <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
            <span style="font-weight:bold; font-size:1rem; background:#fed7aa; color:#c2410c; padding:2px 8px; border-radius:10px;">第 ${s.round||1} 次</span>
            <span style="font-weight:600; color:${statusColor[s.status]||'#475569'};">${statusLabel[s.status]||s.status}</span>
            ${s.qcResult ? `<b style="color:${s.qcResult==='PASS'?'#059669':'#dc2626'}; background:${s.qcResult==='PASS'?'#d1fae5':'#fee2e2'}; padding:1px 8px; border-radius:4px;">${s.qcResult}</b>` : ''}
          </div>
          <div style="font-size:0.82rem; color:#374151;"><b>送樣時間：</b>${formatSimpleDate(s.createdAt)}</div>
          ${s.completedAt ? `<div style="font-size:0.82rem; color:#374151;"><b>完成時間：</b>${formatSimpleDate(s.completedAt)}</div>` : ''}
          ${s.remark ? `<div style="font-size:0.82rem; color:#475569; margin-top:4px;"><b>送樣備註：</b>${s.remark}</div>` : ''}
          ${s.qcNote ? `<div style="font-size:0.82rem; color:#475569; margin-top:4px; background:#f1f5f9; padding:4px 8px; border-radius:4px;"><b>判定備註：</b>${s.qcNote}</div>` : ''}
        </div>
      `).join('')
      : '<div style="text-align:center; color:#94a3b8; padding:20px;">找不到送樣歷史記錄</div>';

    document.getElementById('sampleHistoryModal').style.display = 'flex';
  }

  function closeSampleHistoryModal() {
    document.getElementById('sampleHistoryModal').style.display = 'none';
  }

  // ==========================================
  // 全廠紀錄查詢 (Global History)
  // ==========================================
  function openGlobalHistoryModal() {
    document.getElementById('ghSearchKw').value = '';
    document.getElementById('ghStatusFilter').value = '';
    renderGlobalHistory();
    document.getElementById('globalHistoryModal').style.display = 'flex';
  }

  function closeGlobalHistoryModal() {
    document.getElementById('globalHistoryModal').style.display = 'none';
  }

  function renderGlobalHistory() {
    const kw = document.getElementById('ghSearchKw').value.toLowerCase();
    const status = document.getElementById('ghStatusFilter').value;
    const tbody = document.getElementById('ghTableBody');
    
    // 篩選
    const filtered = allData.filter(s => {
      const matchKw = !kw || 
        String(s.barcode||'').toLowerCase().includes(kw) ||
        String(s.productName||'').toLowerCase().includes(kw) ||
        String(s.tankNo||'').toLowerCase().includes(kw) ||
        String(s.customer||'').toLowerCase().includes(kw);
      const matchStatus = !status || s.status === status;
      return matchKw && matchStatus;
    });

    // 限制顯示筆數避免卡頓
    const maxRows = 200;
    const toShow = filtered.slice(0, maxRows);

    if (toShow.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:30px; color:#94a3b8;">查無符合的歷史紀錄</td></tr>`;
      return;
    }

    tbody.innerHTML = toShow.map(s => {
      let statusBadge = '';
      if (s.status === 'pending') statusBadge = `<span style="background:#fef08a; color:#854d0e; padding:2px 6px; border-radius:4px; font-size:0.8rem;">待檢驗</span>`;
      else if ((s.status === 'completed' || s.status === 'failed') && (s.qcResult === 'PASS' || s.qcResult === 'FAIL' || s.qcResult === '特採')) statusBadge = `<span style="background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':(s.qcResult==='需特採'?'#fef3c7':'#fee2e2'))}; color:${s.qcResult==='PASS'?'#065f46':(s.qcResult==='特採'?'#7c3aed':(s.qcResult==='需特採'?'#d97706':'#b91c1c'))}; padding:2px 6px; border-radius:4px; font-size:0.8rem;">${s.qcResult==='PASS'?'合格(PASS)':(s.qcResult==='特採'?'特採(PASS)':'退回(FAIL)')}</span>`;
      else if (s.status === 'completed' && s.qcResult === 'FAIL') statusBadge = `<span style="background:#fee2e2; color:#991b1b; padding:2px 6px; border-radius:4px; font-size:0.8rem;">不合格(FAIL)</span>`;
      else if (s.status === 'failed') statusBadge = `<span style="background:#fed7aa; color:#9a3412; padding:2px 6px; border-radius:4px; font-size:0.8rem;">退回(failed)</span>`;
      else statusBadge = s.status;

      const roundHtml = (parseInt(s.round)||1) >= 2 ? ` <span style="font-size:0.7rem; color:#ea580c; background:#ffedd5; padding:1px 4px; border-radius:4px;">第${s.round}次</span>` : '';

      return `<tr>
        <td style="font-size:0.85rem; color:#475569;">${s.createdAt ? s.createdAt.substring(0,16).replace('T',' ') : '-'}</td>
        <td><b>${s.barcode}</b>${roundHtml}</td>
        <td><b>${s.productName}</b> <span style="color:#64748b; font-size:0.8rem;">(${s.grade||'-'})</span></td>
        <td>${s.tankNo||'-'} / <span style="font-size:0.8rem;">${s.customer||'-'}</span></td>
        <td style="font-size:0.85rem;">${s.dept} <br><span style="color:#64748b;">(${s.requester})</span></td>
        <td>${statusBadge} <div style="font-size:0.75rem; color:#64748b; margin-top:2px;">${s.qcNote||''}</div></td>
      </tr>`;
    }).join('');
  }


  function setBarcodePlaceholder() {
    const todayStr = new Date().toISOString().split('T')[0].replace(/-/g, '');
    document.getElementById('barcode').placeholder = "例: " + todayStr;
  }

  function showToast(msg) {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.style.display = 'block';
    setTimeout(() => { t.style.display = 'none'; }, 3500);
  }

  // PWA Install Prompt
  let deferredPrompt;
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById('pwa-install-banner').style.display = 'flex';
  });

  function installPWA() {
    if(!deferredPrompt) {
      alert("提示：可使用瀏覽器選單中的「安裝為應用程式」或「加到主畫面」進行安裝！");
      return;
    }
    deferredPrompt.prompt();
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        document.getElementById('pwa-install-banner').style.display = 'none';
      }
      deferredPrompt = null;
    });
  }

  function setLayoutView(mode) {
    localStorage.setItem('HS_QC_LAYOUT_VIEW', mode);
    applyLayoutView(mode);
  }

  function applyLayoutView(mode) {
    const c = document.getElementById('kanbanContainer');
    const tabsBar = document.getElementById('tabsHeaderBar');
    if(!c) return;

    ['btnLayoutAuto', 'btnLayoutStacked', 'btnLayoutTabs', 'btnLayoutSide'].forEach(id => {
      const btn = document.getElementById(id);
      if(btn) btn.classList.remove('active');
    });

    c.classList.remove('view-stacked', 'view-sidebyside', 'view-tabs');
    if(tabsBar) tabsBar.style.display = 'none';

    if(mode === 'stacked') {
      c.classList.add('view-stacked');
      document.getElementById('btnLayoutStacked')?.classList.add('active');
    } else if(mode === 'side') {
      c.classList.add('view-sidebyside');
      document.getElementById('btnLayoutSide')?.classList.add('active');
    } else if(mode === 'tabs') {
      c.classList.add('view-tabs');
      if(tabsBar) tabsBar.style.display = 'inline-flex';
      document.getElementById('btnLayoutTabs')?.classList.add('active');
      const activeTab = localStorage.getItem('HS_QC_ACTIVE_TAB') || 'pending';
      switchKanbanTab(activeTab);
    } else {
      document.getElementById('btnLayoutAuto')?.classList.add('active');
    }
  }

  function switchKanbanTab(tab) {
    localStorage.setItem('HS_QC_ACTIVE_TAB', tab);
    const colP = document.getElementById('col-pending');
    const colC = document.getElementById('col-completed');
    const btnP = document.getElementById('tabBtnPending');
    const btnC = document.getElementById('tabBtnCompleted');
    if(!colP || !colC || !btnP || !btnC) return;

    if(tab === 'completed') {
      colP.classList.remove('active-tab');
      colC.classList.add('active-tab');
      btnP.classList.remove('active');
      btnC.classList.add('active');
    } else {
      colC.classList.remove('active-tab');
      colP.classList.add('active-tab');
      btnC.classList.remove('active');
      btnP.classList.add('active');
    }
  }

  function setTableMode(mode) {
    localStorage.setItem('HS_QC_TABLE_MODE', mode);
    applyTableMode(mode);
    render();
  }

  function toggleTableMode() {
    const current = localStorage.getItem('HS_QC_TABLE_MODE') || 'adaptive';
    const next = current === 'adaptive' ? 'full' : 'adaptive';
    setTableMode(next);
  }

  function applyTableMode(mode) {
    const wrapP = document.getElementById('tableWrapPending');
    const wrapC = document.getElementById('tableWrapCompleted');
    const btnAdap = document.getElementById('btnTableModeAdaptive');
    const btnFull = document.getElementById('btnTableModeFull');
    const isAdaptive = (mode === 'adaptive');

    if(wrapP) {
      wrapP.className = isAdaptive ? 'table-responsive adaptive-mode' : 'table-responsive full-mode';
    }
    if(wrapC) {
      wrapC.className = isAdaptive ? 'table-responsive adaptive-mode' : 'table-responsive full-mode';
    }
    if(btnAdap) btnAdap.classList.toggle('active', isAdaptive);
    if(btnFull) btnFull.classList.toggle('active', !isAdaptive);

    document.querySelectorAll('.table-mode-label').forEach(el => {
      el.innerText = isAdaptive ? '自適應 (免左右移)' : '傳統九欄展開';
    });
    document.querySelectorAll('.table-mode-icon').forEach(el => {
      el.innerText = isAdaptive ? '⚡' : '📋';
    });
  }

  // =========================================================================
  // 🔐 管理員權限驗證與模擬測試箱卡控邏輯
  // =========================================================================
  let isAdminUnlocked = false;

  function getEffectiveAdminPin() {
    // 優先順序：試算表 System_Config 中的 QC_PIN -> localStorage 快取 -> 預設 8888
    return localStorage.getItem('HS_QC_ADMIN_PIN') || '8888';
  }

  function checkAdminUnlockOnStartup() {
    // 1. 檢查網址參數 (?admin=1 或 ?debug=1 或 ?pin=8888)
    const urlParams = new URLSearchParams(window.location.search);
    const pinParam = urlParams.get('pin');
    const validPin = getEffectiveAdminPin();
    
    if (pinParam && pinParam === validPin) {
      unlockAdminFeatures(false);
      return;
    }
    
    // 2. 檢查目前 Session 是否已解鎖過 (關閉分頁或瀏覽器即失效)
    const isSessionUnlocked = sessionStorage.getItem('HS_QC_ADMIN_UNLOCKED');
    if (isSessionUnlocked === 'true') {
      unlockAdminFeatures(false);
    } else {
      lockAdminFeatures(false);
    }
  }

  function handleAdminUnlockClick() {
    if (isAdminUnlocked) {
      // 若已解鎖，點擊則立即上鎖
      lockAdminFeatures(true);
    } else {
      openAdminUnlockModal();
    }
  }

  function handleTeamsBadgeClick() {
    if (isAdminUnlocked) {
      openTeamsConfigModal();
    } else {
      openAdminUnlockModal();
    }
  }

  function openAdminUnlockModal() {
    const modal = document.getElementById('adminUnlockModal');
    const input = document.getElementById('loginUsernameInput');
      const pass = document.getElementById('loginPasswordInput');
    const err = document.getElementById('adminUnlockError');
    if (modal && input) {
      input.value = ''; if(pass) pass.value = '';
      if (err) { err.innerText = ''; err.style.display = 'none'; }
      modal.style.display = 'flex';
      setTimeout(() => input.focus(), 150);
    }
  }

  function closeAdminUnlockModal() {
    const modal = document.getElementById('adminUnlockModal');
    if (modal) modal.style.display = 'none';
  }

  async function confirmAdminUnlock() {
      const u = document.getElementById('loginUsernameInput').value.trim();
      const p = document.getElementById('loginPasswordInput').value;
      const err = document.getElementById('adminUnlockError');
      const btn = document.getElementById('btnLoginConfirm');
      
      if (!u || !p) {
        if (err) { err.innerText = '⛔ 請輸入帳號與密碼！'; err.style.display = 'block'; }
        return;
      }
      
      btn.innerText = '驗證中...';
      btn.disabled = true;

      try {
        const res = await fetch(GAS_API_URL, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ action: 'verifyLogin', username: u, password: p })
        });
        const data = await res.json();
        if (data.success) {
          sessionStorage.setItem('QC_LOGGED_IN_USER', data.username);
          sessionStorage.setItem('QC_LOGGED_IN_ROLE', data.role);
          closeAdminUnlockModal();
          unlockAdminFeatures(true);
          if (typeof pendingActionId !== 'undefined' && pendingActionId) {
             if (pendingActionType === 'judge') openJudge(pendingActionId);
             if (pendingActionType === 'resample') openReturnResample(pendingActionId);
             if (pendingActionType === 'concession') openConcession(pendingActionId);
             pendingActionId = null;
             pendingActionType = null;
          }
        } else {
          if (err) { err.innerText = '⛔ 登入失敗：' + (data.error || '帳號或密碼錯誤'); err.style.display = 'block'; }
        }
      } catch (e) {
        if (err) { err.innerText = '⛔ 系統錯誤，無法連線。'; err.style.display = 'block'; }
      } finally {
        btn.innerText = '登入解鎖 🔓';
        btn.disabled = false;
      }
    }

  function unlockAdminFeatures(showNotification = true) {
    isAdminUnlocked = true;
    sessionStorage.setItem('HS_QC_ADMIN_UNLOCKED', 'true');
    
    const toolbar = document.getElementById('simToolbar');
    if (toolbar) toolbar.style.display = 'flex';
    
    const btn = document.getElementById('btnAdminUnlock');
    if (btn) {
      btn.className = 'btn-admin-unlock unlocked';
      btn.innerHTML = '🔓 管理功能已解鎖 (點擊上鎖)';
      btn.title = '點擊即可重新鎖定並隱藏本機測試箱';
    }
    
    if (showNotification) {
      showToast('✅ 管理員權限已解鎖！本機模擬測試箱已展開。');
    }
  }

  function lockAdminFeatures(showNotification = true) {
    isAdminUnlocked = false;
    sessionStorage.removeItem('HS_QC_ADMIN_UNLOCKED');
    
    const toolbar = document.getElementById('simToolbar');
    if (toolbar) toolbar.style.display = 'none';
    
    const btn = document.getElementById('btnAdminUnlock');
    if (btn) {
      btn.className = 'btn-admin-unlock';
      btn.innerHTML = '🔓 登入解鎖 (QC放行)';
      btn.title = '點擊輸入管理員 PIN 碼解鎖測試箱';
    }
    
    if (showNotification) {
      showToast('🔒 管理功能已上鎖，模擬測試箱已隱藏。');
    }
  }

  window.onload = () => {
    applyLayoutView(localStorage.getItem('HS_QC_LAYOUT_VIEW') || 'auto');
    applyTableMode(localStorage.getItem('HS_QC_TABLE_MODE') || 'adaptive');
    loadTeamsConfig();
    setBarcodePlaceholder();
    renderT100Dropdown();
    checkAdminUnlockOnStartup();
    load();
    if(IS_GAS) setInterval(load, 30000);
    
    // 定時刷新等候時長動畫與 KPI
    setInterval(render, 60000);

    // 註冊 Service Worker (強制檢查更新，保證每次載入最新版本)
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('sw.js').then((reg) => {
        reg.update();
      }).catch(err => console.log('SW register failed:', err));
    }
  };

  // 動態提示字跑馬燈
  function startPlaceholderMarquee(elementId, originalText) {
    const el = document.getElementById(elementId);
    if (!el) return;
    let text = originalText + '   '; 
    setInterval(() => {
      text = text.substring(1) + text[0];
      el.setAttribute('placeholder', text);
    }, 400); 
  }
  document.addEventListener('DOMContentLoaded', () => {
    startPlaceholderMarquee('empIdInput', '掃描或輸入工號... ');
    startPlaceholderMarquee('requester', '姓名（工號查到後會自動填入）... ');
  });


