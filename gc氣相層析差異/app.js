// --- Mock Data Initialization ---
// Standard semiconductor specifications:
// PMA: Purity >= 99.85%, Moisture <= 0.0150% (150 ppm), Acidity <= 0.0200% (200 ppm), Color <= 10 APHA
// PMAC: Purity >= 99.70%, Moisture <= 0.0200% (200 ppm), Acidity <= 0.0250% (250 ppm), Color <= 15 APHA

// Register custom tooltip positioner in Chart.js
if (window.Chart) {
    Chart.Tooltip.positioners.sidePositioner = function(items, eventPosition) {
        const chart = this.chart;
        const chartArea = chart.chartArea;
        if (!chartArea) return { x: 20, y: 20 }; // Fallback

        const tooltipWidth = this.width || 280; // Safe default width
        const gridCenter = chartArea.left + (chartArea.right - chartArea.left) / 2;

        let x = chartArea.left + 15; // Position inside the grid boundary on the left

        // If the cursor is on the left half of the grid width, show the tooltip on the right side
        if (eventPosition.x < gridCenter) {
            x = chartArea.right - tooltipWidth - 15; // Position inside the grid boundary on the right
        } else {
            x = chartArea.left + 15; // Position inside the grid boundary on the left
        }
        
        // Anchor vertical position to the top of the chart grid lines area
        const y = chartArea.top + 15;
        
        return { x, y };
    };
}

let SPECIFICATIONS = {
    PMA: { purity: 99.85, moisture: 0.0150, acidity: 0.0200, color: 10 },
    PMAC: { purity: 99.70, moisture: 0.0200, acidity: 0.0250, color: 15 },
    Other: { purity: 99.50, moisture: 0.0300, acidity: 0.0300, color: 20 }
};

// Original 11 Mock Batches (3 PMA, 6 PMAC, 2 Other/PGME)
const INITIAL_BATCHES = [
    {
        id: "pma-1",
        name: "PMA 6-1-0702-1",
        type: "PMA",
        purity: 99.88,
        moisture: 0.0066,
        acidity: 0.0120,
        color: 5,
        date: "2026-07-02",
        peaks: [
            { no: 1, rt: 3.25, name: "Light Ends / Methanol", area: 250, areaPercent: 0.01 },
            { no: 2, rt: 4.82, name: "Propylene Glycol Methyl Ether (PM)", area: 1250, areaPercent: 0.05 },
            { no: 3, rt: 6.15, name: "Beta-PGMEA (Impurity)", area: 750, areaPercent: 0.03 },
            { no: 4, rt: 7.52, name: "Alpha-PGMEA (Main Product)", area: 2497000, areaPercent: 99.88 },
            { no: 5, rt: 9.80, name: "Heavy Ends / DPMA", area: 750, areaPercent: 0.03 }
        ]
    },
    {
        id: "pma-2",
        name: "PMA 6-1-0702-2",
        type: "PMA",
        purity: 99.91,
        moisture: 0.0054,
        acidity: 0.0112,
        color: 5,
        date: "2026-07-02",
        peaks: [
            { no: 1, rt: 3.25, name: "Light Ends / Methanol", area: 200, areaPercent: 0.008 },
            { no: 2, rt: 4.82, name: "Propylene Glycol Methyl Ether (PM)", area: 1000, areaPercent: 0.040 },
            { no: 3, rt: 6.15, name: "Beta-PGMEA (Impurity)", area: 500, areaPercent: 0.020 },
            { no: 4, rt: 7.52, name: "Alpha-PGMEA (Main Product)", area: 2497750, areaPercent: 99.910 },
            { no: 5, rt: 9.80, name: "Heavy Ends / DPMA", area: 550, areaPercent: 0.022 }
        ]
    },
    {
        id: "pma-3",
        name: "PMA 6-1-0702-3",
        type: "PMA",
        purity: 99.84, // Slightly below specification limit (99.85%)
        moisture: 0.0088,
        acidity: 0.0145,
        color: 6,
        date: "2026-07-02",
        peaks: [
            { no: 1, rt: 3.25, name: "Light Ends / Methanol", area: 300, areaPercent: 0.012 },
            { no: 2, rt: 4.82, name: "Propylene Glycol Methyl Ether (PM)", area: 1650, areaPercent: 0.066 },
            { no: 3, rt: 6.15, name: "Beta-PGMEA (Impurity)", area: 1100, areaPercent: 0.044 },
            { no: 4, rt: 7.52, name: "Alpha-PGMEA (Main Product)", area: 2496000, areaPercent: 99.840 },
            { no: 5, rt: 9.80, name: "Heavy Ends / DPMA", area: 950, areaPercent: 0.038 }
        ]
    },
    {
        id: "pmac-1",
        name: "PMAC 6-2-0801-1",
        type: "PMAC",
        purity: 99.76,
        moisture: 0.0122,
        acidity: 0.0185,
        color: 8,
        date: "2026-08-01",
        peaks: [
            { no: 1, rt: 3.40, name: "Light Ends", area: 450, areaPercent: 0.02 },
            { no: 2, rt: 5.10, name: "Propylene Glycol Methyl Ether (PM)", area: 2680, areaPercent: 0.12 },
            { no: 3, rt: 6.80, name: "PMAC (Main Product)", area: 2235000, areaPercent: 99.76 },
            { no: 4, rt: 8.90, name: "Heavy Ends / Impurity B", area: 2240, areaPercent: 0.10 }
        ]
    },
    {
        id: "pmac-2",
        name: "PMAC 6-2-0801-2",
        type: "PMAC",
        purity: 99.82,
        moisture: 0.0095,
        acidity: 0.0160,
        color: 7,
        date: "2026-08-01",
        peaks: [
            { no: 1, rt: 3.40, name: "Light Ends", area: 330, areaPercent: 0.015 },
            { no: 2, rt: 5.10, name: "Propylene Glycol Methyl Ether (PM)", area: 2010, areaPercent: 0.090 },
            { no: 3, rt: 6.80, name: "PMAC (Main Product)", area: 2236000, areaPercent: 99.820 },
            { no: 4, rt: 8.90, name: "Heavy Ends / Impurity B", area: 1680, areaPercent: 0.075 }
        ]
    },
    {
        id: "pmac-3",
        name: "PMAC 6-2-0801-3",
        type: "PMAC",
        purity: 99.79,
        moisture: 0.0110,
        acidity: 0.0172,
        color: 8,
        date: "2026-08-01",
        peaks: [
            { no: 1, rt: 3.40, name: "Light Ends", area: 380, areaPercent: 0.017 },
            { no: 2, rt: 5.10, name: "Propylene Glycol Methyl Ether (PM)", area: 2350, areaPercent: 0.105 },
            { no: 3, rt: 6.80, name: "PMAC (Main Product)", area: 2235300, areaPercent: 99.790 },
            { no: 4, rt: 8.90, name: "Heavy Ends / Impurity B", area: 1970, areaPercent: 0.088 }
        ]
    },
    {
        id: "pmac-4",
        name: "PMAC 6-2-0802-1",
        type: "PMAC",
        purity: 99.84,
        moisture: 0.0080,
        acidity: 0.0150,
        color: 6,
        date: "2026-08-02",
        peaks: [
            { no: 1, rt: 3.40, name: "Light Ends", area: 280, areaPercent: 0.012 },
            { no: 2, rt: 5.10, name: "Propylene Glycol Methyl Ether (PM)", area: 1790, areaPercent: 0.080 },
            { no: 3, rt: 6.80, name: "PMAC (Main Product)", area: 2236400, areaPercent: 99.840 },
            { no: 4, rt: 8.90, name: "Heavy Ends / Impurity B", area: 1520, areaPercent: 0.068 }
        ]
    },
    {
        id: "pmac-5",
        name: "PMAC 6-2-0802-2",
        type: "PMAC",
        purity: 99.80,
        moisture: 0.0105,
        acidity: 0.0168,
        color: 7,
        date: "2026-08-02",
        peaks: [
            { no: 1, rt: 3.40, name: "Light Ends", area: 350, areaPercent: 0.016 },
            { no: 2, rt: 5.10, name: "Propylene Glycol Methyl Ether (PM)", area: 2240, areaPercent: 0.100 },
            { no: 3, rt: 6.80, name: "PMAC (Main Product)", area: 2235500, areaPercent: 99.800 },
            { no: 4, rt: 8.90, name: "Heavy Ends / Impurity B", area: 1880, areaPercent: 0.084 }
        ]
    },
    {
        id: "pmac-6",
        name: "PMAC 6-2-0802-3",
        type: "PMAC",
        purity: 99.68, // Out of spec (PMAC purity >= 99.70)
        moisture: 0.0210, // Out of spec (PMAC moisture <= 0.0200)
        acidity: 0.0260, // Out of spec (PMAC acidity <= 0.0250)
        color: 16,       // Out of spec (PMAC color <= 15)
        date: "2026-08-02",
        peaks: [
            { no: 1, rt: 3.40, name: "Light Ends", area: 600, areaPercent: 0.027 },
            { no: 2, rt: 5.10, name: "Propylene Glycol Methyl Ether (PM)", area: 4470, areaPercent: 0.200 },
            { no: 3, rt: 6.80, name: "PMAC (Main Product)", area: 2227800, areaPercent: 99.680 },
            { no: 4, rt: 8.90, name: "Heavy Ends / Impurity B", area: 2080, areaPercent: 0.093 }
        ]
    },
    {
        id: "other-1",
        name: "PGME 6-3-0901-1",
        type: "Other",
        purity: 99.72,
        moisture: 0.0180,
        acidity: 0.0195,
        color: 8,
        date: "2026-09-01",
        peaks: [
            { no: 1, rt: 2.80, name: "Methanol", area: 980, areaPercent: 0.04 },
            { no: 2, rt: 4.82, name: "PGME (Main Product)", area: 2443000, areaPercent: 99.72 },
            { no: 3, rt: 8.20, name: "Dipropylene Glycol Methyl Ether isomers", area: 5880, areaPercent: 0.24 }
        ]
    },
    {
        id: "other-2",
        name: "PGME 6-3-0901-2",
        type: "Other",
        purity: 99.78,
        moisture: 0.0140,
        acidity: 0.0150,
        color: 7,
        date: "2026-09-01",
        peaks: [
            { no: 1, rt: 2.80, name: "Methanol", area: 730, areaPercent: 0.03 },
            { no: 2, rt: 4.82, name: "PGME (Main Product)", area: 2444600, areaPercent: 99.78 },
            { no: 3, rt: 8.20, name: "Dipropylene Glycol Methyl Ether isomers", area: 4650, areaPercent: 0.19 }
        ]
    }
];

