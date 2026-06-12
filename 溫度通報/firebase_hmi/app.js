// app.js
// ==================== 1. 全域狀態與初始化 ==================== */
let db = null;
let firebaseApp = null;
let realtimeUnsubscribe = null;
let contactsUnsubscribe = null;
let chartUnsubscribe = null;
let trendChart = null;
let allLogsForChart = [];
let chartMode = "realtime";
let historyChartLogs = [];

// 頁面解鎖狀態
let isSettingsUnlocked = false;
let isContactsUnlocked = false;
let verifiedPassword = ""; // 快取的密碼，用在 RPC

// 目前設定的本機資料快取，供 Modal 等地方使用
let currentHmiSettings = {
    threshold: 28.0,
    startHour: 8,
    endHour: 24,
    frequency: 60,
    password: "admin888",
    webAppUrl: ""
};

// ==================== 2. HMI 分頁導覽切換 ==================== */
document.addEventListener("DOMContentLoaded", () => {
    initTabNavigation();
    initSettingsHourOptions();
    initChartDateInputs();
    loadAndInitFirebase();
});

function initTabNavigation() {
    const navItems = document.querySelectorAll(".nav-item");
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            
            // 切換 active 狀態
            document.querySelectorAll(".nav-item").forEach(nav => nav.classList.remove("active"));
            document.querySelectorAll(`.nav-item[data-tab="${tabId}"]`).forEach(nav => nav.classList.add("active"));
            
            // 切換分頁面板
            document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("active"));
            document.getElementById(`tab-${tabId}`).classList.add("active");
            
            // 若切換到需要即時載入的名單或紀錄
            if (tabId === "contacts") {
                loadContactsRealtime();
            } else if (tabId === "logs") {
                loadLogsRealtime();
            }
        });
    });
}

function initSettingsHourOptions() {
    const startSelect = document.getElementById("startHour");
    const endSelect = document.getElementById("endHour");
    
    for (let i = 0; i <= 23; i++) {
        const option1 = document.createElement("option");
        option1.value = i;
        option1.text = `${i.toString().padStart(2, '0')}:00`;
        startSelect.appendChild(option1);
        
        const option2 = document.createElement("option");
        option2.value = i;
        option2.text = `${i.toString().padStart(2, '0')}:00`;
        // 預設結束為 24 點，這裡下拉選單增加一個 24 點的選項
        endSelect.appendChild(option2);
    }
    
    // 結束時間額外加一個 24:00
    const option24 = document.createElement("option");
    option24.value = 24;
    option24.text = "24:00";
    endSelect.appendChild(option24);
}

// ==================== 3. Firebase 設定載入與初始化 ==================== */
// 預設建立的 Firebase 專案配置
const DEFAULT_FIREBASE_CONFIG = {
    apiKey: "AIzaSyCarGS9LH9Kgu0mr0W8NCmNmNkAsQxF4Sg",
    authDomain: "hongsheng-temp-523.firebaseapp.com",
    projectId: "hongsheng-temp-523",
    storageBucket: "hongsheng-temp-523.firebasestorage.app",
    messagingSenderId: "263225895201",
    appId: "1:263225895201:web:ef6139877e5d2aca32f660"
};

function loadAndInitFirebase() {
    const savedConfig = localStorage.getItem("firebase_config");
    const textarea = document.getElementById("firebaseConfigTextarea");
    
    let config = null;
    if (savedConfig) {
        textarea.value = savedConfig;
        try {
            config = JSON.parse(savedConfig);
            // Auto reset: if cached projectId doesn't match current project, clear it
            if (config && config.projectId !== "hongsheng-temp-523") {
                console.warn("Detected stale Firebase configuration, auto-resetting to default...");
                localStorage.removeItem("firebase_config");
                config = DEFAULT_FIREBASE_CONFIG;
                textarea.value = JSON.stringify(DEFAULT_FIREBASE_CONFIG, null, 2);
            }
        } catch (e) {
            showToast("Firebase 設定 JSON 格式錯誤！", "error");
        }
    } else {
        // 使用預設建立好的專案設定
        const defaultConfigStr = JSON.stringify(DEFAULT_FIREBASE_CONFIG, null, 2);
        textarea.value = defaultConfigStr;
        config = DEFAULT_FIREBASE_CONFIG;
    }
    
    if (config) {
        initFirebase(config);
    } else {
        updateFirebaseUI(false);
    }
}

function initFirebase(config) {
    try {
        // 防止重複初始化
        if (firebase.apps.length > 0) {
            firebaseApp = firebase.app();
        } else {
            firebaseApp = firebase.initializeApp(config);
        }
        
        db = firebase.firestore();
        updateFirebaseUI(true);
        showToast("Firebase 初始化成功，即時資料庫已連線！", "success");
        
        // 啟動首頁實時資料監聽
        listenRealtimeData();
        listenHistoryLogsForChart();
    } catch (e) {
        console.error("Firebase 初始化失敗:", e);
        showToast("連線失敗: " + e.message, "error");
        updateFirebaseUI(false);
    }
}

