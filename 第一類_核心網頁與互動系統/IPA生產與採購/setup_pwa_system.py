import os
import json
import openpyxl

excel_path = r'd:\GOOGLE ANGET\第一類_核心網頁與互動系統\IPA生產與採購\20260824產銷計畫.xlsx'
base_dir = r'd:\GOOGLE ANGET\第一類_核心網頁與互動系統\IPA生產與採購\產銷'
web_dir = os.path.join(base_dir, '1_Web_網頁版')
pwa_dir = os.path.join(base_dir, '2_PWA_App版')
icons_dir = os.path.join(pwa_dir, 'icons')
src_dir = os.path.join(base_dir, 'src')

os.makedirs(web_dir, exist_ok=True)
os.makedirs(pwa_dir, exist_ok=True)
os.makedirs(icons_dir, exist_ok=True)
os.makedirs(src_dir, exist_ok=True)

# 1. Parse Excel
wb = openpyxl.load_workbook(excel_path, data_only=True)
sales_ws = wb.worksheets[0]
products = []

for r in range(5, sales_ws.max_row+1):
    pname = str(sales_ws.cell(r, 1).value or '').strip()
    tanks = str(sales_ws.cell(r, 2).value or '').strip()
    capacity = sales_ws.cell(r, 3).value
    init_stock = sales_ws.cell(r, 7).value or sales_ws.cell(r, 4).value
    
    sales_aug = sales_ws.cell(r, 8).value
    sales_sep = sales_ws.cell(r, 10).value
    sales_oct = sales_ws.cell(r, 12).value
    sales_nov = sales_ws.cell(r, 14).value

    line_aug_1 = str(sales_ws.cell(r, 16).value or '').strip()
    range_aug_1 = str(sales_ws.cell(r, 17).value or '').strip()
    qty_aug_1 = sales_ws.cell(r, 18).value

    line_aug_2 = str(sales_ws.cell(r, 19).value or '').strip()
    range_aug_2 = str(sales_ws.cell(r, 20).value or '').strip()
    qty_aug_2 = sales_ws.cell(r, 21).value

    line_aug_3 = str(sales_ws.cell(r, 22).value or '').strip()
    range_aug_3 = str(sales_ws.cell(r, 23).value or '').strip()
    qty_aug_3 = sales_ws.cell(r, 24).value

    qty_sep_1 = sales_ws.cell(r, 21).value
    qty_oct_1 = sales_ws.cell(r, 24).value
    qty_nov_1 = sales_ws.cell(r, 27).value

    sheet_cat = '產銷總表'
    if r in range(5, 40): sheet_cat = '精餾產銷'
    elif r in range(40, 70): sheet_cat = '初餾產銷'
    elif r in range(70, 120): sheet_cat = '調配產銷'

    if pname and pname != '成品品名' and (capacity is not None or init_stock is not None or sales_aug is not None or sales_sep is not None or qty_aug_1 is not None):
        try:
            products.append({
                'id': f'p_{r}',
                'name': pname,
                'tanks': tanks,
                'cat': sheet_cat,
                'capacity': float(capacity) if capacity else 0,
                'initStock': float(init_stock) if init_stock else 0,
                
                'salesAug': float(sales_aug) if sales_aug else 0,
                'salesSep': float(sales_sep) if sales_sep else 0,
                'salesOct': float(sales_oct) if sales_oct else 0,
                'salesNov': float(sales_nov) if sales_nov else 0,

                'lineAug1': line_aug_1, 'rangeAug1': range_aug_1, 'qtyAug1': float(qty_aug_1) if qty_aug_1 else 0,
                'lineAug2': line_aug_2, 'rangeAug2': range_aug_2, 'qtyAug2': float(qty_aug_2) if qty_aug_2 else 0,
                'lineAug3': line_aug_3, 'rangeAug3': range_aug_3, 'qtyAug3': float(qty_aug_3) if qty_aug_3 else 0,

                'lineSep1': '', 'rangeSep1': '', 'qtySep1': float(qty_sep_1) if qty_sep_1 else 0,
                'lineSep2': '', 'rangeSep2': '', 'qtySep2': 0,
                'lineSep3': '', 'rangeSep3': '', 'qtySep3': 0,

                'lineOct1': '', 'rangeOct1': '', 'qtyOct1': float(qty_oct_1) if qty_oct_1 else 0,
                'lineOct2': '', 'rangeOct2': '', 'qtyOct2': 0,
                'lineOct3': '', 'rangeOct3': '', 'qtyOct3': 0,

                'lineNov1': '', 'rangeNov1': '', 'qtyNov1': float(qty_nov_1) if qty_nov_1 else 0,
                'lineNov2': '', 'rangeNov2': '', 'qtyNov2': 0,
                'lineNov3': '', 'rangeNov3': '', 'qtyNov3': 0,
            })
        except Exception:
            pass

bom_ws = wb.worksheets[4]
boms = []
for r in range(3, bom_ws.max_row+1):
    pname = str(bom_ws.cell(r, 1).value or '').strip()
    mname = str(bom_ws.cell(r, 2).value or '').strip()
    ratio = bom_ws.cell(r, 3).value
    if pname and mname and ratio is not None:
        try:
            boms.append({'product': pname, 'material': mname, 'ratio': float(ratio)})
        except: pass

line_ref_ws = wb.worksheets[5]
line_refs = []
for r in range(1, line_ref_ws.max_row+1):
    c1 = str(line_ref_ws.cell(r, 1).value or '').strip()
    c2 = str(line_ref_ws.cell(r, 2).value or '').strip()
    if c1 or c2:
        line_refs.append({'type': c1, 'code': c2})