// Programmatically generate additional mock batches to reach exactly 100 batches (for QA scalability testing)
const generateMockBatches = () => {
    const types = ["PMA", "PMAC", "Other"];
    let currentId = 3;
    let pmaId = 4;
    let pmacId = 7;
    let otherId = 3;

    for (let i = INITIAL_BATCHES.length + 1; i <= 100; i++) {
        const type = types[Math.floor(Math.random() * 3)];
        let name = "";
        let purity = 0;
        let moisture = 0;
        let acidity = 0;
        let color = 0;
        let id = "";

        if (type === "PMA") {
            name = `PMA 6-1-070${pmaId}-${Math.floor(Math.random()*3)+1}`;
            purity = +(99.80 + Math.random() * 0.15).toFixed(2);
            moisture = +(0.0040 + Math.random() * 0.0090).toFixed(4);
            acidity = +(0.0080 + Math.random() * 0.0080).toFixed(4);
            color = Math.floor(Math.random() * 5) + 3;
            id = `pma-${pmaId++}`;
        } else if (type === "PMAC") {
            name = `PMAC 6-2-080${pmacId}-${Math.floor(Math.random()*3)+1}`;
            purity = +(99.68 + Math.random() * 0.18).toFixed(2);
            moisture = +(0.0070 + Math.random() * 0.0120).toFixed(4);
            acidity = +(0.0120 + Math.random() * 0.0100).toFixed(4);
            color = Math.floor(Math.random() * 8) + 5;
            id = `pmac-${pmacId++}`;
        } else {
            name = `PGME 6-3-090${otherId}-${Math.floor(Math.random()*3)+1}`;
            purity = +(99.70 + Math.random() * 0.15).toFixed(2);
            moisture = +(0.0100 + Math.random() * 0.0120).toFixed(4);
            acidity = +(0.0100 + Math.random() * 0.0120).toFixed(4);
            color = Math.floor(Math.random() * 6) + 4;
            id = `other-${otherId++}`;
        }

        const month = Math.floor(Math.random() * 5) + 5; // May - Sept
        const day = Math.floor(Math.random() * 28) + 1;
        const dateStr = `2026-0${month}-${day < 10 ? '0' + day : day}`;

        const rem = +(100.0 - purity).toFixed(4);
        const peaks = [
            { no: 1, rt: 3.0, name: "Light Ends", area: Math.round(rem * 1000 * 0.2), areaPercent: +(rem * 0.2).toFixed(4) },
            { no: 2, rt: 5.0, name: "Propylene Glycol Methyl Ether", area: Math.round(rem * 1000 * 0.5), areaPercent: +(rem * 0.5).toFixed(4) },
            { no: 3, rt: 7.0, name: "Main Solvent", area: Math.round(purity * 1000), areaPercent: purity },
            { no: 4, rt: 9.0, name: "Heavy Ends", area: Math.round(rem * 1000 * 0.3), areaPercent: +(rem * 0.3).toFixed(4) }
        ];

        INITIAL_BATCHES.push({
            id,
            name,
            type,
            purity,
            moisture,
            acidity,
            color,
            date: dateStr,
            peaks
        });
    }
};
generateMockBatches();

// --- App State ---
let batches = JSON.parse(JSON.stringify(INITIAL_BATCHES));
let selectedBatches = new Set(batches.map(b => b.id)); // Default: Select all 100
let dualBatchA = "pma-1";
let dualBatchB = "pma-2";
let activeTab = "multi"; // Default active tab is Multi-batch trend analysis
let currentFilter = "all";
let searchQuery = "";
let currentPage = 1;
const cardsPerPage = 10;
let maxTrendPoints = 30; // Default trend chart limit is 30 points

// Chart instances
let chromatogramChart = null;
let multiChromChart = null;
let trendCharts = {
    purity: null,
    moisture: null,
    acidity: null,
    color: null
};

// --- DOM Elements ---
const searchInput = document.getElementById("search-input");
const batchCardsList = document.getElementById("batch-cards-list");
const selectedCountEl = document.getElementById("selected-count");
const modeNoticeBox = document.getElementById("mode-notice-hint");

// Tab toggles
const tabDualBtn = document.getElementById("tab-dual");
const tabMultiBtn = document.getElementById("tab-multi");
const tabMultiChromBtn = document.getElementById("tab-multi-chrom");
const tabMatrixBtn = document.getElementById("tab-matrix");
const panelDual = document.getElementById("panel-dual");
const panelMulti = document.getElementById("panel-multi");
const panelMultiChrom = document.getElementById("panel-multi-chrom");
const panelMatrix = document.getElementById("panel-matrix");

// Selectors in Dual comparison
const selectBatchA = document.getElementById("select-batch-a");
const selectBatchB = document.getElementById("select-batch-b");

// Modal upload components
const btnUpload = document.getElementById("btn-upload");
const btnExport = document.getElementById("btn-export");
const btnPrint = document.getElementById("btn-print");
const btnReset = document.getElementById("btn-reset");
const uploadModal = document.getElementById("upload-modal");
const btnModalClose = document.getElementById("btn-modal-close");
const btnUploadCancel = document.getElementById("btn-upload-cancel");

// Category manager modal selectors
const categoryModal = document.getElementById("category-modal");
const btnCategoryModalClose = document.getElementById("btn-category-modal-close");
const btnOpenCategoryMgr = document.getElementById("btn-open-category-mgr");
const btnUploadSubmit = document.getElementById("btn-upload-submit");
const uploadForm = document.getElementById("upload-form");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const fileInfoText = document.getElementById("file-info-text");
const pasteTextArea = document.getElementById("paste-text");

// Counters
const countAll = document.getElementById("count-all");
const countPma = document.getElementById("count-pma");
const countPmac = document.getElementById("count-pmac");

// Toast Container
const toastContainer = document.getElementById("toast-container");

// --- Initialization ---
document.addEventListener("DOMContentLoaded", () => {
    initApp();
    setupEventListeners();
});

function initApp() {
    populateCategoryDropdown();
    currentPage = 1;
    updateCounters();
    renderBatchList();
    populateDualSelectors();
    updateActiveTab();
    
    // Initial renders
    if (activeTab === "multi") {
        renderMultiTrends();
    } else if (activeTab === "dual") {
        renderDualComparison();
    } else if (activeTab === "multi-chrom") {
        renderMultiChromatogram();
    } else {
        renderMatrixTab();
    }
}

