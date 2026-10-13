let activeChartLogs = [];
let currentChartMode = "realtime";

function formatDateToYYYYMMDD(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

// Cloudflare D1 版 app.js

let tempChart = null;
window.currentLogs = [];
const DEMO_PASSWORD = 'admin';

// PWA Install Banner Logic
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    document.getElementById('install-banner').style.display = 'block';
});
document.getElementById('install-banner').addEventListener('click', async () => {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
            document.getElementById('install-banner').style.display = 'none';
        }
        deferredPrompt = null;
    }
});

// UI Tabs Logic
document.querySelectorAll('.nav-item').forEach(nav => {
    nav.addEventListener('click', (e) => {
        if(!nav.hasAttribute('data-tab')) return;
        e.preventDefault();
        const tabId = nav.getAttribute('data-tab');
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        
        document.querySelectorAll(`.nav-item[data-tab="${tabId}"]`).forEach(n => n.classList.add('active'));
        const panel = document.getElementById(`tab-${tabId}`);
        if(panel) panel.classList.add('active');
    });
});

function updateStatus(dotId, textId, isOnline, text) {
    const dot = document.getElementById(dotId);
    const textEl = document.getElementById(textId);
    if(dot && textEl) {
        dot.className = 'status-dot ' + (isOnline ? 'online' : 'offline');
        textEl.innerText = text;
    }
}

async function fetchData() {
    try {
        const res = await fetch('/api/data');
        if (!res.ok) throw new Error('Network response was not ok');
        const data = await res.json();
        
        updateStatus('d1Dot', 'd1StatusText', true, 'API 已連線');
        
        if (data.logs && data.logs.length > 0) {
            window.currentLogs = data.logs;
            const current = data.logs[0];
            
            // Update Dashboard
            const currentTemp = document.getElementById('currentTempDisplay');
            if(currentTemp) currentTemp.innerText = current.temperature.toFixed(1);
            
            const obsTime = document.getElementById('obsTimeDisplay');
            if(obsTime) obsTime.innerText = current.obs_time;
            
                        const tempStatus = document.getElementById('tempStatusDisplay');
            const ring = document.getElementById('tempGaugeRing');
            const threshold = parseFloat(data.config.threshold || 28.0);
            if(current.temperature > threshold) {
                if(tempStatus) { tempStatus.innerText = '高溫警報'; tempStatus.className = 'temp-status danger'; }
                if(ring) ring.className = 'gauge-ring danger';
            } else if (current.temperature >= threshold - 1.5) {
                if(tempStatus) { tempStatus.innerText = '接近閾值'; tempStatus.className = 'temp-status warning'; }
                if(ring) ring.className = 'gauge-ring warning';
            } else {
                if(tempStatus) { tempStatus.innerText = '正常 (未超標)'; tempStatus.className = 'temp-status'; }
                if(ring) ring.className = 'gauge-ring';
            }
            
            // Heartbeat Logic (if updated in last 5 mins)
            const lastTime = new Date(current.timestamp + 'Z'); // UTC
            const now = new Date();
            const diffMin = (now - lastTime) / 60000;
            if (diffMin < 5) {
                updateStatus('heartbeatDot', 'heartbeatStatusText', true, '本機在線');
                const hb = document.getElementById('dashHeartbeatStatus');
                if(hb) { hb.innerText = '在線 (正常)'; hb.className = 'badge bg-success'; }
            } else {
                updateStatus('heartbeatDot', 'heartbeatStatusText', false, '本機離線');
                const hb = document.getElementById('dashHeartbeatStatus');
                if(hb) { hb.innerText = '離線'; hb.className = 'badge bg-danger'; }
            }
            const lastHb = document.getElementById('lastHeartbeatDisplay');
            if(lastHb) lastHb.innerText = `最後心跳時間：${current.timestamp}`;

            // Update Chart
            if (currentChartMode === "realtime") {
                updateChart(data.logs, data.config.threshold || 28.0, "realtime");
            }
            
            // Update Logs Table
            updateLogsTable(data.logs, data.config.threshold || 28.0);
        }
        
        if (data.config) {
            const dashThreshold = document.getElementById('dashThreshold');
            if(dashThreshold) dashThreshold.innerText = `${data.config.threshold || '--.-'}°C`;
            const tv = document.getElementById('thresholdVal');
            if(tv) tv.innerText = data.config.threshold || '--';
            const ts = document.getElementById('thresholdSlider');
            if(ts) ts.value = data.config.threshold || 28.0;
            
            const dashFreq = document.getElementById('dashFrequency');
            if(dashFreq) dashFreq.innerText = `${data.config.frequency || 60} 分鐘`;
            
            const dashTime = document.getElementById('dashTimeWindow');
            if(dashTime) {
                const s = (data.config.start_hour || '0').padStart(2, '0');
                const e = (data.config.end_hour || '24').padStart(2, '0');
                dashTime.innerText = `${s}:00 - ${e}:00`;
            }
        }

    } catch (err) {
        console.error(err);
        updateStatus('d1Dot', 'd1StatusText', false, 'API 斷線');
    }
}