function saveFirebaseConfig() {
    const configText = document.getElementById("firebaseConfigTextarea").value.trim();
    if (!configText) {
        showToast("請輸入有效的設定 JSON 物件！", "error");
        return;
    }
    
    try {
        JSON.parse(configText); // 驗證是否為合規 JSON
        localStorage.setItem("firebase_config", configText);
        loadAndInitFirebase();
        toggleConfigDrawer();
    } catch (e) {
        showToast("輸入的格式不是有效的 JSON！", "error");
    }
}

function clearFirebaseConfig() {
    if (confirm("確定要清除並中斷 Firebase 連線嗎？此操作將清除本機瀏覽器快取。")) {
        localStorage.removeItem("firebase_config");
        document.getElementById("firebaseConfigTextarea").value = "";
        
        // 註銷監聽器
        if (realtimeUnsubscribe) realtimeUnsubscribe();
        if (contactsUnsubscribe) contactsUnsubscribe();
        if (chartUnsubscribe) chartUnsubscribe();
        
        if (trendChart) {
            trendChart.destroy();
            trendChart = null;
        }
        allLogsForChart = [];
        
        // 斷開應用
        if (firebaseApp) {
            firebaseApp.delete().then(() => {
                db = null;
                firebaseApp = null;
                updateFirebaseUI(false);
                showToast("連線已中斷，資料快取已清除。", "info");
            });
        } else {
            updateFirebaseUI(false);
        }
        toggleConfigDrawer();
    }
}

function updateFirebaseUI(connected) {
    const dot = document.getElementById("firebaseDot");
    const text = document.getElementById("firebaseStatusText");
    
    if (connected) {
        dot.className = "status-dot connected";
        text.innerText = "Firebase 已連線";
    } else {
        dot.className = "status-dot disconnected";
        text.innerText = "Firebase 未連線";
        resetDashboardData();
    }
}

function toggleConfigDrawer() {
    const drawer = document.getElementById("configDrawer");
    const overlay = document.getElementById("configDrawerOverlay");
    
    // 開啟時需要驗證密碼
    if (!drawer.classList.contains("open")) {
        if (verifiedPassword !== currentHmiSettings.password) {
            const pwd = prompt("請輸入管理密碼以存取 Firebase 設定：");
            if (pwd === null) return; // 使用者取消
            if (pwd !== currentHmiSettings.password) {
                showToast("密碼錯誤，拒絕存取設定！", "error");
                return;
            }
            verifiedPassword = pwd; // 快取密碼
            showToast("管理驗證成功！", "success");
        }
    }
    
    drawer.classList.toggle("open");
    overlay.classList.toggle("open");
}

// ==================== 4. 儀表板 Real-time 監聽 ==================== */
function listenRealtimeData() {
    if (!db) return;
    
    // 註銷舊監聽
    if (realtimeUnsubscribe) realtimeUnsubscribe();
    
    // 監聽 realtime_data 集合下的 status 文件
    realtimeUnsubscribe = db.collection("realtime_data").doc("status").onSnapshot((doc) => {
        if (doc.exists) {
            const data = doc.data();
            updateDashboardUI(data);
        } else {
            // 文件不存在時，建立初始預設值文件
            initializeDefaultFirebaseDocument();
        }
    }, (error) => {
        console.error("監聽 realtime_data 失敗:", error);
        showToast("資料監聽失敗: " + error.message, "error");
    });
}

function initializeDefaultFirebaseDocument() {
    if (!db) return;
    const initialData = {
        current_temp: -99,
        threshold: 28.0,
        obs_time: "--",
        alert_state: "正常 (未超標)",
        status_text: "無紀錄",
        last_heartbeat: new Date().getTime(),
        start_hour: 8,
        end_hour: 24,
        frequency: 60,
        password: "admin888",
        web_app_url: ""
    };
    db.collection("realtime_data").doc("status").set(initialData)
      .then(() => console.log("Firestore 預設狀態文件建立成功"))
      .catch(e => console.error("Firestore 預設文件建立失敗:", e));
}