function setupEventListeners() {
    // Search input
    searchInput.addEventListener("input", (e) => {
        searchQuery = e.target.value.trim().toLowerCase();
        currentPage = 1; // Reset to page 1 on search
        renderBatchList();
        if (activeTab === "multi") renderMultiTrends();
        if (activeTab === "multi-chrom") renderMultiChromatogram();
        if (activeTab === "matrix") renderMatrixTab();
    });

    // Workspace tab toggling
    tabDualBtn.addEventListener("click", () => {
        activeTab = "dual";
        updateActiveTab();
        renderDualComparison();
    });
    
    tabMultiBtn.addEventListener("click", () => {
        activeTab = "multi";
        updateActiveTab();
        renderMultiTrends();
    });

    tabMultiChromBtn.addEventListener("click", () => {
        activeTab = "multi-chrom";
        updateActiveTab();
        renderMultiChromatogram();
    });

    tabMatrixBtn.addEventListener("click", () => {
        activeTab = "matrix";
        updateActiveTab();
        renderMatrixTab();
    });

    // Dual comparison dropdown switches
    selectBatchA.addEventListener("change", (e) => {
        dualBatchA = e.target.value;
        renderDualComparison();
    });

    selectBatchB.addEventListener("change", (e) => {
        dualBatchB = e.target.value;
        renderDualComparison();
    });

    // Header Action buttons
    btnUpload.addEventListener("click", () => {
        uploadModal.classList.add("open");
    });

    btnExport.addEventListener("click", () => {
        exportComparisonCSV();
    });

    btnPrint.addEventListener("click", () => {
        window.print();
    });

    btnReset.addEventListener("click", () => {
        if(confirm("確定要重設數據為預設的 100 批報告嗎？自定義上傳的檔案將會遺失。")) {
            batches = JSON.parse(JSON.stringify(INITIAL_BATCHES));
            selectedBatches = new Set(batches.map(b => b.id));
            dualBatchA = "pma-1";
            dualBatchB = "pma-2";
            showToast("數據已成功重設！", "success");
            initApp();
        }
    });

    // Clear all batches database
    const btnClearDb = document.getElementById("btn-clear-db");
    if (btnClearDb) {
        btnClearDb.addEventListener("click", () => {
            if (confirm("您確定要清空當前所有的樣品報告資料嗎？清空後即可開始上傳您的真實報告。")) {
                batches = [];
                selectedBatches.clear();
                dualBatchA = "";
                dualBatchB = "";
                currentPage = 1;
                
                updateCounters();
                renderBatchList();
                populateDualSelectors();
                
                if (activeTab === "multi") renderMultiTrends();
                if (activeTab === "multi-chrom") renderMultiChromatogram();
                if (activeTab === "matrix") renderMatrixTab();
                if (activeTab === "dual") {
                    const tbody = document.querySelector("#peak-compare-table tbody");
                    if (tbody) tbody.innerHTML = "<tr><td colspan='8' style='text-align:center; padding:20px; color:var(--text-muted);'>請上傳報表並選擇對比批號</td></tr>";
                }
                
                showToast("已清空所有批號資料，您可以開始上傳真實數據！", "success");
            }
        });
    }

    // Category Manager Modal Open/Close
    if (btnOpenCategoryMgr) {
        btnOpenCategoryMgr.addEventListener("click", () => {
            categoryModal.classList.add("open");
            renderCategoryManagerTable();
        });
    }

    if (btnCategoryModalClose) {
        btnCategoryModalClose.addEventListener("click", () => {
            categoryModal.classList.remove("open");
            clearCategoryManagerForm();
        });
    }

    // Modal forms inputs inside Category Manager
    const btnMgrClear = document.getElementById("btn-mgr-clear");
    const btnMgrSave = document.getElementById("btn-mgr-save");

    if (btnMgrClear) {
        btnMgrClear.addEventListener("click", clearCategoryManagerForm);
    }

    if (btnMgrSave) {
        btnMgrSave.addEventListener("click", saveCategoryManagerForm);
    }

    // Modal Close
    const closeModal = () => {
        uploadModal.classList.remove("open");
        uploadForm.reset();
        fileInfoText.textContent = "";
    };
    btnModalClose.addEventListener("click", closeModal);
    btnUploadCancel.addEventListener("click", (e) => {
        e.preventDefault();
        closeModal();
    });

    // File Drag and Drop logic
    dropzone.addEventListener("click", () => fileInput.click());
    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--primary)";
        dropzone.style.backgroundColor = "rgba(217, 119, 6, 0.05)";
    });
    dropzone.addEventListener("dragleave", () => {
        dropzone.style.borderColor = "var(--border-color)";
        dropzone.style.backgroundColor = "#f8fafc";
    });
    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--border-color)";
        dropzone.style.backgroundColor = "#f8fafc";
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });
    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Modal Form Submission
    btnUploadSubmit.addEventListener("click", (e) => {
        e.preventDefault();
        handleReportImport();
    });

    // Inline Category box events
    const btnAddCategory = document.getElementById("btn-add-category");
    const btnCancelCategory = document.getElementById("btn-cancel-new-category");
    const btnSaveCategory = document.getElementById("btn-save-category");
    const inlineCategoryBox = document.getElementById("inline-category-box");

    btnAddCategory.addEventListener("click", () => {
        inlineCategoryBox.style.display = "flex";
    });

    btnCancelCategory.addEventListener("click", () => {
        inlineCategoryBox.style.display = "none";
        clearInlineCategoryForm();
    });

    btnSaveCategory.addEventListener("click", () => {
        saveCustomCategory();
    });

    // Real-time metadata parser on text paste/input
    pasteTextArea.addEventListener("input", () => {
        const text = pasteTextArea.value;
        if (text) {
            parseReportMetadata(text);
        }
    });

    // Context-aware Bulk Select / Deselect
    document.getElementById("btn-select-all-filtered").addEventListener("click", () => {
        const filtered = getFilteredBatches();
        if (filtered.length === 0) {
            showToast("目前沒有符合篩選條件的樣品！", "error");
            return;
        }
        filtered.forEach(b => selectedBatches.add(b.id));
        showToast(`已全選 ${filtered.length} 筆篩選結果`, "success");
        updateCounters();
        renderBatchList();
        if (activeTab === "multi") renderMultiTrends();
        if (activeTab === "multi-chrom") renderMultiChromatogram();
        if (activeTab === "matrix") renderMatrixTab();
    });

    document.getElementById("btn-deselect-all-filtered").addEventListener("click", () => {
        const filtered = getFilteredBatches();
        if (filtered.length === 0) return;
        filtered.forEach(b => selectedBatches.delete(b.id));
        if (selectedBatches.size === 0 && batches.length > 0) {
            // Keep at least one selected fallback
            selectedBatches.add(batches[0].id);
        }
        showToast(`已取消勾選 ${filtered.length} 筆篩選結果`, "success");
        updateCounters();
        renderBatchList();
        if (activeTab === "multi") renderMultiTrends();
        if (activeTab === "multi-chrom") renderMultiChromatogram();
        if (activeTab === "matrix") renderMatrixTab();
    });

    // Chart Density Limit change
    document.getElementById("select-trend-density").addEventListener("change", (e) => {
        const val = e.target.value;
        maxTrendPoints = val === "all" ? Infinity : parseInt(val);
        renderMultiTrends();
        showToast(`圖表顯示限制已設為最近 ${val === 'all' ? '全部' : val} 筆`, "success");
    });
}

