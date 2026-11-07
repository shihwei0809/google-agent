// 永豐 Shioaji 即時看盤終端前端引擎 (AGY Local)
let chart, candleSeries, volumeSeries;
let currentSymbol = "2330";
let currentMode = "SIMULATION";
let ws = null;
let reconnectTimer = null;
let currentRefPrice = 1000;
let tapeList = [];
let symbolsData = {};

// 初始化 TradingView 圖表
function initChart() {
  const container = document.getElementById("chartContainer");
  container.innerHTML = "";

  chart = LightweightCharts.createChart(container, {
    layout: {
      background: { color: "#0b0e14" },
      textColor: "#9ca3af",
    },
    grid: {
      vertLines: { color: "#1a202c" },
      horzLines: { color: "#1a202c" },
    },
    crosshair: {
      mode: LightweightCharts.CrosshairMode.Normal,
    },
    rightPriceScale: {
      borderColor: "#262e3d",
      scaleMargins: {
        top: 0.1,
        bottom: 0.25,
      },
    },
    timeScale: {
      borderColor: "#262e3d",
      timeVisible: true,
      secondsVisible: false,
    },
  });

  // 台股習慣：上漲紅色，下跌綠色
  candleSeries = chart.addCandlestickSeries({
    upColor: "#ef4444",
    downColor: "#10b981",
    borderUpColor: "#ef4444",
    borderDownColor: "#10b981",
    wickUpColor: "#ef4444",
    wickDownColor: "#10b981",
  });

  volumeSeries = chart.addHistogramSeries({
    color: "#26a69a",
    priceFormat: {
      type: "volume",
    },
    priceScaleId: "",
    scaleMargins: {
      top: 0.8,
      bottom: 0,
    },
  });

  window.addEventListener("resize", () => {
    if (chart && container) {
      chart.applyOptions({
        width: container.clientWidth,
        height: container.clientHeight,
      });
    }
  });

  // 初次適配尺寸
  setTimeout(() => {
    chart.applyOptions({
      width: container.clientWidth,
      height: container.clientHeight,
    });
  }, 100);
}

// 載入標的歷史 K 線
async function loadSymbolHistory(symbol) {
  try {
    const res = await fetch(`/api/history/${symbol}`);
    const data = await res.json();
    currentRefPrice = data.state ? data.state.ref_price : 100;

    // 更新圖表歷史資料
    if (data.bars && data.bars.length > 0) {
      const candles = data.bars.map((b) => ({
        time: b.time,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      }));
      const vols = data.bars.map((b) => ({
        time: b.time,
        value: b.volume,
        color: b.close >= b.open ? "rgba(239, 68, 68, 0.4)" : "rgba(16, 185, 129, 0.4)",
      }));
      candleSeries.setData(candles);
      volumeSeries.setData(vols);
      chart.timeScale().fitContent();
    }

    // 更新頂部總覽
    if (data.state) {
      updateSummaryUI(data.state);
      updateDepthUI(data.state.bids, data.state.asks);
    }
  } catch (err) {
    console.error("載入標的歷史失敗:", err);
  }
}

// 更新總覽 UI
function updateSummaryUI(state) {
  document.getElementById("stockCode").innerText = state.symbol;
  document.getElementById("stockName").innerText = state.name;

  const lastP = state.last_price;
  const refP = state.ref_price;
  const diff = Math.round((lastP - refP) * 100) / 100;
  const pct = Math.round((diff / refP) * 10000) / 100;

  const pEl = document.getElementById("currentPrice");
  const chgEl = document.getElementById("priceChange");
  const pctEl = document.getElementById("pricePctChange");

  pEl.innerText = lastP.toFixed(2);
  const sign = diff > 0 ? "+" : "";
  chgEl.innerText = `${sign}${diff.toFixed(2)}`;
  pctEl.innerText = `(${sign}${pct.toFixed(2)}%)`;

  const colorClass = diff > 0 ? "up" : diff < 0 ? "down" : "equal";
  pEl.className = `price-large ${colorClass}`;
  chgEl.className = `change-val ${colorClass}`;
  pctEl.className = `change-pct ${colorClass}`;

  document.getElementById("metricHigh").innerText = state.high ? state.high.toFixed(2) : "--";
  document.getElementById("metricLow").innerText = state.low ? state.low.toFixed(2) : "--";
  document.getElementById("metricOpen").innerText = state.open ? state.open.toFixed(2) : "--";
  document.getElementById("metricRef").innerText = refP.toFixed(2);
  document.getElementById("metricVolume").innerText = (state.volume || state.total_volume || 0).toLocaleString();
}

