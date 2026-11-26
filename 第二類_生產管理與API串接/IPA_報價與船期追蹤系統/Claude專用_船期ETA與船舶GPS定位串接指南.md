# 🚢 船期 ETA 免帳號追蹤與船舶 AIS/GPS 衛星定位串接開發指南 (Claude 專用提示詞與技術規格書)

> **用途說明**：請將本 Markdown 文件直接上傳或貼給 **Claude**（Claude Web / Claude Project / Claude Code），並告訴 Claude：
> *「請完全依照這份 Markdown 的技術架構與程式碼規範，幫我建立【CPN（或指定化學品）船期 ETA 與船舶 GPS 即時定位追蹤系統】。」*

---

## 一、 核心痛點與「免船公司帳號」破解架構

在追蹤跨國化學品（如 **CPN 環戊酮**、**IPA 異丙醇**、**NMP** 等 ISO-Tank 或桶裝危險品貨櫃）時，不同批次常由不同船公司承運（萬海、長榮、陽明、德翔、KMTC、SITC、ONE、Maersk 等），且部分船公司官網查詢櫃況或 ETA 需要登入會員帳號。

### 💡 三大免帳號破局技術（Claude 實作鐵律）

1. **船的 GPS 與到港 ETA 跟「船公司帳號」無關，跟「船名 (IMO 國際船籍碼)」與「目的港港務局」有關**：
   * 全球所有國際商船皆依法強制開啟 **AIS（自動識別系統）**，每幾秒鐘透過衛星與岸台公開廣播其 **即時 GPS 經緯度、航速 (Knots)、航向、目的港與 AIS ETA**。
   * 只要將出貨單或採購表上的 **「船名 (Vessel Name)」轉換為「7 碼國際 IMO 船籍編號」**，即可 **100% 免帳號、免手動打字**，直接在網頁內嵌海圖或單船直達網址鎖定該艘船的即時 GPS 位置。
2. **透過「櫃號前 4 碼 (BIC / SCAC Code)」100% 免登入反查船公司與櫃型**：
   * 國際標準櫃號為 4 碼英文 + 7 碼數字。前 4 碼直接決定它是哪家船公司或哪家 ISO-Tank 槽罐營運商（如 `WHLU`=萬海、`EGLV`=長榮、`KMTU`=高麗、`TSLU`=德翔、`NRSU`=日陸槽罐、`EXFU`=EXSIF 槽罐）。
3. **透過「台灣港務公司 (TWPORT) 船舶動態」與「採購 Excel 總表一鍵貼上」取得精準 ETA**：
   * 凡停靠台灣（台中港 `TAICHUNG`、高雄港 `KAOHSIUNG`、基隆港 `KEELUNG`）之外輪，船務代理皆須向台灣港務公司申報公開靠泊預報（免帳號即可查）。
   * 支援直接從 Excel / Outlook 複製採購船期表（含 `SC/PO`、`PI/PO`、`Q'ty`、`POD`、`CLOSED`、`ETD`、`ETA`、`Vessel & Voyage`）貼上網頁，自動解析所有批次並綁定船舶 GPS。

---

## 二、 關鍵技術 1：如何把「船名」自動轉成「7 碼 IMO 編號」並串接即時 GPS 海圖

### ⚠️ 為什麼很多系統點開 AIS 海圖還要自己打船名？（避坑重點）
* **錯誤做法**：把網址連到 `https://www.vesselfinder.com/` 或搜尋頁 `?name=WAN%20HAI%20315`。這只會打開首頁或搜尋列表，人員還得自己打字或點選。
* **正確做法（直達單船 GPS 座標）**：必須使用 **7 碼 IMO 編號**！
  * **外部全螢幕單船 GPS 直達網址**：`https://www.vesselfinder.com/?imo=9302695`（點開直接將衛星海圖鏡頭縮放鎖定在該艘船的即時 GPS 座標正中央，完全免打字！）。
  * **網頁內嵌即時 GPS 雷達海圖 (`aismap.js`)**：在網頁內使用 `<iframe srcdoc="...">` 載入官方 `https://www.vesselfinder.com/aismap.js` 並傳入 `var imo="9302695"; var show_track=true;`，即可在自家系統看板內直接顯示該船的即時 GPS 位置與航跡線！

---

### 🧩 模組 A：Python 後端自動由「船名」反查「7 碼 IMO 編號」程式碼

請 Claude 在後端（Python / Node.js）實作以下「內建常用船名 IMO 快取字典 + 線上自動爬蟲反查 IMO」雙重機制：

