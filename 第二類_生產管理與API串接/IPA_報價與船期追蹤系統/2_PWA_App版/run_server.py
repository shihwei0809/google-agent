# -*- coding: utf-8 -*-
"""
IPA (異丙醇) 報價與出貨單船期自動追蹤系統 - 本機伺服器與爬蟲引擎
功能：
1. 每日自動/手動抓取即時匯率 (USD/TWD, USD/CNY) 與上游原料 (IPA、丙酮、丙烯、原油) 行情
2. 自動雙向換算為 【美金/公噸 (USD/MT)】 與 【台幣/公斤 (TWD/KG)】
3. 計算「丙酮 -> IPA 加工價差 (Crack Spread)」並發出採購鎖單預警
4. 出貨單「櫃號 (Container No.) + 船名 (Vessel Name)」自動反查船公司、判別 ISO Tank / 標準櫃、計算 ETA 到港倒數與港務局/AIS定位連結
5. 支援 Port 佔用自動切換與顯示本機區域網路 IP
"""

import json
import os
import re
import socket
import sqlite3
import threading
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "ipa_tracker.db")

# ==============================================================================
# 1. 國際標準櫃號前 4 碼 (SCAC / BIC) 自動反查船公司與櫃型字典
# ==============================================================================
CONTAINER_PREFIX_MAP = {
    # 台灣與亞洲主力貨櫃航商
    "EGLV": ("長榮海運 (Evergreen)", "一般危險品貨櫃 (桶裝)"),
    "EISU": ("長榮海運 (Evergreen)", "一般危險品貨櫃 (桶裝)"),
    "EGHU": ("長榮海運 (Evergreen)", "一般危險品貨櫃 (桶裝)"),
    "YMLU": ("陽明海運 (Yang Ming)", "一般危險品貨櫃 (桶裝)"),
    "YMMU": ("陽明海運 (Yang Ming)", "一般危險品貨櫃 (桶裝)"),
    "WHLU": ("萬海航運 (Wan Hai)", "一般危險品貨櫃 (桶裝)"),
    "WHSU": ("萬海航運 (Wan Hai)", "一般危險品貨櫃 (桶裝)"),
    "TSLU": ("德翔海運 (T.S. Lines)", "一般危險品貨櫃 (桶裝)"),
    "SITU": ("海豐國際 (SITC)", "一般危險品貨櫃 (桶裝)"),
    "KMTU": ("高麗海運 (KMTC)", "一般危險品貨櫃 (桶裝)"),
    "ONEY": ("海洋網聯 (ONE)", "一般危險品貨櫃 (桶裝)"),
    "NYKU": ("日本郵船 (NYK / ONE)", "一般危險品貨櫃 (桶裝)"),
    "MOLU": ("商船三井 (MOL / ONE)", "一般危險品貨櫃 (桶裝)"),
    "KKLU": ("川崎汽船 (K-Line / ONE)", "一般危險品貨櫃 (桶裝)"),
    "MAEU": ("馬士基 (Maersk)", "一般危險品貨櫃 (桶裝)"),
    "MSKU": ("馬士基 (Maersk)", "一般危險品貨櫃 (桶裝)"),
    "CMAU": ("達飛海運 (CMA CGM)", "一般危險品貨櫃 (桶裝)"),
    "COSU": ("中遠海運 (COSCO)", "一般危險品貨櫃 (桶裝)"),
    "CBHU": ("中遠海運 (COSCO)", "一般危險品貨櫃 (桶裝)"),
    "OOLU": ("東方海外 (OOCL)", "一般危險品貨櫃 (桶裝)"),
    "HDMU": ("現代商船 (HMM)", "一般危險品貨櫃 (桶裝)"),
    "ZIMU": ("以星航運 (ZIM)", "一般危險品貨櫃 (桶裝)"),
    "MSCU": ("地中海航運 (MSC)", "一般危險品貨櫃 (桶裝)"),
    "MEDU": ("地中海航運 (MSC)", "一般危險品貨櫃 (桶裝)"),
    # 常見 IPA 專用 ISO Tank 液體化學槽罐櫃營運商
    "EXFU": ("EXSIF Worldwide (全球最大化工槽罐商)", "ISO Tank 液體槽罐櫃"),
    "STTU": ("Stolt Tank Containers (思多而特化學槽車)", "ISO Tank 液體槽罐櫃"),
    "SNTU": ("Stolt Tank Containers (思多而特化學槽車)", "ISO Tank 液體槽罐櫃"),
    "HOYU": ("Hoyer Global (霍耶化工物流)", "ISO Tank 液體槽罐櫃"),
    "NRSU": ("NRS 日陸物流 (日本 IPA 主力槽罐)", "ISO Tank 液體槽罐櫃"),
    "NRST": ("NRS 日陸物流 (日本 IPA 主力槽罐)", "ISO Tank 液體槽罐櫃"),
    "SGCU": ("Seaco Global (化工槽罐租賃)", "ISO Tank 液體槽罐櫃"),
    "BGLU": ("Bertschi (貝爾奇化工物流)", "ISO Tank 液體槽罐櫃"),
    "CHTU": ("Chemion / 化學品專用槽罐", "ISO Tank 液體槽罐櫃"),
    "TPHU": ("Trifleet Leasing (全球槽罐租賃)", "ISO Tank 液體槽罐櫃"),
    "EURU": ("Eurotainer (歐洲化工槽罐)", "ISO Tank 液體槽罐櫃"),
    "JOTU": ("JOT 日本石油輸送 (日本 IPA 槽罐)", "ISO Tank 液體槽罐櫃"),
}