// 更新五檔委託 UI
function updateDepthUI(bids, asks) {
  const container = document.getElementById("depthBody");
  if (!bids || !asks) return;

  const maxVol = Math.max(
    ...bids.map((b) => b.volume),
    ...asks.map((a) => a.volume),
    1
  );

  let html = "";
  for (let i = 0; i < 5; i++) {
    const b = bids[i] || { price: 0, volume: 0 };
    const a = asks[i] || { price: 0, volume: 0 };

    const bPct = Math.round((b.volume / maxVol) * 100);
    const aPct = Math.round((a.volume / maxVol) * 100);

    const bClass = b.price > currentRefPrice ? "up" : b.price < currentRefPrice ? "down" : "equal";
    const aClass = a.price > currentRefPrice ? "up" : a.price < currentRefPrice ? "down" : "equal";

    html += `
      <div class="depth-row">
        <div class="depth-bid-bg" style="width: ${bPct}%"></div>
        <div class="depth-ask-bg" style="width: ${aPct}%"></div>
        <span class="depth-val">${b.volume}</span>
        <span class="depth-val ${bClass}">${b.price.toFixed(2)}</span>
        <span class="depth-val ${aClass}">${a.price.toFixed(2)}</span>
        <span class="depth-val">${a.volume}</span>
      </div>
    `;
  }
  container.innerHTML = html;
}

// 新增逐筆成交流水帳
function prependTape(tick) {
  tapeList.unshift(tick);
  if (tapeList.length > 35) tapeList.pop();

  const container = document.getElementById("tapeBody");
  const isBuy = tick.tick_type === "buy";
  const tagClass = isBuy ? "tag-up" : "tag-down";
  const tagText = isBuy ? "外盤買" : "內盤賣";
  const pClass = tick.price > tick.ref_price ? "up" : tick.price < tick.ref_price ? "down" : "equal";

  const rows = tapeList.map(
    (t) => `
    <div class="tape-row">
      <span>${t.time}</span>
      <span class="${t.price > t.ref_price ? "up" : t.price < t.ref_price ? "down" : "equal"}">${t.price.toFixed(2)}</span>
      <span>${t.volume}</span>
      <span><span class="tape-tag ${t.tick_type === "buy" ? "tag-up" : "tag-down"}">${t.tick_type === "buy" ? "外盤" : "內盤"}</span></span>
    </div>
  `
  );
  container.innerHTML = rows.join("");
}