function updateChart(logs, threshold, mode = "realtime") {
    const canvas = document.getElementById("tempTrendChart");
    if(!canvas) return;
    const ctx = canvas.getContext("2d");
    
    // 確保由舊到新排序 (遞增)
    const chartLogs = [...logs].sort((a,b) => new Date(a.obs_time) - new Date(b.obs_time));
    activeChartLogs = chartLogs;
    
    let labels;
    if (mode === "realtime") {
        // 24小時即時趨勢：X軸顯示時間 (HH:mm)
        labels = chartLogs.map(log => log.obs_time ? log.obs_time.substring(11, 16) : "");
    } else {
        // 歷史查詢區間：X軸顯示日期
        const firstDate = chartLogs[0]?.obs_time ? chartLogs[0].obs_time.substring(0, 10) : "";
        const lastDate = chartLogs[chartLogs.length - 1]?.obs_time ? chartLogs[chartLogs.length - 1].obs_time.substring(0, 10) : "";
        const isSingleDay = (firstDate === lastDate);
        
        if (isSingleDay) {
            // 同一天：顯示時間 (HH:mm)
            labels = chartLogs.map(log => log.obs_time ? log.obs_time.substring(11, 16) : "");
        } else {
            // 跨多天：顯示日期 MM/DD (若跨年份則顯示 YYYY/MM/DD)
            const firstYear = firstDate.substring(0, 4);
            const lastYear = lastDate.substring(0, 4);
            const crossYear = (firstYear && lastYear && firstYear !== lastYear);
            
            labels = chartLogs.map(log => {
                if (!log.obs_time) return "";
                const datePart = log.obs_time.split(" ")[0];
                const parts = datePart.split("-");
                if (crossYear) {
                    return parts[0] + "/" + parts[1] + "/" + parts[2];
                } else {
                    return parts[1] + "/" + parts[2]; // MM/DD 如 05/01, 10/13
                }
            });
        }
    }
    
    const temps = chartLogs.map(log => log.temperature);
    const thresholds = chartLogs.map(() => parseFloat(threshold));
    const pointRadius = chartLogs.length > 50 ? (chartLogs.length > 200 ? 0 : 1.5) : 3;

    const yMin = temps.length ? Math.floor(Math.min(...temps, parseFloat(threshold)) - 2) : 20;
    const yMax = temps.length ? Math.ceil(Math.max(...temps, parseFloat(threshold)) + 2) : 35;

    if (tempChart) {
        tempChart.currentLogs = chartLogs;
        tempChart.data.labels = labels;
        tempChart.data.datasets[0].data = temps;
        tempChart.data.datasets[0].pointRadius = pointRadius;
        tempChart.data.datasets[1].data = thresholds;
        tempChart.data.datasets[1].label = "警報閾值 (" + threshold + "°C)";
        tempChart.options.scales.y.min = yMin;
        tempChart.options.scales.y.max = yMax;
        tempChart.update();
    } else {
        tempChart = new Chart(ctx, {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "觀測溫度 (°C)",
                        data: temps,
                        borderColor: "#00e5ff",
                        backgroundColor: "rgba(0, 229, 255, 0.1)",
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true,
                        pointRadius: pointRadius,
                        pointBackgroundColor: "#fff"
                    },
                    {
                        label: "警報閾值 (" + threshold + "°C)",
                        data: thresholds,
                        borderColor: "#ff4d4d",
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
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: "rgba(255, 255, 255, 0.1)" },
                        ticks: { color: "#ccc" },
                        min: yMin,
                        max: yMax
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: "#ccc", maxTicksLimit: 12 }
                    }
                },
                plugins: {
                    legend: { labels: { color: "#fff" } },
                    tooltip: {
                        callbacks: {
                            title: function(tooltipItems) {
                                const idx = tooltipItems[0].dataIndex;
                                const item = activeChartLogs[idx] || (tooltipItems[0].chart && tooltipItems[0].chart.currentLogs ? tooltipItems[0].chart.currentLogs[idx] : null);
                                return item ? "觀測時間：" + item.obs_time : "";
                            },
                            label: function(context) {
                                return context.dataset.label + ": " + context.parsed.y.toFixed(1) + "°C";
                            }
                        }
                    }
                }
            }
        });
    }
}