function updateDashboardUI(data) {
    // 1. 更新即時溫度與外環樣式
    const temp = parseFloat(data.current_temp);
    const tempDisplay = document.getElementById("currentTempDisplay");
    const statusDisplay = document.getElementById("tempStatusDisplay");
    const ring = document.getElementById("tempGaugeRing");
    const threshold = parseFloat(data.threshold) || 28.0;
    
    // 快取設定，方便其他分頁載入
    currentHmiSettings.threshold = threshold;
    currentHmiSettings.startHour = parseInt(data.start_hour) || 8;
    currentHmiSettings.endHour = parseInt(data.end_hour) || 24;
    currentHmiSettings.frequency = parseInt(data.frequency) || 60;
    currentHmiSettings.password = data.password || "admin888";
    currentHmiSettings.webAppUrl = data.web_app_url || "";
    
    if (temp === -99 || isNaN(temp)) {
        tempDisplay.innerText = "--.-";
        statusDisplay.innerText = "等待數據...";
        statusDisplay.className = "temp-status";
        ring.className = "gauge-ring";
    } else {
        tempDisplay.innerText = temp.toFixed(1);
        
        // 判定顏色
        if (temp > threshold) {
            statusDisplay.innerText = "高溫警報";
            statusDisplay.className = "temp-status danger";
            ring.className = "gauge-ring danger";
        } else if (temp >= threshold - 1.5) {
            statusDisplay.innerText = "接近閾值";
            statusDisplay.className = "temp-status warning";
            ring.className = "gauge-ring warning";
        } else {
            statusDisplay.innerText = "正常 (未超標)";
            statusDisplay.className = "temp-status normal";
            ring.className = "gauge-ring normal";
        }
    }
    
    // 2. 更新觀測時間
    document.getElementById("obsTimeDisplay").innerText = data.obs_time || "--";
    
    // 3. 更新系統概況
    document.getElementById("dashThreshold").innerText = `${threshold.toFixed(1)}°C`;
    document.getElementById("dashTimeWindow").innerText = `${String(data.start_hour).padStart(2, '0')}:00 - ${String(data.end_hour).padStart(2, '0')}:00`;
    document.getElementById("dashFrequency").innerText = `${data.frequency || 60} 分鐘`;
    
    // 4. 更新本機心跳狀態與在線指示
    const lastHbTime = parseInt(data.last_heartbeat) || 0;
    const hbSource = data.heartbeat_source || "local"; // "local" 或 "cloud"
    const hbText = document.getElementById("lastHeartbeatDisplay");
    const hbDot = document.getElementById("heartbeatDot");
    const hbStatusText = document.getElementById("heartbeatStatusText");
    const hbPulse = document.getElementById("hbPulseIcon");
    const dashHbStatus = document.getElementById("dashHeartbeatStatus");
    const hbIconBox = document.querySelector(".hb-icon-container");
    
    if (lastHbTime === 0) {
        // 從未收到心跳
        hbText.innerText = "最後心跳時間：尚未收到心跳";
        hbDot.className = "status-dot offline";
        hbStatusText.innerText = "完全離線";
        dashHbStatus.innerText = "完全離線";
        dashHbStatus.className = "badge offline";
        hbPulse.className = "fa-solid fa-heartbeat";
        hbIconBox.className = "hb-icon-container offline";
    } else {
        const d = new Date(lastHbTime);
        const formatted = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}:${String(d.getSeconds()).padStart(2,'0')}`;
        
        // 判斷在線或離線（頻率的 1.1 倍 + 5分鐘容錯）
        const now = new Date().getTime();
        const diffMins = (now - lastHbTime) / (1000 * 60);
        const freq = parseInt(data.frequency) || 60;
        const timeoutMins = (freq * 1.1) + 5;
        
        if (diffMins < timeoutMins && hbSource === "local") {
            // ✅ 本機正常在線
            hbText.innerText = `最後心跳時間：${formatted}`;
            hbDot.className = "status-dot online";
            hbStatusText.innerText = "本機在線";
            dashHbStatus.innerText = "在線 (正常)";
            dashHbStatus.className = "badge online";
            hbPulse.className = "fa-solid fa-heartbeat pulsing";
            hbIconBox.className = "hb-icon-container online";
        } else if (diffMins < timeoutMins && hbSource === "cloud") {
            // ⚠️ 本機異常，雲端備援接手中
            hbText.innerText = `最後心跳時間：${formatted}（雲端備援）`;
            hbDot.className = "status-dot cloud";
            hbStatusText.innerText = "雲端監控中";
            dashHbStatus.innerText = "雲端監控（本機異常）";
            dashHbStatus.className = "badge cloud";
            hbPulse.className = "fa-solid fa-cloud pulsing";
            hbIconBox.className = "hb-icon-container cloud";
            showToast("警告：本機監控異常，雲端備援機制已接手！", "warning");
        } else {
            // 🔴 心跳逾時，完全離線
            hbText.innerText = `最後心跳時間：${formatted}（已逾時）`;
            hbDot.className = "status-dot offline";
            hbStatusText.innerText = "完全離線";
            dashHbStatus.innerText = "離線警報";
            dashHbStatus.className = "badge offline";
            hbPulse.className = "fa-solid fa-heartbeat";
            hbIconBox.className = "hb-icon-container offline";
            showToast("警告：監控系統已完全離線，請立即檢查！", "error");
        }
    }
    
    // 5. 更新折線圖
    if (allLogsForChart.length > 0) {
        updateTrendChart(allLogsForChart);
    }
}

function resetDashboardData() {
    document.getElementById("currentTempDisplay").innerText = "--.-";
    document.getElementById("tempStatusDisplay").innerText = "等待連線";
    document.getElementById("tempStatusDisplay").className = "temp-status";
    document.getElementById("tempGaugeRing").className = "gauge-ring";
    document.getElementById("obsTimeDisplay").innerText = "--";
    document.getElementById("dashThreshold").innerText = "--.-°C";
    document.getElementById("dashTimeWindow").innerText = "--:-- - --:--";
    document.getElementById("dashFrequency").innerText = "-- 分鐘";
    document.getElementById("lastHeartbeatDisplay").innerText = "最後心跳時間：未連線";
    document.getElementById("heartbeatDot").className = "status-dot offline";
    document.getElementById("heartbeatStatusText").innerText = "未連線";
    document.getElementById("dashHeartbeatStatus").innerText = "未連線";
    document.getElementById("dashHeartbeatStatus").className = "badge offline";
    document.getElementById("hbPulseIcon").className = "fa-solid fa-heartbeat";
    document.querySelector(".hb-icon-container").className = "hb-icon-container offline";
}

// ==================== 5. 系統設定與密碼驗證 ==================== */
function unlockSettingsSection() {
    const entered = document.getElementById("settingsPassword").value;
    if (!entered) {
        showToast("請輸入管理密碼！", "error");
        return;
    }
    
    if (entered === currentHmiSettings.password) {
        isSettingsUnlocked = true;
        verifiedPassword = entered;
        
        // 移除解鎖鎖定樣式
        document.getElementById("settingsAuthArea").style.display = "none";
        document.getElementById("settingsConfigFields").classList.remove("locked");
        
        // 填入目前的數值
        document.getElementById("thresholdSlider").value = currentHmiSettings.threshold;
        document.getElementById("thresholdVal").innerText = currentHmiSettings.threshold;
        document.getElementById("startHour").value = currentHmiSettings.startHour;
        document.getElementById("endHour").value = currentHmiSettings.endHour;
        document.getElementById("frequency").value = currentHmiSettings.frequency;
        
        showToast("設定頁面解鎖成功！", "success");
    } else {
        showToast("密碼錯誤，請重新確認！", "error");
    }
}

function saveHmiSettings(e) {
    e.preventDefault();
    if (!db || !isSettingsUnlocked) return;
    
    const threshold = parseFloat(document.getElementById("thresholdSlider").value);
    const startHour = parseInt(document.getElementById("startHour").value);
    const endHour = parseInt(document.getElementById("endHour").value);
    const freq = parseInt(document.getElementById("frequency").value);
    const newPass = document.getElementById("newPassword").value.trim();
    
    const updated = {
        threshold: threshold,
        start_hour: startHour,
        end_hour: endHour,
        frequency: freq
    };
    
    if (newPass) {
        updated.password = newPass;
        verifiedPassword = newPass;
    }
    
    showToast("正在更新設定...", "info");
    
    // 1. 寫入 Firestore status 文件
    db.collection("realtime_data").doc("status").update(updated)
      .then(() => {
          showToast("Firebase 設定更新成功！", "success");
          document.getElementById("newPassword").value = "";
          
          // 2. 同步寫回 Google Apps Script 試算表 (保持兩端同步)
          if (currentHmiSettings.webAppUrl) {
              syncSettingsToAppsScript(updated);
          }
      })
      .catch(err => {
          showToast("儲存設定失敗: " + err.message, "error");
      });
}

function syncSettingsToAppsScript(settings) {
    const payload = {
        action: "saveSettings",
        password: verifiedPassword,
        settings: {
            threshold: settings.threshold,
            startHour: settings.start_hour,
            endHour: settings.end_hour,
            frequency: settings.frequency,
            password: settings.password || verifiedPassword
        }
    };
    
    // 以 POST 異步發送給 Apps Script Web App
    fetch(currentHmiSettings.webAppUrl, {
        method: "POST",
        mode: "no-cors", // 防止跨域報錯
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(() => {
        showToast("雲端試算表設定同步指令已送出！", "success");
    })
    .catch(e => {
        console.error("同步至 Apps Script 失敗:", e);
    });
}

// ==================== 6. 聯絡人名冊 Real-time 讀寫 ==================== */
function unlockContactsSection() {
    const entered = document.getElementById("contactsPassword").value;
    if (!entered) {
        showToast("請輸入管理密碼！", "error");
        return;
    }
    
    if (entered === currentHmiSettings.password) {
        isContactsUnlocked = true;
        verifiedPassword = entered;
        
        document.getElementById("contactsAuthArea").style.display = "none";
        document.getElementById("contactsTableFields").classList.remove("locked");
        
        // 載入實時聯絡人名單
        loadContactsRealtime();
        showToast("聯絡人名冊解鎖成功！", "success");
    } else {
        showToast("密碼錯誤，請重新確認！", "error");
    }
}

function loadContactsRealtime() {
    if (!db || !isContactsUnlocked) return;
    
    // 註銷舊監聽
    if (contactsUnsubscribe) contactsUnsubscribe();
    
    contactsUnsubscribe = db.collection("contacts").orderBy("name").onSnapshot((snapshot) => {
        const tbody = document.querySelector("#contactsTable tbody");
        tbody.innerHTML = "";
        
        if (snapshot.empty) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim);">∅ 名冊為空，請點選右上角新增。</td></tr>`;
            return;
        }
        
        let index = 0;
        snapshot.forEach(doc => {
            const c = doc.data();
            const docId = doc.id;
            const tr = document.createElement("tr");
            
            tr.innerHTML = `
                <td><strong>${escapeHtml(c.name)}</strong></td>
                <td>${escapeHtml(c.email || '—')}</td>
                <td><code style="color: #60a5fa;">${escapeHtml(c.lineId || '—')}</code></td>
                <td>
                    <label class="switch">
                        <input type="checkbox" ${c.enabled ? 'checked' : ''} onchange="toggleContactStatus('${docId}', this.checked)">
                        <span class="slider"></span>
                    </label>
                    <span style="font-size: 12px; margin-left: 6px; color: ${c.enabled ? 'var(--neon-green)' : 'var(--text-dim)'}">
                        ${c.enabled ? '已啟用' : '已停用'}
                    </span>
                </td>
                <td>
                    <button class="tool-btn" style="background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 4px 10px;" onclick="deleteContact('${docId}', '${escapeHtml(c.name)}')">
                        <i class="fa-solid fa-trash"></i> 刪除
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
            index++;
        });
    }, (error) => {
        showToast("載入聯絡人失敗: " + error.message, "error");
    });
}

function toggleContactStatus(docId, enabled) {
    if (!db) return;
    db.collection("contacts").doc(docId).update({ enabled: enabled })
      .then(() => {
          showToast(`聯絡人狀態已更新`, "success");
          syncContactsToAppsScript();
      })
      .catch(e => showToast("更新失敗: " + e.message, "error"));
}

function openContactModal() {
    document.getElementById("contactForm").reset();
    document.getElementById("editContactIndex").value = "";
    document.getElementById("modalTitle").innerText = "新增聯絡收件人";
    document.getElementById("contactModal").classList.add("open");
}

function closeContactModal() {
    document.getElementById("contactModal").classList.remove("open");
}

function submitContactForm(e) {
    e.preventDefault();
    if (!db) return;
    
    const name = document.getElementById("contactName").value.trim();
    const email = document.getElementById("contactEmail").value.trim();
    const lineId = document.getElementById("contactLine").value.trim();
    const enabled = document.getElementById("contactEnabled").checked;
    
    if (lineId) {
        const prefix = lineId.charAt(0).toUpperCase();
        if (prefix !== 'U' && prefix !== 'C' && prefix !== 'R') {
            showToast("LINE ID 格式錯誤！個人必須是 U 開頭，群組是 C，聊天室是 R", "error");
            return;
        }
    }
    
    showToast("正在儲存聯絡人...", "info");
    
    // 直接寫入 Firestore 集合中
    db.collection("contacts").add({
        name: name,
        email: email,
        lineId: lineId,
        enabled: enabled
    })
    .then(() => {
        showToast("聯絡人新增成功！", "success");
        closeContactModal();
        syncContactsToAppsScript();
    })
    .catch(err => {
        showToast("新增失敗: " + err.message, "error");
    });
}

function deleteContact(docId, name) {
    if (!db) return;
    if (confirm(`確定要將聯絡人「${name}」從通報名單中移除嗎？`)) {
        db.collection("contacts").doc(docId).delete()
          .then(() => {
              showToast("聯絡人已刪除", "success");
              syncContactsToAppsScript();
          })
          .catch(e => showToast("刪除失敗: " + e.message, "error"));
    }
}

// 實時將聯絡人同步寫回 Google Apps Script 試算表第一分頁
function syncContactsToAppsScript() {
    if (!db || !currentHmiSettings.webAppUrl) return;
    
    // 獲取當前所有聯絡人並發送給 Apps Script
    db.collection("contacts").get().then(snapshot => {
        const list = [];
        snapshot.forEach(doc => {
            const c = doc.data();
            list.push({
                name: c.name,
                email: c.email || "",
                lineId: c.lineId || "",
                enabled: c.enabled
            });
        });
        
        const payload = {
            action: "saveContacts",
            password: verifiedPassword,
            contacts: list
        };
        
        fetch(currentHmiSettings.webAppUrl, {
            method: "POST",
            mode: "no-cors",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        })
        .then(() => {
            console.log("聯絡人名冊已成功推播同步給 Google 試算表！");
        })
        .catch(e => console.error("同步聯絡人失敗:", e));
    });
}

// ==================== 7. 通報歷史紀錄 Real-time 讀取 ==================== */
let allLogsData = []; // 用在搜尋與匯出

function loadLogsRealtime() {
    if (!db) return;
    
    // 監聽歷史通報紀錄 (依照時間遞減排列，最多前 100 筆)
    db.collection("history_logs").orderBy("timestamp", "desc").limit(100).onSnapshot((snapshot) => {
        allLogsData = [];
        const tbody = document.querySelector("#logsTable tbody");
        tbody.innerHTML = "";
        
        if (snapshot.empty) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim);">∅ 查無任何通報歷史紀錄。</td></tr>`;
            return;
        }
        
        snapshot.forEach(doc => {
            const log = doc.data();
            allLogsData.push(log);
        });
        
        renderLogsTable(allLogsData);
    }, (error) => {
        console.error("載入歷史紀錄失敗:", error);
    });
}