// 建立 WebSocket 即時連線
function connectWS() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${location.host}/ws/market`;

  const badge = document.getElementById("connBadge");
  const statusText = document.getElementById("connStatusText");

  statusText.innerText = "連線中...";
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    badge.className = currentMode === "SIMULATION" ? "status-badge simulation" : "status-badge";
    statusText.innerText = currentMode === "SIMULATION" ? "模擬即時盤" : "Shioaji 實盤";
    // 送出目前訂閱標的
    ws.send(JSON.stringify({ action: "subscribe", symbol: currentSymbol }));
  };

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.type === "welcome") {
      currentMode = msg.mode;
      badge.className = currentMode === "SIMULATION" ? "status-badge simulation" : "status-badge";
      statusText.innerText = currentMode === "SIMULATION" ? "模擬即時盤" : "Shioaji 實盤";
      return;
    }

    if (msg.type === "tick") {
      // 若是當前關注標的，更新主圖與五檔、明細
      if (msg.symbol === currentSymbol) {
        updateSummaryUI(msg);
        updateDepthUI(msg.bids, msg.asks);
        prependTape(msg);

        // 即時推播 K 線更新
        if (msg.bar && candleSeries) {
          candleSeries.update({
            time: msg.bar.time,
            open: msg.bar.open,
            high: msg.bar.high,
            low: msg.bar.low,
            close: msg.bar.close,
          });
          volumeSeries.update({
            time: msg.bar.time,
            value: msg.bar.volume,
            color: msg.bar.close >= msg.bar.open ? "rgba(239, 68, 68, 0.4)" : "rgba(16, 185, 129, 0.4)",
          });
        }
      }

      // 同步更新自選股列表現價
      updateWatchlistRow(msg);
    }
  };

  ws.onclose = () => {
    badge.className = "status-badge simulation";
    statusText.innerText = "斷線重連中...";
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(connectWS, 2500);
  };

  ws.onerror = () => {
    ws.close();
  };
}

// 載入自選股與快速膠囊
async function loadSymbols() {
  try {
    const res = await fetch("/api/symbols");
    const list = await res.json();
    const watchlist = document.getElementById("watchlistContainer");
    const quickSymbols = document.getElementById("quickSymbols");

    let watchHtml = "";
    let quickHtml = "";

    list.forEach((item) => {
      symbolsData[item.symbol] = item;
      const isUp = item.change > 0;
      const isDown = item.change < 0;
      const cClass = isUp ? "up" : isDown ? "down" : "equal";
      const sign = isUp ? "+" : "";

      watchHtml += `
        <div class="watch-item ${item.symbol === currentSymbol ? "active" : ""}" data-sym="${item.symbol}" onclick="switchSymbol('${item.symbol}')">
          <div>
            <div class="item-sym">${item.symbol}</div>
            <div class="item-name">${item.name}</div>
          </div>
          <div>
            <div class="item-price ${cClass}" id="watch-p-${item.symbol}">${item.last_price.toFixed(2)}</div>
            <div class="item-change ${cClass}" id="watch-c-${item.symbol}">${sign}${item.pct_change.toFixed(2)}%</div>
          </div>
        </div>
      `;

      quickHtml += `
        <div class="symbol-pill ${item.symbol === currentSymbol ? "active" : ""}" onclick="switchSymbol('${item.symbol}')">
          <span>${item.symbol} ${item.name}</span>
          <span class="pill-price ${cClass}" id="pill-p-${item.symbol}">${item.last_price.toFixed(1)}</span>
        </div>
      `;
    });

    watchlist.innerHTML = watchHtml;
    quickSymbols.innerHTML = quickHtml;
  } catch (err) {
    console.error("載入自選標的失敗:", err);
  }
}

// 更新自選股單列價格
function updateWatchlistRow(tick) {
  const pEl = document.getElementById(`watch-p-${tick.symbol}`);
  const cEl = document.getElementById(`watch-c-${tick.symbol}`);
  const pillEl = document.getElementById(`pill-p-${tick.symbol}`);

  const isUp = tick.change > 0;
  const isDown = tick.change < 0;
  const cClass = isUp ? "up" : isDown ? "down" : "equal";
  const sign = isUp ? "+" : "";

  if (pEl) {
    pEl.innerText = tick.price.toFixed(2);
    pEl.className = `item-price ${cClass}`;
  }
  if (cEl) {
    cEl.innerText = `${sign}${tick.pct_change.toFixed(2)}%`;
    cEl.className = `item-change ${cClass}`;
  }
  if (pillEl) {
    pillEl.innerText = tick.price.toFixed(1);
    pillEl.className = `pill-price ${cClass}`;
  }
}

// 切換當前檢視標的
async function switchSymbol(sym) {
  sym = sym.toUpperCase();
  currentSymbol = sym;
  tapeList = [];
  document.getElementById("tapeBody").innerHTML = "";

  // 標記高亮
  document.querySelectorAll(".watch-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.sym === sym);
  });

  // 通知後端訂閱切換
  await fetch("/api/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol: sym }),
  });

  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action: "subscribe", symbol: sym }));
  }

  // 載入歷史資料
  await loadSymbolHistory(sym);
}

// 事件綁定
document.addEventListener("DOMContentLoaded", async () => {
  initChart();
  await loadSymbols();
  await loadSymbolHistory(currentSymbol);
  connectWS();

  // 搜尋按鈕
  document.getElementById("btnSubscribe").addEventListener("click", () => {
    const input = document.getElementById("symbolInput");
    const val = input.value.trim();
    if (val) {
      switchSymbol(val);
      input.value = "";
    }
  });

  document.getElementById("symbolInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      document.getElementById("btnSubscribe").click();
    }
  });

  // Modal 彈窗控制
  const modal = document.getElementById("settingsModal");
  document.getElementById("btnOpenSettings").addEventListener("click", () => {
    modal.classList.add("active");
  });
  document.getElementById("btnCloseSettings").addEventListener("click", () => {
    modal.classList.remove("active");
  });
  document.getElementById("btnCancelSettings").addEventListener("click", () => {
    modal.classList.remove("active");
  });

  // 儲存設定
  document.getElementById("btnSaveSettings").addEventListener("click", async () => {
    const mode = document.querySelector('input[name="mode"]:checked').value;
    const apiKey = document.getElementById("cfgApiKey").value;
    const secretKey = document.getElementById("cfgSecretKey").value;
    const personId = document.getElementById("cfgPersonId").value;

    const res = await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: mode,
        api_key: apiKey,
        secret_key: secretKey,
        person_id: personId,
      }),
    });
    const result = await res.json();
    alert(result.message || "設定已儲存");
    currentMode = mode;
    modal.classList.remove("active");
  });
});
