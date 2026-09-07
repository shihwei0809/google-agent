import openpyxl
import json
import os

excel_path = r'd:\GOOGLE ANGET\第一類_核心網頁與互動系統\IPA生產與採購\20260824產銷計畫.xlsx'
out_html_path = r'd:\GOOGLE ANGET\第一類_核心網頁與互動系統\IPA生產與採購\產銷\src\index.html'

wb = openpyxl.load_workbook(excel_path, data_only=True)
sales_ws = wb.worksheets[0]

products = []

for r in range(5, sales_ws.max_row+1):
    pname = str(sales_ws.cell(r, 1).value or '').strip()
    tanks = str(sales_ws.cell(r, 2).value or '').strip()
    capacity = sales_ws.cell(r, 3).value
    init_stock = sales_ws.cell(r, 7).value or sales_ws.cell(r, 4).value  # G欄/D欄 08/24期初
    
    # 銷售需求 (H, J, L, N)
    sales_aug = sales_ws.cell(r, 8).value
    sales_sep = sales_ws.cell(r, 10).value
    sales_oct = sales_ws.cell(r, 12).value
    sales_nov = sales_ws.cell(r, 14).value

    # 8月 3 次生產期間
    line_aug_1 = str(sales_ws.cell(r, 16).value or '').strip()
    range_aug_1 = str(sales_ws.cell(r, 17).value or '').strip()
    qty_aug_1 = sales_ws.cell(r, 18).value

    line_aug_2 = str(sales_ws.cell(r, 19).value or '').strip()
    range_aug_2 = str(sales_ws.cell(r, 20).value or '').strip()
    qty_aug_2 = sales_ws.cell(r, 21).value

    line_aug_3 = str(sales_ws.cell(r, 22).value or '').strip()
    range_aug_3 = str(sales_ws.cell(r, 23).value or '').strip()
    qty_aug_3 = sales_ws.cell(r, 24).value

    # 9月 生產量
    qty_sep_1 = sales_ws.cell(r, 21).value
    # 10月 生產量
    qty_oct_1 = sales_ws.cell(r, 24).value
    # 11月 生產量
    qty_nov_1 = sales_ws.cell(r, 27).value

    # 分頁歸屬 (對齊 Excel 工作表)
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

                # 8月排程 (1, 2, 3 期間)
                'lineAug1': line_aug_1, 'rangeAug1': range_aug_1, 'qtyAug1': float(qty_aug_1) if qty_aug_1 else 0,
                'lineAug2': line_aug_2, 'rangeAug2': range_aug_2, 'qtyAug2': float(qty_aug_2) if qty_aug_2 else 0,
                'lineAug3': line_aug_3, 'rangeAug3': range_aug_3, 'qtyAug3': float(qty_aug_3) if qty_aug_3 else 0,

                # 9月排程 (1, 2, 3 期間)
                'lineSep1': '', 'rangeSep1': '', 'qtySep1': float(qty_sep_1) if qty_sep_1 else 0,
                'lineSep2': '', 'rangeSep2': '', 'qtySep2': 0,
                'lineSep3': '', 'rangeSep3': '', 'qtySep3': 0,

                # 10月排程 (1, 2, 3 期間)
                'lineOct1': '', 'rangeOct1': '', 'qtyOct1': float(qty_oct_1) if qty_oct_1 else 0,
                'lineOct2': '', 'rangeOct2': '', 'qtyOct2': 0,
                'lineOct3': '', 'rangeOct3': '', 'qtyOct3': 0,

                # 11月排程 (1, 2, 3 期間)
                'lineNov1': '', 'rangeNov1': '', 'qtyNov1': float(qty_nov_1) if qty_nov_1 else 0,
                'lineNov2': '', 'rangeNov2': '', 'qtyNov2': 0,
                'lineNov3': '', 'rangeNov3': '', 'qtyNov3': 0,
            })
        except Exception:
            pass

# 讀取 Sheet 4 (物料標準/耗料)
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

# 讀取 Sheet 5 (生產線別參照)
line_ref_ws = wb.worksheets[5]
line_refs = []
for r in range(1, line_ref_ws.max_row+1):
    c1 = str(line_ref_ws.cell(r, 1).value or '').strip()
    c2 = str(line_ref_ws.cell(r, 2).value or '').strip()
    if c1 or c2:
        line_refs.append({'type': c1, 'code': c2})

data_json_str = json.dumps({'products': products, 'boms': boms, 'lineRefs': line_refs}, ensure_ascii=False)

html_content = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>勝一化工 - 產銷計畫表 Web 系統 (月份切換排程與總表第一頁 v7.0)</title>
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

    const INITIAL_DATA = """ + data_json_str + """;

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

      // 🟢 嚴謹4個月連續滾動公式引擎：
      const calculatedProducts = useMemo(() => {
        return filteredProducts.map(p => {
          const init = p.initStock || 0;
          
          // 各月 3 個期間生產總量加總
          const totalAugProd = (p.qtyAug1 || 0) + (p.qtyAug2 || 0) + (p.qtyAug3 || 0);
          const totalSepProd = (p.qtySep1 || 0) + (p.qtySep2 || 0) + (p.qtySep3 || 0);
          const totalOctProd = (p.qtyOct1 || 0) + (p.qtyOct2 || 0) + (p.qtyOct3 || 0);
          const totalNovProd = (p.qtyNov1 || 0) + (p.qtyNov2 || 0) + (p.qtyNov3 || 0);

          // 1. 8/31 結存
          const endAug = init + totalAugProd - (p.salesAug || 0);

          // 2. 9/30 結存 = 8/31結存 + 9月生產 - 9月銷
          const endSep = endAug + totalSepProd - (p.salesSep || 0);

          // 3. 10/31 結存 = 9/30結存 + 10月生產 - 10月銷
          const endOct = endSep + totalOctProd - (p.salesOct || 0);

          // 4. 11/30 結存 = 10/31結存 + 11月生產 - 11月銷
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
        let rows = [["勝一化工 - 產銷計畫表 (4個月連續滾動生產與結存)"]];
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
          
          {/* Header 頂部 */}
          <div className="bg-slate-800 text-white p-3 rounded-xl shadow flex flex-col md:flex-row justify-between items-center gap-3">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">📊</span>
              <div>
                <h1 className="text-base font-bold flex items-center">
                  勝一化工 - 產銷計畫表 Web 系統 
                  <span className="ml-2 text-xs bg-cyan-600 px-2 py-0.5 rounded-full font-bold">總表置頂 + 月份切換排程版 v7.0</span>
                </h1>
                <p className="text-[11px] text-slate-300">總表為第一頁分頁、可自由切換 8/9/10/11月生產排程，連動最右側 4 個月結存</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
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
  </script>
</body>
</html>"""

os.makedirs(os.path.dirname(out_html_path), exist_ok=True)
with open(out_html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Successfully updated index.html with top tab 產銷總表 and Month Switcher v7.0!')