// --- File Import / Parsing Logics ---
function handleFileSelect(file) {
    fileInfoText.textContent = `已選取檔案: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    const reader = new FileReader();
    reader.onload = function(e) {
        pasteTextArea.value = e.target.result;
        // Prefill batch name based on filename (strip extension)
        const nameWithoutExt = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
        document.getElementById("input-batch-name").value = nameWithoutExt;
    };
    reader.readAsText(file);
}

function handleReportImport() {
    const name = document.getElementById("input-batch-name").value.trim();
    const type = document.getElementById("input-batch-type").value;
    const purityVal = parseFloat(document.getElementById("input-purity").value);
    const moistureVal = parseFloat(document.getElementById("input-moisture").value) || 0.0;
    const acidityVal = parseFloat(document.getElementById("input-acidity").value) || 0.0;
    const colorVal = parseInt(document.getElementById("input-color").value) || 0;
    const textContent = pasteTextArea.value.trim();

    if (!name) {
        showToast("請輸入批號名稱！", "error");
        return;
    }

    let parsedPeaks = [];
    
    // Parse GC table if text is pasted
    if (textContent) {
        parsedPeaks = parseGCText(textContent);
    }

    // Fallback or override purity if manual value is provided
    let finalPurity = purityVal;
    if (isNaN(finalPurity)) {
        // Find main peak from parsed table (peak with largest Area%)
        if (parsedPeaks.length > 0) {
            const mainPeak = parsedPeaks.reduce((prev, current) => (prev.areaPercent > current.areaPercent) ? prev : current);
            finalPurity = mainPeak.areaPercent;
            showToast(`已從 GC 報表中自動偵測主峰純度為 ${finalPurity}%`, "success");
        } else {
            showToast("請輸入純度百分比或貼上有效的 GC 報表內容！", "error");
            return;
        }
    }

    // If we have no parsed peaks, generate mock peaks based on the purity
    if (parsedPeaks.length === 0) {
        if (type === "PMA") {
            const rem = +(100.0 - finalPurity).toFixed(4);
            parsedPeaks = [
                { no: 1, rt: 3.25, name: "Light Ends / Methanol", area: Math.round(rem * 10000 * 0.1), areaPercent: +(rem * 0.1).toFixed(4) },
                { no: 2, rt: 4.82, name: "Propylene Glycol Methyl Ether (PM)", area: Math.round(rem * 10000 * 0.4), areaPercent: +(rem * 0.4).toFixed(4) },
                { no: 3, rt: 6.15, name: "Beta-PGMEA (Impurity)", area: Math.round(rem * 10000 * 0.25), areaPercent: +(rem * 0.25).toFixed(4) },
                { no: 4, rt: 7.52, name: "Alpha-PGMEA (Main Product)", area: Math.round(finalPurity * 10000), areaPercent: finalPurity },
                { no: 5, rt: 9.80, name: "Heavy Ends / DPMA", area: Math.round(rem * 10000 * 0.25), areaPercent: +(rem * 0.25).toFixed(4) }
            ];
        } else {
            // General or PMAC
            const rem = +(100.0 - finalPurity).toFixed(4);
            parsedPeaks = [
                { no: 1, rt: 3.40, name: "Light Ends", area: Math.round(rem * 10000 * 0.15), areaPercent: +(rem * 0.15).toFixed(4) },
                { no: 2, rt: 5.10, name: "Propylene Glycol Methyl Ether (PM)", area: Math.round(rem * 10000 * 0.45), areaPercent: +(rem * 0.45).toFixed(4) },
                { no: 3, rt: 6.80, name: "Main Product Component", area: Math.round(finalPurity * 10000), areaPercent: finalPurity },
                { no: 4, rt: 8.90, name: "Heavy Ends / Impurities", area: Math.round(rem * 10000 * 0.4), areaPercent: +(rem * 0.4).toFixed(4) }
            ];
        }
    }

    const newBatch = {
        id: "custom-" + Date.now(),
        name: name,
        type: type,
        purity: finalPurity,
        moisture: moistureVal,
        acidity: acidityVal,
        color: colorVal,
        date: new Date().toISOString().split('T')[0],
        peaks: parsedPeaks
    };

    // Add to state
    batches.unshift(newBatch);
    selectedBatches.add(newBatch.id); // Automatically select it
    
    // Success flow
    showToast(`批號 ${name} 匯入成功！`, "success");
    
    // Close modal, reset form
    uploadModal.classList.remove("open");
    uploadForm.reset();
    fileInfoText.textContent = "";

    // Refresh UI
    initApp();
}

// Simple text parser for GC tables
function parseGCText(text) {
    const lines = text.split("\n");
    const peaks = [];
    let isHeaderFound = false;
    let rtColIdx = -1;
    let areaPctColIdx = -1;
    let nameColIdx = -1;
    let areaColIdx = -1;
    let peakNoColIdx = -1;

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        // Split by tabs or multiple spaces
        const tokens = line.split(/\s{2,}|\t/);

        if (!isHeaderFound) {
            // Looking for headers like "RT", "Area%", "Peak#"
            const lowercaseTokens = tokens.map(t => t.toLowerCase());
            rtColIdx = lowercaseTokens.findIndex(t => t.includes("rt") || t.includes("ret") || t.includes("保留時間"));
            areaPctColIdx = lowercaseTokens.findIndex(t => t.includes("area%") || t.includes("area %") || t.includes("百分比") || t.includes("面積%"));
            areaColIdx = lowercaseTokens.findIndex(t => t.includes("area") && !t.includes("%") && !t.includes("pct"));
            nameColIdx = lowercaseTokens.findIndex(t => t.includes("name") || t.includes("comp") || t.includes("名稱"));
            peakNoColIdx = lowercaseTokens.findIndex(t => t.includes("peak") || t.includes("no") || t.includes("峰"));

            if (rtColIdx !== -1 && areaPctColIdx !== -1) {
                isHeaderFound = true;
            }
            continue;
        }

        // Parse peak data lines
        if (tokens.length >= 2) {
            const rtVal = parseFloat(tokens[rtColIdx]);
            const pctVal = parseFloat(tokens[areaPctColIdx].replace("%", ""));
            const areaVal = areaColIdx !== -1 ? parseInt(tokens[areaColIdx].replace(/,/g, "")) : 1000;
            const nameVal = nameColIdx !== -1 && tokens[nameColIdx] ? tokens[nameColIdx] : `Peak @ ${rtVal} min`;
            const noVal = peakNoColIdx !== -1 ? parseInt(tokens[peakNoColIdx]) : peaks.length + 1;

            if (!isNaN(rtVal) && !isNaN(pctVal)) {
                peaks.push({
                    no: noVal,
                    rt: rtVal,
                    name: nameVal,
                    area: isNaN(areaVal) ? 1000 : areaVal,
                    areaPercent: pctVal
                });
            }
        }
    }
    
    // Sort peaks by RT
    peaks.sort((a,b) => a.rt - b.rt);
    return peaks;
}

// --- Render Layout Functions ---

function updateCounters() {
    // Dynamic Filter Tabs Rendering
    const container = document.getElementById("dynamic-filter-tabs");
    if (container) {
        container.innerHTML = "";
        
        // Find all unique categories present in specifications
        const allCategories = Object.keys(SPECIFICATIONS);
        
        // Render: 全部, PMA, PMAC, then other custom ones.
        const order = ["all", "PMA", "PMAC"];
        allCategories.forEach(cat => {
            if (cat !== "PMA" && cat !== "PMAC" && cat !== "Other") {
                order.push(cat);
            }
        });
        if (allCategories.includes("Other")) {
            order.push("Other");
        }

        order.forEach(cat => {
            const btn = document.createElement("button");
            btn.className = `filter-tab ${currentFilter === cat ? 'active' : ''}`;
            btn.setAttribute("data-filter", cat);

            let count = 0;
            let displayLabel = "";

            if (cat === "all") {
                count = batches.length;
                displayLabel = "全部";
            } else {
                count = batches.filter(b => b.type === cat).length;
                displayLabel = cat;
            }

            btn.innerHTML = `${displayLabel} (<span id="count-${cat.toLowerCase()}">${count}</span>)`;
            btn.addEventListener("click", () => {
                document.querySelectorAll(".filter-tab").forEach(t => t.classList.remove("active"));
                btn.classList.add("active");
                currentFilter = cat;
                currentPage = 1; // Reset to page 1 when switching tabs
                renderBatchList();
                if (activeTab === "multi") renderMultiTrends();
                if (activeTab === "multi-chrom") renderMultiChromatogram();
                if (activeTab === "matrix") renderMatrixTab();
            });

            container.appendChild(btn);
        });
    }
    selectedCountEl.textContent = selectedBatches.size;
}

// Toggle batch active tab and panel view
function updateActiveTab() {
    if (activeTab === "multi") {
        tabMultiBtn.classList.add("active");
        tabDualBtn.classList.remove("active");
        tabMultiChromBtn.classList.remove("active");
        tabMatrixBtn.classList.remove("active");
        panelMulti.classList.remove("hidden");
        panelDual.classList.add("hidden");
        panelMultiChrom.classList.add("hidden");
        panelMatrix.classList.add("hidden");
        if (modeNoticeBox) modeNoticeBox.classList.remove("hidden");
    } else if (activeTab === "dual") {
        tabDualBtn.classList.add("active");
        tabMultiBtn.classList.remove("active");
        tabMultiChromBtn.classList.remove("active");
        tabMatrixBtn.classList.remove("active");
        panelDual.classList.remove("hidden");
        panelMulti.classList.add("hidden");
        panelMultiChrom.classList.add("hidden");
        panelMatrix.classList.add("hidden");
        if (modeNoticeBox) modeNoticeBox.classList.add("hidden");
    } else if (activeTab === "multi-chrom") {
        tabMultiChromBtn.classList.add("active");
        tabMultiBtn.classList.remove("active");
        tabDualBtn.classList.remove("active");
        tabMatrixBtn.classList.remove("active");
        panelMultiChrom.classList.remove("hidden");
        panelMulti.classList.add("hidden");
        panelDual.classList.add("hidden");
        panelMatrix.classList.add("hidden");
        if (modeNoticeBox) modeNoticeBox.classList.remove("hidden");
    } else if (activeTab === "matrix") {
        tabMatrixBtn.classList.add("active");
        tabMultiBtn.classList.remove("active");
        tabDualBtn.classList.remove("active");
        tabMultiChromBtn.classList.remove("active");
        panelMatrix.classList.remove("hidden");
        panelMulti.classList.add("hidden");
        panelDual.classList.add("hidden");
        panelMultiChrom.classList.add("hidden");
        if (modeNoticeBox) modeNoticeBox.classList.remove("hidden");
    }
}

// Renders the list of batch cards in sidebar
function renderBatchList() {
    batchCardsList.innerHTML = "";

    const filtered = getFilteredBatches();

    if (filtered.length === 0) {
        batchCardsList.innerHTML = `<div style="text-align:center; padding: 40px 0; color: var(--text-muted); font-size:14px;">找不到相符的批號</div>`;
        const paginationControls = document.getElementById("sidebar-pagination-controls");
        if (paginationControls) paginationControls.style.display = "none";
        return;
    }

    // Pagination bounds check
    const totalPages = Math.ceil(filtered.length / cardsPerPage);
    if (currentPage > totalPages) currentPage = Math.max(1, totalPages);

    const startIdx = (currentPage - 1) * cardsPerPage;
    const endIdx = startIdx + cardsPerPage;
    const pageBatches = filtered.slice(startIdx, endIdx);

    pageBatches.forEach(batch => {
        const isSelected = selectedBatches.has(batch.id);
        const card = document.createElement("div");
        card.className = `batch-card ${isSelected ? "selected" : ""}`;
        card.setAttribute("data-id", batch.id);

        card.innerHTML = `
            <div class="batch-card-header" style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                <div class="card-title-group" style="display:flex; align-items:center; gap:8px;">
                    <span class="batch-type-badge ${batch.type}">${batch.type}</span>
                    <span class="batch-card-title" style="font-weight:600; font-size:13.5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:180px;">${batch.name}</span>
                </div>
                <div class="batch-date" style="font-size:11px; color: var(--text-muted);">${batch.date}</div>
            </div>
            <button class="btn-toggle-compare" style="margin-top: 6px;">
                <i class="fa-solid ${isSelected ? 'fa-check' : 'fa-plus'}"></i>
                <span>${isSelected ? '已加入比較' : '加入比較'}</span>
            </button>
        `;

        // Card body click (set as Dual Batch A or B)
        card.addEventListener("click", (e) => {
            if (e.target.closest(".btn-toggle-compare")) {
                e.stopPropagation();
                toggleBatchSelection(batch.id);
                return;
            }
            showDualSelectionMenu(batch.id, e);
        });

        batchCardsList.appendChild(card);
    });

    // Render page controls
    renderSidebarPagination(filtered.length);
}

function toggleBatchSelection(batchId) {
    if (selectedBatches.has(batchId)) {
        if (selectedBatches.size <= 1) {
            showToast("必須至少選擇 1 個批號以進行趨勢分析！", "error");
            return;
        }
        selectedBatches.delete(batchId);
        showToast("已從趨勢分析中移除", "success");
    } else {
        selectedBatches.add(batchId);
        showToast("已加入趨勢分析中", "success");
    }
    
    updateCounters();
    renderBatchList();
    if (activeTab === "multi") {
        renderMultiTrends();
    }
    if (activeTab === "multi-chrom") {
        renderMultiChromatogram();
    }
    if (activeTab === "matrix") {
        renderMatrixTab();
    }
}

// Menu when clicking a card: Set as A or B in dual comparison
function showDualSelectionMenu(batchId, event) {
    const existingMenu = document.getElementById("dual-context-menu");
    if (existingMenu) existingMenu.remove();

    const menu = document.createElement("div");
    menu.id = "dual-context-menu";
    menu.style.position = "fixed";
    menu.style.left = `${event.clientX}px`;
    menu.style.top = `${event.clientY}px`;
    menu.style.backgroundColor = "#ffffff";
    menu.style.border = "1px solid var(--border-color)";
    menu.style.borderRadius = "var(--radius-md)";
    menu.style.boxShadow = "var(--shadow-lg)";
    menu.style.zIndex = "1000";
    menu.style.padding = "6px 0";

    const optA = document.createElement("div");
    optA.className = "context-menu-item";
    optA.innerHTML = `<i class="fa-solid fa-arrow-right-to-bracket" style="color: #3b82f6;"></i> 設為基準批號 (A)`;
    optA.addEventListener("click", () => {
        dualBatchA = batchId;
        selectBatchA.value = batchId;
        activeTab = "dual";
        updateActiveTab();
        renderDualComparison();
        menu.remove();
        showToast("已將批號設為基準 A", "success");
    });

    const optB = document.createElement("div");
    optB.className = "context-menu-item";
    optB.innerHTML = `<i class="fa-solid fa-arrow-right-to-bracket" style="color: #10b981;"></i> 設為比對批號 (B)`;
    optB.addEventListener("click", () => {
        dualBatchB = batchId;
        selectBatchB.value = batchId;
        activeTab = "dual";
        updateActiveTab();
        renderDualComparison();
        menu.remove();
        showToast("已將批號設為比對 B", "success");
    });

    menu.appendChild(optA);
    menu.appendChild(optB);
    document.body.appendChild(menu);

    // Style context menu items
    const items = menu.querySelectorAll(".context-menu-item");
    items.forEach(item => {
        item.style.padding = "10px 16px";
        item.style.fontSize = "13px";
        item.style.cursor = "pointer";
        item.style.display = "flex";
        item.style.alignItems = "center";
        item.style.gap = "10px";
        item.style.transition = "background 0.2s";
        item.addEventListener("mouseenter", () => item.style.backgroundColor = "#f1f5f9");
        item.addEventListener("mouseleave", () => item.style.backgroundColor = "transparent");
    });

    // Close when clicking elsewhere
    const closeMenu = (e) => {
        if (!menu.contains(e.target)) {
            menu.remove();
            document.removeEventListener("click", closeMenu);
        }
    };
    // Delay adding listener to prevent instant close
    setTimeout(() => document.addEventListener("click", closeMenu), 10);
}

// Populate dropdown selectors in dual comparison page
function populateDualSelectors() {
    selectBatchA.innerHTML = "";
    selectBatchB.innerHTML = "";

    batches.forEach(batch => {
        const optionA = document.createElement("option");
        optionA.value = batch.id;
        optionA.textContent = batch.name;
        if (batch.id === dualBatchA) optionA.selected = true;

        const optionB = document.createElement("option");
        optionB.value = batch.id;
        optionB.textContent = batch.name;
        if (batch.id === dualBatchB) optionB.selected = true;

        selectBatchA.appendChild(optionA);
        selectBatchB.appendChild(optionB);
    });
}

// Evaluate values against specifications, returns CSS class: "pass", "fail", or "warn"
function evaluateSpec(batch, metric, val) {
    const spec = SPECIFICATIONS[batch.type] || SPECIFICATIONS.Other;
    if (metric === "purity") {
        return val >= spec.purity ? "pass" : "fail";
    }
    if (metric === "moisture") {
        return val <= spec.moisture ? "pass" : "fail";
    }
    if (metric === "acidity") {
        return val <= spec.acidity ? "pass" : "fail";
    }
    if (metric === "color") {
        return val <= spec.color ? "pass" : "fail";
    }
    return "";
}

// --- DUAL BATCH COMPARISON TAB RENDERS ---

function renderDualComparison() {
    const batchA = batches.find(b => b.id === dualBatchA);
    const batchB = batches.find(b => b.id === dualBatchB);

    if (!batchA || !batchB) return;

    // Update spec label dynamically
    const specA = SPECIFICATIONS[batchA.type] || SPECIFICATIONS.Other;
    const specB = SPECIFICATIONS[batchB.type] || SPECIFICATIONS.Other;
    const labelEl = document.querySelector(".spec-label");
    if (labelEl) {
        if (batchA.type === batchB.type) {
            labelEl.textContent = `${batchB.type} 級規範: Purity ≥ ${specB.purity.toFixed(2)}% | Moisture ≤ ${specB.moisture.toFixed(4)}% | Acidity ≤ ${specB.acidity.toFixed(4)}% | Color ≤ ${specB.color}`;
        } else {
            labelEl.textContent = `A (${batchA.type}) 規範: Purity ≥ ${specA.purity.toFixed(2)}% | B (${batchB.type}) 規範: Purity ≥ ${specB.purity.toFixed(2)}%`;
        }
    }

    // 1. Render KPIs
    updateKPI("purity", batchA.purity, batchB.purity, true);
    updateKPI("moisture", batchA.moisture, batchB.moisture, false, 4);
    updateKPI("acidity", batchA.acidity, batchB.acidity, false, 4);
    updateKPI("color", batchA.color, batchB.color, false, 0);

    // 2. Render Peak Table comparison
    const tableBody = document.querySelector("#peak-compare-table tbody");
    tableBody.innerHTML = "";

    // Match peaks by Retention Time (RT)
    // We group all peaks and compare their area percents
    const allPeakRTs = Array.from(new Set([...batchA.peaks.map(p => p.rt), ...batchB.peaks.map(p => p.rt)])).sort((a,b) => a - b);

    allPeakRTs.forEach((rt, idx) => {
        const peakA = batchA.peaks.find(p => p.rt === rt);
        const peakB = batchB.peaks.find(p => p.rt === rt);

        const valA = peakA ? peakA.areaPercent : 0.0;
        const valB = peakB ? peakB.areaPercent : 0.0;
        const absDiff = +(valB - valA).toFixed(4);
        
        let relChangeStr = "-";
        if (valA > 0) {
            const relChange = ((valB - valA) / valA) * 100;
            relChangeStr = (relChange >= 0 ? "+" : "") + relChange.toFixed(2) + "%";
        }

        const name = (peakA ? peakA.name : "") || (peakB ? peakB.name : "未知成分");
        
        // Evaluate GC peaks: Main product vs impurities
        let evalHtml = '<span class="eval-badge pass">正常</span>';
        if (name.includes("Main") || name.includes("Alpha-") || name.includes("PGME")) {
            // Main product peak
            const spec = SPECIFICATIONS[batchB.type] || SPECIFICATIONS.Other;
            if (valB < spec.purity) {
                evalHtml = '<span class="eval-badge fail">低於規格</span>';
            }
        } else {
            // Impurity peak
            if (valB > valA * 1.5 && valB > 0.05) {
                evalHtml = '<span class="eval-badge warn">增長顯著</span>';
            }
        }

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td class="monospaced">${rt.toFixed(2)}</td>
            <td>${name}</td>
            <td class="monospaced">${valA.toFixed(3)}%</td>
            <td class="monospaced">${valB.toFixed(3)}%</td>
            <td class="monospaced ${absDiff > 0 ? 'text-danger' : absDiff < 0 ? 'text-success' : ''}" style="color: ${absDiff > 0 ? 'var(--danger)' : absDiff < 0 ? 'var(--success)' : 'inherit'}">
                ${absDiff > 0 ? '+' : ''}${absDiff.toFixed(3)}%
            </td>
            <td class="monospaced" style="color: ${absDiff > 0 ? 'var(--danger)' : absDiff < 0 ? 'var(--success)' : 'inherit'}">
                ${relChangeStr}
            </td>
            <td>${evalHtml}</td>
        `;
        tableBody.appendChild(tr);
    });

    // 3. Render Simulated Overlay Chromatogram Chart
    renderChromatogramChart(batchA, batchB);
}