function updateLogsTable(logs, threshold) {
    const tbody = document.querySelector('#logsTable tbody');
    if(!tbody) return;
    tbody.innerHTML = '';
    
    logs.slice(0, 50).forEach(log => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${log.timestamp}</td>
            <td>${threshold}°C</td>
            <td style="color: ${log.temperature >= threshold ? '#ff4d4d' : '#00e5ff'}">${log.temperature}°C</td>
            <td>${log.obs_time}</td>
            <td><span class="badge ${log.status === 'HOT' ? 'bg-danger' : 'bg-success'}">${log.status}</span></td>
            <td>Cloudflare D1</td>
        `;
        tbody.appendChild(tr);
    });
}

function unlockSettingsSection() {
    const pwd = document.getElementById('settingsPassword').value;
    if(pwd === DEMO_PASSWORD || pwd === '1234') {
        document.getElementById('settingsAuthArea').style.display = 'none';
        document.getElementById('settingsConfigFields').classList.remove('locked');
        alert('設定區已解鎖！');
    } else {
        alert('密碼錯誤！提示：admin');
    }
}

function unlockContactsSection() {
    const pwd = document.getElementById('contactsPassword').value;
    if(pwd === DEMO_PASSWORD || pwd === '1234') {
        document.getElementById('contactsAuthArea').style.display = 'none';
        document.getElementById('contactsTableFields').classList.remove('locked');
        alert('聯絡人區已解鎖！');
    } else {
        alert('密碼錯誤！提示：admin');
    }
}

async function exportLogsToExcel() {
    try {
        const btn = document.querySelector('button[onclick="exportLogsToExcel()"]');
        if(btn) { btn.disabled = true; btn.innerHTML = '查詢歷史紀錄'; }

        const res = await fetch('/api/export');
        const logs = await res.json();
        
        if (!logs || logs.length === 0) {
            alert('目前沒有資料可以匯出');
            if(btn) { btn.disabled = false; btn.innerHTML = '查詢歷史紀錄'; }
            return;
        }

        const dailyData = {};
        let minTime = logs[0].timestamp;
        let maxTime = logs[logs.length-1].timestamp;
        
        logs.forEach(log => {
            const dateStr = log.timestamp.split(' ')[0]; // yyyy-mm-dd
            const mdStr = dateStr.substring(5).replace('-', '月') + '日'; // mm月dd日
            if (!dailyData[mdStr]) dailyData[mdStr] = [];
            dailyData[mdStr].push(log);
        });

        const wb = XLSX.utils.book_new();
        
        const summaryData = [
            ['24小時趨勢備份', '季度單一匯總表總覽'],
            [],
            ['【匯總統計與月份標註】'],
            ['項目', '內容說明'],
            ['資料類型', '24小時環境溫度趨勢備份紀錄'],
            ['總資料筆數', logs.length + ' 筆'],
            ['最早記錄時間', minTime],
            ['最新記錄時間', maxTime],
            [],
            ['【各月份明細統計】'],
            ['月份', '記錄筆數', '起始記錄時間', '結束記錄時間', '平均溫度 (°C)', '最高溫度 (°C)', '最低溫度 (°C)']
        ];

        for (const [day, dayLogs] of Object.entries(dailyData)) {
            const count = dayLogs.length;
            const start = dayLogs[0].timestamp;
            const end = dayLogs[count-1].timestamp;
            const temps = dayLogs.map(l => l.temperature);
            const avg = (temps.reduce((a,b) => a+b, 0) / count).toFixed(1);
            const max = Math.max(...temps);
            const min = Math.min(...temps);
            summaryData.push([day, count + ' 筆', start, end, avg, max, min]);
        }

        const wsSummary = XLSX.utils.aoa_to_sheet(summaryData);
        XLSX.utils.book_append_sheet(wb, wsSummary, "季度單一匯總表總覽");

        for (const [day, dayLogs] of Object.entries(dailyData)) {
            const sheetData = [['記錄時間', '溫度 (°C)', '氣象觀測時間', '系統狀態']];
            dayLogs.forEach(log => {
                sheetData.push([log.timestamp, log.temperature, log.obs_time, log.status]);
            });
            const wsDaily = XLSX.utils.aoa_to_sheet(sheetData);
            XLSX.utils.book_append_sheet(wb, wsDaily, day);
        }

        XLSX.writeFile(wb, '2026-Q3_24小時趨勢備份.xlsx');
        if(btn) { btn.disabled = false; btn.innerHTML = '查詢歷史紀錄'; }

    } catch (err) {
        console.error(err);
        alert('匯出失敗');
        const btn = document.querySelector('button[onclick="exportLogsToExcel()"]');
        if(btn) { btn.disabled = false; btn.innerHTML = '查詢歷史紀錄'; }
    }
}

// Initial fetch & set interval
fetchData();
setInterval(fetchData, 60000);

function setChartMode(mode) {
    currentChartMode = mode;
    document.getElementById("btnChartRealtime").classList.remove("active");
    document.getElementById("btnChartHistory").classList.remove("active");
    
    if (mode === "realtime") {
        document.getElementById("btnChartRealtime").classList.add("active");
        document.getElementById("chartFilterRow").style.display = "none";
        document.getElementById("chartTitle").innerHTML = "📈 即時24小時溫度趨勢";
        if(window.currentLogs && window.currentLogs.length > 0) {
            updateChart(window.currentLogs, parseFloat(document.getElementById("dashThreshold").innerText) || 28.0, "realtime");
        }
    } else {
        document.getElementById("btnChartHistory").classList.add("active");
        document.getElementById("chartFilterRow").style.display = "flex";
        
        const startInput = document.getElementById("chartStartDate");
        const endInput = document.getElementById("chartEndDate");
        if(!startInput.value || !endInput.value) {
            const today = new Date();
            const sevenDaysAgo = new Date();
            sevenDaysAgo.setDate(today.getDate() - 7);
            
            endInput.value = formatDateToYYYYMMDD(today);
            startInput.value = formatDateToYYYYMMDD(sevenDaysAgo);
        }
        
        queryHistoricalChartData();
    }
}

async function queryHistoricalChartData() {
    const startDate = document.getElementById("chartStartDate").value;
    const endDate = document.getElementById("chartEndDate").value;
    
    if(!startDate || !endDate) { alert("請選擇開始與結束日期"); return; }
    
    const btn = document.getElementById("btnChartQuery");
    const loader = document.getElementById("chartLoader");
    if(btn) btn.style.display = "none";
    if(loader) loader.style.display = "inline-block";
    
    try {
        const res = await fetch("/api/export");
        const allLogs = await res.json();
        
        const start = startDate + " 00:00:00";
        const end = endDate + " 23:59:59";
        
        const filtered = allLogs.filter(log => log.obs_time && log.obs_time >= start && log.obs_time <= end);
        
        if(filtered.length === 0) {
            alert("該區間沒有資料");
        } else {
            // Sort ascending chronologically
            filtered.sort((a,b) => new Date(a.obs_time) - new Date(b.obs_time));
            
            // 降採樣：如果超過 300 點，等距抽樣確保繪製順暢
            let displayLogs = filtered;
            if (filtered.length > 300) {
                const step = Math.ceil(filtered.length / 300);
                displayLogs = filtered.filter((_, idx) => idx % step === 0);
            }
            
            updateChart(displayLogs, parseFloat(document.getElementById("dashThreshold").innerText) || 28.0, "history");
            
            document.getElementById("chartTitle").innerHTML = "📈 歷史溫度趨勢 (" + startDate + " ~ " + endDate + ")";
        }
    } catch(err) {
        console.error(err);
        alert("查詢失敗");
    }
    
    if(btn) btn.style.display = "inline-block";
    if(loader) loader.style.display = "none";
}