```python
import re
import urllib.parse
import urllib.request

# 1. 台灣近洋航線 (日/韓/華東 <-> 台中港/高雄港/基隆港) 主力船隻 IMO 快取字典
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
    """
    輸入任意船名 (如 'WAN HAI 315 V.S271' 或 'KMTC SINGAPORE/ 2615S')，
    自動清洗航次編號並回傳 7 碼國際 IMO 船籍編號。
    """
    v_clean = (vessel_name or "").strip().upper()
    if not v_clean or "待定" in v_clean:
        return ""

    # 若字串中已包含 7 碼 IMO (9開頭7位數)，直接擷取
    m_imo = re.search(r"\b(9\d{6})\b", v_clean)
    if m_imo:
        return m_imo.group(1)

    # 移除航次後綴 (例如 '/ 2615S', 'V.S271', '2620S')
    v_only = re.split(r"[/]|V\.|S\d{3}|\d{4}[A-Z]", v_clean)[0].strip()

    # 先查快取字典
    for k, imo in KNOWN_VESSEL_IMO.items():
        if k in v_clean or (v_only and v_only in k):
            return imo

    # 若字典未命中，自動連線查詢公開船籍庫抓出第一筆 7 碼 IMO
    try:
        q = urllib.parse.quote(v_only or v_clean)
        req = urllib.request.Request(
            f"https://www.vesselfinder.com/vessels?name={q}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        html = urllib.request.urlopen(req, timeout=6).read().decode("utf-8", errors="ignore")
        m = re.search(r"/vessels/details/(\d{7})", html)
        if m:
            KNOWN_VESSEL_IMO[v_only or v_clean] = m.group(1)
            return m.group(1)
    except Exception:
        pass
    return ""
```

---

### 🧩 模組 B：前端網頁內嵌「單船即時 GPS 衛星海圖彈窗」與「免打字直達連結」程式碼

請 Claude 在前端 HTML / JavaScript 中實作以下函數，讓使用者點擊 **`🗺️ 看板內看船位`** 時直接在畫面內彈出即時 GPS 海圖，點擊 **`🛰️ 直達單船海圖`** 時在新分頁直接鎖定該船 GPS：

```javascript
// 前端常用船隻 IMO 對照字典
const FRONTEND_VESSEL_IMO = {
  "KMTC SINGAPORE": "9217412",
  "WAN HAI 315": "9302695",
  "TS PUSAN": "9854844",
  "WAN HAI 308": "9536985",
  "TS KAOHSIUNG": "9810068",
  "WAN HAI 285": "9871323",
  "EVER BUILD": "9790062",
  "YM MOBILITY": "9457737",
  "SITC KEELUNG": "9712761",
  "KMTC KEELUNG": "9157741"
};

// 從「船名 + 航次」字串中自動提取 7 碼 IMO 編號
function extractImoFromVessel(vesselStr, fallbackImo = "") {
  if (fallbackImo) return fallbackImo;
  const v = (vesselStr || "").toUpperCase();
  const m = v.match(/\b(9\d{6})\b/);
  if (m) return m[1];
  for (const [k, imo] of Object.entries(FRONTEND_VESSEL_IMO)) {
    if (v.includes(k)) return imo;
  }
  return "";
}

// 產生免打字直達單船 GPS 海圖網址
function getDirectGpsUrl(vesselStr, fallbackImo = "") {
  const imo = extractImoFromVessel(vesselStr, fallbackImo);
  if (imo) {
    // 關鍵：使用 ?imo=XXXXXXX 可直接將衛星海圖鏡頭鎖定在該船即時 GPS 上！
    return `https://www.vesselfinder.com/?imo=${imo}`;
  }
  const cleanName = (vesselStr || "").replace(/\(.*?\)/g, "").split("/")[0].trim();
  return cleanName && !cleanName.includes("待定")
    ? `https://www.vesselfinder.com/vessels?name=${encodeURIComponent(cleanName)}`
    : `https://www.vesselfinder.com/?p=TWTXG`; // 預設對焦台中港 (TWTXG) 或高雄港 (TWKHH)
}

