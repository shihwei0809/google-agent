import os
import sys
import time
import json
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Set, Any
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 強制 UTF-8 輸出，防止 Windows cp950 編碼崩潰
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 載入環境變數
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global sim_task
    sim_task = asyncio.create_task(simulation_loop())
    yield
    if sim_task:
        sim_task.cancel()

app = FastAPI(title="永豐 Shioaji 即時看盤儀表板", version="1.0.0", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 系統狀態與設定
CONFIG = {
    "api_key": os.getenv("SHIOAJI_API_KEY", ""),
    "secret_key": os.getenv("SHIOAJI_SECRET_KEY", ""),
    "person_id": os.getenv("SHIOAJI_PERSON_ID", ""),
    "mode": os.getenv("SHIOAJI_MODE", "SIMULATION").upper(),
    "has_shioaji_lib": False,
    "shioaji_connected": False,
    "current_symbol": "2330",
}

# 預設標的資料庫
SYMBOLS_INFO: Dict[str, Dict[str, Any]] = {
    "2330": {"name": "台積電", "category": "半導體", "ref_price": 1080.0, "tick_size": 5.0},
    "2317": {"name": "鴻海", "category": "其他電子", "ref_price": 215.0, "tick_size": 0.5},
    "2454": {"name": "聯發科", "category": "半導體", "ref_price": 1290.0, "tick_size": 5.0},
    "0050": {"name": "元大台灣50", "category": "ETF", "ref_price": 195.0, "tick_size": 0.5},
    "TXF":  {"name": "台指期貨", "category": "指數期貨", "ref_price": 23450.0, "tick_size": 1.0},
}

# 嘗試載入 Shioaji 模組
try:
    import shioaji as sj
    CONFIG["has_shioaji_lib"] = True
except ImportError:
    CONFIG["has_shioaji_lib"] = False

# WebSocket 連線管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        payload = json.dumps(message)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)

manager = ConnectionManager()

# 即時行情模擬器與歷史資料快取
class MarketEngine:
    def __init__(self):
        self.market_state: Dict[str, Dict[str, Any]] = {}
        self.history_bars: Dict[str, List[Dict[str, Any]]] = {}
        self.running = False
        self._init_data()

    def _init_data(self):
        now = datetime.now()
        for sym, meta in SYMBOLS_INFO.items():
            base_p = meta["ref_price"]
            # 建立 120 根歷史 1分K
            bars = []
            curr_p = base_p
            start_t = now - timedelta(minutes=120)
            for i in range(120):
                bar_time = (start_t + timedelta(minutes=i)).replace(second=0, microsecond=0)
                change = (random.random() - 0.49) * (base_p * 0.003)
                o = round(curr_p, 2)
                c = round(curr_p + change, 2)
                h = round(max(o, c) + abs(random.gauss(0, base_p * 0.0015)), 2)
                l = round(min(o, c) - abs(random.gauss(0, base_p * 0.0015)), 2)
                vol = random.randint(30, 250)
                bars.append({
                    "time": int(bar_time.timestamp()),
                    "open": o,
                    "high": h,
                    "low": l,
                    "close": c,
                    "volume": vol
                })
                curr_p = c

            self.history_bars[sym] = bars
            last_bar = bars[-1]
            self.market_state[sym] = {
                "symbol": sym,
                "name": meta["name"],
                "last_price": last_bar["close"],
                "ref_price": base_p,
                "open": bars[0]["open"],
                "high": max(b["high"] for b in bars),
                "low": min(b["low"] for b in bars),
                "volume": sum(b["volume"] for b in bars),
                "tick_size": meta["tick_size"],
                "bids": [],
                "asks": [],
            }
            self._update_depth(sym)

    def _update_depth(self, sym: str):
        state = self.market_state[sym]
        p = state["last_price"]
        tick = state["tick_size"]
        bids = []
        asks = []
        for i in range(1, 6):
            bp = round(p - i * tick, 2)
            ap = round(p + i * tick, 2)
            bv = random.randint(15, 180)
            av = random.randint(15, 180)
            bids.append({"price": bp, "volume": bv})
            asks.append({"price": ap, "volume": av})
        state["bids"] = bids
        state["asks"] = asks

    def generate_tick(self, sym: str) -> Dict[str, Any]:
        state = self.market_state[sym]
        tick_sz = state["tick_size"]
        ref_p = state["ref_price"]
        curr_p = state["last_price"]

        # 隨機波動: 70% 盤整或 1 tick 跳動，30% 持平
        step = random.choice([-2, -1, -1, 0, 0, 1, 1, 2])
        new_p = round(curr_p + step * tick_sz, 2)
        # 限制漲跌停 10%
        limit_up = round(ref_p * 1.10, 2)
        limit_down = round(ref_p * 0.90, 2)
        new_p = max(limit_down, min(limit_up, new_p))

        vol = random.choices([1, 2, 5, 10, 25, 50], weights=[40, 25, 15, 10, 7, 3])[0]
        state["volume"] += vol
        state["high"] = max(state["high"], new_p)
        state["low"] = min(state["low"], new_p)
        state["last_price"] = new_p

        is_buy = new_p >= curr_p
        tick_type = "buy" if is_buy else "sell"
        diff = round(new_p - ref_p, 2)
        pct = round((diff / ref_p) * 100, 2)

        now = datetime.now()
        now_ts = int(now.timestamp())
        now_str = now.strftime("%H:%M:%S.%f")[:-3]

        self._update_depth(sym)

        # 更新最新 1 分 K
        bars = self.history_bars[sym]
        current_minute_ts = int(now.replace(second=0, microsecond=0).timestamp())
        if bars and bars[-1]["time"] == current_minute_ts:
            b = bars[-1]
            b["high"] = max(b["high"], new_p)
            b["low"] = min(b["low"], new_p)
            b["close"] = new_p
            b["volume"] += vol
        else:
            bars.append({
                "time": current_minute_ts,
                "open": new_p,
                "high": new_p,
                "low": new_p,
                "close": new_p,
                "volume": vol
            })
            if len(bars) > 300:
                bars.pop(0)

        tick_data = {
            "type": "tick",
            "symbol": sym,
            "name": state["name"],
            "time": now_str,
            "timestamp": now_ts,
            "price": new_p,
            "volume": vol,
            "total_volume": state["volume"],
            "change": diff,
            "pct_change": pct,
            "tick_type": tick_type,
            "high": state["high"],
            "low": state["low"],
            "open": state["open"],
            "ref_price": ref_p,
            "bar": bars[-1],
            "bids": state["bids"],
            "asks": state["asks"],
        }
        return tick_data

engine = MarketEngine()

# 背景廣播任務 (模擬模式)
async def simulation_loop():
    while True:
        try:
            if CONFIG["mode"] == "SIMULATION":
                # 對各訂閱標的產生真實跳動
                for sym in SYMBOLS_INFO.keys():
                    tick = engine.generate_tick(sym)
                    # 優先高頻推播當前前端關注的標的
                    if sym == CONFIG["current_symbol"] or random.random() < 0.35:
                        await manager.broadcast(tick)
            await asyncio.sleep(random.uniform(0.3, 0.9))
        except asyncio.CancelledError:
            break
        except Exception as e:
            await asyncio.sleep(1)

sim_task = None



# REST 介面
@app.get("/api/status")
def get_status():
    return {
        "status": "ok",
        "mode": CONFIG["mode"],
        "has_shioaji_lib": CONFIG["has_shioaji_lib"],
        "shioaji_connected": CONFIG["shioaji_connected"],
        "current_symbol": CONFIG["current_symbol"],
        "active_clients": len(manager.active_connections),
        "supported_symbols": list(SYMBOLS_INFO.keys()),
    }

class ConfigPayload(BaseModel):
    api_key: str = ""
    secret_key: str = ""
    person_id: str = ""
    mode: str = "SIMULATION"

@app.post("/api/config")
def update_config(payload: ConfigPayload):
    CONFIG["api_key"] = payload.api_key.strip()
    CONFIG["secret_key"] = payload.secret_key.strip()
    CONFIG["person_id"] = payload.person_id.strip()
    CONFIG["mode"] = payload.mode.upper()
    return {"status": "ok", "message": f"設定已更新，目前模式: {CONFIG['mode']}"}

@app.get("/api/symbols")
def get_symbols():
    return [
        {
            "symbol": sym,
            "name": meta["name"],
            "category": meta["category"],
            "ref_price": meta["ref_price"],
            "last_price": engine.market_state[sym]["last_price"],
            "volume": engine.market_state[sym]["volume"],
            "change": round(engine.market_state[sym]["last_price"] - meta["ref_price"], 2),
            "pct_change": round(((engine.market_state[sym]["last_price"] - meta["ref_price"]) / meta["ref_price"]) * 100, 2),
        }
        for sym, meta in SYMBOLS_INFO.items()
    ]

@app.get("/api/history/{symbol}")
def get_history(symbol: str):
    sym = symbol.upper()
    if sym not in engine.history_bars:
        # 動態補建未收錄標的
        SYMBOLS_INFO[sym] = {"name": sym, "category": "個股", "ref_price": 100.0, "tick_size": 0.5}
        engine.market_state[sym] = {
            "symbol": sym,
            "name": sym,
            "last_price": 100.0,
            "ref_price": 100.0,
            "open": 100.0,
            "high": 102.0,
            "low": 98.0,
            "volume": 500,
            "tick_size": 0.5,
            "bids": [],
            "asks": []
        }
        engine._update_depth(sym)
        engine.history_bars[sym] = []
    
    return {
        "symbol": sym,
        "name": SYMBOLS_INFO[sym]["name"],
        "bars": engine.history_bars[sym],
        "state": engine.market_state[sym]
    }

class SubscribePayload(BaseModel):
    symbol: str

@app.post("/api/subscribe")
def subscribe_symbol(payload: SubscribePayload):
    sym = payload.symbol.strip().upper()
    CONFIG["current_symbol"] = sym
    if sym not in SYMBOLS_INFO:
        SYMBOLS_INFO[sym] = {"name": f"{sym} 自訂標的", "category": "觀察股", "ref_price": 100.0, "tick_size": 0.5}
        engine.market_state[sym] = {
            "symbol": sym,
            "name": SYMBOLS_INFO[sym]["name"],
            "last_price": 100.0,
            "ref_price": 100.0,
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "volume": 100,
            "tick_size": 0.5,
            "bids": [],
            "asks": []
        }
        engine._update_depth(sym)
        engine.history_bars[sym] = []

    return {"status": "ok", "current_symbol": sym}

@app.websocket("/ws/market")
async def websocket_market(websocket: WebSocket):
    await manager.connect(websocket)
    # 連線成功時先發送當前全狀態
    curr_sym = CONFIG["current_symbol"]
    try:
        await websocket.send_json({
            "type": "welcome",
            "mode": CONFIG["mode"],
            "current_symbol": curr_sym,
            "state": engine.market_state.get(curr_sym, {})
        })
        while True:
            # 接收前端的心跳或即時指令
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "subscribe":
                    CONFIG["current_symbol"] = msg.get("symbol", "2330").upper()
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

# 靜態網站掛載
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

def get_local_ip() -> str:
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def find_available_port(start_port: int = 8088, max_attempts: int = 50) -> int:
    import socket
    for p in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return start_port

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading

    port = find_available_port(8088)
    local_ip = get_local_ip()

    print("\n" + "=" * 56)
    print("  [Shioaji Trading Terminal] 永豐 Shioaji 即時看盤儀表板")
    print("=" * 56)
    print(f"  本機網址:  http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"  區網網址:  http://{local_ip}:{port}")
    print("=" * 56)
    print("  [提示] 預設啟用「高仿真即時模擬盤」，開箱即看即時行情！")
    print("  按 Ctrl+C 可停止伺服器\n")

    # 延遲 1.2 秒後自動於瀏覽器開啟網頁
    def open_browser():
        time.sleep(1.2)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)