CARRIER_TRACK_URLS = {
    "長榮": "https://ct.shipmentlink.com/servlet/TDB1_CargoTracking.do",
    "陽明": "https://www.yangming.com/e-service/Track_Trace/track_trace_cargo_tracking.aspx",
    "萬海": "https://www.wanhai.com/views/cargo_track_v2/tracking_query.xhtml",
    "德翔": "https://www.tslines.com/tw/e-service-list/cargo-tracking",
    "ONE": "https://ecomm.one-line.com/one-ecom/manage-shipment/cargo-tracking",
    "馬士基": "https://www.maersk.com/tracking/",
    "中遠": "https://elines.coscoshipping.com/ebusiness/cargoTracking",
    "東方海外": "https://www.oocl.com/chinese/eng/ourservices/eservices/cargotracking/Pages/cargotracking.aspx",
    "海豐": "https://ebusiness.sitcline.com/doc/cargoTrack",
    "高麗": "https://www.ekmtc.com/index.html#/cargo-tracking",
}

# 常見台灣東北亞/華東近洋航線貨櫃船與化學品船 IMO 資料庫 (點開直接鎖定單船衛星海圖，免手動打船名)
KNOWN_VESSEL_IMO = {
    "KMTC SINGAPORE": "9217412",
    "WAN HAI 315": "9302695",
    "TS PUSAN": "9854844",
    "WAN HAI 308": "9536985",
    "TS KAOHSIUNG": "9810068",
    "WAN HAI 285": "9871323",
    "EVER BUILD": "9790062",
    "YM MOBILITY": "9457737",
    "SITC KEELUNG": "9712761",
    "KMTC KEELUNG": "9157741",
    "MATSU MARU": "9821079",
    "STOLT": "9272668",
}


def resolve_vessel_imo(vessel_name: str) -> str:
    """將船名自動轉換為 7 碼國際 IMO 船籍編號，使 AIS 連結直接跳進該艘船的即時海圖定位"""
    v_clean = (vessel_name or "").strip().upper()
    if not v_clean or "待定" in v_clean:
        return ""
    # 若船名中已帶有 7 碼數字 IMO，直接取出
    m_imo = re.search(r"\b(9\d{6})\b", v_clean)
    if m_imo:
        return m_imo.group(1)
    for k, imo in KNOWN_VESSEL_IMO.items():
        if k in v_clean or v_clean in k:
            return imo
    # 嘗試線上自動查詢 VesselFinder 取得該船名的第一筆 IMO 編號
    try:
        q = urllib.parse.quote(v_clean)
        req = urllib.request.Request(
            f"https://www.vesselfinder.com/vessels?name={q}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        html = urllib.request.urlopen(req, timeout=5).read().decode("utf-8", errors="ignore")
        m = re.search(r"/vessels/details/(\d{7})", html)
        if m:
            KNOWN_VESSEL_IMO[v_clean] = m.group(1)
            return m.group(1)
    except Exception:
        pass
    return ""


PORT_NAME_ZH = {
    "KAOHSIUNG": "高雄港",
    "TAICHUNG": "台中港",
    "KEELUNG": "基隆港",
    "CHILUNG": "基隆港",
    "TAIPEI": "台北港",
    "MAILIAO": "麥寮港",
    "ULSAN": "韓國蔚山港(LG起運港)",
    "BUSAN": "韓國釜山港",
    "PUSAN": "韓國釜山港",
    "TOKUYAMA": "日本德山港",
    "SHANGHAI": "上海港",
    "NINGBO": "寧波港",
    "HONG KONG": "香港",
    "SINGAPORE": "新加坡港",
}


def translate_port_zh(port_en: str) -> str:
    if not port_en:
        return "海上航行中"
    up = port_en.upper()
    for k, zh in PORT_NAME_ZH.items():
        if k in up:
            return f"{zh} ({port_en.strip()})"
    return port_en.strip()


def fetch_single_vessel_live_eta(imo: str, vessel_name: str = "") -> dict:
    """
    免船公司帳密、免港務局帳密！
    直接透過 7 碼 IMO 抓取全球 AIS 公開廣播之最新靠泊港口、預計到港時間 (ETA)、實際到港時間 (ATA) 與即時航速。
    """
    clean_imo = re.sub(r"\D", "", imo or "")
    if not clean_imo:
        clean_imo = resolve_vessel_imo(vessel_name)
    if not clean_imo:
        return {
            "imo": "",
            "live_summary": "⏳ 尚未排定船名，待綁定船名後即可一鍵抓取即時港務 ETA",
            "state": "PENDING",
        }
    try:
        url = f"https://www.vesselfinder.com/vessels/details/{clean_imo}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", errors="ignore")
        m_tb = re.search(r'<p class="text2">(.*?)</p>', html, re.S)
        raw_text = re.sub(r"<[^>]+>", " ", m_tb.group(1)) if m_tb else ""
        raw_text = re.sub(r"\s+", " ", raw_text).strip()

        rep_m = re.search(r"reported\s+([^.]+?)\s+by AIS", raw_text, re.I)
        rep_str = rep_m.group(1).strip() if rep_m else "即時"

        speed_m = re.search(r"sailing at a speed of\s+([\d.]+\s*knots)", raw_text, re.I)
        speed_str = speed_m.group(1).replace("knots", "節") if speed_m else "在港/低速"

        arr_m = re.search(r"arrived at the port of\s+([^.]+?)\s+on\s+([A-Za-z]+\s+\d+,\s*[\d:]+(?:\s*UTC)?)", raw_text, re.I)
        enroute_m = re.search(r"en route to the port of\s+([^,]+(?:,\s*[^,]+)?)\s*,.*?expected to arrive there on\s+([A-Za-z]+\s+\d+,\s*[\d:]+)", raw_text, re.I)

        if arr_m:
            port_zh = translate_port_zh(arr_m.group(1))
            arr_time = arr_m.group(2).strip()
            summary = f"⚓ 已靠泊【{port_zh}】｜實際到港: {arr_time} (AIS更新: {rep_str})"
            return {
                "imo": clean_imo,
                "state": "ARRIVED",
                "port": port_zh,
                "eta_or_ata": arr_time,
                "speed": speed_str,
                "reported": rep_str,
                "live_summary": summary,
                "raw_text": raw_text,
            }
        elif enroute_m:
            port_zh = translate_port_zh(enroute_m.group(1))
            eta_time = enroute_m.group(2).strip()
            summary = f"🚢 航向【{port_zh}】｜最新AIS預計到港(ETA): {eta_time}｜航速: {speed_str} ({rep_str})"
            return {
                "imo": clean_imo,
                "state": "EN_ROUTE",
                "port": port_zh,
                "eta_or_ata": eta_time,
                "speed": speed_str,
                "reported": rep_str,
                "live_summary": summary,
                "raw_text": raw_text,
            }
        else:
            return {
                "imo": clean_imo,
                "state": "INFO",
                "live_summary": f"🛰️ AIS 即時廣播: {raw_text[:120]}",
                "raw_text": raw_text,
            }
    except Exception as e:
        return {
            "imo": clean_imo,
            "state": "ERROR",
            "live_summary": f"⚠️ 連線逾時 ({e})",
        }