function updateKPI(metric, valA, valB, isPurity, decimalPlaces = 2) {
    const aEl = document.getElementById(`dual-${metric}-a`);
    const bEl = document.getElementById(`dual-${metric}-b`);
    const diffEl = document.getElementById(`dual-${metric}-diff`);

    aEl.textContent = valA.toFixed(decimalPlaces);
    bEl.textContent = valB.toFixed(decimalPlaces);

    const diff = valB - valA;
    const diffStr = (diff >= 0 ? "+" : "") + diff.toFixed(decimalPlaces);

    if (isPurity) {
        // Higher purity is better
        if (diff > 0) {
            diffEl.innerHTML = `<i class="fa-solid fa-circle-arrow-up"></i> ${diffStr}% (提升)`;
            diffEl.className = "kpi-diff green";
        } else if (diff < 0) {
            diffEl.innerHTML = `<i class="fa-solid fa-circle-arrow-down"></i> ${diffStr}% (下降)`;
            diffEl.className = "kpi-diff red";
        } else {
            diffEl.textContent = "無變動";
            diffEl.className = "kpi-diff gray";
        }
    } else {
        // Lower moisture/acidity/color is better
        if (diff < 0) {
            diffEl.innerHTML = `<i class="fa-solid fa-circle-arrow-down"></i> ${diffStr}${metric === 'color' ? '' : '%'} (改善)`;
            diffEl.className = "kpi-diff green";
        } else if (diff > 0) {
            diffEl.innerHTML = `<i class="fa-solid fa-circle-arrow-up"></i> ${diffStr}${metric === 'color' ? '' : '%'} (劣化)`;
            diffEl.className = "kpi-diff red";
        } else {
            diffEl.textContent = "無變動";
            diffEl.className = "kpi-diff gray";
        }
    }
}

// Generate continuous simulated Gaussian chromatography curves
function generateGaussianCurve(peaks, xPoints) {
    const sigma = 0.08; // width of peaks
    const yPoints = [];

    for (let i = 0; i < xPoints.length; i++) {
        const x = xPoints[i];
        let y = 0.01; // baseline noise baseline

        peaks.forEach(peak => {
            // f(x) = AreaPercent * e^(-(x - RT)^2 / (2 * sigma^2))
            // We scale amplitude to make it fit visually
            const height = peak.areaPercent * 5; // scaling factor
            y += height * Math.exp(-Math.pow(x - peak.rt, 2) / (2 * Math.pow(sigma, 2)));
        });

        // Add minor baseline noise fluctuation
        y += Math.sin(x * 30) * 0.005;

        yPoints.push(y);
    }
    return yPoints;
}

function renderChromatogramChart(batchA, batchB) {
    // Generate RT sampling points from 2.0 to 11.0
    const xPoints = [];
    for (let rt = 2.0; rt <= 11.0; rt += 0.04) {
        xPoints.push(+rt.toFixed(2));
    }

    const yPointsA = generateGaussianCurve(batchA.peaks, xPoints);
    const yPointsB = generateGaussianCurve(batchB.peaks, xPoints);

    if (chromatogramChart) {
        chromatogramChart.destroy();
    }

    const ctx = document.getElementById("chromatogram-chart").getContext("2d");
    chromatogramChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: xPoints,
            datasets: [
                {
                    label: batchA.name,
                    data: yPointsA,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.05)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.4
                },
                {
                    label: batchB.name,
                    data: yPointsB,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.05)',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: true,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                tooltip: {
                    position: 'sidePositioner',
                    caretSize: 0,
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toFixed(2) + ' mV';
                        }
                    }
                },
                legend: {
                    display: false // We use our own customized legend in HTML
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: '保留時間 Retention Time (min)',
                        color: 'var(--text-muted)'
                    },
                    grid: {
                        color: '#f1f5f9'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: '訊號強度 Signal Intensity (mV)',
                        color: 'var(--text-muted)'
                    },
                    grid: {
                        color: '#f1f5f9'
                    },
                    suggestedMax: 20
                }
            }
        }
    });
}