data_json_str = json.dumps({'products': products, 'boms': boms, 'lineRefs': line_refs}, ensure_ascii=False)

# HTML 模板 (使用純文字取代，不使用 f-string 避免 JSX 衝突)
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  __PWA_HEAD__
  <title>勝一化工 - 產銷計畫表 Web 系統__TITLE_SUFFIX__</title>
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
    input[type=number] { -moz-appearance: textfield; }
    .sticky-col { position: sticky; left: 0; z-index: 20; background: #ffffff; border-right: 2px solid #cbd5e1; min-width: 150px; }
    .table-input { width: 100%; border: 1px solid transparent; background: transparent; text-align: center; font-weight: bold; padding: 2px; }
    .table-input:hover, .table-input:focus { border: 1px solid #3b82f6; background: #eff6ff; outline: none; border-radius: 4px; }
  </style>
</head>
<body class="bg-slate-100 min-h-screen text-slate-800 font-sans p-3">
  <div id="root"></div>

  <script type="text/babel">
    const { useState, useMemo } = React;

    const INITIAL_DATA = __INITIAL_DATA_JSON__;

    function ExactExcelSalesApp() {
      const [products, setProducts] = useState(INITIAL_DATA.products || []);
      const [boms, setBoms] = useState(INITIAL_DATA.boms || []);
      const [lineRefs, setLineRefs] = useState(INITIAL_DATA.lineRefs || []);
      const [searchQuery, setSearchQuery] = useState('');

      // 👁️ 自動隱藏無生產/無需求產品開關
      const [hideEmptyProducts, setHideEmptyProducts] = useState(false);
      
      // 🌟 第一個工作表分頁預設為「產銷總表」
      // '產銷總表' | '精餾產銷' | '初餾產銷' | '調配產銷' | '耗料' | '生產線別參照'
      const [activeTab, setActiveTab] = useState('產銷總表');

      // 🌟 生產排程月份切換狀態：'8月' | '9月' | '10月' | '11月'
      const [selectedProdMonth, setSelectedProdMonth] = useState('8月');

      // ☁️ 雲端 GAS 連線網址配置
      const [gasUrl, setGasUrl] = useState('https://script.google.com/macros/s/AKfycbwhIv8PseJnzrJaT7CnfJCzUYiQcVIG4Oz5H44yJniIrIBT9I0S5BfRKQMO7nHYDMbo6w/exec');
      const [showCloudConfig, setShowCloudConfig] = useState(false);

      // 數字過濾
      const cleanNum = (val) => {
        if (val === undefined || val === null || val === '') return '';
        const s = String(val).trim();
        if (s === '0') return '0';
        return s.replace(/^0+(?=\\d)/, '');
      };

      // 手動更新儲存格
      const handleCellChange = (pId, field, val) => {
        const isNumField = ['capacity', 'initStock', 'salesAug', 'salesSep', 'salesOct', 'salesNov', 'qtyAug1', 'qtyAug2', 'qtyAug3', 'qtySep1', 'qtySep2', 'qtySep3', 'qtyOct1', 'qtyOct2', 'qtyOct3', 'qtyNov1', 'qtyNov2', 'qtyNov3'].includes(field);
        const finalVal = isNumField ? (val === '' ? 0 : parseFloat(val) || 0) : val;
        setProducts(prev => prev.map(p => p.id === pId ? { ...p, [field]: finalVal } : p));
      };

      // 依據工作表頁籤過濾 + 無生產產品隱藏過濾
      const filteredProducts = useMemo(() => {
        return products.filter(p => {
          if (activeTab !== '產銷總表' && activeTab !== '耗料' && activeTab !== '生產線別參照') {
            if (p.cat !== activeTab) return false;
          }

          const augProd = (p.qtyAug1 || 0) + (p.qtyAug2 || 0) + (p.qtyAug3 || 0);
          const sepProd = (p.qtySep1 || 0) + (p.qtySep2 || 0) + (p.qtySep3 || 0);
          const octProd = (p.qtyOct1 || 0) + (p.qtyOct2 || 0) + (p.qtyOct3 || 0);
          const novProd = (p.qtyNov1 || 0) + (p.qtyNov2 || 0) + (p.qtyNov3 || 0);

          if (hideEmptyProducts) {
            const hasStock = (p.initStock || 0) > 0;
            const hasSales = (p.salesAug || 0) > 0 || (p.salesSep || 0) > 0 || (p.salesOct || 0) > 0 || (p.salesNov || 0) > 0;
            const hasProd = augProd > 0 || sepProd > 0 || octProd > 0 || novProd > 0;
            if (!hasStock && !hasSales && !hasProd) return false;
          }

          if (searchQuery.trim()) {
            const q = searchQuery.trim().toLowerCase();
            return (p.name || '').toLowerCase().includes(q) || (p.tanks || '').toLowerCase().includes(q);
          }
          return true;
        });
      }, [products, activeTab, searchQuery, hideEmptyProducts]);

      // 🟢 嚴謹 4 個月連續滾動公式引擎：
      // 1. 8/31 預估結存 = 08/24期初庫存 + 8月生產總量(數量1+2+3) - 08/24~08/31銷
      // 2. 9/30 預估結存 = 8/31庫存 - 09/30銷 + 9月生產總量(數量1+2+3)
      // 3. 10/31 預估結存 = 9/30庫存 - 10/31銷 + 10月生產總量(數量1+2+3)
      // 4. 11/30 預估結存 = 10/31庫存 - 11/30銷 + 11月生產總量(數量1+2+3)
      const calculatedProducts = useMemo(() => {
        return filteredProducts.map(p => {
          const init = p.initStock || 0;
          
          const totalAugProd = (p.qtyAug1 || 0) + (p.qtyAug2 || 0) + (p.qtyAug3 || 0);
          const totalSepProd = (p.qtySep1 || 0) + (p.qtySep2 || 0) + (p.qtySep3 || 0);
          const totalOctProd = (p.qtyOct1 || 0) + (p.qtyOct2 || 0) + (p.qtyOct3 || 0);
          const totalNovProd = (p.qtyNov1 || 0) + (p.qtyNov2 || 0) + (p.qtyNov3 || 0);

          const endAug = init + totalAugProd - (p.salesAug || 0);
          const endSep = endAug + totalSepProd - (p.salesSep || 0);
          const endOct = endSep + totalOctProd - (p.salesOct || 0);
          const endNov = endOct + totalNovProd - (p.salesNov || 0);

          return { 
            ...p, 
            totalAugProd, totalSepProd, totalOctProd, totalNovProd,
            endAug, endSep, endOct, endNov 
          };
        });
      }, [filteredProducts]);

      // BOM 物料需求連動
      const materialRequirements = useMemo(() => {
        const summary = {};
        products.forEach(p => {
          const matchingBoms = boms.filter(b => b.product === p.name);
          matchingBoms.forEach(b => {
            const mat = b.material;
            if (!summary[mat]) summary[mat] = { ratio: b.ratio, aug: 0, sep: 0, oct: 0, nov: 0 };
            summary[mat].aug += (p.salesAug || 0) * b.ratio;
            summary[mat].sep += (p.salesSep || 0) * b.ratio;
            summary[mat].oct += (p.salesOct || 0) * b.ratio;
            summary[mat].nov += (p.salesNov || 0) * b.ratio;
          });
        });
        return summary;
      }, [products, boms]);

      // 依據選擇的月份動態取得該月份的排程動態 Key
      const getMonthFieldKeys = (m) => {
        if (m === '9月') return { l1: 'lineSep1', r1: 'rangeSep1', q1: 'qtySep1', l2: 'lineSep2', r2: 'rangeSep2', q2: 'qtySep2', l3: 'lineSep3', r3: 'rangeSep3', q3: 'qtySep3' };
        if (m === '10月') return { l1: 'lineOct1', r1: 'rangeOct1', q1: 'qtyOct1', l2: 'lineOct2', r2: 'rangeOct2', q2: 'qtyOct2', l3: 'lineOct3', r3: 'rangeOct3', q3: 'qtyOct3' };
        if (m === '11月') return { l1: 'lineNov1', r1: 'rangeNov1', q1: 'qtyNov1', l2: 'lineNov2', r2: 'rangeNov2', q2: 'qtyNov2', l3: 'lineNov3', r3: 'rangeNov3', q3: 'qtyNov3' };
        return { l1: 'lineAug1', r1: 'rangeAug1', q1: 'qtyAug1', l2: 'lineAug2', r2: 'rangeAug2', q2: 'qtyAug2', l3: 'lineAug3', r3: 'rangeAug3', q3: 'qtyAug3' };
      };

      const mKeys = getMonthFieldKeys(selectedProdMonth);

      // 匯出完整 Excel / CSV 報表
      const exportCSV = () => {
        let rows = [["勝一化工 - 產銷計畫表 (4個月連續滾動生產與嚴謹結存)"]];
        rows.push([
          "成品品名", "儲槽容量(MT)", "08/24期初庫存",
          "08/24~08/31銷", "09/30銷", "10/31銷", "11/30銷",
          "8月生產總量", "8/31當月預估結存",
          "9月生產總量", "9/30當月預估結存",
          "10月生產總量", "10/31當月預估結存",
          "11月生產總量", "11/30當月預估結存"
        ]);

        calculatedProducts.forEach(p => {
          rows.push([
            p.name, p.capacity, p.initStock,
            p.salesAug, p.salesSep, p.salesOct, p.salesNov,
            p.totalAugProd, Math.round(p.endAug*10)/10,
            p.totalSepProd, Math.round(p.endSep*10)/10,
            p.totalOctProd, Math.round(p.endOct*10)/10,
            p.totalNovProd, Math.round(p.endNov*10)/10
          ]);
        });

        const csvContent = "\\uFEFF" + rows.map(r => r.join(",")).join("\\n");
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.setAttribute("href", url);
        link.setAttribute("download", `勝一化工_4個月滾動產銷總表_${new Date().toISOString().slice(0,10)}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      };

      return (
        <div className="max-w-[1920px] mx-auto space-y-3 text-xs">
          __PWA_BANNER__
          
          {/* Header 頂部 */}
          <div className="bg-slate-800 text-white p-3 rounded-xl shadow flex flex-col md:flex-row justify-between items-center gap-3">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">📊</span>
              <div>
                <h1 className="text-base font-bold flex items-center">
                  勝一化工 - 產銷計畫表 Web 系統 
                  <span className="ml-2 text-xs bg-cyan-600 px-2 py-0.5 rounded-full font-bold">
                    __SUB_TITLE_BADGE__
                  </span>
                </h1>
                <p className="text-[11px] text-slate-300">總表為第一頁分頁、可自由切換 8/9/10/11月生產排程，連動最右側 4 個月結存</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <button 
                onClick={() => setShowCloudConfig(!showCloudConfig)}
                className="bg-indigo-700 hover:bg-indigo-600 text-white px-2.5 py-1.5 rounded-lg font-bold border border-indigo-500 shadow flex items-center space-x-1"
                title="查看或設定 Google Apps Script 雲端串接網址"
              >
                <span>☁️ 雲端 GAS 串接</span>
              </button>

              <label className="flex items-center space-x-1.5 cursor-pointer bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg border border-slate-600 font-bold text-xs select-none">
                <input 
                  type="checkbox" 
                  checked={hideEmptyProducts}
                  onChange={e => setHideEmptyProducts(e.target.checked)}
                  className="h-4 w-4 text-cyan-500 rounded focus:ring-0"
                />
                <span className={hideEmptyProducts ? 'text-amber-300' : 'text-slate-300'}>
                  {hideEmptyProducts ? '👁️ 已隱藏無生產產品' : '👁️ 隱藏無生產/需求產品'}
                </span>
              </label>

              <input 
                type="text" 
                placeholder="🔍 搜尋成品名稱或槽號..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="bg-slate-700 text-white px-3 py-1.5 rounded-lg border border-slate-600 text-xs w-52 focus:outline-none focus:border-cyan-400 font-bold"
              />
              <button onClick={exportCSV} className="bg-emerald-600 hover:bg-emerald-500 text-white px-3.5 py-1.5 rounded-lg font-bold shadow flex items-center space-x-1">
                <span>📥 匯出 CSV 報表</span>
              </button>
            </div>
          </div>

          {/* 雲端 GAS 網址折疊面板 */}
          {showCloudConfig && (
            <div className="bg-indigo-950 text-indigo-100 p-3 rounded-xl border border-indigo-800 shadow space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-bold text-xs text-amber-300">🔗 Google Apps Script 雲端同步節點配置</span>
                <button onClick={() => setShowCloudConfig(false)} className="text-slate-400 hover:text-white">✕ 關閉</button>
              </div>
              <div className="flex gap-2">
                <input 
                  type="text" 
                  value={gasUrl}
                  onChange={e => setGasUrl(e.target.value)}
                  className="flex-1 bg-slate-900 text-white px-3 py-1 rounded border border-indigo-700 text-xs font-mono"
                  placeholder="請輸入 GAS 網頁應用程式部署網址 (/exec)..."
                />
                <a 
                  href={gasUrl} 
                  target="_blank" 
                  rel="noreferrer"
                  className="bg-cyan-600 hover:bg-cyan-500 text-white px-3 py-1 rounded font-bold text-xs flex items-center"
                >
                  🚀 開啟雲端 GAS
                </a>
              </div>
              <p className="text-[10px] text-indigo-300">
                目前綁定 GAS Web App：https://script.google.com/macros/s/AKfycbwhIv8PseJnzrJaT7CnfJCzUYiQcVIG4Oz5H44yJniIrIBT9I0S5BfRKQMO7nHYDMbo6w/exec
              </p>
            </div>
          )}

          {/* 🌟 100% 對齊 Excel 工作表分頁 (總表放在第一個分頁！) */}
          <div className="flex border-b-2 border-slate-300 space-x-1">
            {[
              { id: '產銷總表', label: '產銷總表' },
              { id: '精餾產銷', label: '精餾產銷' },
              { id: '初餾產銷', label: '初餾產銷' },
              { id: '調配產銷', label: '調配產銷' },
              { id: '耗料', label: '🧪 耗料 (BOM 換算)' },
              { id: '生產線別參照', label: '⚙️ 生產線別參照' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-5 py-2 font-bold rounded-t-lg transition-all border-t border-x ${activeTab === tab.id ? 'bg-cyan-700 text-white border-cyan-800 shadow-md scale-105 z-10' : 'bg-white text-slate-700 hover:bg-slate-200 border-slate-300'}`}
              >
                <span>{tab.label}</span>
              </button>
            ))}
          </div>

          {/* 產銷與生產排程主力表格 */}
          {activeTab !== '耗料' && activeTab !== '生產線別參照' && (
            <div className="bg-white rounded-xl shadow border overflow-hidden space-y-2 p-2">
              
              {/* 🌟 藍紫色生產排程月份切換選單 */}
              <div className="bg-indigo-900 text-white p-2 rounded-lg flex justify-between items-center px-4">
                <div className="flex items-center space-x-2 font-bold">
                  <span>📅 排程月份切換填報：</span>
                  {['8月', '9月', '10月', '11月'].map(m => (
                    <button
                      key={m}
                      onClick={() => setSelectedProdMonth(m)}
                      className={`px-3 py-1 rounded font-black transition-all text-xs ${selectedProdMonth === m ? 'bg-amber-400 text-indigo-950 shadow-md scale-110' : 'bg-indigo-800 text-indigo-200 hover:bg-indigo-700'}`}
                    >
                      {m} 排程
                    </button>
                  ))}
                </div>

                <div className="text-[11px] text-indigo-200 font-bold">
                  目前正在填報：<span className="text-amber-300 underline font-black text-sm">{selectedProdMonth}</span> 的 3 次生產期間與線別
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-center border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-800 text-white font-bold border-b border-slate-700">
                      <th className="sticky-col p-2.5 text-left border-b border-slate-700 bg-slate-800 text-white">成品品名</th>
                      <th className="p-2.5 border-r border-slate-700">儲槽容量 (MT)</th>
                      <th className="p-2.5 bg-cyan-900 border-r border-slate-700">08/24 期初</th>

                      {/* 銷售需求區塊 */}
                      <th className="p-2.5 bg-sky-900/90">08/24~08/31 銷</th>
                      <th className="p-2.5 bg-sky-900/90">09/30 銷</th>
                      <th className="p-2.5 bg-sky-900/90">10/31 銷</th>
                      <th className="p-2.5 bg-sky-900/90 border-r border-slate-700">11/30 銷</th>

                      {/* 動態顯示所選月份的 3 次生產期間排程 (藍紫底) */}
                      <th className="p-2.5 bg-indigo-900/90">{selectedProdMonth} 線別 1</th>
                      <th className="p-2.5 bg-indigo-900/90">{selectedProdMonth} 日期 1</th>
                      <th className="p-2.5 bg-indigo-900/90 border-r border-indigo-700">{selectedProdMonth} 數量 1 (MT)</th>

                      <th className="p-2.5 bg-indigo-900/70">{selectedProdMonth} 線別 2</th>
                      <th className="p-2.5 bg-indigo-900/70">{selectedProdMonth} 日期 2</th>
                      <th className="p-2.5 bg-indigo-900/70 border-r border-indigo-700">{selectedProdMonth} 數量 2 (MT)</th>

                      <th className="p-2.5 bg-indigo-900/50">{selectedProdMonth} 線別 3</th>
                      <th className="p-2.5 bg-indigo-900/50">{selectedProdMonth} 日期 3</th>
                      <th className="p-2.5 bg-indigo-900/50 border-r-2 border-slate-700">{selectedProdMonth} 數量 3 (MT)</th>

                      {/* 最右側 4 個月連動結存庫存區塊 */}
                      <th className="p-2.5 bg-slate-900 border-r border-slate-700 text-cyan-300">8/31 結存</th>
                      <th className="p-2.5 bg-slate-900 border-r border-slate-700 text-cyan-300">9/30 結存</th>
                      <th className="p-2.5 bg-slate-900 border-r border-slate-700 text-cyan-300">10/31 結存</th>
                      <th className="p-2.5 bg-slate-900 text-cyan-300">11/30 結存</th>
                    </tr>
                  </thead>
                  <tbody>
                    {calculatedProducts.map((p, idx) => (
                      <tr key={p.id} className={`border-b hover:bg-cyan-50/50 ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}>
                        <td className="sticky-col p-2 text-left font-black text-slate-800 border-r">{p.name}</td>
                        <td className="p-2 font-bold text-slate-600 border-r">{p.capacity > 0 ? p.capacity : '---'}</td>
                        
                        {/* 08/24 期初 */}
                        <td className="p-0 bg-cyan-50/40 border-r">
                          <input 
                            type="number" 
                            value={cleanNum(p.initStock)}
                            onFocus={e => e.target.select()}
                            onChange={e => handleCellChange(p.id, 'initStock', e.target.value)}
                            className="table-input text-cyan-900"
                          />
                        </td>

                        {/* 08/24~08/31 銷 */}
                        <td className="p-0 bg-sky-50/30">
                          <input type="number" value={cleanNum(p.salesAug)} onFocus={e => e.target.select()} onChange={e => handleCellChange(p.id, 'salesAug', e.target.value)} className="table-input text-sky-900" />
                        </td>

                        {/* 09/30 銷 */}
                        <td className="p-0 bg-sky-50/30">
                          <input type="number" value={cleanNum(p.salesSep)} onFocus={e => e.target.select()} onChange={e => handleCellChange(p.id, 'salesSep', e.target.value)} className="table-input text-sky-900" />
                        </td>

                        {/* 10/31 銷 */}
                        <td className="p-0 bg-sky-50/30">
                          <input type="number" value={cleanNum(p.salesOct)} onFocus={e => e.target.select()} onChange={e => handleCellChange(p.id, 'salesOct', e.target.value)} className="table-input text-sky-900" />
                        </td>

                        {/* 11/30 銷 */}
                        <td className="p-0 bg-sky-50/30 border-r">
                          <input type="number" value={cleanNum(p.salesNov)} onFocus={e => e.target.select()} onChange={e => handleCellChange(p.id, 'salesNov', e.target.value)} className="table-input text-sky-900" />
                        </td>

                        {/* 所選月份 排程 1 */}
                        <td className="p-0 bg-indigo-50/30">
                          <input type="text" value={p[mKeys.l1] || ''} onChange={e => handleCellChange(p.id, mKeys.l1, e.target.value)} className="table-input text-indigo-900 text-[11px]" placeholder="如 S01" />
                        </td>
                        <td className="p-0 bg-indigo-50/30">
                          <input type="text" value={p[mKeys.r1] || ''} onChange={e => handleCellChange(p.id, mKeys.r1, e.target.value)} className="table-input text-indigo-800 text-[11px]" placeholder="如 24~31" />
                        </td>
                        <td className="p-0 bg-indigo-50/30 border-r">
                          <input type="number" value={cleanNum(p[mKeys.q1])} onFocus={e => e.target.select()} onChange={e => handleCellChange(p.id, mKeys.q1, e.target.value)} className="table-input text-indigo-900 font-black" />
                        </td>

                        {/* 所選月份 排程 2 */}
                        <td className="p-0 bg-indigo-50/20">
                          <input type="text" value={p[mKeys.l2] || ''} onChange={e => handleCellChange(p.id, mKeys.l2, e.target.value)} className="table-input text-indigo-900 text-[11px]" />
                        </td>
                        <td className="p-0 bg-indigo-50/20">
                          <input type="text" value={p[mKeys.r2] || ''} onChange={e => handleCellChange(p.id, mKeys.r2, e.target.value)} className="table-input text-indigo-800 text-[11px]" />
                        </td>
                        <td className="p-0 bg-indigo-50/20 border-r">
                          <input type="number" value={cleanNum(p[mKeys.q2])} onFocus={e => e.target.select()} onChange={e => handleCellChange(p.id, mKeys.q2, e.target.value)} className="table-input text-indigo-900 font-black" />
                        </td>

                        {/* 所選月份 排程 3 */}
                        <td className="p-0 bg-indigo-50/10">
                          <input type="text" value={p[mKeys.l3] || ''} onChange={e => handleCellChange(p.id, mKeys.l3, e.target.value)} className="table-input text-indigo-900 text-[11px]" />
                        </td>
                        <td className="p-0 bg-indigo-50/10">
                          <input type="text" value={p[mKeys.r3] || ''} onChange={e => handleCellChange(p.id, mKeys.r3, e.target.value)} className="table-input text-indigo-800 text-[11px]" />
                        </td>
                        <td className="p-0 bg-indigo-50/10 border-r-2 border-slate-700">
                          <input type="number" value={cleanNum(p[mKeys.q3])} onFocus={e => e.target.select()} onChange={e => handleCellChange(p.id, mKeys.q3, e.target.value)} className="table-input text-indigo-900 font-black" />
                        </td>

                        {/* 最右側 4 個月連動結存庫存 (嚴謹連動：庫存[M] = 庫存[M-1] + 生產[M] - 銷[M]) */}
                        <td className={`p-2 font-black border-r ${p.endAug < 0 ? 'bg-red-500 text-white animate-pulse' : (p.endAug < 50 ? 'bg-emerald-100 text-red-700 font-black' : 'bg-amber-100 text-slate-900')}`}>
                          {Math.round(p.endAug)}
                        </td>

                        <td className={`p-2 font-black border-r ${p.endSep < 0 ? 'bg-red-500 text-white animate-pulse' : (p.endSep < 50 ? 'bg-emerald-100 text-red-700 font-black' : 'bg-amber-100 text-slate-900')}`}>
                          {Math.round(p.endSep)}
                        </td>

                        <td className={`p-2 font-black border-r ${p.endOct < 0 ? 'bg-red-500 text-white animate-pulse' : (p.endOct < 50 ? 'bg-emerald-100 text-red-700 font-black' : 'bg-amber-100 text-slate-900')}`}>
                          {Math.round(p.endOct)}
                        </td>

                        <td className={`p-2 font-black ${p.endNov < 0 ? 'bg-red-500 text-white animate-pulse' : (p.endNov < 50 ? 'bg-emerald-100 text-red-700 font-black' : 'bg-amber-100 text-slate-900')}`}>
                          {Math.round(p.endNov)}
                        </td>

                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 耗料頁籤 */}
          {activeTab === '耗料' && (
            <div className="bg-white rounded-xl shadow border overflow-hidden p-4 space-y-3">
              <div className="bg-cyan-50 p-2.5 rounded-lg border border-cyan-200 text-cyan-900 font-bold text-xs flex justify-between items-center">
                <span>🧪 依據成品銷售填報量與物料標準，自動連動計算全廠所需之原料耗用量 (MT)：</span>
                <span className="bg-cyan-700 text-white px-2.5 py-0.5 rounded text-[10px]">即時連動</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-center border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-800 text-white font-bold border-b">
                      <th className="p-2.5 text-left">原料品名</th>
                      <th className="p-2.5">單耗換算係數</th>
                      <th className="p-2.5 bg-sky-900">08/24~08/31 耗用量 (MT)</th>
                      <th className="p-2.5 bg-sky-900">09/30 耗用量 (MT)</th>
                      <th className="p-2.5 bg-sky-900">10/31 耗用量 (MT)</th>
                      <th className="p-2.5 bg-sky-900">11/30 耗用量 (MT)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(materialRequirements).map((mat, idx) => {
                      const info = materialRequirements[mat];
                      return (
                        <tr key={mat} className={`border-b hover:bg-cyan-50/50 ${idx % 2 === 0 ? 'bg-white' : 'bg-slate-50/50'}`}>
                          <td className="p-2.5 text-left font-black text-slate-800">{mat}</td>
                          <td className="p-2.5 font-bold text-slate-600">{info.ratio}</td>
                          <td className="p-2.5 font-black text-sky-900">{Math.round(info.aug)}</td>
                          <td className="p-2.5 font-black text-sky-900">{Math.round(info.sep)}</td>
                          <td className="p-2.5 font-black text-sky-900">{Math.round(info.oct)}</td>
                          <td className="p-2.5 font-black text-sky-900">{Math.round(info.nov)}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 生產線別參照頁籤 */}
          {activeTab === '生產線別參照' && (
            <div className="bg-white rounded-xl shadow border overflow-hidden p-4 space-y-3">
              <h2 className="text-sm font-bold text-slate-800 border-b pb-2">⚙️ 生產線別與代號對照表</h2>
              <div className="grid grid-cols-2 gap-4 max-w-lg">
                {lineRefs.map((item, idx) => (
                  <div key={idx} className="p-2 border rounded bg-slate-50 flex justify-between font-bold">
                    <span className="text-slate-600">{item.type}</span>
                    <span className="text-cyan-800">{item.code}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      );
    }

    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<ExactExcelSalesApp />);
    __PWA_SCRIPT__
  </script>
</body>
</html>"""

PWA_HEAD = """
  <!-- PWA 配置 -->
  <link rel="manifest" href="manifest.json">
  <meta name="theme-color" content="#1e293b">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
  <meta name="apple-mobile-web-app-title" content="勝一產銷計畫">
  <link rel="apple-touch-icon" href="icons/icon-192.png">
"""

PWA_BANNER = """
          {/* PWA 頂部安裝橫幅 */}
          <div id="pwa-install-banner" className="hidden bg-gradient-to-r from-blue-700 via-indigo-700 to-cyan-700 text-white px-4 py-2.5 rounded-xl shadow-lg flex items-center justify-between border border-blue-400/30">
            <div className="flex items-center space-x-2.5">
              <span className="text-xl">📱</span>
              <div>
                <span className="font-black text-sm tracking-wide">安裝「勝一產銷計畫」獨立桌面/手機 App</span>
                <span className="ml-2 text-[11px] text-blue-200 hidden sm:inline">支援無網格全螢幕獨立視窗與離線即時推算</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button id="pwa-install-btn" className="bg-white text-indigo-900 hover:bg-blue-50 font-black px-4 py-1 rounded-full text-xs shadow transition active:scale-95">
                立即安裝
              </button>
              <button onClick={() => { const b = document.getElementById('pwa-install-banner'); if (b) b.style.display = 'none'; }} className="text-white/80 hover:text-white px-1.5 py-0.5 text-sm font-bold">
                ✕
              </button>
            </div>
          </div>
"""

PWA_SCRIPT = """
    // PWA Service Worker 註冊與安裝事件監聽
    let deferredPrompt = null;
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      const banner = document.getElementById('pwa-install-banner');
      if (banner) {
        banner.classList.remove('hidden');
        banner.classList.add('flex');
      }
    });

    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.addEventListener('click', async () => {
        if (deferredPrompt) {
          deferredPrompt.prompt();
          const { outcome } = await deferredPrompt.userChoice;
          if (outcome === 'accepted') {
            const banner = document.getElementById('pwa-install-banner');
            if (banner) banner.style.display = 'none';
          }
          deferredPrompt = null;
        } else {
          alert('請由瀏覽器右上角選單點選「安裝勝一產銷計畫」或「新增至主畫面」！');
        }
      });
    }

    if ('serviceWorker' in navigator) {
      window.addEventListener('load', () => {
        navigator.serviceWorker.register('./sw.js')
          .then(reg => console.log('PWA ServiceWorker registered:', reg.scope))
          .catch(err => console.log('PWA ServiceWorker registration failed:', err));
      });
    }
"""

# 1. 產生 1_Web_網頁版/index.html
web_html = HTML_TEMPLATE.replace('__PWA_HEAD__', '')\
                        .replace('__TITLE_SUFFIX__', ' (Web 網頁版)')\
                        .replace('__INITIAL_DATA_JSON__', data_json_str)\
                        .replace('__PWA_BANNER__', '')\
                        .replace('__SUB_TITLE_BADGE__', '總表置頂 + 月份切換排程 Web 版 v7.0')\
                        .replace('__PWA_SCRIPT__', '')

with open(os.path.join(web_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(web_html)

# 2. 產生 2_PWA_App版/index.html
pwa_html = HTML_TEMPLATE.replace('__PWA_HEAD__', PWA_HEAD)\
                        .replace('__TITLE_SUFFIX__', ' (PWA 獨立 App 版)')\
                        .replace('__INITIAL_DATA_JSON__', data_json_str)\
                        .replace('__PWA_BANNER__', PWA_BANNER)\
                        .replace('__SUB_TITLE_BADGE__', '總表置頂 + 月份切換排程 PWA 獨立 App 版 v7.0')\
                        .replace('__PWA_SCRIPT__', PWA_SCRIPT)

with open(os.path.join(pwa_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(pwa_html)

# 3. 產生 src/index.html (相容性)
with open(os.path.join(src_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(web_html)

# 4. 產生 2_PWA_App版/manifest.json
manifest_data = {
  "name": "勝一化工 - 產銷計畫表 Web 系統",
  "short_name": "勝一產銷計畫",
  "description": "勝一化工 4 個月連續滾動生產排程與嚴謹結存試算 PWA 應用程式",
  "start_url": "./index.html",
  "display": "standalone",
  "background_color": "#0f172a",
  "theme_color": "#1e293b",
  "orientation": "any",
  "icons": [
    {
      "src": "icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
with open(os.path.join(pwa_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
    json.dump(manifest_data, f, ensure_ascii=False, indent=2)

# 5. 產生 2_PWA_App版/sw.js
sw_code = """const CACHE_NAME = 'sales-plan-pwa-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(ASSETS).catch(err => console.log('PWA Cache assets failed:', err));
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => {
      return Promise.all(
        keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
"""
with open(os.path.join(pwa_dir, 'sw.js'), 'w', encoding='utf-8') as f:
    f.write(sw_code)

# 6. 產生 2_PWA_App版/run_server.py
run_server_code = """import os
import sys
import socket
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

class UTF8Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        if self.path.endswith('.html') or self.path == '/' or self.path == '':
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        super().end_headers()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'

def find_available_port(start_port=8086):
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
            port += 1
    return start_port

def main():
    if sys.platform == 'win32':
        os.system('chcp 65001 >nul')
        
    title = '勝一化工 - 產銷計畫表 Web 系統 (PWA 獨立 App 版)'
    port = find_available_port(8086)
    local_ip = get_local_ip()
    
    print('=' * 65)
    print(f'   🚀 {title}')
    print('=' * 65)
    print(f'[✓] 電腦本機網址:   http://localhost:{port}')
    print(f'[✓] 手機/區域網網址: http://{local_ip}:{port}')
    print('-' * 65)
    print('【📱 如何安裝為桌面 / 手機 獨立 App】:')
    print('  1. 電腦瀏覽器 (Chrome/Edge): 點擊網址列右側「安裝」或頁面頂部「立即安裝」')
    print('  2. Android 手機: 點擊頁面上方「立即安裝」或選單「新增至主畫面」')
    print('  3. iPhone (Safari): 點擊底部「分享」按鈕 ->「加入主畫面」')
    print('=' * 65)
    print(f'正在為您自動開啟瀏覽器: http://localhost:{port} ...\\n')
    
    webbrowser.open(f'http://localhost:{port}')
    
    print('伺服器運行中 (按 Ctrl+C 可停止)...')
    server = HTTPServer(('0.0.0.0', port), UTF8Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\\n伺服器已安全停止。')

if __name__ == '__main__':
    main()
"""
with open(os.path.join(pwa_dir, 'run_server.py'), 'w', encoding='utf-8') as f:
    f.write(run_server_code)

# 7. 產生 2_PWA_App版/啟動PWA本機測試.bat
bat_pwa = """@echo off
chcp 65001 >nul
cd /d "%~dp0"
python run_server.py
pause
"""
with open(os.path.join(pwa_dir, '啟動PWA本機測試.bat'), 'w', encoding='utf-8') as f:
    f.write(bat_pwa)

# 8. 產生 2_PWA_App版/一鍵產生圖文手冊.bat
bat_manual = """@echo off
chcp 65001 >nul
cd /d "%~dp0"
python build_manual_doc.py
pause
"""
with open(os.path.join(pwa_dir, '一鍵產生圖文手冊.bat'), 'w', encoding='utf-8') as f:
    f.write(bat_manual)

# 9. 產生 2_PWA_App版/build_manual_doc.py
build_manual_code = """import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def create_manual():
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)
        
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_title = p_title.add_run("【系統操作手冊】勝一化工 - 產銷計畫 Web 系統 (PWA 獨立 App 版)")
    run_title.font.name = "微軟正黑體"
    run_title.font.size = Pt(20)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(14, 116, 144)
    
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_sub = p_sub.add_run("版本：v7.0 (PWA 雙軌版) | 適用設備：Windows 電腦 / Android 手機 / iPhone / 平板")
    run_sub.font.name = "微軟正黑體"
    run_sub.font.size = Pt(10)
    run_sub.font.color.rgb = RGBColor(100, 100, 100)
    
    doc.add_paragraph("―" * 50)
    
    doc.add_heading("一、 系統簡介與 4 個月滾動生產公式", level=1)
    doc.add_paragraph("本系統為勝一化工產銷計畫表之現代化 PWA 系統，直接對齊 Excel 產銷計畫，具備 4 個月連續滾動連動公式：")
    
    formulas = [
        ("1. 8/31 預估結存", "08/24 期初庫存 + 8月生產總量 (數量1+2+3) - 08/24~08/31 銷"),
        ("2. 9/30 預估結存", "8/31 庫存 + 9月生產總量 (數量1+2+3) - 09/30 銷"),
        ("3. 10/31 預估結存", "9/30 庫存 + 10月生產總量 (數量1+2+3) - 10/31 銷"),
        ("4. 11/30 預估結存", "10/31 庫存 + 11月生產總量 (數量1+2+3) - 11/30 銷")
    ]
    for f_title, f_calc in formulas:
        p = doc.add_paragraph()
        r = p.add_run(f"◆ {f_title} = ")
        r.bold = True
        r.font.color.rgb = RGBColor(14, 116, 144)
        p.add_run(f_calc)

    doc.add_heading("二、 核心亮點功能", level=1)
    highlights = [
        ("產銷總表置頂", "首頁直接呈現產銷總表，並提供精餾、初餾、調配、耗料BOM、生產線別參照快速頁籤。"),
        ("月份切換排程", "點選「8月 / 9月 / 10月 / 11月 排程」按鈕，立即切換當月 3 次排程（線別、日期區間、數量），即時連動最右側 4 個月結存。"),
        ("隱藏無生產/需求產品", "勾選「👁️ 隱藏無生產/需求產品」，畫面立即過濾無需求品項，聚焦於當月實際運作項目。"),
        ("雲端 GAS 串接", "內建 GAS Web App 快速啟動與雲端同步設定，方便與既有 Google Apps Script 資料庫對接。")
    ]
    for h_title, h_desc in highlights:
        p = doc.add_paragraph()
        r = p.add_run(f"★ {h_title}：")
        r.bold = True
        p.add_run(h_desc)

    doc.add_heading("三、 PWA 獨立 App 安裝與離線使用指引", level=1)
    steps = [
        ("Windows 電腦端 (Chrome/Edge)", "雙擊「啟動PWA本機測試.bat」開啟網頁，點擊頁面頂部「立即安裝」或網址列右側「安裝勝一產銷計畫」圖示，即可將系統安裝為桌面獨立 App。"),
        ("Android 手機 / 平板", "手機連線本機伺服器之區域網 IP (例如 http://192.168.x.x:8086)，點擊頂部「立即安裝」或瀏覽器選單「新增至主畫面」。"),
        ("iPhone / iPad (Safari)", "在 Safari 中開啟網址，點擊底部「分享」按鈕，選擇「加入主畫面」，即可如同原生 App 般在主畫面開啟使用。")
    ]
    for s_title, s_desc in steps:
        p = doc.add_paragraph()
        r = p.add_run(f"【{s_title}】\\n")
        r.bold = True
        r.font.color.rgb = RGBColor(14, 116, 144)
        p.add_run(s_desc)

    base = os.path.dirname(os.path.abspath(__file__))
    docx_path = os.path.join(base, "勝一產銷計畫系統_操作手冊.docx")
    doc.save(docx_path)
    print(f"Word 手冊已成功生成: {docx_path}")

    try:
        import win32com.client
        word = win32com.client.Dispatch('Word.Application')
        doc_obj = word.Documents.Open(docx_path)
        pdf_path = os.path.join(base, "勝一產銷計畫系統_操作手冊.pdf")
        doc_obj.SaveAs(pdf_path, FileFormat=17)
        doc_obj.Close()
        word.Quit()
        print(f"PDF 手冊已成功生成: {pdf_path}")
    except Exception as e:
        print(f"PDF 轉換略過或由系統自動產生: {e}")

if __name__ == '__main__':
    create_manual()
"""
with open(os.path.join(pwa_dir, 'build_manual_doc.py'), 'w', encoding='utf-8') as f:
    f.write(build_manual_code)

print("All PWA dual-track files generated successfully!")