// 在網頁看板內直接渲染即時 AIS/GPS 衛星雷達海圖 (iframe srcdoc)
function renderEmbeddedGpsMap(containerElementId, vesselStr, fallbackImo = "") {
  const imo = extractImoFromVessel(vesselStr, fallbackImo);
  const box = document.getElementById(containerElementId);
  if (!box) return;

  // 若有 IMO 則直接鎖定單船 GPS 與航跡線 (show_track=true)；若尚未排船則對焦台灣海峽/台中港座標
  const mapConfigScript = imo
    ? `var imo="${imo}"; var zoom=9; var show_track=true;`
    : `var latitude="24.26"; var longitude="120.51"; var zoom=8;`;

  const srcDoc = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>body,html{margin:0;padding:0;height:100%;overflow:hidden;background:#0b1120;}</style>
</head>
<body>
  <script type="text/javascript">
    var width="100%";
    var height="500";
    var names=true;
    ${mapConfigScript}
  <\/script>
  <script type="text/javascript" src="https://www.vesselfinder.com/aismap.js"><\/script>
</body>
</html>`;

  box.innerHTML = `<iframe style="width:100%; height:500px; border:none;" srcdoc='${srcDoc.replace(/'/g, "&#39;")}'></iframe>`;
}
```

---

## 三、 關鍵技術 2：櫃號前 4 碼 (SCAC / BIC) 免帳號自動反查船公司與 ISO-Tank 字典

當人員只有出貨單上的「櫃號（Container No.）」、不知道是哪家船公司時，請 Claude 內建以下前 4 碼反查字典：

```javascript
const CONTAINER_PREFIX_DICT = {
  // 主力貨櫃航商
  "EGLV": { carrier: "長榮海運 (Evergreen)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "EISU": { carrier: "長榮海運 (Evergreen)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "YMLU": { carrier: "陽明海運 (Yang Ming)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "WHLU": { carrier: "萬海航運 (Wan Hai)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "TSLU": { carrier: "德翔海運 (T.S. Lines)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "SITU": { carrier: "海豐國際 (SITC)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "KMTU": { carrier: "高麗海運 (KMTC)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "ONEY": { carrier: "海洋網聯 (ONE)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "MAEU": { carrier: "馬士基 (Maersk)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "CMAU": { carrier: "達飛海運 (CMA CGM)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "COSU": { carrier: "中遠海運 (COSCO)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  "OOLU": { carrier: "東方海外 (OOCL)", type: "一般危險品貨櫃 (桶裝)", isTank: false },
  // 常見化學品 (CPN / IPA / NMP) 專用 ISO-Tank 液體槽罐營運商
  "EXFU": { carrier: "EXSIF Worldwide (化工槽罐商)", type: "ISO-Tank 液體槽罐櫃", isTank: true },
  "STTU": { carrier: "Stolt Tank Containers (思多而特)", type: "ISO-Tank 液體槽罐櫃", isTank: true },
  "HOYU": { carrier: "Hoyer Global (霍耶化工物流)", type: "ISO-Tank 液體槽罐櫃", isTank: true },
  "NRSU": { carrier: "NRS 日陸物流 (日本主力槽罐)", type: "ISO-Tank 液體槽罐櫃", isTank: true },
  "SGCU": { carrier: "Seaco Global (化工槽罐租賃)", type: "ISO-Tank 液體槽罐櫃", isTank: true },
  "BGLU": { carrier: "Bertschi (貝爾奇化工物流)", type: "ISO-Tank 液體槽罐櫃", isTank: true },
  "JOTU": { carrier: "JOT 日本石油輸送", type: "ISO-Tank 液體槽罐櫃", isTank: true }
};
```

---

## 四、 關鍵技術 3：免船公司帳密、免港務局帳密！「一鍵全自動批次抓取所有船隻最新靠泊港口與 AIS ETA」

### ⚠️ 為什麼不能只放台灣港務公司 (`tpnet.twport.com.tw`) 或船公司官網連結？
* 台灣港務公司港棧資訊網 (`tpnet.twport.com.tw/IFAWeb/Function/ShipTrk`) 與部分船公司官網現在會要求登入 B2B 會員帳號密碼，且人員必須一筆一筆手動打字查詢。
* **終極免帳密解法（一鍵全表自動查詢）**：直接由後端（Python 或 Cloudflare Pages Functions）透過各船的 **7 碼 IMO 編號**，批次請求公開免登入的 `https://www.vesselfinder.com/vessels/details/{IMO}`，解析其 `<p class="text2">` 內的 **AIS 衛星即時港務廣播**，一次抓回全表所有船隻的：
  1. **目前狀態**：`⚓ 已靠泊 (arrived at the port of ...)` 或 `🚢 航行中 (en route to the port of ...)`
  2. **目標港口 / 靠泊港口**（自動轉繁體中文：高雄港、台中港、基隆港、台北港、韓國蔚山港等）
  3. **船長廣播最新預計到港時間 (`expected to arrive there on Nov 28, 08:00`) 或實際到港時間 (`ATA`)**
  4. **目前即時航速 (`sailing at a speed of 17.0 knots`) 與最後 AIS 回報時間 (`reported 1 min ago by AIS`)**

### 🧩 模組 C：免帳密「一鍵全查所有船隻最新港務動態 & AIS ETA」後端程式碼 (Python / Cloudflare Worker 通用)

```python
import re
import urllib.request

PORT_NAME_ZH = {
    "KAOHSIUNG": "高雄港",
    "TAICHUNG": "台中港",
    "KEELUNG": "基隆港",
    "CHILUNG": "基隆港",
    "TAIPEI": "台北港",
    "ULSAN": "韓國蔚山港",
    "BUSAN": "韓國釜山港",
    "PUSAN": "韓國釜山港",
    "SHANGHAI": "上海港",
    "NINGBO": "寧波港",
}

def translate_port_zh(port_en: str) -> str:
    if not port_en:
        return "海上航行中"
    up = port_en.upper()
    for k, zh in PORT_NAME_ZH.items():
        if k in up:
            return f"{zh} ({port_en.strip()})"
    return port_en.strip()

def fetch_single_vessel_live_eta(imo: str) -> dict:
    """
    免船公司帳密、免港務局帳密！
    輸入 7 碼 IMO 船籍碼，直接抓回該船最新靠泊港口、預計到港時間 (ETA)、實際到港時間 (ATA) 與即時航速。
    """
    clean_imo = re.sub(r"\D", "", imo or "")
    if not clean_imo:
        return {"imo": "", "state": "PENDING", "live_summary": "⏳ 待綁定船名"}

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

    arr_m = re.search(
        r"arrived at the port of\s+([^.]+?)\s+on\s+([A-Za-z]+\s+\d+,\s*[\d:]+(?:\s*UTC)?)",
        raw_text, re.I
    )
    enroute_m = re.search(
        r"en route to the port of\s+([^,]+(?:,\s*[^,]+)?)\s*,.*?expected to arrive there on\s+([A-Za-z]+\s+\d+,\s*[\d:]+)",
        raw_text, re.I
    )

    if arr_m:
        port_zh = translate_port_zh(arr_m.group(1))
        arr_time = arr_m.group(2).strip()
        return {
            "imo": clean_imo,
            "state": "ARRIVED",
            "port": port_zh,
            "eta_or_ata": arr_time,
            "speed": speed_str,
            "live_summary": f"⚓ 已靠泊【{port_zh}】｜實際到港: {arr_time} (AIS更新: {rep_str})"
        }
    elif enroute_m:
        port_zh = translate_port_zh(enroute_m.group(1))
        eta_time = enroute_m.group(2).strip()
        return {
            "imo": clean_imo,
            "state": "EN_ROUTE",
            "port": port_zh,
            "eta_or_ata": eta_time,
            "speed": speed_str,
            "live_summary": f"🚢 航向【{port_zh}】｜最新AIS預計到港(ETA): {eta_time}｜航速: {speed_str} ({rep_str})"
        }
    return {
        "imo": clean_imo,
        "state": "INFO",
        "live_summary": f"🛰️ AIS即時狀態: {raw_text[:110]}"
    }
```

---

## 五、 關鍵技術 4：採購 Excel / Email 船期總表一鍵貼上與到期自動歸檔（免人工刪除）

1. **支援 Excel / Email 船期表複製貼上一鍵匯入**（自動拆算槽車/貨櫃數、每日入廠日曆、開航➔到港➔入廠三段式甘特圖）。
2. **到期自動歸檔邏輯**：
   * 當 `今日日期 >= ETA` 且未入廠：自動標示 **`⚓ 船已到港報關中`**。
   * 當 `今日日期 > 最後預計入廠日`（或 `ETA + 5 天`）：自動從「🟢 進行中 / 待入廠」主看板隱藏，移入 **`📂 已過期 / 已入廠自動歸檔`** 分頁，無須人工逐筆刪除。

---

## 五、 給人員直接複製貼到 Claude 的啟動指令 (Prompt)

人員在 Claude 開新對話時，只需上傳本 `.md` 檔案，並貼上以下這段話即可：

```text
請幫我依照這份《船期 ETA 免帳號追蹤與船舶 AIS/GPS 衛星定位串接開發指南.md》的完整規格，建立一套【CPN 報價與船期 GPS 自動追蹤系統】。
需求重點：
1. 支援從 Excel 或 Email 直接貼上採購提供的 CPN 船期表（或輸入櫃號/船名），自動反查船公司並自動提取船名的 7 碼 IMO 船籍編號。
2. 每一列都要有「🗺️ 看板內看船位（使用 VesselFinder aismap.js 內嵌鎖定 IMO 即時 GPS 與航跡）」與「🛰️ 直達單船海圖（https://www.vesselfinder.com/?imo=XXXXXXX 免打字直達）」兩顆按鈕。
3. 內建「📅 每日預計入廠日曆」、「📊 開航➔到港➔入廠甘特圖」以及「📂 超過最後入廠日自動移入歷史歸檔區（免人工刪除）」功能。
```