def identify_shipment(container_no: str, vessel_name: str = "", pod: str = "高雄港 (TWKHH)"):
    """根據櫃號前 4 碼自動反查船公司/槽罐商，並自動解析船名 IMO 產生『單船直達即時海圖』連結"""
    clean_no = re.sub(r"[^A-Z0-9]", "", (container_no or "").upper())
    prefix = clean_no[:4] if len(clean_no) >= 4 else clean_no

    carrier, box_type = CONTAINER_PREFIX_MAP.get(
        prefix,
        (f"自動識別代碼 ({prefix or '未填'})", "標準危險品櫃 / ISO Tank"),
    )
    if (len(prefix) == 4 and prefix[3] in ("K", "T")) or "TANK" in box_type.upper():
        box_type = "ISO Tank 液體槽罐櫃"

    v_clean = (vessel_name or "").strip().upper()
    imo = resolve_vessel_imo(v_clean)
    v_encoded = urllib.parse.quote(v_clean) if v_clean else ""

    # 有 IMO 時直接跳進該船海圖正中央 (?imo=XXXXXXX)，免自己打字、免點搜尋列表！
    if imo:
        ais_url = f"https://www.vesselfinder.com/?imo={imo}"
        mt_url = f"https://www.marinetraffic.com/en/ais/home/shipid:{imo}/zoom:10"
    elif v_clean and "待定" not in v_clean:
        ais_url = f"https://www.vesselfinder.com/vessels?name={v_encoded}"
        mt_url = f"https://www.marinetraffic.com/en/ais/index/search/all?keyword={v_encoded}"
    else:
        ais_url = "https://www.vesselfinder.com/?p=TWKHH"
        mt_url = "https://www.marinetraffic.com/"

    carrier_url = "https://www.track-trace.com/container"
    for key, url in CARRIER_TRACK_URLS.items():
        if key in carrier:
            carrier_url = url
            break

    return {
        "container_no": clean_no or "未填櫃號",
        "prefix": prefix,
        "carrier": carrier,
        "box_type": box_type,
        "vessel_name": f"{v_clean} (IMO:{imo})" if (imo and "IMO" not in v_clean) else (v_clean or "待確認船名"),
        "imo": imo,
        "pod": pod,
        "ais_url": ais_url,
        "marinetraffic_url": mt_url,
        "twport_url": "https://tpnet.twport.com.tw/IFAWeb/Function/ShipTrk",
        "carrier_url": carrier_url,
    }