// --- MULTI-BATCH TREND TAB RENDERS ---

function renderMultiTrends() {
    // Filter batches to only selected ones of the current category (or all if current filter is 'all')
    let selectedList = batches.filter(b => {
        const matchCategory = (currentFilter === "all" || b.type === currentFilter);
        return selectedBatches.has(b.id) && matchCategory;
    }).reverse(); // Reverse to keep chronological order (newest right)

    if (selectedList.length === 0) {
        // Destroy existing charts if no data to display
        Object.keys(trendCharts).forEach(key => {
            if (trendCharts[key]) {
                trendCharts[key].destroy();
                trendCharts[key] = null;
            }
        });
        const table = document.getElementById("multi-matrix-table");
        if (table) table.innerHTML = "<tbody><tr><td style='text-align:center; padding:20px; color:var(--text-muted);'>請在左側選取批號加入比較</td></tr></tbody>";
        return;
    }

    // Limit trend chart data density based on filter (e.g. show only recent N selected batches)
    if (selectedList.length > maxTrendPoints) {
        selectedList = selectedList.slice(-maxTrendPoints);
    }

    // Determine specifications dynamically
    const activeSpecType = (currentFilter !== "all") ? currentFilter : selectedList[0].type;
    const activeSpec = SPECIFICATIONS[activeSpecType] || SPECIFICATIONS.Other;

    const labels = selectedList.map(b => b.name);
    
    // Extracted values
    const purities = selectedList.map(b => b.purity);
    const moistures = selectedList.map(b => b.moisture);
    const acidities = selectedList.map(b => b.acidity);
    const colors = selectedList.map(b => b.color);

    // Destroy existing charts to redraw
    Object.keys(trendCharts).forEach(key => {
        if (trendCharts[key]) {
            trendCharts[key].destroy();
        }
    });

    // Update spec labels dynamically on chart cards
    document.querySelector('#chart-trend-purity').closest('.trend-card').querySelector('.spec-text').textContent = `規格值: ≥ ${activeSpec.purity.toFixed(2)}%`;
    document.querySelector('#chart-trend-moisture').closest('.trend-card').querySelector('.spec-text').textContent = `規格值: ≤ ${activeSpec.moisture.toFixed(4)}%`;
    document.querySelector('#chart-trend-acidity').closest('.trend-card').querySelector('.spec-text').textContent = `規格值: ≤ ${activeSpec.acidity.toFixed(4)}%`;
    document.querySelector('#chart-trend-color').closest('.trend-card').querySelector('.spec-text').textContent = `規格值: ≤ ${activeSpec.color}`;

    // 1. Purity Trend
    trendCharts.purity = createTrendChart(
        'chart-trend-purity', 
        labels, 
        purities, 
        '純度 (%)', 
        '#d97706', 
        activeSpec.purity, 
        'min',
        '#fef3c7'
    );

    // 2. Moisture Trend
    trendCharts.moisture = createTrendChart(
        'chart-trend-moisture', 
        labels, 
        moistures, 
        '水份 (%)', 
        '#2563eb', 
        activeSpec.moisture, 
        'max',
        '#dbeafe'
    );

    // 3. Acidity Trend
    trendCharts.acidity = createTrendChart(
        'chart-trend-acidity', 
        labels, 
        acidities, 
        '酸度 (%)', 
        '#dc2626', 
        activeSpec.acidity, 
        'max',
        '#fee2e2'
    );

    // 4. Color Trend
    trendCharts.color = createTrendChart(
        'chart-trend-color', 
        labels, 
        colors, 
        '色度 (APHA)', 
        '#475569', 
        activeSpec.color, 
        'max',
        '#f1f5f9'
    );

}

function createTrendChart(canvasId, labels, data, datasetLabel, color, specValue, specDirection = 'max', fillColor = 'rgba(0,0,0,0.05)') {
    const ctx = document.getElementById(canvasId).getContext("2d");
    
    // Generate spec limit annotations/dataset
    const specDataset = {
        label: '規格界限',
        data: Array(labels.length).fill(specValue),
        borderColor: '#ef4444',
        borderWidth: 1.5,
        borderDash: [5, 5],
        pointRadius: 0,
        fill: false
    };

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: datasetLabel,
                    data: data,
                    borderColor: color,
                    backgroundColor: fillColor,
                    borderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.2,
                    fill: false
                },
                specDataset
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        font: { size: 10 }
                    }
                },
                y: {
                    grid: { color: '#f1f5f9' },
                    ticks: {
                        font: { size: 10 }
                    }
                }
            }
        }
    });
}

function renderComparisonMatrixTable(selectedList) {
    const table = document.getElementById("matrix-tab-table");
    if (!table) return;
    table.innerHTML = "";

    if (selectedList.length === 0) {
        table.innerHTML = "<tbody><tr><td style='text-align:center; padding:20px; color:var(--text-muted);'>請在左側選取批號以進行數據對照</td></tr></tbody>";
        return;
    }

    // Transposed: parameters as columns, batches as rows
    let html = `
        <thead>
            <tr>
                <th>批號名稱</th>
                <th style="text-align:center; width: 100px;">樣品類別</th>
                <th style="text-align:center; width: 110px;">分析日期</th>
                <th style="text-align:right;">純度 Purity (Area%)</th>
                <th style="text-align:right;">水份 Moisture (%)</th>
                <th style="text-align:right;">酸度 Acidity (%)</th>
                <th style="text-align:right;">色度 Color (APHA)</th>
                <th style="text-align:right;">主要雜質 PM (Area%)</th>
                <th style="text-align:right;">Beta-isomer (Area%)</th>
            </tr>
        </thead>
        <tbody>
    `;

    selectedList.forEach(batch => {
        const evalPurity = evaluateSpec(batch, 'purity', batch.purity) === 'pass' ? 'pass' : 'fail';
        const evalMoisture = evaluateSpec(batch, 'moisture', batch.moisture) === 'pass' ? 'pass' : 'fail';
        const evalAcidity = evaluateSpec(batch, 'acidity', batch.acidity) === 'pass' ? 'pass' : 'fail';
        const evalColor = evaluateSpec(batch, 'color', batch.color) === 'pass' ? 'pass' : 'fail';

        const pmPeak = batch.peaks.find(p => p.name.includes("PM"));
        const pmVal = pmPeak ? pmPeak.areaPercent : 0.0;

        const betaPeak = batch.peaks.find(p => p.name.includes("Beta"));
        const betaVal = betaPeak ? betaPeak.areaPercent : 0.0;

        html += `
            <tr>
                <td style="font-weight:600; color:var(--text-main);">${batch.name}</td>
                <td style="text-align:center;"><span class="batch-type-badge ${batch.type}">${batch.type}</span></td>
                <td style="text-align:center; color: var(--text-muted); font-size:12px;">${batch.date}</td>
                <td class="monospaced" style="text-align:right;"><span class="eval-badge ${evalPurity}">${batch.purity.toFixed(2)}%</span></td>
                <td class="monospaced" style="text-align:right;"><span class="eval-badge ${evalMoisture}">${batch.moisture.toFixed(4)}%</span></td>
                <td class="monospaced" style="text-align:right;"><span class="eval-badge ${evalAcidity}">${batch.acidity.toFixed(4)}%</span></td>
                <td class="monospaced" style="text-align:right;"><span class="eval-badge ${evalColor}">${batch.color}</span></td>
                <td class="monospaced" style="text-align:right;">${pmVal.toFixed(3)}%</td>
                <td class="monospaced" style="text-align:right;">${betaVal > 0 ? betaVal.toFixed(3) + '%' : '-'}</td>
            </tr>
        `;
    });

    html += "</tbody>";
    table.innerHTML = html;
}