function renderLogsTable(data) {
    const tbody = document.querySelector("#logsTable tbody");
    tbody.innerHTML = "";
    
    data.forEach(log => {
        const tr = document.createElement("tr");
        const temp = parseFloat(log.temp);
        
        // 警報狀態樣式
        // 注意：「正常 (未超標)」含有「超標」，需排除「未超標」才不會誤判為紅色
        let alertBadgeClass = "badge normal";
        const alertText = log.alert_state;
        if (alertText.includes("高溫") || alertText.includes("警報") ||
            (alertText.includes("超標") && !alertText.includes("未超標"))) {
            alertBadgeClass = "badge danger";
        } else if (alertText.includes("回落") || alertText.includes("解除")) {
            alertBadgeClass = "badge success";
        }
        
        tr.innerHTML = `
            <td><strong>${escapeHtml(log.time)}</strong></td>
            <td>${log.threshold.toFixed(1)}°C</td>
            <td style="font-weight: 600; color: ${temp > log.threshold ? 'var(--neon-red)' : 'var(--text-main)'}">${temp === -99 ? '異常' : temp.toFixed(1) + '°C'}</td>
            <td>${escapeHtml(log.obs_time || '—')}</td>
            <td><span class="${alertBadgeClass}">${escapeHtml(log.alert_state)}</span></td>
            <td>
                <div class="badge-row">
                    <span style="font-weight: 600;">${escapeHtml(log.status_text)}</span>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function filterLogsTable() {
    const query = document.getElementById("logSearch").value.trim().toLowerCase();
    if (!query) {
        renderLogsTable(allLogsData);
        return;
    }
    
    const filtered = allLogsData.filter(log => {
        return log.time.toLowerCase().includes(query) ||
               log.alert_state.toLowerCase().includes(query) ||
               log.status_text.toLowerCase().includes(query) ||
               String(log.temp).includes(query);
    });
    
    renderLogsTable(filtered);
}

function exportLogsToCSV() {
    if (allLogsData.length === 0) {
        showToast("沒有資料可供匯出！", "error");
        return;
    }
    
    let csvContent = "\ufeff"; // BOM，防 Excel 亂碼
    csvContent += "通報時間,溫度閾值設定 (°C),通報環境溫度 (°C),氣象觀測時間,警報狀態,通知狀態\n";
    
    allLogsData.forEach(log => {
        const row = [
            `"${log.time}"`,
            log.threshold,
            log.temp,
            `"${log.obs_time || ''}"`,
            `"${log.alert_state}"`,
            `"${log.status_text}"`
        ];
        csvContent += row.join(",") + "\n";
    });
    
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    
    const today = new Date();
    const dateStr = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,'0')}-${String(today.getDate()).padStart(2,'0')}`;
    
    link.setAttribute("href", url);
    link.setAttribute("download", `環境溫度通報紀錄_${dateStr}.csv`);
    link.style.visibility = "hidden";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("CSV 紀錄檔下載成功！", "success");
}

// ==================== 8. 快速測試工具與心跳 (需管理密碼) ==================== */
function triggerFastAction(action) {
    // 取得驗證密碼
    let pass = verifiedPassword;
    if (!pass) {
        pass = prompt("請輸入 HMI 管理密碼進行快速驗證：");
        if (pass === null) return; // 取消
        if (pass !== currentHmiSettings.password) {
            showToast("密碼錯誤，拒絕執行！", "error");
            return;
        }
        verifiedPassword = pass; // 快取
    }
    
    if (!currentHmiSettings.webAppUrl) {
        showToast("錯誤：試算表 Web App URL 未配置，無法執行測試！", "error");
        return;
    }
    
    showToast("正在發送命令給雲端...", "info");
    
    const payload = {
        action: action,
        password: pass
    };
    
    fetch(currentHmiSettings.webAppUrl, {
        method: "POST",
        mode: "no-cors",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(() => {
        showToast("指令已成功觸發，請檢查您的 LINE / 信箱是否收到！", "success");
    })
    .catch(err => {
        showToast("指令執行失敗: " + err.message, "error");
    });
}

// ==================== 9. UI 輔助函式 ==================== */
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    
    let iconClass = "fa-solid fa-info-circle";
    if (type === "success") iconClass = "fa-solid fa-circle-check";
    else if (type === "error") iconClass = "fa-solid fa-circle-exclamation";
    
    toast.innerHTML = `<i class="${iconClass}"></i><span>${message}</span>`;
    container.appendChild(toast);
    
    // 3秒後淡出刪除
    setTimeout(() => {
        toast.classList.add("fade-out");
        toast.addEventListener("animationend", () => {
            toast.remove();
        });
    }, 4000);
}

function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// ==================== 10. 溫度變化趨勢圖繪製邏輯 ==================== */
function listenHistoryLogsForChart() {
    if (!db) return;
    
    // 註銷舊監聽
    if (chartUnsubscribe) chartUnsubscribe();
    
    // 即時 24H：只抓「現在往前 24 小時」的 realtime_logs 資料（每 10 分鐘 CWA 觀測）
    const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);
    
    chartUnsubscribe = db.collection("realtime_logs")
      .where("timestamp", ">=", oneDayAgo)
      .orderBy("timestamp", "asc")
      .onSnapshot((snapshot) => {
          allLogsForChart = [];
          snapshot.forEach(doc => {
              const d = doc.data();
              // 統一欄位格式：X 軸用 obs_time（氣象站實際觀測時間）
              allLogsForChart.push({
                  temp: d.temp,
                  time: d.obs_time || d.time,   // 優先用 obs_time，fallback 用 time
                  obs_time: d.obs_time || d.time,
                  timestamp: d.timestamp
              });
          });
          
          // 已按 timestamp asc 排序，直接繪製（過去 -> 現在）
          updateTrendChart(allLogsForChart);
      }, (error) => {
          console.error("監聽即時觀測紀錄圖表失敗:", error);
      });
}

function updateTrendChart(logs) {
    const ctx = document.getElementById('tempTrendChart');
    if (!ctx) return;
    
    // 降採樣邏輯：如果數據大於 200 點，則進行等距降採樣，確保瀏覽器繪製流暢
    let displayLogs = logs;
    if (logs.length > 200) {
        const step = Math.ceil(logs.length / 200);
        displayLogs = logs.filter((_, idx) => idx % step === 0);
    }
    
    // 篩選出有效溫度數據
    const chartData = displayLogs.map(log => parseFloat(log.temp)).filter(temp => !isNaN(temp) && temp !== -99);
    const validLogs = displayLogs.filter(log => !isNaN(parseFloat(log.temp)) && parseFloat(log.temp) !== -99);
    const labels = validLogs.map(log => {
        // 如果是歷史模式且總數據量大，X軸標記加上日期 (MM-DD HH:MM)
        if (chartMode === "history" && logs.length > 400) {
            const t = log.time;
            if (t && t.length >= 16) {
                return t.substring(5, 16);
            }
            return t;
        }
        return getShortTime(log.time);
    });
    
    // 取得當前設定的警報閾值，繪製輔助線
    const threshold = parseFloat(currentHmiSettings.threshold) || 28.0;
    const thresholdLine = Array(labels.length).fill(threshold);
    
    if (trendChart) {
        // 更新數據
        trendChart.data.labels = labels;
        trendChart.data.datasets[0].data = chartData;
        trendChart.data.datasets[1].data = thresholdLine;
        trendChart.data.datasets[1].label = `警報閾值 (${threshold.toFixed(1)}°C)`;
        trendChart.update('none');
    } else {
        // 首次初始化圖表
        const chartCtx = ctx.getContext('2d');
        trendChart = new Chart(chartCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '觀測溫度 (°C)',
                        data: chartData,
                        borderColor: '#22d3ee', // Cyan 400
                        borderWidth: 2,
                        pointBackgroundColor: '#22d3ee',
                        pointBorderColor: 'rgba(255,255,255,0.8)',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#22d3ee',
                        pointRadius: labels.length > 50 ? 0 : 3,
                        pointHoverRadius: 5,
                        fill: true,
                        backgroundColor: createChartGradient(chartCtx),
                        tension: 0.3
                    },
                    {
                        label: `警報閾值 (${threshold.toFixed(1)}°C)`,
                        data: thresholdLine,
                        borderColor: '#ef4444', // Red 500
                        borderWidth: 1.5,
                        borderDash: [5, 5],
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#f3f4f6',
                            font: {
                                family: "'Outfit', 'Noto Sans TC', sans-serif",
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 25, 40, 0.95)',
                        borderColor: 'rgba(255, 255, 255, 0.1)',
                        borderWidth: 1,
                        titleColor: '#f3f4f6',
                        bodyColor: '#22d3ee',
                        titleFont: {
                            family: "'Outfit', 'Noto Sans TC', sans-serif",
                            weight: 'bold'
                        },
                        bodyFont: {
                            family: "'Outfit', 'Noto Sans TC', sans-serif"
                        },
                        padding: 10,
                        displayColors: true
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                          },
                          ticks: {
                              color: '#9ca3af',
                              font: {
                                  family: "'Outfit', 'Noto Sans TC', sans-serif",
                                  size: 10
                              },
                              maxTicksLimit: window.innerWidth < 600 ? 6 : 12
                          }
                      },
                      y: {
                          grid: {
                              color: 'rgba(255, 255, 255, 0.05)',
                              drawBorder: false
                          },
                          ticks: {
                              color: '#9ca3af',
                              font: {
                                  family: "'Outfit', 'Noto Sans TC', sans-serif",
                                  size: 11
                              }
                          },
                          suggestedMin: 20,
                          suggestedMax: 35
                      }
                  }
              }
          });
      }
  }

  function createChartGradient(ctx) {
      const gradient = ctx.createLinearGradient(0, 0, 0, 300);
      gradient.addColorStop(0, 'rgba(34, 211, 238, 0.25)');
      gradient.addColorStop(1, 'rgba(34, 211, 238, 0.0)');
      return gradient;
  }

  function getShortTime(obsTimeStr) {
      if (!obsTimeStr) return "";
      const parts = obsTimeStr.split(" ");
      if (parts.length < 2) return obsTimeStr;
      const timeParts = parts[1].split(":");
      if (timeParts.length < 2) return parts[1];
      return `${timeParts[0]}:${timeParts[1]}`;
  }

  // 初始化日期選擇器 (預設 7 天前到今天)
  function initChartDateInputs() {
      const startInput = document.getElementById("chartStartDate");
      const endInput = document.getElementById("chartEndDate");
      if (!startInput || !endInput) return;
      
      const today = new Date();
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(today.getDate() - 7);
      
      endInput.value = formatDateToYYYYMMDD(today);
      startInput.value = formatDateToYYYYMMDD(sevenDaysAgo);
  }

  function formatDateToYYYYMMDD(date) {
      const yyyy = date.getFullYear();
      const mm = String(date.getMonth() + 1).padStart(2, '0');
      const dd = String(date.getDate()).padStart(2, '0');
      return `${yyyy}-${mm}-${dd}`;
  }

  // 切換圖表模式
  function setChartMode(mode) {
      if (chartMode === mode) return;
      chartMode = mode;
      
      const btnRealtime = document.getElementById("btnChartRealtime");
      const btnHistory = document.getElementById("btnChartHistory");
      const filterRow = document.getElementById("chartFilterRow");
      const title = document.getElementById("chartTitle");
      
      if (mode === "realtime") {
          btnRealtime.classList.add("active");
          btnHistory.classList.remove("active");
          filterRow.style.display = "none";
          title.innerText = "📈 即時24小時溫度趨勢";
          
          // 重新開啟即時上報監聽
          listenHistoryLogsForChart();
      } else {
          btnRealtime.classList.remove("active");
          btnHistory.classList.add("active");
          filterRow.style.display = "flex";
          title.innerText = "📈 歷史區間溫度趨勢";
          
          // 關閉即時監聽，不讓即時數據打擾查詢
          if (chartUnsubscribe) {
              chartUnsubscribe();
              chartUnsubscribe = null;
          }
          
          // 若有已有查詢結果直接呈現，否則預設執行查詢
          if (historyChartLogs.length > 0) {
              updateTrendChart(historyChartLogs);
          } else {
              queryHistoricalChartData();
          }
      }
  }

  // 查詢歷史區間數據 (最大 90 天以防止讀取量暴增)
  function queryHistoricalChartData() {
      if (!db) {
          showToast("Firebase 未連線，無法查詢！", "error");
          return;
      }
      
      const startInput = document.getElementById("chartStartDate");
      const endInput = document.getElementById("chartEndDate");
      const loader = document.getElementById("chartLoader");
      const btnQuery = document.getElementById("btnChartQuery");
      
      if (!startInput.value || !endInput.value) {
          showToast("請選擇開始與結束日期！", "error");
          return;
      }
      
      const startDate = new Date(startInput.value);
      const endDate = new Date(endInput.value);
      
      if (startDate > endDate) {
          showToast("開始日期不能晚於結束日期！", "error");
          return;
      }
      
      const diffTime = Math.abs(endDate - startDate);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      if (diffDays > 90) {
          showToast("查詢區間最大限制為 90 天，以維護系統效能！", "warning");
          return;
      }
      
      startDate.setHours(0, 0, 0, 0);
      const startMs = startDate.getTime();
      
      endDate.setHours(23, 59, 59, 999);
      const endMs = endDate.getTime();
      
      loader.style.display = "flex";
      btnQuery.disabled = true;
      
      db.collection("history_logs")
        .where("timestamp", ">=", startMs)
        .where("timestamp", "<=", endMs)
        .orderBy("timestamp", "asc")
        .get()
        .then((querySnapshot) => {
            historyChartLogs = [];
            querySnapshot.forEach(doc => {
                historyChartLogs.push(doc.data());
            });
            
            if (historyChartLogs.length === 0) {
                showToast("該時間區段內無觀測記錄！", "info");
                if (trendChart) {
                    trendChart.destroy();
                    trendChart = null;
                }
            } else {
                updateTrendChart(historyChartLogs);
                showToast(`查詢成功，載入 ${historyChartLogs.length} 筆觀測點！`, "success");
            }
        })
        .catch((error) => {
            console.error("歷史資料庫查詢失敗:", error);
            showToast("查詢失敗: " + error.message, "error");
        })
        .finally(() => {
            loader.style.display = "none";
            btnQuery.disabled = false;
        });
  }