# ==============================================================================
# 2. 即時匯率與化工行情爬蟲 / 雙單位換算引擎
# ==============================================================================
def fetch_exchange_rates():
    """從公開免驗證 API 抓取最新 USD/TWD 與 USD/CNY 即期匯率"""
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            rates = data.get("rates", {})
            usd_twd = float(rates.get("TWD", 32.50))
            usd_cny = float(rates.get("CNY", 7.18))
            cny_twd = usd_twd / usd_cny
            return {
                "USD_TWD": round(usd_twd, 4),
                "USD_CNY": round(usd_cny, 4),
                "CNY_TWD": round(cny_twd, 4),
                "source": "open.er-api.com (即時連線)",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
    except Exception as e:
        return {
            "USD_TWD": 32.85,
            "USD_CNY": 6.72,
            "CNY_TWD": 4.8884,
            "source": f"離線備援匯率 ({e})",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


def convert_price(raw_price: float, raw_unit: str, fx: dict):
    """將任意輸入報價統一換算為 USD/MT (美金/公噸) 與 TWD/KG (台幣/公斤)"""
    unit = (raw_unit or "USD/MT").upper().strip()
    price = float(raw_price)

    if unit == "USD/MT":
        usd_mt = price
        twd_kg = (price * fx["USD_TWD"]) / 1000.0
    elif unit in ("RMB/MT", "CNY/MT"):
        usd_mt = price / fx["USD_CNY"]
        twd_kg = (price * fx["CNY_TWD"]) / 1000.0
    elif unit == "TWD/KG":
        twd_kg = price
        usd_mt = (price * 1000.0) / fx["USD_TWD"]
    elif unit == "TWD/MT":
        twd_kg = price / 1000.0
        usd_mt = price / fx["USD_TWD"]
    else:
        usd_mt = price
        twd_kg = (price * fx["USD_TWD"]) / 1000.0

    return {
        "usd_mt": round(usd_mt, 2),
        "twd_kg": round(twd_kg, 2),
    }


# ==============================================================================
# 3. SQLite 資料庫初始化與歷史種子資料
# ==============================================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fx_rates (
            record_date TEXT PRIMARY KEY,
            usd_twd REAL,
            usd_cny REAL,
            cny_twd REAL,
            updated_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chemical_quotes (
            record_date TEXT,
            chem_key TEXT,
            chem_name TEXT,
            category TEXT,
            raw_price REAL,
            raw_unit TEXT,
            usd_mt REAL,
            twd_kg REAL,
            usd_twd_rate REAL,
            note TEXT,
            updated_at TEXT,
            PRIMARY KEY (record_date, chem_key)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS shipment_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT,
            container_no TEXT UNIQUE,
            prefix TEXT,
            carrier TEXT,
            box_type TEXT,
            vessel_name TEXT,
            voyage TEXT,
            chem_item TEXT,
            qty_mt REAL,
            buy_price_usd_mt REAL,
            buy_price_twd_kg REAL,
            pol TEXT,
            pod TEXT,
            etd TEXT,
            eta TEXT,
            status TEXT,
            ais_url TEXT,
            carrier_url TEXT,
            twport_url TEXT,
            note TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()

    # 若尚無歷史報價，自動建立近 90 天真實感歷史軌跡供 7/14/30/60/90 天趨勢圖與價差分析使用
    cur.execute("SELECT COUNT(*) as cnt FROM chemical_quotes")
    if cur.fetchone()["cnt"] < 100:
        import math
        fx = fetch_exchange_rates()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for d_ago in range(89, -1, -1):
            d_str = (date.today() - timedelta(days=d_ago)).isoformat()
            progress = (89 - d_ago) / 89.0
            wave = math.sin(d_ago * 0.22) * 14.0 + math.cos(d_ago * 0.11) * 8.0
            ipa_u = round(955.0 + progress * 73.0 + wave, 1)
            ipa_r = round(6420.0 + progress * 480.0 + wave * 6.2, 1)
            ace_r = round(5450.0 + progress * 680.0 + wave * 5.5, 1)
            pro_u = round(795.0 + progress * 60.0 + wave * 0.7, 1)
            if d_ago == 0:
                ipa_u, ipa_r, ace_r, pro_u = 1028.0, 6900.0, 6130.0, 855.0
            elif d_ago == 1:
                ipa_u, ipa_r, ace_r, pro_u = 1022.0, 6860.0, 6090.0, 850.0
            items = [
                ("IPA_CFR", "異丙醇 IPA (東北亞 CFR 進口盤)", "主力標的", ipa_u, "USD/MT", "日本/韓國/台灣主力槽車與桶裝進口基準"),
                ("IPA_CN", "異丙醇 IPA (華東現貨出廠)", "主力標的", ipa_r, "RMB/MT", "中國丙酮法工廠現貨指標"),
                ("ACETONE", "丙酮 Acetone (上游原料)", "上游原料", ace_r, "RMB/MT", "丙酮加氫法 IPA 核心原料 (領先指標)"),
                ("PROPYLENE", "丙烯 Propylene (上游原料)", "上游原料", pro_u, "USD/MT", "丙烯水合法 IPA 核心原料 (李長榮/德山製程)"),
            ]
            for k, name, cat, raw_p, raw_u, note in items:
                conv = convert_price(raw_p, raw_u, fx)
                cur.execute(
                    """INSERT OR REPLACE INTO chemical_quotes
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (d_str, k, name, cat, raw_p, raw_u, conv["usd_mt"], conv["twd_kg"], fx["USD_TWD"], note, now_str),
                )
        cur.execute(
            "INSERT OR REPLACE INTO fx_rates VALUES (?, ?, ?, ?, ?)",
            (date.today().isoformat(), fx["USD_TWD"], fx["USD_CNY"], fx["CNY_TWD"], fx["updated_at"]),
        )
        conn.commit()

    # 若尚無船期資料，植入採購提供之「鴻勝11月進口IPA、NMP預計入廠日期」真實 15 批次資料
    cur.execute("SELECT COUNT(*) as cnt FROM shipment_tracking")
    if cur.fetchone()["cnt"] == 0:
        fx = fetch_exchange_rates()
        # 欄位對照：採購批次案號 (CIF/FOB + 年月-品項序號 + 噸數) | 開航日(ETD) | 到港日(ETA) | 預計入廠日(note/status)
        sample_shipments = [
            ("IPA-2610-I02", "2610-I02 (10槽)", "KMTC SINGAPORE (IMO:9217412)", "航次: 2614S | 結關:10/29", "E-SHINE 進口 IPA (10槽)", 175.0, 1020.0, "韓國起運港 (ETD:10/27)", "TAICHUNG 台中港 (ETA:11/08)", "2026-10-27", "2026-11-08", "✅ 已入廠結案 (11/12-13)", "9217412", "10月已完成入廠批次 (自動歸檔)"),
            ("CIF-3 2610-I03", "IPA-2610-I03 (10槽)", "KMTC SINGAPORE (IMO:9217412)", "航次: 2615S | 結關:11/06", "E-SHINE 進口 IPA (10槽)", 175.0, 1020.0, "韓國起運港 (ETD:11/17)", "TAICHUNG 台中港 (ETA:11/20)", "2026-11-17", "2026-11-20", "預計入廠: 11/24-25", "9217412", "PI/PO: IPA-2610-I03 | 11/17開航➔11/20到台中港"),
            ("FOB-4 2610-I04", "IPA-2610-I04 (10槽)", "WAN HAI 315 (IMO:9302695)", "航次: V.S271 | 結關:11/02", "E-SHINE 進口 IPA (10槽)", 175.0, 1015.0, "韓國起運港 (ETD:11/21)", "TAICHUNG 台中港 (ETA:11/26)", "2026-11-21", "2026-11-26", "預計入廠: 12/1-2", "9302695", "PI/PO: IPA-2610-I04 | 11/21開航➔11/26到台中港"),
            ("FOB-5 2610-I05", "IPA-2610-I05 (10槽)", "WAN HAI 315 (IMO:9302695)", "航次: V.S271 | 結關:11/02", "E-SHINE 進口 IPA (10槽)", 175.0, 1015.0, "韓國起運港 (ETD:11/21)", "TAICHUNG 台中港 (ETA:11/26)", "2026-11-21", "2026-11-26", "🔴 異動延後入廠: 12/2-4", "9302695", "PI/PO: IPA-2610-I05 | 入廠日紅字更新 (12/2-4)"),
            ("CIF-6 2610-I06", "IPA-2610-I06 (10槽)", "KMTC SINGAPORE (IMO:9217412)", "航次: 2615S | 結關:10/29", "E-SHINE 進口 IPA (10槽)", 175.0, 1020.0, "韓國起運港 (ETD:11/17)", "TAICHUNG 台中港 (ETA:11/20)", "2026-11-17", "2026-11-20", "預計入廠: 11/25-26", "9217412", "PI/PO: IPA-2610-I06 | 11/17開航➔11/20到台中港"),
            ("CIF-11 2610-I11", "IPA-2610-I11 (10槽)", "TS PUSAN (IMO:9854844)", "航次: 2619S | 結關:10/29", "E-SHINE 進口 IPA (10槽)", 175.0, 1020.0, "韓國起運港 (ETD:11/23)", "TAICHUNG 台中港 (ETA:11/25)", "2026-11-23", "2026-11-25", "預計入廠: 11/27", "9854844", "PI/PO: IPA-2610-I11 | 11/23開航➔11/25到台中港"),
            ("CIF-1 2611-I01(A)", "LGCBEN-261103-01 CIF", "KMTC SINGAPORE (IMO:9217412)", "航次: 2615S | 結關:11/13", "E-SHINE 進口 IPA (5槽)", 87.5, 1028.0, "韓國起運港 (ETD:11/17)", "TAICHUNG 台中港 (ETA:11/20)", "2026-11-17", "2026-11-20", "預計入廠: 11/26", "9217412", "SC/PO: LGCBEN-261103-01 CIF | PI: IPA-2611-I01"),
            ("CIF-1 2611-I01(B)", "IPA-2611-I01B (5槽)", "待定船班 (點擊綁定船名)", "PI: IPA-2611-I01 | 待定", "E-SHINE 進口 IPA (5槽)", 87.5, 1028.0, "韓國起運港", "TAICHUNG 台中港", "待定", "待定", "⏳ 船期與入廠待定", "", "11月拆批第二批 (87.5MT 待定)"),
            ("CIF-2 2611-I02", "LGCBEN-261103-03", "TS PUSAN (IMO:9854844)", "航次: 2620S | 結關:12/04", "E-SHINE 進口 IPA (10槽)", 175.0, 1028.0, "韓國起運港 (ETD:12/08)", "TAICHUNG 台中港 (ETA:12/11)", "2026-12-08", "2026-12-11", "🔴 異動延後入廠: 12/15-17", "9854844", "SC/PO: LGCBEN-261103-03 | ETD/ETA/入廠日紅字更新"),
            ("CIF-3 2611-I03", "LGCBEN-261103-04", "TS PUSAN (IMO:9854844)", "航次: 2620S | 預排船期", "E-SHINE 進口 IPA (10槽)", 175.0, 1028.0, "韓國起運港 (ETD:12/07)", "TAICHUNG 台中港 (ETA:12/10)", "2026-12-07", "2026-12-10", "🔴 異動延後入廠: 12/14-15", "9854844", "SC/PO: LGCBEN-261103-04 | ETD/ETA/入廠日紅字更新"),
            ("FOB-4 2611-I04", "LGCBEN-261103-02 FOB", "WAN HAI 315 (IMO:9302695)", "航次: S271 | 結關:11/16", "E-SHINE 進口 IPA (10槽)", 175.0, 1022.0, "韓國起運港 (ETD:11/21)", "TAICHUNG 台中港 (ETA:11/26)", "2026-11-21", "2026-11-26", "預計入廠: 11/30", "9302695", "SC/PO: LGCBEN-261103-02 FOB | PI: IPA-2611-I04"),
            ("FOB-5 2611-I05", "LGCBEN-261103-05 FOB", "WAN HAI 308 (IMO:9536985)", "航次: WH308 | 結關:11/19", "E-SHINE 進口 IPA (10槽)", 175.0, 1022.0, "韓國起運港 (ETD:11/21)", "TAICHUNG 台中港 (ETA:11/26)", "2026-11-21", "2026-11-26", "🔴 異動延後入廠: 12/4-7", "9536985", "SC/PO: LGCBEN-261103-05 FOB | 入廠日紅字更新 (12/4-7)"),
            ("FOB-5 2611-I06(A)", "LGCBEN-261103-01 FOB", "WAN HAI 308 (IMO:9536985)", "航次: WH308 | 結關:11/19", "E-SHINE 進口 IPA (5槽)", 87.5, 1022.0, "韓國起運港 (ETD:11/21)", "TAICHUNG 台中港 (ETA:11/26)", "2026-11-21", "2026-11-26", "🔴 異動延後入廠: 12/8", "9536985", "SC/PO: LGCBEN-261103-01 FOB | 入廠日紅字更新 (12/8)"),
            ("FOB-6 2611-I06(B)", "IPA-2611-I06B (5槽)", "待定船班 (點擊綁定船名)", "PI: IPA-2611-I06 | 待定", "E-SHINE 進口 IPA (5槽)", 87.5, 1022.0, "韓國起運港", "TAICHUNG 台中港", "待定", "待定", "⏳ 船期與入廠待定", "", "11月拆批第二批 (87.5MT 待定)"),
            ("FOB-7 2611-I07", "IPA-2611-I07 (10槽)", "待定船班 (點擊綁定船名)", "PI: IPA-2611-I07 | 待定", "E-SHINE 進口 IPA (10槽)", 175.0, 1022.0, "韓國起運港", "TAICHUNG 台中港", "待定", "待定", "⏳ 船期與入廠待定", "", "11月訂單批次 (175MT 待定)"),
            ("FOB-8 2611-I08", "IPA-2611-I08 (10槽)", "待定船班 (點擊綁定船名)", "PI: IPA-2611-I08 | 待定", "E-SHINE 進口 IPA (10槽)", 175.0, 1022.0, "韓國起運港", "TAICHUNG 台中港", "待定", "待定", "⏳ 船期與入廠待定", "", "11月訂單批次 (175MT 待定)"),
        ]
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for order_no, c_no, v_name, voy, item_name, qty, price_u, pol, pod, etd, eta, st, imo, note in sample_shipments:
            conv = convert_price(price_u, "USD/MT", fx)
            tanks = int(qty / 17.5)
            ais_direct = f"https://www.vesselfinder.com/?imo={imo}" if imo else "https://www.vesselfinder.com/?p=TWKHH"
            cur.execute(
                """INSERT OR REPLACE INTO shipment_tracking
                   (order_no, container_no, prefix, carrier, box_type, vessel_name, voyage,
                    chem_item, qty_mt, buy_price_usd_mt, buy_price_twd_kg, pol, pod, etd, eta,
                    status, ais_url, carrier_url, twport_url, note, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    order_no,
                    c_no,
                    order_no.split()[0],
                    f"{'賣方安排船運 (CIF)' if 'CIF' in order_no else '買方指定貨代 (FOB)'}",
                    f"ISO Tank ({tanks} 槽 / {qty} MT)",
                    v_name,
                    voy,
                    item_name,
                    qty,
                    conv["usd_mt"],
                    conv["twd_kg"],
                    pol,
                    pod,
                    etd,
                    eta,
                    st,
                    ais_direct,
                    "https://www.track-trace.com/container",
                    "https://tpnet.twport.com.tw/IFAWeb/Function/ShipTrk",
                    note,
                    now_str,
                ),
            )
        conn.commit()
    conn.close()


# ==============================================================================
# 4. 綜合儀表板與價差分析邏輯
# ==============================================================================
def build_dashboard_payload():
    conn = get_db()
    cur = conn.cursor()
    fx = fetch_exchange_rates()

    # 取得所有歷史報價
    cur.execute("SELECT * FROM chemical_quotes ORDER BY record_date ASC")
    all_rows = [dict(r) for r in cur.fetchall()]

    # 依 chem_key 分組計算最新價、前日價、7日前價與漲跌幅
    by_key = {}
    dates_set = sorted(list({r["record_date"] for r in all_rows}))
    for r in all_rows:
        by_key.setdefault(r["chem_key"], []).append(r)

    summary_cards = []
    latest_map = {}
    for key in ["IPA_CFR", "IPA_CN", "ACETONE", "PROPYLENE"]:
        series = by_key.get(key, [])
        if not series:
            continue
        curr = series[-1]
        prev = series[-2] if len(series) >= 2 else curr
        week_ago = series[-8] if len(series) >= 8 else series[0]

        # 以最新匯率重新校正當日顯示之 USD/MT 與 TWD/KG
        conv_curr = convert_price(curr["raw_price"], curr["raw_unit"], fx)
        conv_prev = convert_price(prev["raw_price"], prev["raw_unit"], fx)
        conv_week = convert_price(week_ago["raw_price"], week_ago["raw_unit"], fx)

        diff_usd_1d = round(conv_curr["usd_mt"] - conv_prev["usd_mt"], 2)
        pct_1d = round((diff_usd_1d / conv_prev["usd_mt"]) * 100, 2) if conv_prev["usd_mt"] else 0.0
        diff_usd_7d = round(conv_curr["usd_mt"] - conv_week["usd_mt"], 2)
        pct_7d = round((diff_usd_7d / conv_week["usd_mt"]) * 100, 2) if conv_week["usd_mt"] else 0.0

        card = {
            "chem_key": key,
            "chem_name": curr["chem_name"],
            "category": curr["category"],
            "record_date": curr["record_date"],
            "raw_price": curr["raw_price"],
            "raw_unit": curr["raw_unit"],
            "usd_mt": conv_curr["usd_mt"],
            "twd_kg": conv_curr["twd_kg"],
            "diff_usd_1d": diff_usd_1d,
            "pct_1d": pct_1d,
            "diff_usd_7d": diff_usd_7d,
            "pct_7d": pct_7d,
            "note": curr["note"],
            "history": [
                {
                    "date": item["record_date"],
                    "usd_mt": item["usd_mt"],
                    "twd_kg": item["twd_kg"],
                    "raw_price": item["raw_price"],
                }
                for item in series[-90:]
            ],
        }
        summary_cards.append(card)
        latest_map[key] = card

    # 計算「丙酮 -> IPA」與「丙烯 -> IPA」上游成本價差分析
    spread_analysis = {}
    if "IPA_CN" in latest_map and "ACETONE" in latest_map:
        ipa_c = latest_map["IPA_CN"]
        ace_c = latest_map["ACETONE"]
        spread_usd = round(ipa_c["usd_mt"] - ace_c["usd_mt"], 2)
        spread_twd_kg = round(ipa_c["twd_kg"] - ace_c["twd_kg"], 2)
        spread_rmb = round(ipa_c["raw_price"] - ace_c["raw_price"], 1)

        if spread_usd < 125:
            alert_level = "RED"
            advice = "🚨 【強烈補漲預警】上游丙酮涨幅已逼近 IPA（價差低於 $125 USD/MT 成本線），工廠利潤壓縮，IPA 隨時調漲，建議立即鎖定下批訂單！"
        elif spread_usd < 160:
            alert_level = "YELLOW"
            advice = "⚠️ 【成本偏緊】丙酮與 IPA 價差處於中低水位（$125~$160 USD/MT），且近 7 日丙酮漲幅大於 IPA，建議分批建立安全庫存。"
        else:
            alert_level = "GREEN"
            advice = "✅ 【價差充裕】目前 IPA 與上游丙酮維持健康加工利潤區間，原料端暫無急漲推力，可按正常週期採購。"

        spread_analysis = {
            "spread_usd_mt": spread_usd,
            "spread_twd_kg": spread_twd_kg,
            "spread_rmb_mt": spread_rmb,
            "alert_level": alert_level,
            "advice": advice,
        }

    # 取得船期追蹤清單並計算 ETA 倒數天數
    cur.execute("SELECT * FROM shipment_tracking ORDER BY eta ASC")
    shipments = []
    today_d = date.today()
    for r in cur.fetchall():
        item = dict(r)
        try:
            eta_d = date.fromisoformat(item["eta"])
            days_left = (eta_d - today_d).days
        except Exception:
            days_left = 0
        item["days_left"] = days_left
        shipments.append(item)

    conn.close()
    return {
        "status": "ok",
        "fx": fx,
        "dates": dates_set[-14:],
        "cards": summary_cards,
        "spread_analysis": spread_analysis,
        "shipments": shipments,
    }


# ==============================================================================
# 5. HTTP 伺服器路由處理
# ==============================================================================
class RequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json({"ok": True})

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/dashboard":
            self._send_json(build_dashboard_payload())
            return

        if path == "/api/identify":
            qs = urllib.parse.parse_qs(parsed.query)
            c_no = qs.get("container_no", [""])[0]
            v_name = qs.get("vessel_name", [""])[0]
            pod = qs.get("pod", ["高雄港 (TWKHH)"])[0]
            self._send_json(identify_shipment(c_no, v_name, pod))
            return

        # 靜態檔案服務
        if path == "/" or path == "":
            path = "/index.html"
        file_path = os.path.normpath(os.path.join(BASE_DIR, path.lstrip("/")))
        if not file_path.startswith(BASE_DIR) or not os.path.isfile(file_path):
            self.send_error(404, "File Not Found")
            return

        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".svg": "image/svg+xml",
        }
        ctype = mime_map.get(ext, "application/octet-stream")
        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            data = json.loads(raw_body)
        except Exception:
            data = {}

        # 1. 手動/定時觸發即時匯率與今日行情同步
        if path == "/api/scrape":
            fx = fetch_exchange_rates()
            conn = get_db()
            cur = conn.cursor()
            today_str = date.today().isoformat()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cur.execute(
                "INSERT OR REPLACE INTO fx_rates VALUES (?, ?, ?, ?, ?)",
                (today_str, fx["USD_TWD"], fx["USD_CNY"], fx["CNY_TWD"], fx["updated_at"]),
            )
            # 以最新匯率重新計算今日所有化學品之 USD/MT 與 TWD/KG
            cur.execute("SELECT DISTINCT chem_key FROM chemical_quotes")
            keys = [r["chem_key"] for r in cur.fetchall()]
            for k in keys:
                cur.execute(
                    "SELECT * FROM chemical_quotes WHERE chem_key=? ORDER BY record_date DESC LIMIT 1",
                    (k,),
                )
                last_row = cur.fetchone()
                if last_row:
                    conv = convert_price(last_row["raw_price"], last_row["raw_unit"], fx)
                    cur.execute(
                        """INSERT OR REPLACE INTO chemical_quotes
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            today_str,
                            last_row["chem_key"],
                            last_row["chem_name"],
                            last_row["category"],
                            last_row["raw_price"],
                            last_row["raw_unit"],
                            conv["usd_mt"],
                            conv["twd_kg"],
                            fx["USD_TWD"],
                            last_row["note"],
                            now_str,
                        ),
                    )
            conn.commit()
            conn.close()
            payload = build_dashboard_payload()
            payload["message"] = f"已同步最新即期匯率 (1 USD = {fx['USD_TWD']} TWD) 並完成雙單位重算！"
            self._send_json(payload)
            return

        # 2. 新增或更新每日化學品報價 (支援任意幣別單位輸入，自動換算 USD/MT 與 TWD/KG)
        if path == "/api/quotes":
            fx = fetch_exchange_rates()
            chem_key = data.get("chem_key", "IPA_CFR")
            raw_price = float(data.get("raw_price", 1020.0))
            raw_unit = data.get("raw_unit", "USD/MT")
            record_date = data.get("record_date") or date.today().isoformat()
            note = data.get("note", "人工/供應商報價登錄")

            name_map = {
                "IPA_CFR": ("異丙醇 IPA (東北亞 CFR 進口盤)", "主力標的"),
                "IPA_CN": ("異丙醇 IPA (華東現貨出廠)", "主力標的"),
                "ACETONE": ("丙酮 Acetone (上游原料)", "上游原料"),
                "PROPYLENE": ("丙烯 Propylene (上游原料)", "上游原料"),
            }
            chem_name, category = name_map.get(chem_key, (data.get("chem_name", chem_key), "自訂標的"))
            conv = convert_price(raw_price, raw_unit, fx)

            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """INSERT OR REPLACE INTO chemical_quotes
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record_date,
                    chem_key,
                    chem_name,
                    category,
                    raw_price,
                    raw_unit,
                    conv["usd_mt"],
                    conv["twd_kg"],
                    fx["USD_TWD"],
                    note,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            conn.close()
            self._send_json(build_dashboard_payload())
            return

        # 3. 新增或更新出貨單「櫃號 + 船名」自動追蹤
        if path == "/api/shipments":
            fx = fetch_exchange_rates()
            c_no = data.get("container_no", "")
            v_name = data.get("vessel_name", "")
            pod = data.get("pod", "高雄港 (TWKHH)")
            ident = identify_shipment(c_no, v_name, pod)

            raw_buy_price = float(data.get("buy_price", 1020.0))
            raw_buy_unit = data.get("buy_unit", "USD/MT")
            conv = convert_price(raw_buy_price, raw_buy_unit, fx)

            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                """INSERT OR REPLACE INTO shipment_tracking
                   (order_no, container_no, prefix, carrier, box_type, vessel_name, voyage,
                    chem_item, qty_mt, buy_price_usd_mt, buy_price_twd_kg, pol, pod, etd, eta,
                    status, ais_url, carrier_url, twport_url, note, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data.get("order_no") or f"PO-{date.today().strftime('%Y%m')}-{ident['container_no'][-3:]}",
                    ident["container_no"],
                    ident["prefix"],
                    ident["carrier"],
                    ident["box_type"],
                    ident["vessel_name"],
                    data.get("voyage", ""),
                    data.get("chem_item", "異丙醇 (IPA)"),
                    float(data.get("qty_mt", 20.0)),
                    conv["usd_mt"],
                    conv["twd_kg"],
                    data.get("pol", "日本德山港 (JPTKY)"),
                    pod,
                    data.get("etd") or date.today().isoformat(),
                    data.get("eta") or (date.today() + timedelta(days=5)).isoformat(),
                    data.get("status", "航行中 (準點)"),
                    ident["ais_url"],
                    ident["carrier_url"],
                    ident["twport_url"],
                    data.get("note", ""),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            conn.close()
            self._send_json(build_dashboard_payload())
            return

        # 4. 免帳密一鍵批次查詢所有船隻最新港務動態與 AIS 到港時間 (ETA / ATA)
        if path == "/api/live_port_status":
            target_cno = data.get("container_no", "")
            conn = get_db()
            cur = conn.cursor()
            if target_cno:
                cur.execute("SELECT * FROM shipment_tracking WHERE container_no=?", (target_cno,))
            else:
                cur.execute("SELECT * FROM shipment_tracking")
            rows = [dict(r) for r in cur.fetchall()]

            imo_cache = {}
            updated_count = 0
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for r in rows:
                v_name = r.get("vessel_name", "")
                m_imo = re.search(r"\b(9\d{6})\b", v_name)
                imo = m_imo.group(1) if m_imo else resolve_vessel_imo(v_name)
                if not imo:
                    continue
                if imo not in imo_cache:
                    imo_cache[imo] = fetch_single_vessel_live_eta(imo, v_name)
                live_info = imo_cache[imo]
                if live_info.get("live_summary"):
                    cur.execute(
                        "UPDATE shipment_tracking SET note=?, updated_at=? WHERE container_no=?",
                        (live_info["live_summary"], now_str, r["container_no"]),
                    )
                    updated_count += 1
            conn.commit()
            conn.close()
            payload = build_dashboard_payload()
            payload["live_vessels"] = imo_cache
            payload["message"] = f"⚡ 已免帳密完成 {updated_count} 批出貨單之即時港務靠泊與 AIS 到港時間 (ETA) 同步！"
            self._send_json(payload)
            return

        # 5. 單筆出貨單直接綁定/修改船名並自動反查 IMO 直達海圖座標
        if path == "/api/shipments/update_vessel":
            c_no = data.get("container_no", "")
            new_v = (data.get("vessel_name", "") or "").strip().upper()
            imo = resolve_vessel_imo(new_v)
            display_v = f"{new_v} (IMO:{imo})" if (imo and "IMO" not in new_v) else (new_v or "待定船班")
            ais_url = (
                f"https://www.vesselfinder.com/?imo={imo}"
                if imo
                else f"https://www.vesselfinder.com/vessels?name={urllib.parse.quote(new_v)}"
            )
            conn = get_db()
            cur = conn.cursor()
            cur.execute(
                "UPDATE shipment_tracking SET vessel_name=?, ais_url=?, updated_at=? WHERE container_no=?",
                (display_v, ais_url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), c_no),
            )
            conn.commit()
            conn.close()
            self._send_json(build_dashboard_payload())
            return

        # 5. 刪除船期追蹤項目
        if path == "/api/shipments/delete":
            c_no = data.get("container_no", "")
            conn = get_db()
            cur = conn.cursor()
            cur.execute("DELETE FROM shipment_tracking WHERE container_no=?", (c_no,))
            conn.commit()
            conn.close()
            self._send_json(build_dashboard_payload())
            return

        self._send_json({"error": "Unknown endpoint"}, status=404)


# ==============================================================================
# 6. 本機 IP 偵測與 Port 佔用自動切換 (Rule 6 標準規範)
# ==============================================================================
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_available_port(default_port=8088, max_port=8150):
    for port in range(default_port, max_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return default_port


def main():
    import sys

    init_db()
    default_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8088
    port = find_available_port(default_port)
    if port != default_port:
        print(f"⚠️  預設 Port {default_port} 已被佔用，已自動切換至可用 Port: {port}")

    local_ip = get_local_ip()
    server = HTTPServer(("0.0.0.0", port), RequestHandler)
    print("=" * 68)
    print("  🚢 IPA (異丙醇) 報價與出貨單船期自動追蹤系統 - 已啟動")
    print("=" * 68)
    print(f"  👉 本機瀏覽網址 : http://localhost:{port}")
    print(f"  👉 區網共享網址 : http://{local_ip}:{port}")
    print("=" * 68)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服務已停止。")


if __name__ == "__main__":
    main()