// --- CSV Export Logic ---
function exportComparisonCSV() {
    let csvContent = "data:text/csv;charset=utf-8,\uFEFF"; // Adding UTF-8 BOM
    
    if (activeTab === "dual") {
        const batchA = batches.find(b => b.id === dualBatchA);
        const batchB = batches.find(b => b.id === dualBatchB);
        if (!batchA || !batchB) return;

        csvContent += `氣相層析比對報表 (雙批號精細比對)\r\n`;
        csvContent += `基準批號 A,${batchA.name}\r\n`;
        csvContent += `比對批號 B,${batchB.name}\r\n`;
        csvContent += `導出時間,${new Date().toLocaleString()}\r\n\r\n`;

        // KPI Summary
        csvContent += `指標項目,基準 A,比對 B,絕對差異,結果評估\r\n`;
        csvContent += `純度 Purity (Area%),${batchA.purity}%,${batchB.purity}%,${(batchB.purity - batchA.purity).toFixed(2)}%,${batchB.purity >= SPECIFICATIONS[batchB.type].purity ? '合格' : '不合格'}\r\n`;
        csvContent += `水分 Moisture (%),${batchA.moisture}%,${batchB.moisture}%,${(batchB.moisture - batchA.moisture).toFixed(4)}%,${batchB.moisture <= SPECIFICATIONS[batchB.type].moisture ? '合格' : '不合格'}\r\n`;
        csvContent += `酸度 Acidity (%),${batchA.acidity}%,${batchB.acidity}%,${(batchB.acidity - batchA.acidity).toFixed(4)}%,${batchB.acidity <= SPECIFICATIONS[batchB.type].acidity ? '合格' : '不合格'}\r\n`;
        csvContent += `色度 Color (APHA),${batchA.color},${batchB.color},${batchB.color - batchA.color},${batchB.color <= SPECIFICATIONS[batchB.type].color ? '合格' : '不合格'}\r\n\r\n`;

        // Peak details
        csvContent += `峰號,保留時間 (min),成分名稱,基準 A Area%,比對 B Area%,絕對差異\r\n`;
        const allPeakRTs = Array.from(new Set([...batchA.peaks.map(p => p.rt), ...batchB.peaks.map(p => p.rt)])).sort((a,b) => a - b);
        allPeakRTs.forEach((rt, idx) => {
            const peakA = batchA.peaks.find(p => p.rt === rt);
            const peakB = batchB.peaks.find(p => p.rt === rt);
            const valA = peakA ? peakA.areaPercent : 0.0;
            const valB = peakB ? peakB.areaPercent : 0.0;
            const name = (peakA ? peakA.name : "") || (peakB ? peakB.name : "未知成分");
            csvContent += `${idx+1},${rt},${name},${valA}%,${valB}%,${(valB - valA).toFixed(3)}%\r\n`;
        });

    } else {
        const selectedList = batches.filter(b => selectedBatches.has(b.id)).reverse();
        if (selectedList.length === 0) return;

        const firstBatch = selectedList[0];
        const spec = firstBatch ? (SPECIFICATIONS[firstBatch.type] || SPECIFICATIONS.Other) : SPECIFICATIONS.PMA;

        csvContent += `氣相層析比對報表 (多批號趨勢比較)\r\n`;
        csvContent += `導出時間,${new Date().toLocaleString()}\r\n\r\n`;

        // Matrix structure
        csvContent += `品質指標,規格標準,` + selectedList.map(b => b.name).join(",") + "\r\n";
        
        csvContent += `純度 Purity (Area%),>=${spec.purity.toFixed(2)}%,` + selectedList.map(b => b.purity.toFixed(2) + "%").join(",") + "\r\n";
        csvContent += `水份 Moisture (%),<=${spec.moisture.toFixed(4)}%,` + selectedList.map(b => b.moisture.toFixed(4) + "%").join(",") + "\r\n";
        csvContent += `酸度 Acidity (%),<=${spec.acidity.toFixed(4)}%,` + selectedList.map(b => b.acidity.toFixed(4) + "%").join(",") + "\r\n";
        csvContent += `色度 Color (APHA),<=${spec.color} APHA,` + selectedList.map(b => b.color).join(",") + "\r\n";
        csvContent += `主要雜質 PM (Area%),-,` + selectedList.map(b => {
            const p = b.peaks.find(k => k.name.includes("PM"));
            return p ? p.areaPercent.toFixed(3) + "%" : "0%";
        }).join(",") + "\r\n";
    }

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `GC_Comparison_Report_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("報告已成功導出 CSV！", "success");
}

// --- Toast System ---
function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-circle-xmark'}"></i>
        <span>${message}</span>
    `;
    toastContainer.appendChild(toast);

    // Fade out after 3 seconds
    setTimeout(() => {
        toast.style.animation = "toast-out 0.25s forwards";
        toast.addEventListener("animationend", () => {
            toast.remove();
        });
    }, 3000);
}

// Add CSS keyframe for toast exit
const styleSheet = document.createElement("style");
styleSheet.innerText = `
@keyframes toast-out {
    to {
        transform: translateY(-20px);
        opacity: 0;
    }
}
`;
document.head.appendChild(styleSheet);


// --- New Dynamically Configurable Category & Metadata Auto-populate Helpers ---

function populateCategoryDropdown() {
    const dropdown = document.getElementById("input-batch-type");
    if (!dropdown) return;
    dropdown.innerHTML = "";
    Object.keys(SPECIFICATIONS).forEach(cat => {
        const option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        dropdown.appendChild(option);
    });
}

function clearInlineCategoryForm() {
    document.getElementById("new-category-name").value = "";
    document.getElementById("new-category-purity").value = "";
    document.getElementById("new-category-moisture").value = "";
    document.getElementById("new-category-acidity").value = "";
    document.getElementById("new-category-color").value = "";
}

function saveCustomCategory() {
    const newName = document.getElementById("new-category-name").value.trim().toUpperCase();
    if (!newName) {
        showToast("請輸入類別名稱！", "error");
        return;
    }

    const purity = parseFloat(document.getElementById("new-category-purity").value) || SPECIFICATIONS.Other.purity;
    const moisture = parseFloat(document.getElementById("new-category-moisture").value) || SPECIFICATIONS.Other.moisture;
    const acidity = parseFloat(document.getElementById("new-category-acidity").value) || SPECIFICATIONS.Other.acidity;
    const color = parseInt(document.getElementById("new-category-color").value) || SPECIFICATIONS.Other.color;

    SPECIFICATIONS[newName] = { purity, moisture, acidity, color };
    
    // Refresh dropdowns and filters
    populateCategoryDropdown();
    document.getElementById("input-batch-type").value = newName;
    updateCounters(); // Redraw filter tabs
    
    // Hide form
    document.getElementById("inline-category-box").style.display = "none";
    clearInlineCategoryForm();

    showToast(`成功新增樣品類別 ${newName}！`, "success");
}

function parseReportMetadata(text) {
    // Regex matches
    const nameMatch = text.match(/(?:Batch|批號|Sample|樣品名稱|樣品)[:：\s]+([^\r\n,;]+)/i);
    const typeMatch = text.match(/(?:Category|類別|樣品類別)[:：\s]+([^\r\n,;]+)/i);
    const purityMatch = text.match(/(?:Purity|純度|主成分)[:：\s]+([0-9.]+)/i);
    const moistureMatch = text.match(/(?:Moisture|水份|水分|H2O)[:：\s]+([0-9.]+)/i);
    const acidityMatch = text.match(/(?:Acidity|酸度|Acid)[:：\s]+([0-9.]+)/i);
    const colorMatch = text.match(/(?:Color|色度|APHA)[:：\s]+([0-9.]+)/i);

    let isAutofilled = false;

    if (nameMatch) {
        document.getElementById("input-batch-name").value = nameMatch[1].trim();
        isAutofilled = true;
    }

    if (typeMatch) {
        let detectedType = typeMatch[1].trim().toUpperCase();
        
        // If type doesn't exist, register it with default settings
        if (!SPECIFICATIONS[detectedType]) {
            SPECIFICATIONS[detectedType] = {
                purity: 99.50,
                moisture: 0.0300,
                acidity: 0.0300,
                color: 20
            };
            populateCategoryDropdown();
            updateCounters();
        }
        
        document.getElementById("input-batch-type").value = detectedType;
        isAutofilled = true;
    }

    if (purityMatch) {
        document.getElementById("input-purity").value = parseFloat(purityMatch[1]);
        isAutofilled = true;
    }

    if (moistureMatch) {
        document.getElementById("input-moisture").value = parseFloat(moistureMatch[1]);
        isAutofilled = true;
    }

    if (acidityMatch) {
        document.getElementById("input-acidity").value = parseFloat(acidityMatch[1]);
        isAutofilled = true;
    }

    if (colorMatch) {
        document.getElementById("input-color").value = parseInt(colorMatch[1]);
        isAutofilled = true;
    }

    if (isAutofilled) {
        showToast("已從黏貼內容自動填入相關欄位！", "success");
    }
}

// --- Dynamic Pagination & Bulk Selection Helpers ---

function getFilteredBatches() {
    return batches.filter(batch => {
        const matchSearch = batch.name.toLowerCase().includes(searchQuery) ||
                             batch.type.toLowerCase().includes(searchQuery);
        if (currentFilter === "all") return matchSearch;
        return batch.type === currentFilter && matchSearch;
    });
}

function renderSidebarPagination(totalCount) {
    const container = document.getElementById("sidebar-pagination-controls");
    if (!container) return;

    const totalPages = Math.ceil(totalCount / cardsPerPage);
    if (totalPages <= 1) {
        container.innerHTML = "";
        container.style.display = "none";
        return;
    }
    container.style.display = "flex";

    container.innerHTML = `
        <span class="page-info">第 ${currentPage} / ${totalPages} 頁 (共 ${totalCount} 筆)</span>
        <div class="page-btn-group">
            <button class="btn-page" id="btn-page-prev" ${currentPage === 1 ? 'disabled' : ''} title="上一頁">
                <i class="fa-solid fa-chevron-left"></i>
            </button>
            <button class="btn-page" id="btn-page-next" ${currentPage === totalPages ? 'disabled' : ''} title="下一頁">
                <i class="fa-solid fa-chevron-right"></i>
            </button>
        </div>
    `;

    document.getElementById("btn-page-prev")?.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            renderBatchList();
        }
    });

    document.getElementById("btn-page-next")?.addEventListener("click", () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderBatchList();
        }
    });
}

// Renders the Multi-Batch Chromatogram Overlay and legend table
function renderMultiChromatogram() {
    const tbody = document.querySelector("#multi-chrom-legend-table tbody");
    if (!tbody) return;

    // Filter selected batches by active category
    let selectedList = batches.filter(b => {
        const matchCategory = (currentFilter === "all" || b.type === currentFilter);
        return selectedBatches.has(b.id) && matchCategory;
    });

    if (selectedList.length === 0) {
        if (multiChromChart) {
            multiChromChart.destroy();
            multiChromChart = null;
        }
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:20px; color:var(--text-muted);;">請在左側選取批號以進行譜圖疊合比較</td></tr>`;
        return;
    }

    // Display all selected batches (no arbitrary limit, just like trend charts!)
    const displayList = selectedList;

    // Initialize display state tracking in window if not present
    if (!window.hiddenMultiChroms) {
        window.hiddenMultiChroms = new Set();
    }

    // Dynamically generate high-contrast colors using golden ratio angle distribution
    const getColor = (index) => {
        const hue = (index * 137.508) % 360;
        return {
            border: `hsl(${hue}, 75%, 50%)`,
            fill: `hsla(${hue}, 75%, 50%, 0.05)`
        };
    };

    // Generate retention times X-axis labels (2.0 to 11.0, step 0.04)
    const labels = [];
    for (let x = 2.0; x <= 11.001; x += 0.04) {
        labels.push(x.toFixed(2));
    }

    // Map each batch to a Chart.js dataset
    const datasets = displayList.map((batch, index) => {
        const colorSet = getColor(index);
        const borderColor = colorSet.border;
        const backgroundColor = colorSet.fill;
        
        // Generate simulated Gaussian peak profile curve
        const data = [];
        for (let x = 2.0; x <= 11.001; x += 0.04) {
            let y = 0.0;
            batch.peaks.forEach(peak => {
                // Y = Peak_Area_Percent * 5 * e^(-(x - RT)^2 / (2 * 0.08^2))
                y += peak.areaPercent * 5.0 * Math.exp(-Math.pow(x - peak.rt, 2) / (2.0 * Math.pow(0.08, 2)));
            });
            // Baseline noise (semi-deterministic based on batch name to avoid chaotic redraw jitter)
            const noiseSeed = (x * 100 + batch.name.length) % 7;
            y += (noiseSeed - 3) * 0.05;
            data.push(y < 0 ? 0 : +y.toFixed(2));
        }

        const isHidden = window.hiddenMultiChroms.has(batch.id);

        return {
            label: batch.name,
            data: data,
            borderColor: borderColor,
            backgroundColor: backgroundColor,
            borderWidth: 2,
            pointRadius: 0,
            pointHoverRadius: 4,
            fill: false,
            tension: 0.3,
            hidden: isHidden
        };
    });

    // Render/Update Chart.js line chart
    const canvas = document.getElementById("chart-multi-chromatogram");
    if (canvas) {
        const ctx = canvas.getContext("2d");
        if (multiChromChart) {
            multiChromChart.destroy();
        }
        multiChromChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false // Use our interactive table legend below
                    },
                    tooltip: {
                        position: 'sidePositioner',
                        caretSize: 0,
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: (context) => `保留時間 (RT): ${context[0].label} min`,
                            label: (context) => ` ${context.dataset.label}: ${context.raw} mV`
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: '保留時間 Retention Time (min)',
                            font: { size: 12, weight: 'bold' }
                        },
                        grid: { color: '#f1f5f9' }
                    },
                    y: {
                        title: {
                            display: true,
                            text: '訊號強度 Signal Intensity (mV)',
                            font: { size: 12, weight: 'bold' }
                        },
                        grid: { color: '#f1f5f9' },
                        min: 0
                    }
                }
            }
        });
    }

    // Render custom table legend with toggles
    tbody.innerHTML = "";
    displayList.forEach((batch, index) => {
        const colorSet = getColor(index);
        const color = colorSet.border;
        const isChecked = !window.hiddenMultiChroms.has(batch.id);

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td style="text-align:center;">
                <input type="checkbox" class="legend-toggle" data-id="${batch.id}" ${isChecked ? 'checked' : ''} style="cursor:pointer; width:16px; height:16px; accent-color: var(--primary);">
            </td>
            <td style="text-align:center;">
                <span class="color-swatch" style="background-color: ${color};"></span>
            </td>
            <td style="font-weight:600; color:var(--text-main);">${batch.name}</td>
            <td><span class="batch-type-badge ${batch.type}">${batch.type}</span></td>
            <td>${batch.purity.toFixed(2)}%</td>
            <td>${batch.moisture.toFixed(4)}%</td>
            <td>${batch.acidity.toFixed(4)}%</td>
            <td>${batch.color}</td>
        `;

        // Toggle checkbox change listener
        tr.querySelector(".legend-toggle").addEventListener("change", (e) => {
            const id = e.target.getAttribute("data-id");
            if (e.target.checked) {
                window.hiddenMultiChroms.delete(id);
            } else {
                window.hiddenMultiChroms.add(id);
            }
            
            // Toggle dataset visibility dynamically in Chart.js
            const dsIdx = datasets.findIndex(d => d.label === batch.name);
            if (dsIdx !== -1 && multiChromChart) {
                multiChromChart.setDatasetVisibility(dsIdx, e.target.checked);
                multiChromChart.update();
            }
        });

        tbody.appendChild(tr);
    });
}

// Renders the data matrix comparison tab content
function renderMatrixTab() {
    let selectedList = batches.filter(b => {
        const matchCategory = (currentFilter === "all" || b.type === currentFilter);
        return selectedBatches.has(b.id) && matchCategory;
    }).reverse(); // Chronological order

    renderComparisonMatrixTable(selectedList);
}

// Clear Category Management Form
function clearCategoryManagerForm() {
    document.getElementById("mgr-cat-name").value = "";
    document.getElementById("mgr-cat-purity").value = "";
    document.getElementById("mgr-cat-moisture").value = "";
    document.getElementById("mgr-cat-acidity").value = "";
    document.getElementById("mgr-cat-color").value = "";
    document.getElementById("mgr-cat-name").disabled = false; // Re-enable for new categories
    document.getElementById("mgr-form-title").innerHTML = `<i class="fa-solid fa-plus"></i> 新增 / 編輯類別規格`;
}

// Render Category Management Table rows
function renderCategoryManagerTable() {
    const tbody = document.querySelector("#table-category-specs tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    Object.keys(SPECIFICATIONS).forEach(cat => {
        const spec = SPECIFICATIONS[cat];
        const isSystem = (cat === "PMA" || cat === "PMAC" || cat === "Other");

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td style="font-weight:600; color:var(--text-main); font-size: 13px;">${cat} ${isSystem ? '<span style="font-size:10px; font-weight:normal; color:var(--text-muted);">(系統)</span>' : ''}</td>
            <td class="monospaced" style="text-align:right;">${spec.purity.toFixed(2)}%</td>
            <td class="monospaced" style="text-align:right;">${spec.moisture.toFixed(4)}%</td>
            <td class="monospaced" style="text-align:right;">${spec.acidity.toFixed(4)}%</td>
            <td class="monospaced" style="text-align:right;">${spec.color}</td>
            <td style="text-align:center;">
                <button type="button" class="btn-edit-spec" style="background:none; border:none; color:var(--primary); cursor:pointer; margin-right:8px;" title="編輯規格"><i class="fa-solid fa-pen-to-square"></i></button>
                <button type="button" class="btn-delete-spec" ${isSystem ? 'disabled style="color:#cbd5e1; cursor:not-allowed; background:none; border:none;"' : 'style="background:none; border:none; color:var(--danger); cursor:pointer;"'} title="${isSystem ? '系統預設，不可刪除' : '刪除類別'}"><i class="fa-solid fa-trash-can"></i></button>
            </td>
        `;

        // Bind events
        tr.querySelector(".btn-edit-spec").addEventListener("click", () => {
            editCategoryManagerItem(cat);
        });

        if (!isSystem) {
            tr.querySelector(".btn-delete-spec").addEventListener("click", () => {
                deleteCategoryManagerItem(cat);
            });
        }

        tbody.appendChild(tr);
    });
}

// Edit Category spec info
function editCategoryManagerItem(cat) {
    const spec = SPECIFICATIONS[cat];
    document.getElementById("mgr-cat-name").value = cat;
    document.getElementById("mgr-cat-name").disabled = true; // Lock name input when editing
    document.getElementById("mgr-cat-purity").value = spec.purity;
    document.getElementById("mgr-cat-moisture").value = spec.moisture;
    document.getElementById("mgr-cat-acidity").value = spec.acidity;
    document.getElementById("mgr-cat-color").value = spec.color;
    document.getElementById("mgr-form-title").innerHTML = `<i class="fa-solid fa-pen-to-square"></i> 編輯類別規格 [ ${cat} ]`;
}

// Delete custom category
function deleteCategoryManagerItem(cat) {
    if (confirm(`確定要刪除自定義樣品類別 [ ${cat} ] 嗎？這將會清除其品質規格標準。`)) {
        delete SPECIFICATIONS[cat];
        showToast(`已刪除樣品類別 ${cat}`, "success");
        
        // Refresh dropdowns, filter tabs, and matrix views
        populateCategoryDropdown();
        updateCounters();
        
        // If current filter was the deleted category, reset to 'all'
        if (currentFilter === cat) {
            currentFilter = "all";
            currentPage = 1;
            renderBatchList();
            if (activeTab === "multi") renderMultiTrends();
            if (activeTab === "multi-chrom") renderMultiChromatogram();
            if (activeTab === "matrix") renderMatrixTab();
        } else {
            renderBatchList();
            if (activeTab === "multi") renderMultiTrends();
            if (activeTab === "multi-chrom") renderMultiChromatogram();
            if (activeTab === "matrix") renderMatrixTab();
        }

        renderCategoryManagerTable();
    }
}

// Save Category Spec Form (insert/update)
function saveCategoryManagerForm() {
    const nameInput = document.getElementById("mgr-cat-name");
    const name = nameInput.value.trim().toUpperCase();
    if (!name) {
        showToast("請輸入類別名稱！", "error");
        return;
    }

    const purity = parseFloat(document.getElementById("mgr-cat-purity").value);
    const moisture = parseFloat(document.getElementById("mgr-cat-moisture").value);
    const acidity = parseFloat(document.getElementById("mgr-cat-acidity").value);
    const color = parseInt(document.getElementById("mgr-cat-color").value);

    if (isNaN(purity) || isNaN(moisture) || isNaN(acidity) || isNaN(color)) {
        showToast("請填寫所有規格數值！", "error");
        return;
    }

    const isExisting = SPECIFICATIONS[name] !== undefined;

    SPECIFICATIONS[name] = { purity, moisture, acidity, color };

    showToast(isExisting ? `已更新類別 ${name} 的品質規格！` : `成功新增樣品類別 ${name}！`, "success");

    clearCategoryManagerForm();
    renderCategoryManagerTable();

    // Refresh UI dropdowns and filters
    populateCategoryDropdown();
    updateCounters();
    renderBatchList();

    if (activeTab === "multi") renderMultiTrends();
    if (activeTab === "multi-chrom") renderMultiChromatogram();
    if (activeTab === "matrix") renderMatrixTab();
}
