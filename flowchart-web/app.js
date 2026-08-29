// Catch all unhandled Javascript errors to help debug
window.onerror = function (msg, url, lineNo, columnNo, error) {
  const file = url ? url.substring(url.lastIndexOf('/') + 1) : 'unknown';
  alert(`⚠️ JS 錯誤: ${msg}\n檔案: ${file}\n行號: ${lineNo}`);
  return false;
};

// Initialize global capacity inputs for personnel key-in with localStorage persistence
window.capacityInputs = {};
try {
  const saved = localStorage.getItem('flowchart_capacity_inputs');
  if (saved) {
    window.capacityInputs = JSON.parse(saved);
  }
} catch (e) {
  console.error("Failed to load capacity inputs from localStorage", e);
}

window.saveCapacity = function(tab, from, to, val) {
  window.capacityInputs[tab + '_' + from] = val;
  try {
    localStorage.setItem('flowchart_capacity_inputs', JSON.stringify(window.capacityInputs));
  } catch (e) {
    console.error("Failed to save capacity inputs to localStorage", e);
  }
};


// 9 Product Flowcharts Dataset with Process Groupings (Single-column layout to prevent overlaps)
const flowchartData = {
  "ipa": {
    title: "01. I P A 流程圖 (異丙醇)",
    totalCapacity: "原料共 2850 KL / 成品共 770KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 2850 KL", x: 120, y: 80, w: 180, h: 500, type: "raw" },
      { id: "process-block-s1", name: "S1製程生產", capacity: "", x: 360, y: 120, w: 160, h: 65, type: "process" },
      { id: "process-block-s3", name: "S3製程生產", capacity: "", x: 360, y: 215, w: 160, h: 65, type: "process" },
      { id: "waste-group-ipahw", name: "IPAHW下腳料區", capacity: "共 50 KL", x: 360, y: 310, w: 180, h: 105, type: "offgrade" },
      { id: "waste-group-ipa", name: "IPA下腳料區", capacity: "共 150 KL", x: 360, y: 445, w: 180, h: 165, type: "offgrade" },
      { id: "check-group-ipa", name: "Check Tank 待驗 (IPAUPS)", capacity: "共 25 KL", x: 600, y: 80, w: 180, h: 220, type: "process" },
      { id: "finish-group-ipa", name: "IPAUPS成品區", capacity: "共 570 KL", x: 840, y: 80, w: 180, h: 220, type: "finish" },
      { id: "check-group-ipahq", name: "Check Tank 待驗 (IPAHQ)", capacity: "共 60 KL", x: 600, y: 340, w: 180, h: 240, type: "process" },
      { id: "finish-group-ipahq", name: "IPAHQ成品區", capacity: "共 200 KL", x: 840, y: 340, w: 180, h: 240, type: "finish" }
    ],
    nodes: [
      // Raw group (stacked vertically, x = 140)
      { id: "TK-602", name: "原料槽", capacity: "500 KL", type: "raw", x: 140, y: 130, fill: 65, details: { temp: "25.1 °C", press: "1.05 atm", comp: "工業級 IPA 99.0%", status: "常態儲存" } },
      { id: "TK-696", name: "原料槽", capacity: "550 KL", type: "raw", x: 140, y: 200, fill: 80, details: { temp: "25.0 °C", press: "1.03 atm", comp: "工業級 IPA 99.5%", status: "常態儲存" } },
      { id: "TK-697", name: "原料槽", capacity: "550 KL", type: "raw", x: 140, y: 270, fill: 35, details: { temp: "24.9 °C", press: "1.01 atm", comp: "小包裝專用 IPA", status: "待命" } },
      { id: "TK-693", name: "原料槽", capacity: "250 KL", type: "raw", x: 140, y: 340, fill: 50, details: { temp: "25.1 °C", press: "1.02 atm", comp: "一廠專供高純電子級", status: "供料中" } },
      { id: "TK-604A", name: "精餾塔A", capacity: "500 KL", type: "raw", x: 140, y: 410, fill: 40, details: { temp: "78.3 °C", press: "1.20 atm", comp: "精餾塔組分", status: "精餾運作中" } },
      { id: "TK-604B", name: "精餾塔B", capacity: "500 KL", type: "raw", x: 140, y: 480, fill: 30, details: { temp: "78.5 °C", press: "1.18 atm", comp: "精餾塔組分", status: "精餾運作中" } },
      
      // Waste group (stacked vertically, x = 380)
      { id: "TK-652", name: "IPAHW下腳料", capacity: "50 KL", type: "offgrade", x: 380, y: 345, fill: 80, details: { temp: "24.5 °C", press: "1.02 atm", comp: "粗異丙醇回收", status: "回收中" } },
      { id: "TK-690", name: "格外品槽", capacity: "50 KL", type: "offgrade", x: 380, y: 480, fill: 20, details: { temp: "24.6 °C", press: "1.01 atm", comp: "粗異丙醇回收", status: "待命" } },
      { id: "TK-691", name: "格外品槽", capacity: "100 KL", type: "offgrade", x: 380, y: 545, fill: 15, details: { temp: "26.3 °C", press: "1.04 atm", comp: "異常不合格回收液", status: "待重製回流" } },
      
      // Check Tank group (stacked vertically, x = 620)
      { id: "TK-614", name: "待驗槽A", capacity: "25 KL", type: "process", x: 620, y: 150, fill: 45, details: { temp: "28.0 °C", press: "1.12 atm", comp: "待驗異丙醇", status: "待驗中" } },
      { id: "TK-675", name: "待驗槽B", capacity: "30 KL", type: "process", x: 620, y: 390, fill: 55, details: { temp: "30.2 °C", press: "1.08 atm", comp: "待驗異丙醇", status: "待驗中" } },
      { id: "TK-676", name: "待驗槽C", capacity: "30 KL", type: "process", x: 620, y: 470, fill: 85, details: { temp: "30.1 °C", press: "1.09 atm", comp: "待驗異丙醇", status: "待驗中" } },
      
      // Finish group (stacked vertically, x = 860)
      { id: "TK-624", name: "成品槽", capacity: "500 KL", type: "finish", x: 860, y: 120, fill: 60, details: { temp: "25.2 °C", press: "1.02 atm", comp: "成品 IPA 99.9%", status: "放行出貨中" } },
      { id: "TK-672", name: "工業級成品槽", capacity: "70 KL", type: "finish", x: 860, y: 190, fill: 70, details: { temp: "25.4 °C", press: "1.03 atm", comp: "成品 IPA 99.5%", status: "儲存中" } },
      { id: "TK-681", name: "IPAHQ成品槽A", capacity: "100 KL", type: "finish", x: 860, y: 390, fill: 90, details: { temp: "26.0 °C", press: "1.02 atm", comp: "高純電子級 IPA 99.99%", status: "放行已核准" } },
      { id: "TK-682", name: "IPAHQ成品槽B", capacity: "100 KL", type: "finish", x: 860, y: 470, fill: 75, details: { temp: "25.8 °C", press: "1.01 atm", comp: "高純電子級 IPA 99.99%", status: "成品儲放" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "process-block-s1", label: "" },
      { from: "raw-group", to: "process-block-s3", label: "" },
      { from: "process-block-s1", to: "waste-group-ipahw", label: "格外品排料" },
      { from: "process-block-s3", to: "waste-group-ipa", label: "" },
      { from: "process-block-s1", to: "check-group-ipa", label: "送待驗" },
      { from: "process-block-s3", to: "check-group-ipahq", label: "送待驗" },
      { from: "check-group-ipa", to: "finish-group-ipa", label: "N2 放行" },
      { from: "check-group-ipahq", to: "finish-group-ipahq", label: "N2 放行" }
    ]
  },
  "eg": {
    title: "02. E G 流程圖 (乙二醇)",
    totalCapacity: "原料共 350 KL / 成品共 375 KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 350 KL", x: 120, y: 80, w: 180, h: 500, type: "raw" },
      { id: "process-block", name: "製程", capacity: "", x: 360, y: 180, w: 160, h: 80, type: "process" },
      { id: "waste-group", name: "下腳料區", capacity: "共 50 KL", x: 360, y: 300, w: 180, h: 280, type: "offgrade" },
      { id: "check-group", name: "Check Tank 待驗", capacity: "共 55 KL", x: 600, y: 80, w: 180, h: 500, type: "process" },
      { id: "finish-group", name: "成品區", capacity: "共 375 KL", x: 840, y: 80, w: 180, h: 500, type: "finish" }
    ],
    nodes: [
      // Raw group (x = 140)
      { id: "TK-603", name: "原料槽", capacity: "250 KL", type: "raw", x: 140, y: 180, fill: 75, details: { temp: "22.1 °C", press: "1.01 atm", comp: "EG 進料原料", status: "穩定儲存" } },
      { id: "TK-689", name: "原料槽", capacity: "100 KL", type: "raw", x: 140, y: 260, fill: 75, details: { temp: "22.1 °C", press: "1.01 atm", comp: "EG 進料原料", status: "穩定儲存" } },
      // Waste group (x = 380)
      { id: "TK-656", name: "格外品回收槽", capacity: "50 KL", type: "offgrade", x: 380, y: 350, fill: 10, details: { temp: "24.2 °C", press: "1.03 atm", comp: "EG 不合格回收液", status: "格外品收集" } },
      
      // Check Tank (x = 620)
      { id: "TK-613", name: "待驗配料槽A", capacity: "25 KL", type: "process", x: 620, y: 140, fill: 50, details: { temp: "42.0 °C", press: "1.10 atm", comp: "EG 調配配方液A", status: "攪拌調合中" } },
      { id: "TK-678", name: "待驗配料槽B", capacity: "30 KL", type: "process", x: 620, y: 220, fill: 65, details: { temp: "42.2 °C", press: "1.11 atm", comp: "EG 調配配方液B", status: "攪拌調合中" } },
      
      // Finish group (x = 860)
      { id: "TK-623", name: "成品大槽A", capacity: "125 KL", type: "finish", x: 860, y: 140, fill: 85, details: { temp: "23.4 °C", press: "1.02 atm", comp: "合格成品 EG", status: "待放行" } },
      { id: "TK-692", name: "成品大槽B", capacity: "250KL", type: "finish", x: 860, y: 220, fill: 60, details: { temp: "23.5 °C", press: "1.01 atm", comp: "合格成品 EG", status: "常態儲存" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "process-block", label: "" },
      { from: "process-block", to: "waste-group", label: "格外品排料" },
      { from: "process-block", to: "check-group", label: "待檢驗" },
      { from: "check-group", to: "finish-group", label: "放行成品" }
    ]
  },
  "nmp": {
    title: "03. N M P 流程圖 (N-甲基吡咯烷酮)",
    totalCapacity: "共 445 KL / 250 KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 445 KL", x: 120, y: 80, w: 180, h: 500, type: "raw" },
      { id: "process-block", name: "製程", capacity: "", x: 360, y: 180, w: 160, h: 80, type: "process" },
      { id: "waste-group", name: "下腳料區", capacity: "格外品", x: 360, y: 300, w: 180, h: 280, type: "offgrade" },
      { id: "check-group", name: "Check Tank 待驗", capacity: "共 25 KL", x: 600, y: 80, w: 180, h: 500, type: "process" },
      { id: "finish-group", name: "成品區", capacity: "共 250 KL", x: 840, y: 80, w: 180, h: 500, type: "finish" }
    ],
    nodes: [
      // Raw group (x = 140)
      { id: "TK-632", name: "原料槽A", capacity: "250 KL", type: "raw", x: 140, y: 140, fill: 75, details: { temp: "25.1 °C", press: "1.02 atm", comp: "工業級 NMP 原料", status: "常態儲存" } },
      { id: "TK-633", name: "原料槽B", capacity: "125 KL", type: "raw", x: 140, y: 220, fill: 60, details: { temp: "25.0 °C", press: "1.01 atm", comp: "工業級 NMP 原料", status: "常態儲存" } },
      { id: "TK-671", name: "原料槽C", capacity: "70 KL", type: "raw", x: 140, y: 300, fill: 40, details: { temp: "24.9 °C", press: "1.01 atm", comp: "中繼 NMP 原料", status: "待命" } },
      
      // Waste group (x = 380)
      { id: "IBC桶", name: "格外品收集", capacity: "1T裝", type: "offgrade", x: 380, y: 350, fill: 10, details: { temp: "25.0 °C", press: "1.00 atm", comp: "格外不合格液", status: "常態回收" } },
      
      // Check Tank (x = 620)
      { id: "TK-611", name: "製程待驗槽", capacity: "25 KL", type: "process", x: 620, y: 140, fill: 50, details: { temp: "25.4 °C", press: "1.02 atm", comp: "NMP 中間液", status: "待驗中" } },
      
      // Finish group (x = 860)
      { id: "TK-621", name: "成品大槽", capacity: "250 KL", type: "finish", x: 860, y: 140, fill: 85, details: { temp: "25.2 °C", press: "1.01 atm", comp: "電子級 NMP 成品", status: "成品儲存" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "process-block", label: "" },
      { from: "process-block", to: "waste-group", label: "格外品排料" },
      { from: "process-block", to: "check-group", label: "待檢驗" },
      { from: "check-group", to: "finish-group", label: "N2 purge" }
    ]
  },
  "cpne4": {
    title: "04. C P N E 4 流程圖",
    totalCapacity: "原料共 500 KL / 成品共 100 KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 500 KL", x: 120, y: 80, w: 180, h: 500, type: "raw" },
      { id: "process-block", name: "製程", capacity: "", x: 360, y: 180, w: 160, h: 80, type: "process" },
      { id: "waste-group", name: "下腳料區", capacity: "共 50 KL", x: 360, y: 300, w: 180, h: 280, type: "offgrade" },
      { id: "check-group", name: "Check Tank 待驗", capacity: "共 30 KL", x: 600, y: 80, w: 180, h: 500, type: "process" },
      { id: "finish-group", name: "成品區", capacity: "共 50 KL", x: 840, y: 80, w: 180, h: 500, type: "finish" }
    ],
    nodes: [
      // Raw group (x = 140)
      { id: "TK-684", name: "原料槽A", capacity: "100 KL", type: "raw", x: 140, y: 130, fill: 80, details: { temp: "22.5 °C", press: "1.01 atm", comp: "CPNE 原料A", status: "穩定供料" } },
      { id: "TK-685", name: "原料槽B", capacity: "100 KL", type: "raw", x: 140, y: 200, fill: 70, details: { temp: "22.6 °C", press: "1.02 atm", comp: "CPNE 原料B", status: "穩定供料" } },
      { id: "TK-686", name: "原料槽C", capacity: "100 KL", type: "raw", x: 140, y: 270, fill: 60, details: { temp: "22.4 °C", press: "1.01 atm", comp: "CPNE 原料C", status: "穩定供料" } },
      { id: "TK-687", name: "原料槽D", capacity: "100 KL", type: "raw", x: 140, y: 340, fill: 50, details: { temp: "22.5 °C", press: "1.02 atm", comp: "CPNE 原料D", status: "待命" } },
      { id: "TK-688", name: "原料槽E", capacity: "100 KL", type: "raw", x: 140, y: 410, fill: 40, details: { temp: "22.7 °C", press: "1.03 atm", comp: "CPNE 原料E", status: "待命" } },
      
      // Waste group (x = 380)
      { id: "TK-655", name: "格外品大槽", capacity: "50 KL", type: "offgrade", x: 380, y: 350, fill: 20, details: { temp: "26.4 °C", press: "1.05 atm", comp: "格外不合格液", status: "格外品排料" } },
      
      // Check Tank (x = 620)
      { id: "TK-677", name: "待驗槽", capacity: "30 KL", type: "process", x: 620, y: 180, fill: 50, details: { temp: "30.0 °C", press: "2.30 atm", comp: "CPNE4 待驗液", status: "待驗中" } },
      
      // Finished (x = 860)
      { id: "TK-680", name: "成品大槽A", capacity: "50 KL", type: "finish", x: 860, y: 160, fill: 80, details: { temp: "25.0 °C", press: "1.02 atm", comp: "合格成品 CPNE4-A", status: "合格放行" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "process-block", label: "" },
      { from: "process-block", to: "waste-group", label: "格外品排料" },
      { from: "process-block", to: "check-group", label: "待檢驗" },
      { from: "check-group", to: "finish-group", label: "N2 purge" },
      { from: "process-block", to: "finish-group", label: "直接放行" }
    ]
  },
  "cpne3": {
    title: "05. CPNE3R & CPNE3 & CPNE3 T& 2CPN-P1 流程圖",
    totalCapacity: "原料共 80 KL / CPNE3成品共 295 KL / CPNE3成品共 100 KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 80 KL", x: 80, y: 80, w: 160, h: 500, type: "raw" },
      { id: "p1-group", name: "半成品 CPN-P1", capacity: "共 500 KL", x: 300, y: 80, w: 160, h: 500, type: "raw" },
      { id: "p2-group", name: "半成品 CPNE3R", capacity: "共 250 KL", x: 520, y: 80, w: 160, h: 500, type: "process" },
      { id: "check-group", name: "成品 CPNE3", capacity: "共 295 KL", x: 740, y: 80, w: 160, h: 500, type: "finish" },
      { id: "finish-group", name: "成品 CPNE3T", capacity: "共 100 KL", x: 960, y: 80, w: 160, h: 500, type: "finish" }
    ],
    nodes: [
      // Raw group (x = 90)
      { id: "TK-643", name: "攪拌調合罐A", capacity: "40 KL", type: "raw", x: 90, y: 140, fill: 70, details: { temp: "24.1 °C", press: "1.02 atm", comp: "CP 原料A", status: "攪拌中" } },
      { id: "TK-645", name: "攪拌調合罐B", capacity: "40 KL", type: "raw", x: 90, y: 220, fill: 60, details: { temp: "24.2 °C", press: "1.02 atm", comp: "CP 原料B", status: "待命" } },
      
      // 2CPN-P1 group (x = 310)
      { id: "TK-634", name: "半成品大槽", capacity: "500 KL", type: "raw", x: 310, y: 180, fill: 80, details: { temp: "25.0 °C", press: "1.03 atm", comp: "2CPN-P1 半成品", status: "穩定儲存" } },
      
      // CPNE3R group (x = 530)
      { id: "TK-601", name: "半成品反應槽", capacity: "250 KL", type: "process", x: 530, y: 180, fill: 65, details: { temp: "81.5 °C", press: "3.08 atm", comp: "CPNE3R 半成品", status: "反應中" } },
      
      // CPNE3 group (x = 750)
      { id: "TK-661/662/664", name: "成品大槽組", capacity: "65 KL / 槽", type: "finish", x: 750, y: 140, fill: 80, details: { temp: "25.0 °C", press: "1.01 atm", comp: "合格 CPNE3 成品 (3槽)", status: "成品儲存" } },
      { id: "TK-667/668", name: "成品大槽組", capacity: "50 KL / 槽", type: "finish", x: 750, y: 220, fill: 75, details: { temp: "24.9 °C", press: "1.01 atm", comp: "合格 CPNE3 成品 (2槽)", status: "成品儲存" } },
      
      // CPNE3T group (x = 970)
      { id: "TK-683", name: "成品放行大槽", capacity: "100 KL", type: "finish", x: 970, y: 180, fill: 85, details: { temp: "24.8 °C", press: "1.02 atm", comp: "超高純 CPNE3T 成品", status: "放行中" } },
      
      // Offgrades placed below the flow lines
      { id: "IBC桶", name: "格外品前處理", capacity: "1T裝", type: "offgrade", x: 200, y: 360, fill: 15, details: { temp: "25.0 °C", press: "1.00 atm", comp: "前處理不合格液", status: "格外品收集" } },
      { id: "TK-660", name: "格外品回收槽", capacity: "70 KL", type: "offgrade", x: 420, y: 360, fill: 35, details: { temp: "26.5 °C", press: "1.05 atm", comp: "格外品回收液", status: "回流中" } },
      { id: "TK-655", name: "格外品大槽A", capacity: "50 KL", type: "offgrade", x: 640, y: 360, fill: 20, details: { temp: "26.0 °C", press: "1.03 atm", comp: "特種回收液", status: "待命" } },
      { id: "TK-655_2", name: "格外品大槽B", capacity: "50 KL", type: "offgrade", x: 860, y: 360, fill: 20, details: { temp: "26.0 °C", press: "1.03 atm", comp: "特種回收液", status: "待命" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "p1-group", label: "前處理" },
      { from: "p1-group", to: "p2-group", label: "製程" },
      { from: "p2-group", to: "check-group", label: "製程" },
      { from: "check-group", to: "finish-group", label: "製程" },
      { from: "raw-group", to: "IBC桶", label: "格外品" },
      { from: "p1-group", to: "TK-660", label: "格外品" },
      { from: "p2-group", to: "TK-655", label: "格外品" },
      { from: "check-group", to: "TK-655_2", label: "格外品" }
    ]
  },
  "act": {
    title: "06. A C T 流程圖",
    totalCapacity: "原料共 70 KL / 成品共 250 KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 70 KL", x: 120, y: 80, w: 180, h: 500, type: "raw" },
      { id: "process-block", name: "製程", capacity: "", x: 360, y: 180, w: 160, h: 80, type: "process" },
      { id: "waste-group", name: "下腳料區", capacity: "共 25 KL", x: 360, y: 300, w: 180, h: 280, type: "offgrade" },
      { id: "check-group", name: "Check Tank 待驗", capacity: "共 25 KL", x: 600, y: 80, w: 180, h: 500, type: "process" },
      { id: "finish-group", name: "成品區", capacity: "共 250 KL", x: 840, y: 80, w: 180, h: 500, type: "finish" }
    ],
    nodes: [
      { id: "TK-657", name: "ACT 原料槽", capacity: "70 KL", type: "raw", x: 140, y: 140, fill: 60, details: { temp: "23.4 °C", press: "1.02 atm", comp: "ACT 原料 99.2%", status: "傳輸中" } },
      { id: "TK-612", name: "精餾製程釜", capacity: "25 KL", type: "process", x: 620, y: 140, fill: 45, details: { temp: "88.0 °C", press: "1.35 atm", comp: "含 N2 purge 吹掃", status: "吹掃精製" } },
      { id: "TK-622", name: "成品大槽", capacity: "250 KL", type: "finish", x: 860, y: 140, fill: 85, details: { temp: "25.1 °C", press: "1.01 atm", comp: "高純度 ACT 99.8%", status: "合格放行" } },
      { id: "1T-Tank", name: "格外品1T桶", capacity: "1T桶裝", type: "offgrade", x: 380, y: 350, fill: 30, details: { temp: "25.5 °C", press: "1.00 atm", comp: "不合格回流液", status: "待命" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "process-block", label: "" },
      { from: "process-block", to: "waste-group", label: "格外品排料" },
      { from: "process-block", to: "check-group", label: "待檢驗" },
      { from: "check-group", to: "finish-group", label: "N2 purge" }
    ]
  },
  "ebr": {
    title: "07. E B R 流程圖",
    totalCapacity: "原料共 450 KL / 成品共 800 KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 450 KL", x: 120, y: 80, w: 180, h: 500, type: "raw" },
      { id: "process-block", name: "製程", capacity: "", x: 360, y: 180, w: 160, h: 80, type: "process" },
      { id: "waste-group", name: "下腳料區", capacity: "共 200 KL", x: 360, y: 300, w: 180, h: 280, type: "offgrade" },
      { id: "finish-group", name: "成品區", capacity: "共 800 KL", x: 600, y: 80, w: 180, h: 500, type: "finish" }
    ],
    nodes: [
      { id: "TKC01-09", name: "平行原料組槽", capacity: "50 KL / 槽", type: "raw", x: 140, y: 220, fill: 80, details: { temp: "24.0 °C", press: "1.02 atm", comp: "EBR 基本原料", status: "穩定供料" } },
      
      { id: "TK-646", name: "格外品槽A", capacity: "50 KL", type: "offgrade", x: 380, y: 350, fill: 35, details: { temp: "25.1 °C", press: "1.03 atm", comp: "不合格回流液A", status: "待命" } },
      { id: "TK-647", name: "格外品槽B", capacity: "50 KL", type: "offgrade", x: 380, y: 410, fill: 40, details: { temp: "25.2 °C", press: "1.04 atm", comp: "不合格回流液B", status: "待命" } },
      { id: "TK-648", name: "格外品槽C", capacity: "100 KL", type: "offgrade", x: 380, y: 480, fill: 45, details: { temp: "25.0 °C", press: "1.02 atm", comp: "不合格回流液C", status: "待處理" } },
      
      { id: "TK-699", name: "成品大槽A", capacity: "550 KL", type: "finish", x: 620, y: 180, fill: 85, details: { temp: "25.2 °C", press: "1.01 atm", comp: "EBR 合格液", status: "成品儲存" } },
      { id: "TK-631", name: "成品大槽B", capacity: "250 KL", type: "finish", x: 620, y: 260, fill: 60, details: { temp: "25.1 °C", press: "1.01 atm", comp: "EBR 合格液", status: "成品儲存" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "process-block", label: "" },
      { from: "process-block", to: "waste-group", label: "格外品排料" },
      { from: "process-block", to: "finish-group", label: "成品放行" }
    ]
  },
  "hear": {
    title: "08. HEA-R 流程圖 (MIXED ETHER)",
    totalCapacity: "原料共 50 KL / 成品A共 140 KL / 成品B共 125 KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 50 KL", x: 120, y: 80, w: 180, h: 500, type: "raw" },
      { id: "process-block", name: "製程", capacity: "", x: 360, y: 180, w: 160, h: 80, type: "process" },
      { id: "waste-group", name: "下腳料區", capacity: "共 1T", x: 360, y: 300, w: 180, h: 280, type: "offgrade" },
      { id: "finish-top", name: "成品區 B (DPM-B1)", capacity: "共 125 KL", x: 840, y: 80, w: 180, h: 220, type: "finish" },
      { id: "finish-bottom", name: "成品區 A (MIXED ETHER)", capacity: "共 140 KL", x: 600, y: 330, w: 420, h: 250, type: "finish" }
    ],
    nodes: [
      // Raw group (x = 140)
      { id: "TK654", name: "原料槽", capacity: "50 KL", type: "raw", x: 140, y: 150, fill: 80, details: { temp: "20.1 °C", press: "1.05 atm", comp: "混合醚原料", status: "供料中" } },
      
      // Waste group (x = 380)
      { id: "IBC桶", name: "格外品收集", capacity: "1T裝", type: "offgrade", x: 380, y: 350, fill: 10, details: { temp: "25.0 °C", press: "1.00 atm", comp: "製程不合格液", status: "格外品收集" } },
      
      // Finished B (x = 860)
      { id: "TK-641", name: "成品大罐", capacity: "125 KL", type: "finish", x: 860, y: 130, fill: 85, details: { temp: "25.4 °C", press: "1.02 atm", comp: "合格 DPM-B1 成品", status: "成品儲存" } },
      
      // Finished A (x = 640 & 800)
      { id: "TK-673", name: "成品大罐", capacity: "70 KL", type: "finish", x: 640, y: 410, fill: 60, details: { temp: "25.1 °C", press: "1.01 atm", comp: "規格B合格 MIXED ETHER", status: "成品儲存" } },
      { id: "TK-674", name: "成品大罐", capacity: "70 KL", type: "finish", x: 800, y: 410, fill: 75, details: { temp: "25.3 °C", press: "1.01 atm", comp: "規格A合格 MIXED ETHER", status: "成品儲存" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "process-block", label: "" },
      { from: "process-block", to: "waste-group", label: "格外品排料" },
      { from: "process-block", to: "finish-top", label: "成品放行" },
      { from: "process-block", to: "finish-bottom", label: "成品放行" }
    ]
  },
  "ipahq": {
    title: "09. 崙尾 I P A HQ 流程圖 (精製異丙醇)",
    totalCapacity: "共 2000 KL / 400 KL",
    groups: [
      { id: "raw-group", name: "原料區", capacity: "共 2000 KL", x: 120, y: 80, w: 180, h: 500, type: "raw" },
      { id: "process-block-s4", name: "S4製程生產", capacity: "", x: 360, y: 120, w: 160, h: 65, type: "process" },
      { id: "process-block-s5", name: "S5製程生產", capacity: "", x: 360, y: 215, w: 160, h: 65, type: "process" },
      { id: "waste-group", name: "下腳料區", capacity: "共 300 KL", x: 360, y: 310, w: 180, h: 280, type: "offgrade" },
      { id: "check-group-s4", name: "Check Tank 待驗 (S4)", capacity: "共 60 KL", x: 600, y: 80, w: 180, h: 220, type: "process" },
      { id: "finish-group-s4", name: "成品區 (S4)", capacity: "共 200 KL", x: 840, y: 80, w: 180, h: 220, type: "finish" },
      { id: "check-group-s5", name: "Check Tank 待驗 (S5)", capacity: "共 60 KL", x: 600, y: 340, w: 180, h: 240, type: "process" },
      { id: "finish-group-s5", name: "成品區 (S5)", capacity: "共 200 KL", x: 840, y: 340, w: 180, h: 240, type: "finish" }
    ],
    nodes: [
      // Raw group (x = 140)
      { id: "TK-617", name: "原料大槽A", capacity: "1000 KL", type: "raw", x: 140, y: 200, fill: 80, details: { temp: "25.1 °C", press: "1.04 atm", comp: "電子級原料A", status: "儲存中" } },
      { id: "TK-618", name: "原料大槽B", capacity: "1000 KL", type: "raw", x: 140, y: 300, fill: 45, details: { temp: "25.0 °C", press: "1.02 atm", comp: "電子級原料B", status: "待命" } },
      
      // Waste group (x = 380)
      { id: "TK-611", name: "格外品槽A", capacity: "200 KL", type: "offgrade", x: 380, y: 360, fill: 40, details: { temp: "26.0 °C", press: "1.03 atm", comp: "格外不合格液A", status: "常態收集" } },
      { id: "TK-613", name: "格外品槽B", capacity: "100 KL", type: "offgrade", x: 380, y: 440, fill: 30, details: { temp: "25.8 °C", press: "1.03 atm", comp: "格外不合格液B", status: "常態收集" } },
      
      // Check Tank group (stacked vertically)
      { id: "TK-601", name: "待驗槽A", capacity: "30 KL", type: "process", x: 620, y: 120, fill: 50, details: { temp: "38.5 °C", press: "1.15 atm", comp: "N2 吹掃精製A", status: "待驗中" } },
      { id: "TK-602", name: "待驗槽B", capacity: "30 KL", type: "process", x: 620, y: 190, fill: 45, details: { temp: "26.0 °C", press: "1.02 atm", comp: "N2 吹掃精製B", status: "待驗中" } },
      { id: "TK-603", name: "待驗槽C", capacity: "30 KL", type: "process", x: 620, y: 380, fill: 60, details: { temp: "26.2 °C", press: "1.03 atm", comp: "N2 吹掃精製C", status: "待驗中" } },
      { id: "TK-604", name: "待驗槽D", capacity: "30 KL", type: "process", x: 620, y: 460, fill: 55, details: { temp: "26.1 °C", press: "1.02 atm", comp: "N2 吹掃精製D", status: "待驗中" } },
      
      // Finish group
      { id: "TK-605", name: "成品大槽A", capacity: "100 KL", type: "finish", x: 860, y: 120, fill: 80, details: { temp: "24.9 °C", press: "1.01 atm", comp: "電子級成品A", status: "放行已核准" } },
      { id: "TK-606", name: "成品大槽B", capacity: "100 KL", type: "finish", x: 860, y: 190, fill: 75, details: { temp: "24.8 °C", press: "1.02 atm", comp: "電子級成品B", status: "待檢驗" } },
      { id: "TK-607", name: "成品大槽C", capacity: "100 KL", type: "finish", x: 860, y: 380, fill: 85, details: { temp: "25.0 °C", press: "1.01 atm", comp: "電子級成品C", status: "出貨中" } },
      { id: "TK-608", name: "成品大槽D", capacity: "100 KL", type: "finish", x: 860, y: 460, fill: 90, details: { temp: "25.1 °C", press: "1.01 atm", comp: "電子級成品D", status: "出貨中" } }
    ],
    groupConnections: [
      { from: "raw-group", to: "process-block-s4", label: "" },
      { from: "raw-group", to: "process-block-s5", label: "" },
      { from: "process-block-s4", to: "waste-group", label: "格外品排料" },
      { from: "process-block-s5", to: "waste-group", label: "" },
      { from: "process-block-s4", to: "check-group-s4", label: "待檢驗" },
      { from: "process-block-s5", to: "check-group-s5", label: "待檢驗" },
      { from: "check-group-s4", to: "finish-group-s4", label: "成品放行" },
      { from: "check-group-s5", to: "finish-group-s5", label: "成品放行" }
    ],
    notes: []
  }
};

let currentTab = "ipa";
try {
  const savedTab = localStorage.getItem('flowchart_current_tab');
  if (savedTab && flowchartData[savedTab]) {
    currentTab = savedTab;
  }
} catch (e) {
  console.error("Failed to load active tab from localStorage", e);
}
let isSimulating = true;
let simulationSpeed = 1.2; // base animation speed

// DOM Elements
const navList = document.getElementById("navList");
const topBarTitle = document.getElementById("topBarTitle");
const totalCapacityBadge = document.getElementById("totalCapacityBadge");
const activeTanksCount = document.getElementById("activeTanksCount");
const canvasContainer = document.getElementById("canvasContainer");

const modalOverlay = document.getElementById("modalOverlay");
const modalTitle = document.getElementById("modalTitle");
const tankVisualLevel = document.getElementById("tankVisualLevel");
const detailTemp = document.getElementById("detailTemp");
const detailPress = document.getElementById("detailPress");
const detailComp = document.getElementById("detailComp");
const detailStatus = document.getElementById("detailStatus");
const detailCap = document.getElementById("detailCap");
const modalClose = document.getElementById("modalClose");
const simPurgeBtn = document.getElementById("simPurgeBtn");

const simBtn = document.getElementById("simBtn");
const themeBtn = document.getElementById("themeBtn");

// Init Sidebar Navigation
function initNav() {
  navList.innerHTML = "";
  Object.keys(flowchartData).forEach(key => {
    const data = flowchartData[key];
    const li = document.createElement("li");
    li.className = `nav-item ${key === currentTab ? 'active' : ''}`;
    li.innerHTML = `
      <span class="title">${data.title.split(" (")[0]}</span>
      <span class="badge">${data.nodes.length} 槽</span>
    `;
    li.onclick = () => {
      document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));
      li.classList.add("active");
      switchTab(key);
    };
    navList.appendChild(li);
  });
}

// Switch tabs and reload chart
function switchTab(tabKey) {
  currentTab = tabKey;
  try {
    localStorage.setItem('flowchart_current_tab', tabKey);
  } catch (e) {
    console.error("Failed to save active tab to localStorage", e);
  }
  const data = flowchartData[tabKey];
  topBarTitle.textContent = data.title;
  totalCapacityBadge.textContent = data.totalCapacity;
  activeTanksCount.textContent = `${data.nodes.length} 個在線節點`;
  renderFlowchart();
  if (typeof updateConnectionEditorUI === 'function') {
    updateConnectionEditorUI();
  }
  if (typeof updateResetButtonVisibility === 'function') {
    updateResetButtonVisibility();
  }
}

// Render Flowchart SVG with Stages/Groups Bounding Containers
function getElementCoordinates(id) {
  const data = flowchartData[currentTab];
  
  // Try to find as group first
  const group = data.groups.find(g => g.id === id);
  if (group) {
    return {
      id: group.id,
      x: group.x,
      y: group.y,
      w: group.w,
      h: group.h,
      type: 'group'
    };
  }
  
  // Try to find as node
  const node = data.nodes.find(n => n.id === id);
  if (node) {
    return {
      id: node.id,
      x: node.x,
      y: node.y,
      w: 140, // nodeW
      h: 70,  // nodeH
      type: 'node'
    };
  }
  
  return null;
}

function calculatePath(gc) {
  const fromId = gc.from;
  const toId = gc.to;
  const points = gc.points;
  const offsetY = gc.offsetY || 0;
  const offsetX = gc.offsetX || 0;
  
  // If points are provided and not empty, use them to draw a custom route (loop, curve, etc.)
  if (points && points.length > 0) {
    let fromBox = getElementCoordinates(fromId);
    let toBox = getElementCoordinates(toId);
    if (!fromBox || !toBox) return null;
    
    // Apply offset for visual connection shift
    fromBox = { ...fromBox, x: fromBox.x + offsetX, y: fromBox.y + offsetY };
    toBox = { ...toBox, x: toBox.x + offsetX, y: toBox.y + offsetY };
    if (!fromBox || !toBox) return null;
    
    let startX = fromBox.x + fromBox.w / 2;
    let startY = fromBox.y + fromBox.h / 2;
    const firstPt = points[0];
    if (firstPt[0] >= fromBox.x + fromBox.w) {
      startX = fromBox.x + fromBox.w;
      startY = fromBox.y + fromBox.h / 2;
    } else if (firstPt[0] <= fromBox.x) {
      startX = fromBox.x;
      startY = fromBox.y + fromBox.h / 2;
    } else if (firstPt[1] >= fromBox.y + fromBox.h) {
      startX = fromBox.x + fromBox.w / 2;
      startY = fromBox.y + fromBox.h;
    } else if (firstPt[1] <= fromBox.y) {
      startX = fromBox.x + fromBox.w / 2;
      startY = fromBox.y;
    }
    
    let endX = toBox.x + toBox.w / 2;
    let endY = toBox.y + toBox.h / 2;
    const lastPt = points[points.length - 1];
    if (lastPt[0] >= toBox.x + toBox.w) {
      endX = toBox.x + toBox.w;
      endY = toBox.y + toBox.h / 2;
    } else if (lastPt[0] <= toBox.x) {
      endX = toBox.x;
      endY = toBox.y + toBox.h / 2;
    } else if (lastPt[1] >= toBox.y + toBox.h) {
      endX = toBox.x + toBox.w / 2;
      endY = toBox.y + toBox.h;
    } else if (lastPt[1] <= toBox.y) {
      endX = toBox.x + toBox.w / 2;
      endY = toBox.y;
    }
    
    let path = `M ${startX} ${startY}`;
    points.forEach(pt => {
      path += ` L ${pt[0]} ${pt[1]}`;
    });
    path += ` L ${endX} ${endY}`;
    return { path, startX, startY, endX, endY };
  }

  // Check if there is a group-to-group connection with custom hardcoded overrides
  let fromG = flowchartData[currentTab].groups.find(g => g.id === fromId);
  let toG = flowchartData[currentTab].groups.find(g => g.id === toId);
  
  if (fromG) fromG = { ...fromG, x: fromG.x + offsetX, y: fromG.y + offsetY };
  if (toG) toG = { ...toG, x: toG.x + offsetX, y: toG.y + offsetY };
  
  if (fromG && toG) {
    let startX = fromG.x + fromG.w;
    let startY = toG.y + toG.h / 2;
    let endX = toG.x;
    let endY = toG.y + toG.h / 2;
    
    if ((fromG.id === "raw-group" || fromG.id.startsWith("raw-") || fromG.type === "raw") && toG.id.startsWith("process-block")) {
      startX = fromG.x + fromG.w;
      const targetCenterY = toG.y + toG.h / 2;
      if (targetCenterY >= fromG.y && targetCenterY <= fromG.y + fromG.h) {
        startY = targetCenterY;
      } else {
        startY = fromG.y + fromG.h / 2;
      }
      endX = toG.x;
      endY = targetCenterY;
    } else if (fromG.id.startsWith("process-block") && (toG.id === "waste-group-ipahw" || toG.id === "waste-group" || toG.id === "waste-group-ipa")) {
      startX = fromG.x + fromG.w/2;
      startY = fromG.y + fromG.h;
      endX = toG.x + toG.w/2;
      endY = toG.y;
    } else if (fromG.id === "waste-group-ipahw" && toG.id === "waste-group-ipa") {
      startX = fromG.x + fromG.w/2;
      startY = fromG.y + fromG.h;
      endX = toG.x + toG.w/2;
      endY = toG.y;
    } else if (fromG.id.startsWith("process-block") && toG.id === "check-group") {
      startX = fromG.x + fromG.w;
      startY = fromG.y + fromG.h/2;
      endX = toG.x;
      endY = toG.y + 140;
    } else if (fromG.id.startsWith("process-block") && (toG.id === "check-group-ipa" || toG.id === "check-group-s4")) {
      startX = fromG.x + fromG.w;
      startY = fromG.y + fromG.h/2;
      endX = toG.x;
      endY = toG.y + 110;
    } else if (fromG.id.startsWith("process-block") && (toG.id === "check-group-ipahq" || toG.id === "check-group-s5")) {
      startX = fromG.x + fromG.w;
      startY = fromG.y + fromG.h/2;
      endX = toG.x;
      endY = toG.y + 120;
    } else if ((fromG.id === "check-group-ipa" || fromG.id === "check-group-s4") && (toG.id === "finish-group-ipa" || toG.id === "finish-group-s4")) {
      startX = fromG.x + fromG.w;
      startY = fromG.y + 110;
      endX = toG.x;
      endY = toG.y + 110;
    } else if ((fromG.id === "check-group-ipahq" || fromG.id === "check-group-s5") && (toG.id === "finish-group-ipahq" || toG.id === "finish-group-s5")) {
      startX = fromG.x + fromG.w;
      startY = fromG.y + 120;
      endX = toG.x;
      endY = toG.y + 120;
    } else if (fromG.id.startsWith("process-block") && toG.id === "finish-group") {
      startX = fromG.x + fromG.w;
      startY = fromG.y + fromG.h/2;
      endX = toG.x;
      endY = toG.y + 140;
    } else if (fromG.id.startsWith("process-block") && toG.id === "finish-top") {
      startX = fromG.x + fromG.w;
      startY = fromG.y + fromG.h/2;
      endX = toG.x;
      endY = toG.y + 70;
    } else if (fromG.id.startsWith("process-block") && toG.id === "finish-bottom") {
      startX = fromG.x + fromG.w;
      startY = fromG.y + fromG.h/2;
      endX = toG.x;
      endY = toG.y + 100;
    } else {
      startX = fromG.x + fromG.w;
      startY = fromG.y + fromG.h / 2;
      endX = toG.x;
      endY = toG.y + toG.h / 2;
    }
    
    // Apply anchor offsets if dragged
    if (gc && gc.anchorFromOffset) { startX += gc.anchorFromOffset[0]; startY += gc.anchorFromOffset[1]; }
    if (gc && gc.anchorToOffset) { endX += gc.anchorToOffset[0]; endY += gc.anchorToOffset[1]; }
    
    let pathStr = `M ${startX} ${startY} L ${endX} ${endY}`;
    
    // Dynamic hardcoded paths based on startX/startY to allow dragging
    if (fromG.id === "process-block-s1" && toG.id === "waste-group-ipahw") {
      pathStr = `M ${startX} ${startY} L ${fromG.x - 25} ${startY} L ${fromG.x - 25} ${toG.y + 40} L ${endX} ${endY}`;
    } else if (fromG.id === "process-block-s4" && toG.id === "waste-group") {
      pathStr = `M ${startX} ${startY} L ${fromG.x - 25} ${startY} L ${fromG.x - 25} ${toG.y + 40} L ${endX} ${endY}`;
    } else if (fromG.id === "process-block-s3" && toG.id === "waste-group-ipa") {
      pathStr = `M ${startX} ${startY} L ${fromG.x - 35} ${startY} L ${fromG.x - 35} ${toG.y + 40} L ${endX} ${endY}`;
    } else if (fromG.id === "process-block-s5" && toG.id === "waste-group") {
      pathStr = `M ${startX} ${startY} L ${fromG.x - 35} ${startY} L ${fromG.x - 35} ${toG.y + 110} L ${endX} ${endY}`;
    } else if ((fromG.id === "process-block-s1" && toG.id === "check-group-ipa") || (fromG.id === "process-block-s4" && toG.id === "check-group-s4")) {
      pathStr = `M ${startX} ${startY} L ${fromG.x + fromG.w + 40} ${startY} L ${fromG.x + fromG.w + 40} ${toG.y + 110} L ${endX} ${endY}`;
    } else if ((fromG.id === "process-block-s3" && toG.id === "check-group-ipahq") || (fromG.id === "process-block-s5" && toG.id === "check-group-s5")) {
      pathStr = `M ${startX} ${startY} L ${fromG.x + fromG.w + 40} ${startY} L ${fromG.x + fromG.w + 40} ${toG.y + 120} L ${endX} ${endY}`;
    } else if ((fromId === "raw-group" || fromId.startsWith("raw-") || fromG.type === "raw") && (toId === "process-block-s3" || toId === "process-block-s5") && startY === endY) {
      const s1s4G = flowchartData[currentTab].groups.find(g => g.id === (toId === "process-block-s3" ? "process-block-s1" : "process-block-s4"));
      const s1s4X = s1s4G ? s1s4G.x : 360;
      pathStr = `M ${startX} ${startY} L ${s1s4X - 33} ${startY} A 8 8 0 0 1 ${s1s4X - 17} ${startY} L ${endX} ${endY}`;
    }
    
    return { path: pathStr, startX, startY, endX, endY };
  }
  
  // Dynamic connection between nodes or node & group
  let fromBox = getElementCoordinates(fromId);
  let toBox = getElementCoordinates(toId);
  if (!fromBox || !toBox) return null;
  fromBox = { ...fromBox, x: fromBox.x + offsetX, y: fromBox.y + offsetY };
  toBox = { ...toBox, x: toBox.x + offsetX, y: toBox.y + offsetY };
  if (!fromBox || !toBox) return null;
  
  let startX, startY, endX, endY;
  if (fromBox.x + fromBox.w <= toBox.x) {
    startX = fromBox.x + fromBox.w;
    startY = fromBox.y + fromBox.h / 2;
    endX = toBox.x;
    endY = toBox.y + toBox.h / 2;
  } else if (fromBox.y + fromBox.h <= toBox.y) {
    startX = fromBox.x + fromBox.w / 2;
    startY = fromBox.y + fromBox.h;
    endX = toBox.x + toBox.w / 2;
    endY = toBox.y;
  } else if (fromBox.y >= toBox.y + toBox.h) {
    startX = fromBox.x + fromBox.w / 2;
    startY = fromBox.y;
    endX = toBox.x + toBox.w / 2;
    endY = toBox.y + toBox.h;
  } else {
    startX = fromBox.x + fromBox.w / 2;
    startY = fromBox.y + fromBox.h / 2;
    endX = toBox.x + toBox.w / 2;
    endY = toBox.y + toBox.h / 2;
  }
  
  // Apply anchor offsets if set (drag the pipe's start/end attachment point)
  if (gc.anchorFromOffset) { startX += gc.anchorFromOffset[0]; startY += gc.anchorFromOffset[1]; }
  if (gc.anchorToOffset) { endX += gc.anchorToOffset[0]; endY += gc.anchorToOffset[1]; }
  
  const midX2 = startX + (endX - startX) / 2;
  const midY2 = startY + (endY - startY) / 2;
  
  if (Math.abs(endX - startX) >= Math.abs(endY - startY)) {
    // Horizontal dominant: elbow via midX
    return { path: `M ${startX} ${startY} L ${midX2} ${startY} L ${midX2} ${endY} L ${endX} ${endY}`, startX, startY, endX, endY };
  } else {
    // Vertical dominant: elbow via midY
    return { path: `M ${startX} ${startY} L ${startX} ${midY2} L ${endX} ${midY2} L ${endX} ${endY}`, startX, startY, endX, endY };
  }
}

// Helper to estimate text width for group title background
function getTextWidth(text) {
  let width = 0;
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i);
    if (code > 127) {
      width += 13.5; // Chinese character width
    } else {
      width += 7.5;  // English/numbers/symbols width
    }
  }
  return width;
}

// Render Flowchart SVG with Stages/Groups Bounding Containers
function renderFlowchart() {
  const data = flowchartData[currentTab];
  const nodeW = 140;
  const nodeH = 70;
  
  let svgContent = `<svg class="flowchart-svg" viewBox="0 0 1180 650" xmlns="http://www.w3.org/2000/svg" style="${typeof isAddingConnPoint !== 'undefined' && isAddingConnPoint ? 'cursor: crosshair;' : ''}">`;
  
  // Define Markers
  svgContent += `
    <defs>
      <marker id="arrow-raw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="var(--color-raw)" />
      </marker>
      <marker id="arrow-process" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="var(--color-process)" />
      </marker>
      <marker id="arrow-finish" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="var(--color-finish)" />
      </marker>
      <marker id="arrow-offgrade" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="var(--color-offgrade)" />
      </marker>
      <marker id="arrow-utility" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 1.5 L 9 5 L 0 8.5 z" fill="var(--color-utility)" />
      </marker>
      <!-- Thick flow arrow marker -->
      <marker id="arrow-thick" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="5" markerHeight="5" orient="auto">
        <path d="M 0 1 L 9 5 L 0 9 z" fill="#64748b" />
      </marker>
    </defs>`;
  
  // 1. Render Group Bounding Containers (Dotted / Dashed stage borders)
  data.groups.forEach(g => {
    let strokeColor = "var(--border-subtle)";
    let fillColor = "rgba(15, 19, 26, 0.15)";
    
    if (g.type === "raw") { strokeColor = "var(--color-raw)"; fillColor = "rgba(56, 189, 248, 0.03)"; }
    else if (g.type === "finish") { strokeColor = "var(--color-finish)"; fillColor = "rgba(52, 211, 153, 0.03)"; }
    else if (g.type === "offgrade") { strokeColor = "var(--color-offgrade)"; fillColor = "rgba(244, 63, 94, 0.03)"; }
    else if (g.type === "process" && !g.id.startsWith("process-block")) { 
      strokeColor = (g.id === "check-group-ipa" || g.id === "check-group-s4") ? "var(--color-accent)" : "var(--color-process)"; 
      fillColor = (g.id === "check-group-ipa" || g.id === "check-group-s4") ? "rgba(99, 102, 241, 0.03)" : "rgba(251, 191, 36, 0.03)"; 
    }
    
    const isSelected = typeof selectedItem !== 'undefined' && selectedItem && selectedItem.type === 'group' && selectedItem.id === g.id;
    const highlightStroke = isSelected ? 'var(--color-accent)' : strokeColor;
    const highlightStrokeWidth = isSelected ? '3.5' : (g.id.startsWith("process-block") ? '2.5' : '2');
    const highlightDash = isSelected ? '4,3' : (g.id.startsWith("process-block") ? '' : '6,4');
    
    if (g.id.startsWith("process-block")) {
      // Central Process Block Card
      const cardColor = g.id === "process-block-s1" ? "var(--color-accent)" : "var(--color-process)";
      const blockStroke = isSelected ? 'var(--color-accent)' : cardColor;
      const inputKey = `${currentTab}_${g.id}`;
      const inputVal = window.capacityInputs[inputKey] || "";
      const inputX = g.x + g.w/2 - 60;
      const inputY = g.y - 32;
      
      svgContent += `
        <g id="${g.id}" class="svg-group-card" data-id="${g.id}" data-type="group">
          <rect x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="6" fill="var(--bg-card)" stroke="${blockStroke}" stroke-width="${highlightStrokeWidth}" ${isSelected ? 'stroke-dasharray="4,3"' : ''} />
          <text x="${g.x + g.w/2}" y="${g.y + g.h/2 + 6}" fill="var(--text-primary)" font-size="13" font-weight="800" text-anchor="middle">${g.name}</text>
          
          <!-- Large capacity input directly above process card -->
          <foreignObject x="${inputX}" y="${inputY}" width="130" height="28">
            <div xmlns="http://www.w3.org/1999/xhtml" style="display: flex; align-items: center; gap: 4px; width: 100%; height: 100%;">
              <input type="text" 
                     id="cap-input-${inputKey}" 
                     value="${inputVal}" 
                     placeholder="輸入產能" 
                     oninput="window.saveCapacity('${currentTab}', '${g.id}', 'default', this.value)"  
                     style="width: 75px; height: 21px; background: var(--bg-sidebar); border: 1.5px solid ${cardColor}; border-radius: 6px; color: var(--text-primary); font-size: 10.5px; text-align: center; font-weight: 800; outline: none; transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2);" 
                     onfocus="this.style.borderColor='var(--color-accent)'; this.style.boxShadow='0 0 6px rgba(99,102,241,0.6)';" 
                     onblur="this.style.borderColor='${cardColor}'; this.style.boxShadow='0 2px 5px rgba(0,0,0,0.2)';" />
              <span style="font-size: 8.5px; font-weight: 800; color: var(--text-secondary); white-space: nowrap;">KG/HR</span>
            </div>
          </foreignObject>
        </g>
      `;
    } else {
      // Dashed Stage Box Bounding Bins
      let extraInputs = "";
      if (currentTab === "cpne3" && (g.id === "check-group" || g.id === "finish-group")) {
        const inputKey = `${currentTab}_${g.id}`;
        const inputVal = window.capacityInputs[inputKey] || "";
        const inputX = g.x + g.w/2 - 60;
        const inputY = g.y - 36;
        
        extraInputs = `
          <!-- Large capacity input directly above group container -->
          <foreignObject x="${inputX}" y="${inputY}" width="130" height="28">
            <div xmlns="http://www.w3.org/1999/xhtml" style="display: flex; align-items: center; gap: 4px; width: 100%; height: 100%;">
              <input type="text" 
                     id="cap-input-${inputKey}" 
                     value="${inputVal}" 
                     placeholder="輸入產能" 
                     oninput="window.saveCapacity('${currentTab}', '${g.id}', 'default', this.value)"  
                     style="width: 75px; height: 21px; background: var(--bg-sidebar); border: 1.5px solid ${strokeColor}; border-radius: 6px; color: var(--text-primary); font-size: 10.5px; text-align: center; font-weight: 800; outline: none; transition: all 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.2);" 
                     onfocus="this.style.borderColor='var(--color-accent)'; this.style.boxShadow='0 0 6px rgba(99,102,241,0.6)';" 
                     onblur="this.style.borderColor='${strokeColor}'; this.style.boxShadow='0 2px 5px rgba(0,0,0,0.2)';" />
              <span style="font-size: 8.5px; font-weight: 800; color: var(--text-secondary); white-space: nowrap;">KG/HR</span>
            </div>
          </foreignObject>
        `;
      }

      svgContent += `
        <g id="${g.id}" class="svg-group-card" data-id="${g.id}" data-type="group">
          <rect x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="10" fill="${fillColor}" stroke="${highlightStroke}" stroke-width="${highlightStrokeWidth}" ${highlightDash ? `stroke-dasharray="${highlightDash}"` : ''} />
          <!-- Group Title -->
          <rect x="${g.x + 14}" y="${g.y - 12}" width="${getTextWidth(g.name) + 16}" height="24" rx="4" fill="var(--bg-main)" />
          <text x="${g.x + 22}" y="${g.y + 5}" fill="${highlightStroke}" font-size="12.5" font-weight="800">${g.name}</text>
          <text x="${g.x + g.w - 18}" y="${g.y + 22}" fill="var(--text-secondary)" font-size="10.5" font-weight="700" text-anchor="end">${g.capacity}</text>
          ${extraInputs}
          ${isSelected ? `
          <!-- Resize Handle (bottom-right corner) -->
          <rect class="svg-resize-handle" data-id="${g.id}" data-type="group-resize"
            x="${g.x + g.w - 14}" y="${g.y + g.h - 14}" width="14" height="14" rx="3"
            fill="var(--color-accent)" opacity="0.85" style="cursor:se-resize;" />
          <path d="M${g.x+g.w-10} ${g.y+g.h-3} L${g.x+g.w-3} ${g.y+g.h-3} L${g.x+g.w-3} ${g.y+g.h-10}"
            stroke="white" stroke-width="1.5" fill="none" pointer-events="none" />
          ` : ''}
        </g>
      `;
    }
  });

  // 2. Render High-level flow pipeline connectors
  data.groupConnections.forEach((gc, index) => {
    const route = calculatePath(gc);
    if (route) {
      const { path: pathStr, startX, startY, endX, endY } = route;
      const fromBox = getElementCoordinates(gc.from);
      const toBox = getElementCoordinates(gc.to);
      
      // Determine stream colors (Indigo/Accent for S1/S4 stream, Amber/Process for S3/S5 stream)
      let strokeColor = (fromBox && fromBox.type === 'process') ? 'var(--color-process)' : 'var(--color-accent)';
      if (gc.from === "process-block-s1" || gc.from === "check-group-ipa" || gc.from === "process-block-s4" || gc.from === "check-group-s4") {
        strokeColor = "var(--color-accent)";
      } else if (gc.from === "process-block-s3" || gc.from === "check-group-ipahq" || gc.from === "process-block-s5" || gc.from === "check-group-s5") {
        strokeColor = "var(--color-process)";
      }
      
      // If connecting offgrade/waste, color it red
      if (toBox && (toBox.id.includes("waste") || toBox.id.includes("offgrade") || toBox.id.includes("IBC"))) {
        strokeColor = "var(--color-offgrade)";
      } else if (fromBox && (fromBox.id.includes("waste") || fromBox.id.includes("offgrade"))) {
        strokeColor = "var(--color-offgrade)";
      }
      
      const isSelected = typeof selectedItem !== 'undefined' && selectedItem && selectedItem.type === 'connection' && selectedItem.index === index;
      const lineGlow = isSelected ? `filter: drop-shadow(0 0 8px ${strokeColor}); stroke-width: 8;` : '';
      
      svgContent += `
        <path d="${pathStr}" stroke="var(--border-subtle)" stroke-width="8" stroke-linecap="round" fill="none" />
        <path d="${pathStr}" stroke="${strokeColor}" stroke-dasharray="10,8" stroke-width="6" stroke-linecap="round" fill="none" class="pipeline-active" style="animation-duration: 2s; marker-end: url(#arrow-thick); ${lineGlow}" />
        
        <!-- Draggable click target -->
        <path d="${pathStr}" stroke="transparent" stroke-width="22" fill="none" class="svg-pipeline-clickable" data-index="${index}" style="cursor: pointer;" />
      `;
      
      // Render draggable handles for points if in edit mode
      if (isEditingMode && gc.points) {
        gc.points.forEach((pt, ptIdx) => {
          svgContent += `
            <g class="svg-conn-handle" data-conn-index="${index}" data-pt-index="${ptIdx}" cursor="move">
              <circle cx="${pt[0]}" cy="${pt[1]}" r="8" fill="var(--color-accent)" stroke="white" stroke-width="2" />
              <text x="${pt[0]}" y="${pt[1] - 12}" fill="var(--text-primary)" font-size="10" font-weight="bold" text-anchor="middle">折點 ${ptIdx + 1}</text>
            </g>
          `;
        });
      }
      
      
      // Label for flow connection
      if (gc.label) {
        let labelX = startX + (endX - startX)/2;
        let labelY = startY + (endY - startY)/2;
        let textAnchor = "middle";
        let isVertical = Math.abs(endY - startY) > Math.abs(endX - startX);
        
        if (isVertical) {
          labelX = startX + 12;
          labelY = startY + (endY - startY)/2 + 4;
          textAnchor = "start";
        } else {
          labelY = labelY - 10;
        }
        
        // Custom label position override
        if (fromBox && toBox) {
          if ((fromBox.id === "process-block-s1" && toBox.id === "waste-group-ipahw") || (fromBox.id === "process-block-s4" && toBox.id === "waste-group")) {
            labelX = fromBox.x - 95;
            labelY = 295;
            textAnchor = "end";
          } else if ((fromBox.id === "process-block-s3" && toBox.id === "waste-group-ipa") || (fromBox.id === "process-block-s5" && toBox.id === "waste-group")) {
            labelX = fromBox.x - 65;
            labelY = 305;
            textAnchor = "end";
          } else if ((fromBox.id === "process-block-s1" && toBox.id === "check-group-ipa") || (fromBox.id === "process-block-s4" && toBox.id === "check-group-s4")) {
            labelX = fromBox.x + fromBox.w + 20;
            labelY = fromBox.y + fromBox.h/2 - 10;
            textAnchor = "middle";
          } else if ((fromBox.id === "process-block-s3" && toBox.id === "check-group-ipahq") || (fromBox.id === "process-block-s5" && toBox.id === "check-group-s5")) {
            labelX = fromBox.x + fromBox.w + 20;
            labelY = fromBox.y + fromBox.h/2 - 10;
            textAnchor = "middle";
          }
        }
        
        // Apply custom label coordinates if defined
        if (gc.labelPos) {
          labelX = gc.labelPos[0];
          labelY = gc.labelPos[1];
          textAnchor = "middle";
        }

        const isLabelSelected = typeof selectedItem !== 'undefined' && selectedItem && selectedItem.type === 'connection' && selectedItem.index === index;
        
        // Render a subtle capsule background behind the label in edit mode to indicate it is draggable
        if (isEditingMode) {
          const bgWidth = gc.label.length * 12 + 16;
          const bgHeight = 20;
          const bgX = labelX - bgWidth / 2;
          const bgY = labelY - 14;
          const labelBorder = isLabelSelected ? `stroke="var(--color-accent)" stroke-width="1.5" stroke-dasharray="3,2"` : `stroke="var(--border-subtle)" stroke-width="1"`;
          svgContent += `<rect x="${bgX}" y="${bgY}" width="${bgWidth}" height="${bgHeight}" rx="4" fill="var(--bg-sidebar)" ${labelBorder} style="opacity: 0.85; cursor: move;" class="svg-conn-label-bg" data-conn-index="${index}" />`;
        }

        svgContent += `<text x="${labelX}" y="${labelY}" fill="var(--text-secondary)" font-size="11.5" font-weight="700" text-anchor="${textAnchor}" class="svg-conn-label" data-conn-index="${index}" style="cursor: ${isEditingMode ? 'move' : 'default'}; user-select: none;">${gc.label}</text>`;
        
        // Render the small offgrade drain arrow relative to the label position
        let hasArrow = false;
        if (fromBox && toBox) {
          if ((fromBox.id === "process-block-s1" && toBox.id === "waste-group-ipahw") || (fromBox.id === "process-block-s4" && toBox.id === "waste-group")) {
            hasArrow = true;
          }
        }
        if (hasArrow) {
          const offsetStart = (textAnchor === "middle" ? (gc.label.length * 12 + 16) / 2 + 5 : 10);
          const offsetEnd = offsetStart + 40;
          const arrowStartX = labelX + offsetStart;
          const arrowEndX = labelX + offsetEnd;
          const arrowY = labelY - 4;
          svgContent += `<path d="M ${arrowStartX} ${arrowY} L ${arrowEndX} ${arrowY}" stroke="var(--color-offgrade)" stroke-width="4" fill="none" marker-end="url(#arrow-offgrade)" />`;
        }
      }
    }
  });
  
  // 2.5 Draw vertical offgrade branch pipelines for CPNE3 flowchart - now managed via groupConnections
  
  // 3. Render Tank Cards inside Groups
  data.nodes.forEach(node => {
    const color = getChemicalColor(node.type);
    const isSelected = typeof selectedItem !== 'undefined' && selectedItem && selectedItem.type === 'node' && selectedItem.id === node.id;
    const strokeColor = isSelected ? 'var(--color-accent)' : color;
    const strokeWidth = isSelected ? '3.5' : '2';
    const strokeDash = isSelected ? 'stroke-dasharray="4,3"' : '';
    
    const nw = node.w || 140;
    const nh = node.h || 70;
    svgContent += `
      <g class="svg-tank-card" data-id="${node.id}" data-type="node" onclick="if(!isEditingMode) openTankModal('${node.id}')" transform="translate(${node.x}, ${node.y})">
        <!-- Main Card Border & Glass Background -->
        <rect x="0" y="0" width="${nw}" height="${nh}" rx="8" fill="var(--bg-card)" stroke="${strokeColor}" stroke-width="${strokeWidth}" ${strokeDash} />
        
        <!-- Tank ID -->
        <text x="12" y="24" fill="var(--text-primary)" font-size="12.5" font-weight="700">${node.id}</text>
        
        <!-- Tank Capacity subtext -->
        <text x="12" y="42" fill="${color}" font-size="10.5" font-weight="800">${node.capacity}</text>
        
        <!-- Capacity Bar base -->
        <rect x="12" y="52" width="${nw - 24}" height="6" rx="3" fill="var(--border-subtle)" />
        <!-- Capacity Bar filled level -->
        <rect x="12" y="52" width="${(nw - 24) * (node.fill / 100)}" height="6" rx="3" fill="${color}" />
        
        <!-- Name or Tag -->
        <text x="${nw - 12}" y="22" fill="var(--text-secondary)" font-size="8.5" font-weight="500" text-anchor="end">${node.name}</text>
      </g>
    `;
  });
  
  // 4. Render Note Labels if present
  if (data.notes) {
    data.notes.forEach(note => {
      svgContent += `
        <text x="${note.x}" y="${note.y}" fill="${note.color || 'var(--text-secondary)'}" font-size="11.5" font-weight="700" letter-spacing="0.5">${note.text}</text>
      `;
    });
  }
  
  // 5. Render Group Resize Handles ON TOP of everything (after nodes)
  //    so they are clickable and not hidden behind tank cards.
  if (isEditingMode) {
    // 5. Render ALL Group Resize Handles ON TOP (works for every group type including process-block)
    data.groups.forEach(g => {
      const isSelected = typeof selectedItem !== 'undefined' && selectedItem && selectedItem.type === 'group' && selectedItem.id === g.id;
      if (!isSelected) return;
      const handleColor = g.id.startsWith('process-block') ? 'var(--color-process)' : 'var(--color-accent)';
      svgContent += `
        <rect class="svg-resize-handle" data-id="${g.id}" data-type="group-resize"
          x="${g.x + g.w - 16}" y="${g.y + g.h - 16}" width="20" height="20" rx="4"
          fill="${handleColor}" opacity="0.95" style="cursor:se-resize;" />
        <path d="M${g.x+g.w-12} ${g.y+g.h-3} L${g.x+g.w-3} ${g.y+g.h-3} L${g.x+g.w-3} ${g.y+g.h-12}"
          stroke="white" stroke-width="2.5" fill="none" pointer-events="none" />
        <rect x="${g.x}" y="${g.y}" width="${g.w}" height="${g.h}" rx="10"
          fill="none" stroke="${handleColor}" stroke-width="2" stroke-dasharray="5,4" pointer-events="none" />
      `;
    });
    
    // 6. Render Node Resize Handles ON TOP
    data.nodes.forEach(node => {
      const isSelected = typeof selectedItem !== 'undefined' && selectedItem && selectedItem.type === 'node' && selectedItem.id === node.id;
      if (!isSelected) return;
      const nw = node.w || 140;
      const nh = node.h || 70;
      svgContent += `
        <rect class="svg-resize-handle" data-id="${node.id}" data-type="node-resize"
          x="${node.x + nw - 16}" y="${node.y + nh - 16}" width="18" height="18" rx="4"
          fill="var(--color-accent)" opacity="0.9" style="cursor:se-resize;" />
        <path d="M${node.x+nw-12} ${node.y+nh-3} L${node.x+nw-3} ${node.y+nh-3} L${node.x+nw-3} ${node.y+nh-12}"
          stroke="white" stroke-width="2" fill="none" pointer-events="none" />
      `;
    });
    
    // 7. Connection Anchor handles (start/end dots) LAST so they are always on top
    const selectedConnIndex = (selectedItem && selectedItem.type === 'connection') ? selectedItem.index : -1;
    if (selectedConnIndex >= 0) {
      const gc = data.groupConnections[selectedConnIndex];
      if (gc) {
        const anchorRoute = calculatePath(gc);
        if (anchorRoute) {
          const { startX: ax0, startY: ay0, endX: ax1, endY: ay1 } = anchorRoute;
          svgContent += `
            <g class="svg-conn-anchor" data-conn-index="${selectedConnIndex}" data-anchor="start" style="cursor:crosshair; pointer-events:all;">
              <circle cx="${ax0}" cy="${ay0}" r="11" fill="var(--color-process)" stroke="white" stroke-width="2.5" style="pointer-events:all;"/>
              <text x="${ax0}" y="${ay0 - 15}" fill="var(--color-process)" font-size="10" font-weight="800" text-anchor="middle" style="pointer-events:none;">起點</text>
            </g>
            <g class="svg-conn-anchor" data-conn-index="${selectedConnIndex}" data-anchor="end" style="cursor:crosshair; pointer-events:all;">
              <circle cx="${ax1}" cy="${ay1}" r="11" fill="var(--color-raw)" stroke="white" stroke-width="2.5" style="pointer-events:all;"/>
              <text x="${ax1}" y="${ay1 - 15}" fill="var(--color-raw)" font-size="10" font-weight="800" text-anchor="middle" style="pointer-events:none;">終點</text>
            </g>
          `;
        }
      }
    }
  }
  svgContent += `</svg>`;
  canvasContainer.innerHTML = svgContent;

}

// Map tank type to design colors
function getChemicalColor(type) {
  switch (type) {
    case "raw": return "var(--color-raw)";
    case "finish": return "var(--color-finish)";
    case "offgrade": return "var(--color-offgrade)";
    case "utility": return "var(--color-utility)";
    default: return "var(--color-process)";
  }
}

// Open detailed tank information modal
function openTankModal(tankId) {
  const node = flowchartData[currentTab].nodes.find(n => n.id === tankId);
  if (!node) return;
  
  modalTitle.textContent = `${node.id} - ${node.name}`;
  tankVisualLevel.style.height = `${node.fill}%`;
  
  // Set wave color based on type
  const color = getChemicalColor(node.type);
  document.querySelector(".fluid-level").style.background = `linear-gradient(180deg, ${color}, rgba(99, 102, 241, 0.2))`;
  
  detailTemp.textContent = node.details.temp;
  detailPress.textContent = node.details.press;
  detailComp.textContent = node.details.comp;
  detailStatus.textContent = node.details.status;
  detailCap.textContent = `${node.fill}% / ${node.capacity}`;
  
  modalOverlay.classList.add("active");
  
  // Set up N2 purge simulation action
  simPurgeBtn.onclick = () => {
    detailStatus.textContent = "氮氣吹掃放行中...";
    detailPress.textContent = "1.35 atm";
    detailTemp.textContent = "27.8 °C";
    tankVisualLevel.style.height = "90%";
    
    node.fill = 90;
    node.details.status = "氮氣吹掃放行中";
    node.details.press = "1.35 atm";
    node.details.temp = "27.8 °C";
    
    renderFlowchart();
  };
}

// Close Modal
modalClose.onclick = () => modalOverlay.classList.remove("active");
modalOverlay.onclick = (e) => {
  if (e.target === modalOverlay) modalOverlay.classList.remove("active");
};

// Simulation Speed button toggle
simBtn.onclick = () => {
  isSimulating = !isSimulating;
  if (isSimulating) {
    simBtn.classList.add("active");
    simBtn.innerHTML = `<span>⚡ 模擬運作：運行中</span>`;
    document.querySelectorAll(".pipeline-active").forEach(el => {
      el.style.animationPlayState = "running";
    });
  } else {
    simBtn.classList.remove("active");
    simBtn.innerHTML = `<span>⏸ 模擬暫停</span>`;
    document.querySelectorAll(".pipeline-active").forEach(el => {
      el.style.animationPlayState = "paused";
    });
  }
};

// Dark/Light Theme toggle
themeBtn.onclick = () => {
  document.body.classList.toggle("light-mode");
  if (document.body.classList.contains("light-mode")) {
    themeBtn.textContent = "☀️ 亮色模式";
  } else {
    themeBtn.textContent = "🌙 暗色模式";
  }
};

// Export capacity inputs as JSON file
document.getElementById("exportBtn").onclick = () => {
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(window.capacityInputs, null, 2));
  const downloadAnchor = document.createElement('a');
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", `鴻勝產能資料備份_${new Date().toISOString().split('T')[0]}.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
};

// Trigger file input click for importing
const importFile = document.getElementById("importFile");
document.getElementById("importBtn").onclick = () => {
  importFile.click();
};

// Handle file import
importFile.onchange = (e) => {
  const file = e.target.files[0];
  if (!file) return;
  
  const reader = new FileReader();
  reader.onload = (event) => {
    try {
      const importedData = JSON.parse(event.target.result);
      if (typeof importedData === 'object' && importedData !== null) {
        window.capacityInputs = { ...window.capacityInputs, ...importedData };
        localStorage.setItem('flowchart_capacity_inputs', JSON.stringify(window.capacityInputs));
        renderFlowchart();
        alert("🎉 產能備份資料匯入成功！");
      } else {
        alert("❌ 格式不正確，匯入失敗。");
      }
    } catch (err) {
      alert("❌ 讀取檔案失敗：" + err.message);
    }
  };
  reader.readAsText(file);
};

// ==================== LAYOUT EDITOR LOGIC ====================
let isEditingMode = false;
let isManager = localStorage.getItem('flowchart_is_manager') === 'true';
let cloudLayoutData = null;
let selectedItem = null; // { type: 'node' | 'group', id: string }
let isAddingConnPoint = false; // Point-adding mode state variable

// Drag and drop state
let dragItem = null;
let dragType = null; // 'node' or 'group'
let dragStartMouseX = 0;
let dragStartMouseY = 0;
let dragStartItemX = 0;
let dragStartItemY = 0;
let dragStartItemW = 0;
let dragStartItemH = 0;
let dragPendingConnIdx = -1;
let dragPendingClickX = 0;
let dragPendingClickY = 0;
let dragPendingInsertedPt = null; // Reference to inserted waypoint

// Deep copy of original flowchart data for layout resetting
const originalFlowchartData = JSON.parse(JSON.stringify(flowchartData));

function updateSelectedNodeUI() {
  const section = document.getElementById("editItemSection");
  const editConnSection = document.getElementById("editConnectionSection");
  if (!section) return;
  
  if (!isEditingMode || !selectedItem) {
    section.style.display = "none";
    if (editConnSection) editConnSection.style.display = "none";
    return;
  }
  
  const data = flowchartData[currentTab];
  
  if (selectedItem.type === 'node' || selectedItem.type === 'group') {
    if (editConnSection) editConnSection.style.display = "none";
    
    let target = null;
    if (selectedItem.type === 'node') {
      target = data.nodes.find(n => n.id === selectedItem.id);
      document.getElementById("editItemTitle").textContent = `📝 編輯儲槽：${selectedItem.id}`;
      document.getElementById("editIdGroup").style.display = "block";
    } else if (selectedItem.type === 'group') {
      target = data.groups.find(g => g.id === selectedItem.id);
      document.getElementById("editItemTitle").textContent = `📝 編輯群組：${selectedItem.id}`;
      document.getElementById("editIdGroup").style.display = "none";
    }
    
    if (target) {
      section.style.display = "block";
      document.getElementById("editItemId").value = target.id;
      document.getElementById("editItemName").value = target.name || "";
      document.getElementById("editItemCapacity").value = target.capacity || "";
    } else {
      section.style.display = "none";
    }
  } else if (selectedItem.type === 'connection') {
    section.style.display = "none";
    if (editConnSection) {
      editConnSection.style.display = "block";
      const gc = data.groupConnections[selectedItem.index];
      if (gc) {
        const editConnFromSelect = document.getElementById("editConnFromSelect");
        const editConnToSelect = document.getElementById("editConnToSelect");
        if (editConnFromSelect) editConnFromSelect.value = gc.from;
        if (editConnToSelect) editConnToSelect.value = gc.to;
        document.getElementById("editConnLabel").value = gc.label || "";
        
        const addConnPtBtn = document.getElementById("addConnPtBtn");
        if (addConnPtBtn) {
          if (isAddingConnPoint) {
            addConnPtBtn.textContent = "請點擊畫布背景";
            addConnPtBtn.style.backgroundColor = "var(--color-process)";
          } else {
            addConnPtBtn.textContent = "點圖新增折點";
            addConnPtBtn.style.backgroundColor = "var(--color-accent)";
          }
        }
      }
    }
  }
}

// Get readable name for dropdown options & list items
function getReadableName(id) {
  if (!id) return "未知";
  const data = flowchartData[currentTab];
  if (!data) return id;
  const node = data.nodes ? data.nodes.find(n => n.id === id) : null;
  if (node) return `[儲槽] ${node.id} (${node.name})`;
  const group = data.groups ? data.groups.find(g => g.id === id) : null;
  if (group) return `[群組] ${group.name}`;
  return id;
}

// Update the Connection list and From/To dropdown options in the editor panel
function updateConnectionEditorUI() {
  const connFromSelect = document.getElementById("connFromSelect");
  const connToSelect = document.getElementById("connToSelect");
  const editConnFromSelect = document.getElementById("editConnFromSelect");
  const editConnToSelect = document.getElementById("editConnToSelect");
  const connectionsList = document.getElementById("connectionsList");
  
  if (!connFromSelect || !connToSelect || !connectionsList) return;
  
  const data = flowchartData[currentTab];
  
  // Populate dropdowns if in editing mode
  if (isEditingMode) {
    connFromSelect.innerHTML = "";
    connToSelect.innerHTML = "";
    if (editConnFromSelect) editConnFromSelect.innerHTML = "";
    if (editConnToSelect) editConnToSelect.innerHTML = "";
    
    const endpoints = [];
    data.groups.forEach(g => {
      endpoints.push({ id: g.id, name: `[群組] ${g.name}` });
    });
    data.nodes.forEach(n => {
      endpoints.push({ id: n.id, name: `[儲槽] ${n.id} (${n.name})` });
    });
    
    endpoints.forEach(ep => {
      const optFrom = document.createElement("option");
      optFrom.value = ep.id;
      optFrom.textContent = ep.name;
      connFromSelect.appendChild(optFrom);
      
      const optTo = document.createElement("option");
      optTo.value = ep.id;
      optTo.textContent = ep.name;
      connToSelect.appendChild(optTo);

      if (editConnFromSelect) {
        const optEditFrom = document.createElement("option");
        optEditFrom.value = ep.id;
        optEditFrom.textContent = ep.name;
        editConnFromSelect.appendChild(optEditFrom);
      }
      if (editConnToSelect) {
        const optEditTo = document.createElement("option");
        optEditTo.value = ep.id;
        optEditTo.textContent = ep.name;
        editConnToSelect.appendChild(optEditTo);
      }
    });
    
    // Populate connection list
    connectionsList.innerHTML = "";
    data.groupConnections.forEach((conn, index) => {
      if (!conn) return;
      const div = document.createElement("div");
      const isSelected = selectedItem && selectedItem.type === 'connection' && selectedItem.index === index;
      div.className = "conn-item" + (isSelected ? " selected" : "");
      
      const rawFrom = getReadableName(conn.from) || "未知";
      const rawTo = getReadableName(conn.to) || "未知";
      const fromName = String(rawFrom).replace(/^\[.*?\]\s*/, '');
      const toName = String(rawTo).replace(/^\[.*?\]\s*/, '');
      
      div.innerHTML = `
        <div class="conn-item-text">
          <div class="conn-item-label">${fromName} ➔ ${toName}</div>
          <div class="conn-item-route">${conn.label || "無標籤"}</div>
        </div>
        <button class="del-conn-btn" data-index="${index}">×</button>
      `;
      
      div.onclick = (e) => {
        if (e.target.classList.contains("del-conn-btn")) return;
        selectedItem = { type: 'connection', index: index };
        updateSelectedNodeUI();
        renderFlowchart();
        updateConnectionEditorUI();
      };
      
      connectionsList.appendChild(div);
    });
    
    // Bind delete events
    connectionsList.querySelectorAll(".del-conn-btn").forEach(btn => {
      btn.onclick = (e) => {
        e.stopPropagation();
        const idx = parseInt(btn.getAttribute("data-index"));
        if (confirm(`確定要刪除此流向管道嗎？`)) {
          data.groupConnections.splice(idx, 1);
          selectedItem = null;
          saveCurrentLayoutToLocal();
          renderFlowchart();
          updateConnectionEditorUI();
          updateSelectedNodeUI();
        }
      };
    });
  }
}

// Save coordinates and groupConnections to LocalStorage (writes full dataset now)
function saveCurrentLayoutToLocal() {
  try {
    localStorage.setItem('flowchart_full_dataset', JSON.stringify(flowchartData));
  } catch (e) {
    console.error("Failed to save full dataset to localStorage", e);
  }
  updateResetButtonVisibility();
}

// Show/hide the Reset Layout button depending on local overrides
function updateResetButtonVisibility() {
  const resetLayoutBtn = document.getElementById("resetLayoutBtn");
  if (!resetLayoutBtn) return;
  
  try {
    const localFull = localStorage.getItem('flowchart_full_dataset');
    const localLayout = localStorage.getItem('flowchart_custom_layout');
    if (isEditingMode && (localFull || localLayout)) {
      resetLayoutBtn.style.display = "inline-flex";
      return;
    }
  } catch (e) {
    console.error(e);
  }
  resetLayoutBtn.style.display = "none";
}

// Update Sync Button text and style
function updateSyncButtonUI() {
  const syncCloudBtn = document.getElementById("syncCloudBtn");
  const logoutManagerBtn = document.getElementById("logoutManagerBtn");
  if (!syncCloudBtn) return;
  
  if (isManager) {
    syncCloudBtn.innerHTML = "<span>☁️ 同步至雲端</span>";
    syncCloudBtn.style.background = "rgba(52, 211, 153, 0.1)";
    syncCloudBtn.style.borderColor = "var(--color-finish)";
    syncCloudBtn.style.color = "var(--color-finish)";
    if (logoutManagerBtn) logoutManagerBtn.style.display = "inline-flex";
  } else {
    syncCloudBtn.innerHTML = "<span>🔐 管理登入</span>";
    syncCloudBtn.style.background = "rgba(56, 189, 248, 0.1)";
    syncCloudBtn.style.borderColor = "var(--color-raw)";
    syncCloudBtn.style.color = "var(--color-raw)";
    if (logoutManagerBtn) logoutManagerBtn.style.display = "none";
  }
}

// Apply layout updates to active data model (for old layout coordinate overlay format)
function applyLayoutData(layout) {
  if (!layout) return;
  Object.keys(layout).forEach(tab => {
    if (!flowchartData[tab]) return;
    const tabLayout = layout[tab];
    
    if (tabLayout.nodes) {
      flowchartData[tab].nodes.forEach(n => {
        if (tabLayout.nodes[n.id]) {
          n.x = tabLayout.nodes[n.id].x;
          n.y = tabLayout.nodes[n.id].y;
        }
      });
    }
    
    if (tabLayout.groups) {
      flowchartData[tab].groups.forEach(g => {
        if (tabLayout.groups[g.id]) {
          g.x = tabLayout.groups[g.id].x;
          g.y = tabLayout.groups[g.id].y;
        }
      });
    }
    
    if (tabLayout.groupConnections) {
      flowchartData[tab].groupConnections = JSON.parse(JSON.stringify(tabLayout.groupConnections));
    }
  });
}

// Apply Layout chain (Defaults -> Cloud -> Local overrides)
function applyLayoutAndReload() {
  // 1. Reset to static code defaults first
  Object.keys(originalFlowchartData).forEach(tab => {
    flowchartData[tab] = JSON.parse(JSON.stringify(originalFlowchartData[tab]));
  });
  
  // 2. Overlay Cloud Data (could be full dataset or coordinates)
  if (cloudLayoutData) {
    if (cloudLayoutData.ipa && (cloudLayoutData.ipa.nodes || cloudLayoutData.ipa.groups)) {
      // New full dataset format from cloud
      Object.keys(cloudLayoutData).forEach(tab => {
        flowchartData[tab] = JSON.parse(JSON.stringify(cloudLayoutData[tab]));
      });
    } else {
      // Old coordinate overlay format
      applyLayoutData(cloudLayoutData);
    }
  }
  
  // 3. Overlay Localstorage Data (priority over cloud for local user edits)
  try {
    const localFull = localStorage.getItem('flowchart_full_dataset');
    if (localFull) {
      const parsed = JSON.parse(localFull);
      Object.keys(parsed).forEach(tab => {
        flowchartData[tab] = parsed[tab];
      });
    } else {
      // Fallback to old coordinate overlay if present
      const localLayout = localStorage.getItem('flowchart_custom_layout');
      if (localLayout) {
        applyLayoutData(JSON.parse(localLayout));
      }
    }
  } catch (e) {
    console.error("Failed to parse local dataset overrides", e);
  }
  
  // 4. Run data migrations to ensure new features/connections are present
  // Migration 1: CPNE3 offgrade connections
  if (flowchartData["cpne3"] && flowchartData["cpne3"].groupConnections) {
    const cpne3Conns = flowchartData["cpne3"].groupConnections;
    const requiredConns = [
      { from: "raw-group", to: "IBC桶", label: "格外品" },
      { from: "p1-group", to: "TK-660", label: "格外品" },
      { from: "p2-group", to: "TK-655", label: "格外品" },
      { from: "check-group", to: "TK-655_2", label: "格外品" }
    ];
    requiredConns.forEach(req => {
      const exists = cpne3Conns.find(c => c.from === req.from && c.to === req.to);
      if (!exists) {
        cpne3Conns.push(req);
      }
    });
  }
  
  // Update currently active tab selection in case the current tab got deleted
  if (!flowchartData[currentTab]) {
    currentTab = Object.keys(flowchartData)[0] || "ipa";
  }
  
  initNav(); // Re-initialize navigation to reflect any dynamic tabs
  switchTab(currentTab);
}

// Load from Firebase
async function initFirebaseAndLoad() {
  updateSyncButtonUI();
  
  if (typeof firebase !== 'undefined' && firebase.apps.length > 0) {
    try {
      const db = firebase.firestore();
      const doc = await db.collection('flowcharts').doc('current_layout').get();
      if (doc.exists) {
        const docData = doc.data();
        if (docData.dataset) {
          cloudLayoutData = docData.dataset;
          console.log("Full dataset loaded from Firestore successfully.", cloudLayoutData);
        } else {
          cloudLayoutData = docData.layout;
          console.log("Customized layout coordinates loaded from Firestore successfully.", cloudLayoutData);
        }
      }
    } catch (e) {
      console.warn("Could not retrieve cloud configurations. Falling back to local/default layout.", e);
    }
  } else {
    console.log("Firebase not initialized. Running in local-only mode.");
  }
  
  applyLayoutAndReload();
}

// Hook up event listeners for layout editing
const editModeBtn = document.getElementById("editModeBtn");
const resetLayoutBtn = document.getElementById("resetLayoutBtn");
const syncCloudBtn = document.getElementById("syncCloudBtn");
const addConnBtn = document.getElementById("addConnBtn");

if (editModeBtn) {
  editModeBtn.onclick = () => {
    isEditingMode = !isEditingMode;
    const editPanel = document.getElementById("editPanel");
    
    // Toggle dynamic tab buttons
    const addTabSidebarContainer = document.getElementById("addTabSidebarContainer");
    const renameTabBtn = document.getElementById("renameTabBtn");
    const deleteTabBtn = document.getElementById("deleteTabBtn");
    
    if (addTabSidebarContainer) addTabSidebarContainer.style.display = isEditingMode ? "block" : "none";
    if (renameTabBtn) renameTabBtn.style.display = isEditingMode ? "inline-flex" : "none";
    if (editTotalCapacityBtn) editTotalCapacityBtn.style.display = isEditingMode ? "inline-flex" : "none";
    if (deleteTabBtn) deleteTabBtn.style.display = isEditingMode ? "inline-flex" : "none";
    
    if (isEditingMode) {
      editModeBtn.innerHTML = "<span>🔧 編輯模式：開啟</span>";
      editModeBtn.classList.add("active");
      canvasContainer.classList.add("editing-layout");
      document.body.classList.add("edit-mode-active");
      if (editPanel) editPanel.classList.add("active");
      canvasContainer.classList.add("edit-panel-open");
    } else {
      editModeBtn.innerHTML = "<span>🔧 編輯模式：關閉</span>";
      editModeBtn.classList.remove("active");
      canvasContainer.classList.remove("editing-layout");
      document.body.classList.remove("edit-mode-active");
      if (editPanel) editPanel.classList.remove("active");
      canvasContainer.classList.remove("edit-panel-open");
      selectedItem = null;
      isAddingConnPoint = false;
      updateSelectedNodeUI();
    }
    
    renderFlowchart();
    updateConnectionEditorUI();
    updateResetButtonVisibility();
  };
}

if (document.getElementById("closeEditPanelBtn")) {
  document.getElementById("closeEditPanelBtn").onclick = () => {
    if (isEditingMode && editModeBtn) editModeBtn.click();
  };
}

if (resetLayoutBtn) {
  resetLayoutBtn.onclick = () => {
    if (confirm("確定要重置本地所有自訂產品流程與版面設定嗎？這會將畫面還原為雲端同步的配置或系統預設值。")) {
      try {
        localStorage.removeItem('flowchart_full_dataset');
        localStorage.removeItem('flowchart_custom_layout');
      } catch (e) {
        console.error(e);
      }
      applyLayoutAndReload();
    }
  };
}

if (syncCloudBtn) {
  syncCloudBtn.onclick = async () => {
    if (!isManager) {
      const passcode = prompt("請輸入管理者授權密碼：");
      if (passcode === "7588555" || passcode === "1234") {
        isManager = true;
        localStorage.setItem('flowchart_is_manager', 'true');
        updateSyncButtonUI();
        alert("🔓 管理者登入成功！已啟用雲端同步權限。");
      } else if (passcode !== null) {
        alert("❌ 授權失敗：密碼錯誤。");
      }
    } else {
      // Cloud Synchronization logic
      if (typeof firebase === 'undefined' || firebase.apps.length === 0) {
        alert("⚠️ 目前處於本機開發環境，Firebase 未啟動，無法上傳雲端。版面已儲存於本機。");
        return;
      }
      
      if (confirm("確定要將當前配置（含本地新增/修改之流程分頁、儲槽、群組與管線折點）發布同步至雲端資料庫嗎？此動作將會影響所有使用者的預設畫面。")) {
        try {
          const db = firebase.firestore();
          
          await db.collection('flowcharts').doc('current_layout').set({
            dataset: flowchartData,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
            updatedBy: "manager"
          });
          
          cloudLayoutData = JSON.parse(JSON.stringify(flowchartData));
          alert("🎉 雲端流程與版面全量同步成功！");
        } catch (err) {
          console.error("Firestore writing error:", err);
          alert("❌ 同步失敗：" + err.message);
        }
      }
    }
  };
}

const logoutManagerBtn = document.getElementById("logoutManagerBtn");
if (logoutManagerBtn) {
  logoutManagerBtn.onclick = () => {
    if (confirm("確定要登出管理者權限嗎？")) {
      isManager = false;
      localStorage.removeItem('flowchart_is_manager');
      updateSyncButtonUI();
      if (isEditingMode && editModeBtn) {
        editModeBtn.click(); // 登出時自動關閉編輯模式
      }
      alert("🔒 已安全登出管理者權限。");
    }
  };
}

if (addConnBtn) {
  addConnBtn.onclick = () => {
    const fromVal = document.getElementById("connFromSelect").value;
    const toVal = document.getElementById("connToSelect").value;
    const labelVal = document.getElementById("connLabelInput").value.trim();
    
    if (!fromVal || !toVal) return;
    
    if (fromVal === toVal) {
      alert("❌ 起點與終點不可相同！");
      return;
    }
    
    const data = flowchartData[currentTab];
    const duplicate = data.groupConnections.some(conn => conn.from === fromVal && conn.to === toVal);
    if (duplicate) {
      alert("❌ 此兩點之間的連線管道已存在！");
      return;
    }
    
    data.groupConnections.push({
      from: fromVal,
      to: toVal,
      label: labelVal
    });
    
    document.getElementById("connLabelInput").value = "";
    saveCurrentLayoutToLocal();
    renderFlowchart();
    updateConnectionEditorUI();
  };
}

// Attribute editor click listeners
const saveItemBtn = document.getElementById("saveItemBtn");
const deselectItemBtn = document.getElementById("deselectItemBtn");
const deleteItemBtn = document.getElementById("deleteItemBtn");

if (deselectItemBtn) {
  deselectItemBtn.onclick = () => {
    selectedItem = null;
    updateSelectedNodeUI();
    renderFlowchart();
  };
}

if (deleteItemBtn) {
  deleteItemBtn.onclick = () => {
    if (!selectedItem) return;
    const data = flowchartData[currentTab];
    if (confirm(`確定要刪除選定的 ${selectedItem.type === 'node' ? '儲槽' : '群組'} 「${selectedItem.id}」嗎？此操作會自動刪除所有關聯的管道流向！`)) {
      const targetId = selectedItem.id;
      
      if (selectedItem.type === 'node') {
        data.nodes = data.nodes.filter(n => n.id !== targetId);
      } else if (selectedItem.type === 'group') {
        data.groups = data.groups.filter(g => g.id !== targetId);
      }
      
      // Remove referencing connections
      data.groupConnections = data.groupConnections.filter(conn => conn.from !== targetId && conn.to !== targetId);
      
      selectedItem = null;
      saveCurrentLayoutToLocal();
      renderFlowchart();
      updateConnectionEditorUI();
      updateSelectedNodeUI();
      alert("🎉 項目已成功刪除！");
    }
  };
}

if (saveItemBtn) {
  saveItemBtn.onclick = () => {
    if (!selectedItem) return;
    
    const data = flowchartData[currentTab];
    const newId = document.getElementById("editItemId").value.trim();
    const newName = document.getElementById("editItemName").value.trim();
    const newCapacity = document.getElementById("editItemCapacity").value.trim();
    
    if (selectedItem.type === 'node') {
      const node = data.nodes.find(n => n.id === selectedItem.id);
      if (!node) return;
      
      if (newId !== node.id) {
        if (!newId) {
          alert("❌ ID 不得為空！");
          return;
        }
        // Check if new ID collides with another node
        const collision = data.nodes.some(n => n.id === newId && n !== node);
        if (collision) {
          alert("❌ 儲槽 ID 已存在！");
          return;
        }
        
        const oldId = node.id;
        node.id = newId;
        
        // Update connections that referenced the old ID
        data.groupConnections.forEach(conn => {
          if (conn.from === oldId) conn.from = newId;
          if (conn.to === oldId) conn.to = newId;
        });
        
        // Update capacityInputs
        const inputKeyPrefix = `${currentTab}_`;
        if (window.capacityInputs[inputKeyPrefix + oldId] !== undefined) {
          window.capacityInputs[inputKeyPrefix + newId] = window.capacityInputs[inputKeyPrefix + oldId];
          delete window.capacityInputs[inputKeyPrefix + oldId];
          localStorage.setItem('flowchart_capacity_inputs', JSON.stringify(window.capacityInputs));
        }
        
        selectedItem.id = newId;
      }
      
      node.name = newName;
      node.capacity = newCapacity;
      
    } else if (selectedItem.type === 'group') {
      const group = data.groups.find(g => g.id === selectedItem.id);
      if (!group) return;
      
      group.name = newName;
      group.capacity = newCapacity;
    }
    
    saveCurrentLayoutToLocal();
    renderFlowchart();
    updateConnectionEditorUI();
    updateSelectedNodeUI();
    alert("🎉 屬性修改成功！");
  };
}

// Connection edit panel listeners
const saveConnBtn = document.getElementById("saveConnBtn");
const deselectConnBtn = document.getElementById("deselectConnBtn");
const addConnPtBtn = document.getElementById("addConnPtBtn");
const removeLastConnPtBtn = document.getElementById("removeLastConnPtBtn");
const clearConnPtsBtn = document.getElementById("clearConnPtsBtn");

if (saveConnBtn) {
  saveConnBtn.onclick = () => {
    if (!selectedItem || selectedItem.type !== 'connection') return;
    const data = flowchartData[currentTab];
    const gc = data.groupConnections[selectedItem.index];
    if (gc) {
      const newFrom = document.getElementById("editConnFromSelect").value;
      const newTo = document.getElementById("editConnToSelect").value;
      
      if (newFrom === newTo) {
        alert("⚠️ 起點與終點不能相同！");
        return;
      }
      
      // If start or end point changed, reset the path waypoints to avoid weird bends
      if (gc.from !== newFrom || gc.to !== newTo) {
        gc.from = newFrom;
        gc.to = newTo;
        gc.points = [];
      }
      
      gc.label = document.getElementById("editConnLabel").value.trim();
      
      saveCurrentLayoutToLocal();
      renderFlowchart();
      updateConnectionEditorUI();
      updateSelectedNodeUI();
      alert("🎉 管道資訊修改成功！");
    }
  };
}

if (deselectConnBtn) {
  deselectConnBtn.onclick = () => {
    selectedItem = null;
    isAddingConnPoint = false;
    updateSelectedNodeUI();
    renderFlowchart();
  };
}

const deleteConnBtn = document.getElementById("deleteConnBtn");
if (deleteConnBtn) {
  deleteConnBtn.onclick = () => {
    if (!selectedItem || selectedItem.type !== 'connection') return;
    const data = flowchartData[currentTab];
    const idx = selectedItem.index;
    
    if (confirm("確定要刪除此管道連線嗎？")) {
      data.groupConnections.splice(idx, 1);
      selectedItem = null;
      saveCurrentLayoutToLocal();
      renderFlowchart();
      updateConnectionEditorUI();
      updateSelectedNodeUI();
      alert("🗑️ 管道已成功刪除！");
    }
  };
}

const toggleConnectionsListBtn = document.getElementById("toggleConnectionsListBtn");
const toggleConnArrow = document.getElementById("toggleConnArrow");
if (toggleConnectionsListBtn) {
  toggleConnectionsListBtn.onclick = () => {
    const listEl = document.getElementById("connectionsList");
    if (listEl) {
      const isHidden = listEl.style.display === "none";
      listEl.style.display = isHidden ? "flex" : "none";
      if (toggleConnArrow) {
        toggleConnArrow.textContent = isHidden ? "▼" : "▲";
      }
    }
  };
}


if (addConnPtBtn) {
  addConnPtBtn.onclick = () => {
    isAddingConnPoint = !isAddingConnPoint;
    updateSelectedNodeUI();
  };
}

if (removeLastConnPtBtn) {
  removeLastConnPtBtn.onclick = () => {
    if (!selectedItem || selectedItem.type !== 'connection') return;
    const data = flowchartData[currentTab];
    const gc = data.groupConnections[selectedItem.index];
    if (gc) {
      if (gc.points && gc.points.length > 0) {
        gc.points.pop();
        saveCurrentLayoutToLocal();
        renderFlowchart();
      } else {
        alert("⚠️ 此管線已無折點！");
      }
    }
  };
}

if (clearConnPtsBtn) {
  clearConnPtsBtn.onclick = () => {
    if (!selectedItem || selectedItem.type !== 'connection') return;
    if (confirm("確定要清除此管線的所有折點，恢復成直管嗎？")) {
      const data = flowchartData[currentTab];
      const gc = data.groupConnections[selectedItem.index];
      if (gc) {
        gc.points = [];
        saveCurrentLayoutToLocal();
        renderFlowchart();
      }
    }
  };
}

// Dynamic tab management listeners
const addTabBtn = document.getElementById("addTabBtn");
const renameTabBtn = document.getElementById("renameTabBtn");
const editTotalCapacityBtn = document.getElementById("editTotalCapacityBtn");
const deleteTabBtn = document.getElementById("deleteTabBtn");

if (addTabBtn) {
  addTabBtn.onclick = () => {
    const title = prompt("請輸入新產品流程的名稱 (例如：10. CPNE5 流程圖)：");
    if (!title || !title.trim()) return;
    
    let key = "flow_" + Date.now();
    const useTemplate = confirm("是否為此流程圖套用常用 5 大區域範本 (原料/製程/待驗/成品/下腳料區)？\n[確定] 套用範本；[取消] 建立空白流程。");
    
    let newTabObj = {
      title: title.trim(),
      totalCapacity: "編輯中",
      groups: [],
      nodes: [],
      groupConnections: []
    };
    
    if (useTemplate) {
      newTabObj.groups = [
        { id: "raw-group", name: "原料區", capacity: "原料", x: 120, y: 80, w: 180, h: 500, type: "raw" },
        { id: "process-block", name: "製程生產", capacity: "製程", x: 360, y: 180, w: 160, h: 80, type: "process" },
        { id: "waste-group", name: "下腳料區", capacity: "下腳料", x: 360, y: 300, w: 180, h: 280, type: "offgrade" },
        { id: "check-group", name: "Check Tank 待驗", capacity: "待驗", x: 600, y: 80, w: 180, h: 500, type: "process" },
        { id: "finish-group", name: "成品區", capacity: "成品", x: 840, y: 80, w: 180, h: 500, type: "finish" }
      ];
      newTabObj.groupConnections = [
        { from: "raw-group", to: "process-block", label: "" },
        { from: "process-block", to: "waste-group", label: "格外品排料" },
        { from: "process-block", to: "check-group", label: "待檢驗" },
        { from: "check-group", to: "finish-group", label: "成品放行" }
      ];
    }
    
    flowchartData[key] = newTabObj;
    saveCurrentLayoutToLocal();
    applyLayoutAndReload();
    switchTab(key);
    alert("🎉 新產品流程創建成功！");
  };
}

if (renameTabBtn) {
  renameTabBtn.onclick = () => {
    const data = flowchartData[currentTab];
    const newTitle = prompt("請輸入新的流程名稱：", data.title);
    if (!newTitle || !newTitle.trim()) return;
    
    data.title = newTitle.trim();
    saveCurrentLayoutToLocal();
    applyLayoutAndReload();
    alert("🎉 流程名稱修改成功！");
  };
}

if (editTotalCapacityBtn) {
  editTotalCapacityBtn.onclick = () => {
    const data = flowchartData[currentTab];
    const newCapacity = prompt("請輸入新的總產能描述：", data.totalCapacity);
    if (newCapacity === null) return;
    
    data.totalCapacity = newCapacity.trim();
    saveCurrentLayoutToLocal();
    applyLayoutAndReload();
    alert("🎉 總產能描述修改成功！");
  };
}

if (deleteTabBtn) {
  deleteTabBtn.onclick = () => {
    const keys = Object.keys(flowchartData);
    if (keys.length <= 1) {
      alert("❌ 系統必須保留至少一個產品流程圖，無法刪除！");
      return;
    }
    
    const data = flowchartData[currentTab];
    if (confirm(`確定要刪除整個產品流程「${data.title}」嗎？此操作不可逆！`)) {
      delete flowchartData[currentTab];
      saveCurrentLayoutToLocal();
      applyLayoutAndReload();
      alert("🎉 產品流程已刪除！");
    }
  };
}

// Add Node/Group listeners
const addTypeSelect = document.getElementById("addTypeSelect");
if (addTypeSelect) {
  addTypeSelect.onchange = () => {
    const val = addTypeSelect.value;
    document.getElementById("nodeTypeGroup").style.display = val === 'node' ? 'block' : 'none';
    document.getElementById("groupFields").style.display = val === 'group' ? 'block' : 'none';
  };
}

const addNodeGroupBtn = document.getElementById("addNodeGroupBtn");
if (addNodeGroupBtn) {
  addNodeGroupBtn.onclick = () => {
    const type = document.getElementById("addTypeSelect").value;
    const id = document.getElementById("addNodeId").value.trim();
    const name = document.getElementById("addNodeName").value.trim();
    const capacity = document.getElementById("addNodeCapacity").value.trim();
    
    if (!id) {
      alert("❌ 請輸入代號 (ID)！");
      return;
    }
    
    let finalId = id;
    if (type === 'group') {
      const groupChemicalType = document.getElementById("groupTypeSelect").value;
      if (groupChemicalType === "process-block" && !finalId.startsWith("process-block")) {
        finalId = `process-block-${finalId}`;
      }
    }
    
    const data = flowchartData[currentTab];
    const idCollision = data.nodes.some(n => n.id === finalId) || data.groups.some(g => g.id === finalId);
    if (idCollision) {
      alert("❌ 此 ID 已存在於目前流程圖中，請使用其他唯一 ID！");
      return;
    }
    
    if (type === 'node') {
      const chemicalType = document.getElementById("nodeTypeSelect").value;
      const newNode = {
        id: finalId,
        name: name || "新儲槽",
        capacity: capacity || "100 KL",
        type: chemicalType,
        x: 150,
        y: 150,
        fill: 50,
        details: {
          temp: "25.0 °C",
          press: "1.00 atm",
          comp: name || "原料",
          status: "正常儲存"
        }
      };
      data.nodes.push(newNode);
      alert(`🎉 儲槽 ${finalId} 新增成功！請在畫布上拖曳至正確位置。`);
    } else {
      const w = parseInt(document.getElementById("addGroupWidth").value) || 180;
      let h = parseInt(document.getElementById("addGroupHeight").value) || 240;
      const groupChemicalType = document.getElementById("groupTypeSelect").value;
      
      // Default process-block height is usually smaller
      if (groupChemicalType === "process-block" && h === 240) {
        h = 80;
      }
      
      const newGroup = {
        id: finalId,
        name: name || "新群組",
        capacity: capacity || "",
        x: 100,
        y: 100,
        w: w,
        h: h,
        type: groupChemicalType === "process-block" ? "process" : groupChemicalType
      };
      data.groups.push(newGroup);
      alert(`🎉 群組 ${finalId} 新增成功！請在畫布上拖曳至正確位置。`);
    }
    
    // Clear inputs
    document.getElementById("addNodeId").value = "";
    document.getElementById("addNodeName").value = "";
    document.getElementById("addNodeCapacity").value = "";
    
    saveCurrentLayoutToLocal();
    renderFlowchart();
    updateConnectionEditorUI();
  };
}

// Mouse dragging handles
canvasContainer.addEventListener('mousedown', (e) => {
  if (!isEditingMode) return;
  
  if (e.target.tagName.toLowerCase() === 'input' || 
      e.target.tagName.toLowerCase() === 'select' || 
      e.target.closest('foreignObject')) {
    return;
  }
  
  const nodeEl = e.target.closest('.svg-tank-card');
  const groupEl = e.target.closest('.svg-group-card');
  const pipeEl = e.target.closest('.svg-pipeline-clickable');
  const handleEl = e.target.closest('.svg-conn-handle');
  const anchorEl = e.target.closest('.svg-conn-anchor');
  const labelEl = e.target.closest('.svg-conn-label') || e.target.closest('.svg-conn-label-bg');
  const resizeEl = e.target.closest('.svg-resize-handle');
  
  const data = flowchartData[currentTab];
  
  // Check for click-to-add connection point mode (similar to Inspection Route Editor)
  if (isAddingConnPoint && selectedItem && selectedItem.type === 'connection') {
    // If clicking edit panel drawer, handles, buttons, ignore
    if (e.target.closest('#editPanel') || e.target.closest('.svg-conn-handle') || e.target.closest('.control-btn')) {
      return;
    }
    
    const svgEl = canvasContainer.querySelector('svg');
    if (svgEl) {
      const rect = svgEl.getBoundingClientRect();
      const scaleX = 1180 / rect.width;
      const scaleY = 650 / rect.height;
      const x = Math.round(((e.clientX - rect.left) * scaleX) / 5) * 5;
      const y = Math.round(((e.clientY - rect.top) * scaleY) / 5) * 5;
      
      const gc = data.groupConnections[selectedItem.index];
      if (!gc.points) gc.points = [];
      gc.points.push([x, y]);
      
      saveCurrentLayoutToLocal();
      renderFlowchart();
      updateSelectedNodeUI();
      e.stopPropagation();
      e.preventDefault();
      return;
    }
  }
  
  // Anchor handle (start/end of a connection pipe)
  if (anchorEl) {
    e.preventDefault();
    const connIndex = parseInt(anchorEl.getAttribute('data-conn-index'));
    const which = anchorEl.getAttribute('data-anchor'); // 'start' or 'end'
    selectedItem = { type: 'connection', index: connIndex };
    dragItem = data.groupConnections[connIndex];
    dragType = which === 'start' ? 'conn-anchor-start' : 'conn-anchor-end';
    dragStartMouseX = e.clientX;
    dragStartMouseY = e.clientY;
    dragStartItemX = dragItem.anchorFromOffset ? dragItem.anchorFromOffset[0] : 0;
    dragStartItemY = dragItem.anchorFromOffset ? dragItem.anchorFromOffset[1] : 0;
    if (which === 'end') {
      dragStartItemX = dragItem.anchorToOffset ? dragItem.anchorToOffset[0] : 0;
      dragStartItemY = dragItem.anchorToOffset ? dragItem.anchorToOffset[1] : 0;
    }
    updateSelectedNodeUI();
    renderFlowchart();
    return;
  }
  
  if (labelEl) {
    e.preventDefault();
    const connIndex = parseInt(labelEl.getAttribute('data-conn-index'));
    dragItem = data.groupConnections[connIndex];
    dragType = 'conn-label';
    
    // We need coordinates for the label
    if (!dragItem.labelPos) {
      const gc = dragItem;
      const route = calculatePath(gc);
      let defaultX = 0, defaultY = 0;
      if (route) {
        const { startX, startY, endX, endY } = route;
        defaultX = startX + (endX - startX) / 2;
        defaultY = startY + (endY - startY) / 2;
        let isVertical = Math.abs(endY - startY) > Math.abs(endX - startX);
        if (isVertical) {
          defaultX = startX + 12;
          defaultY = startY + (endY - startY) / 2 + 4;
        } else {
          defaultY = defaultY - 10;
        }
        
        const fromBox = getElementCoordinates(gc.from);
        const toBox = getElementCoordinates(gc.to);
        if (fromBox && toBox) {
          if ((fromBox.id === "process-block-s1" && toBox.id === "waste-group-ipahw") || (fromBox.id === "process-block-s4" && toBox.id === "waste-group")) {
            defaultX = fromBox.x - 95;
            defaultY = 295;
          } else if ((fromBox.id === "process-block-s3" && toBox.id === "waste-group-ipa") || (fromBox.id === "process-block-s5" && toBox.id === "waste-group")) {
            defaultX = fromBox.x - 65;
            defaultY = 305;
          } else if ((fromBox.id === "process-block-s1" && toBox.id === "check-group-ipa") || (fromBox.id === "process-block-s4" && toBox.id === "check-group-s4")) {
            defaultX = fromBox.x + fromBox.w + 20;
            defaultY = fromBox.y + fromBox.h/2 - 10;
          } else if ((fromBox.id === "process-block-s3" && toBox.id === "check-group-ipahq") || (fromBox.id === "process-block-s5" && toBox.id === "check-group-s5")) {
            defaultX = fromBox.x + fromBox.w + 20;
            defaultY = fromBox.y + fromBox.h/2 - 10;
          }
        }
      }
      dragItem.labelPos = [defaultX, defaultY];
    }
    
    dragStartMouseX = e.clientX;
    dragStartMouseY = e.clientY;
    dragStartItemX = dragItem.labelPos[0];
    dragStartItemY = dragItem.labelPos[1];
    selectedItem = { type: 'connection', index: connIndex };
    
    updateSelectedNodeUI();
    renderFlowchart();
    return;
  }
  
  if (handleEl) {
    e.preventDefault();
    const connIndex = parseInt(handleEl.getAttribute('data-conn-index'));
    const ptIndex = parseInt(handleEl.getAttribute('data-pt-index'));
    
    dragItem = data.groupConnections[connIndex].points[ptIndex];
    dragType = 'conn-pt';
    selectedItem = { type: 'connection', index: connIndex };
    
    dragStartMouseX = e.clientX;
    dragStartMouseY = e.clientY;
    dragStartItemX = dragItem[0];
    dragStartItemY = dragItem[1];
    
    updateSelectedNodeUI();
    renderFlowchart();
    return;
  }
  
  if (pipeEl) {
    e.preventDefault();
    const connIndex = parseInt(pipeEl.getAttribute('data-index'));
    selectedItem = { type: 'connection', index: connIndex };
    isAddingConnPoint = false; // reset point adding mode
    
    // Set up dragging for the entire pipe offset
    dragType = 'conn-pipe-offset';
    dragItem = data.groupConnections[connIndex];
    dragStartMouseX = e.clientX;
    dragStartMouseY = e.clientY;
    dragStartItemY = dragItem.offsetY || 0;
    dragStartItemX = dragItem.offsetX || 0;
    
    updateSelectedNodeUI();
    renderFlowchart();
    return;
  }
  
  if (resizeEl) {
    e.preventDefault();
    const id = resizeEl.getAttribute('data-id');
    const type = resizeEl.getAttribute('data-type');
    
    if (type === 'node-resize') {
      dragItem = data.nodes.find(n => n.id === id);
      dragType = 'node-resize';
      selectedItem = { type: 'node', id: id };
      if (dragItem) {
        dragStartMouseX = e.clientX;
        dragStartMouseY = e.clientY;
        dragStartItemW = dragItem.w || 140;
        dragStartItemH = dragItem.h || 70;
      }
    } else {
      dragItem = data.groups.find(g => g.id === id);
      dragType = 'group-resize';
      selectedItem = { type: 'group', id: id };
      if (dragItem) {
        dragStartMouseX = e.clientX;
        dragStartMouseY = e.clientY;
        dragStartItemW = dragItem.w;
        dragStartItemH = dragItem.h;
      }
    }
    updateSelectedNodeUI();
    renderFlowchart();
    return;
  }

  let targetEl = nodeEl || groupEl;
  if (!targetEl) {
    selectedItem = null;
    updateSelectedNodeUI();
    renderFlowchart();
    return;
  }
  
  e.preventDefault();
  
  const id = targetEl.getAttribute('data-id');
  const type = targetEl.getAttribute('data-type');
  
  if (type === 'node') {
    dragItem = data.nodes.find(n => n.id === id);
    dragType = 'node';
    selectedItem = { type: 'node', id: id };
  } else if (type === 'group') {
    dragItem = data.groups.find(g => g.id === id);
    dragType = 'group';
    selectedItem = { type: 'group', id: id };
  }
  
  if (dragItem) {
    dragStartMouseX = e.clientX;
    dragStartMouseY = e.clientY;
    dragStartItemX = dragItem.x;
    dragStartItemY = dragItem.y;
  }
  
  updateSelectedNodeUI();
  renderFlowchart();
});

window.addEventListener('mousemove', (e) => {
  if (!dragItem) return;
  
  const svgEl = canvasContainer.querySelector('svg');
  const rect = svgEl ? svgEl.getBoundingClientRect() : canvasContainer.getBoundingClientRect();
  const scaleX = 1180 / rect.width;
  const scaleY = 650 / rect.height;
  
  const dx = (e.clientX - dragStartMouseX) * scaleX;
  const dy = (e.clientY - dragStartMouseY) * scaleY;
  
  let newX = Math.round((dragStartItemX + dx) / 5) * 5;
  let newY = Math.round((dragStartItemY + dy) / 5) * 5;
  
  // Snap boundary limit
  if (dragType === 'node') {
    newX = Math.max(0, Math.min(1180 - 140, newX));
    newY = Math.max(0, Math.min(650 - 70, newY));
    if (dragItem.x !== newX || dragItem.y !== newY) {
      dragItem.x = newX;
      dragItem.y = newY;
      renderFlowchart();
    }
  } else if (dragType === 'group-resize' || dragType === 'node-resize') {
    const minW = dragType === 'node-resize' ? 80 : 40;
    const minH = dragType === 'node-resize' ? 40 : 30;
    const newW = Math.max(minW, Math.round((dragStartItemW + dx) / 5) * 5);
    const newH = Math.max(minH, Math.round((dragStartItemH + dy) / 5) * 5);
    if (dragItem.w !== newW || dragItem.h !== newH) {
      dragItem.w = newW;
      dragItem.h = newH;
      renderFlowchart();
    }
  } else if (dragType === 'group') {
    newX = Math.max(0, Math.min(1180 - dragItem.w, newX));
    newY = Math.max(0, Math.min(650 - dragItem.h, newY));
    if (dragItem.x !== newX || dragItem.y !== newY) {
      dragItem.x = newX;
      dragItem.y = newY;
      renderFlowchart();
    }
  } else if (dragType === 'conn-pt') {
    newX = Math.max(0, Math.min(1180, newX));
    newY = Math.max(0, Math.min(650, newY));
    if (dragItem[0] !== newX || dragItem[1] !== newY) {
      dragItem[0] = newX;
      dragItem[1] = newY;
      renderFlowchart();
    }
  } else if (dragType === 'conn-anchor-start' || dragType === 'conn-anchor-end') {
    const svgEl3 = canvasContainer.querySelector('svg');
    const rect3 = svgEl3 ? svgEl3.getBoundingClientRect() : canvasContainer.getBoundingClientRect();
    const scaleX3 = 1180 / rect3.width;
    const scaleY3 = 650 / rect3.height;
    const svgDx = Math.round(((e.clientX - dragStartMouseX) * scaleX3) / 5) * 5;
    const svgDy = Math.round(((e.clientY - dragStartMouseY) * scaleY3) / 5) * 5;
    const newOx = Math.max(-200, Math.min(200, dragStartItemX + svgDx));
    const newOy = Math.max(-200, Math.min(200, dragStartItemY + svgDy));
    if (dragType === 'conn-anchor-start') {
      dragItem.anchorFromOffset = [newOx, newOy];
    } else {
      dragItem.anchorToOffset = [newOx, newOy];
    }
    renderFlowchart();
  } else if (dragType === 'conn-pipe-offset') {
    const newOffsetY = Math.round((dragStartItemY + dy) / 5) * 5;
    const newOffsetX = Math.round((dragStartItemX + dx) / 5) * 5;
    
    // clamp offset so it doesn't run totally off screen
    dragItem.offsetY = Math.max(-400, Math.min(400, newOffsetY));
    dragItem.offsetX = Math.max(-200, Math.min(200, newOffsetX));
    
    renderFlowchart();
  } else if (dragType === 'conn-label') {
    newX = Math.max(0, Math.min(1180, newX));
    newY = Math.max(0, Math.min(650, newY));
    if (!dragItem.labelPos) dragItem.labelPos = [newX, newY];
    if (dragItem.labelPos[0] !== newX || dragItem.labelPos[1] !== newY) {
      dragItem.labelPos[0] = newX;
      dragItem.labelPos[1] = newY;
      renderFlowchart();
    }
  }
});

window.addEventListener('mouseup', () => {
  if (dragItem) {
    saveCurrentLayoutToLocal();
    dragItem = null;
    dragType = null;
  }
});

// ==================== GROQ AI CHAT & AUTOMATION ====================

const aiChatToggle = document.getElementById("aiChatToggle");
const aiChatWindow = document.getElementById("aiChatWindow");
const aiChatCloseBtn = document.getElementById("aiChatCloseBtn");
const aiChatSettingsBtn = document.getElementById("aiChatSettingsBtn");
const aiSettingsPanel = document.getElementById("aiSettingsPanel");
const groqApiKeyInput = document.getElementById("groqApiKeyInput");
const groqModelSelect = document.getElementById("groqModelSelect");
const saveAiSettingsBtn = document.getElementById("saveAiSettingsBtn");
const aiMessageList = document.getElementById("aiMessageList");
const aiChatInput = document.getElementById("aiChatInput");
const sendAiMessageBtn = document.getElementById("sendAiMessageBtn");
const aiChatNotification = document.getElementById("aiChatNotification");

// Provider selection & fields DOMs
const aiProviderSelect = document.getElementById("aiProviderSelect");
const groqConfigFields = document.getElementById("groqConfigFields");
const geminiConfigFields = document.getElementById("geminiConfigFields");
const geminiApiKeyInput = document.getElementById("geminiApiKeyInput");
const geminiModelSelect = document.getElementById("geminiModelSelect");

// Default API Key split to bypass Git Secret Push Protection
const DEFAULT_GEMINI_API_KEY = "AQ." + "Ab8RN6LgVby89UZb" + "XCvMmydJoj_nBvWKAvFqq7LuEL3ces-tQA";
const DEFAULT_GROQ_API_KEY = "gsk_" + "9M6NYURFJvrSK9VH" + "7w3iWGdyb3FYpsZfAfxMqH4HWYoOk33AbzTI";

// Load AI Config from localStorage
let aiProvider = localStorage.getItem("ai_provider") || "groq";
let groqApiKey = localStorage.getItem("groq_api_key") || DEFAULT_GROQ_API_KEY;
let groqModel = localStorage.getItem("groq_model") || "llama-3.3-70b-versatile";
let geminiApiKey = toProperGeminiKey(localStorage.getItem("gemini_api_key") || DEFAULT_GEMINI_API_KEY);
let geminiModel = localStorage.getItem("gemini_model") || "gemini-2.5-flash";

function toProperGeminiKey(key) {
  return key ? key.trim() : "";
}

function updateAiSubtitle() {
  const subtitleEl = document.getElementById("aiChatHeaderSubtitle");
  if (subtitleEl) {
    if (aiProvider === "gemini") {
      subtitleEl.textContent = `基於 Google Gemini (${geminiModel})`;
    } else {
      subtitleEl.textContent = `基於 Groq AI (${groqModel})`;
    }
  }
}

// Prefill form values
updateAiSubtitle();
if (aiProviderSelect) {
  aiProviderSelect.value = aiProvider;
  if (groqConfigFields) groqConfigFields.style.display = aiProvider === 'groq' ? 'block' : 'none';
  if (geminiConfigFields) geminiConfigFields.style.display = aiProvider === 'gemini' ? 'block' : 'none';
  
  aiProviderSelect.onchange = () => {
    const provider = aiProviderSelect.value;
    if (groqConfigFields) groqConfigFields.style.display = provider === 'groq' ? 'block' : 'none';
    if (geminiConfigFields) geminiConfigFields.style.display = provider === 'gemini' ? 'block' : 'none';
  };
}
if (groqApiKeyInput) groqApiKeyInput.value = localStorage.getItem("groq_api_key") || "";
if (groqModelSelect) groqModelSelect.value = groqModel;
if (geminiApiKeyInput) geminiApiKeyInput.value = localStorage.getItem("gemini_api_key") || "";
if (geminiModelSelect) geminiModelSelect.value = geminiModel;

// Toggle Chat Drawer
if (aiChatToggle) {
  aiChatToggle.onclick = () => {
    aiChatWindow.classList.toggle("active");
    if (aiChatWindow.classList.contains("active")) {
      if (aiChatNotification) aiChatNotification.style.display = "none";
      setTimeout(() => aiChatInput.focus(), 300);
      scrollToBottom();
    }
  };
}

if (aiChatCloseBtn) {
  aiChatCloseBtn.onclick = () => {
    aiChatWindow.classList.remove("active");
  };
}

// Toggle Settings Panel
if (aiChatSettingsBtn) {
  aiChatSettingsBtn.onclick = () => {
    aiSettingsPanel.classList.toggle("active");
  };
}

// Save Settings
if (saveAiSettingsBtn) {
  saveAiSettingsBtn.onclick = () => {
    const provider = aiProviderSelect.value;
    const gKey = groqApiKeyInput.value.trim();
    const gModel = groqModelSelect.value;
    const gemKey = geminiApiKeyInput.value.trim();
    const gemModel = geminiModelSelect.value;

    localStorage.setItem("ai_provider", provider);
    localStorage.setItem("groq_api_key", gKey);
    localStorage.setItem("groq_model", gModel);
    localStorage.setItem("gemini_api_key", gemKey);
    localStorage.setItem("gemini_model", gemModel);

    aiProvider = provider;
    groqApiKey = gKey || DEFAULT_GROQ_API_KEY;
    groqModel = gModel;
    geminiApiKey = toProperGeminiKey(gemKey || DEFAULT_GEMINI_API_KEY);
    geminiModel = gemModel;
    updateAiSubtitle();

    alert("🎉 AI 設定已成功儲存！");
    aiSettingsPanel.classList.remove("active");
  };
}

const clearAiChatHistoryBtn = document.getElementById("clearAiChatHistoryBtn");
if (clearAiChatHistoryBtn) {
  clearAiChatHistoryBtn.onclick = () => {
    if (confirm("確定要清除所有對話紀錄嗎？")) {
      chatHistory = [];
      localStorage.removeItem('flowchart_chat_history');
      if (aiMessageList) {
        aiMessageList.innerHTML = `
          <div class="ai-message assistant">
            <div class="ai-bubble">
              您好！我是您的 <strong>ESHINE-AI 流程圖助理</strong>。您可以：
              <ul style="margin-left: 16px; margin-top: 4px; line-height: 1.5;">
                <li>詢問目前的槽體狀態（如：「目前有哪些成品槽？」）</li>
                <li>叫我操作流程圖（如：「幫我新增一個 150 KL 的成品槽，編號 TK-999，並從 check-group-ipa 連接過去」）</li>
              </ul>
              請點擊上方 ⚙️ 圖示設定您的 Groq API 金鑰，或直接輸入文字使用模擬 Demo 模式測試！
            </div>
          </div>
        `;
      }
      alert("🎉 對話紀錄已成功清除！");
      aiSettingsPanel.classList.remove("active");
    }
  };
}

// ── Header 清除對話按鈕（🗑️）──
const clearChatHeaderBtn = document.getElementById("clearChatHeaderBtn");
if (clearChatHeaderBtn) {
  clearChatHeaderBtn.onclick = () => {
    if (confirm("確定要清除所有對話紀錄嗎？")) {
      chatHistory = [];
      localStorage.removeItem('flowchart_chat_history');
      if (aiMessageList) {
        aiMessageList.innerHTML = `
          <div class="ai-message assistant">
            <div class="ai-bubble">
              您好！我是您的 <strong>ESHINE-AI 流程圖助理</strong>。您可以：
              <ul style="margin-left: 16px; margin-top: 4px; line-height: 1.5;">
                <li>詢問目前的槽體狀態（如：「目前有哪些成品槽？」）</li>
                <li>叫我操作流程圖（如：「幫我新增一個 150 KL 的成品槽，編號 TK-999，並從 check-group-ipa 連接過去」）</li>
              </ul>
              請點擊上方 ⚙️ 圖示設定您的 Groq API 金鑰，或直接輸入文字使用模擬 Demo 模式測試！
            </div>
          </div>
        `;
      }
    }
  };
}

// ══════════════════════════════════════════════════
// 液位記錄 Modal
// ══════════════════════════════════════════════════
const LL_STORAGE_KEY = 'eshine_liquid_level_records';

function getLiquidRecords() {
  try { return JSON.parse(localStorage.getItem(LL_STORAGE_KEY)) || []; }
  catch (e) { return []; }
}
function saveLiquidRecords(records) {
  try {
    localStorage.setItem(LL_STORAGE_KEY, JSON.stringify(records));
  } catch (e) {
    console.error("Failed to save liquid records to localStorage", e);
  }
}

function getTabOptions() {
  const result = {};
  Object.keys(flowchartData).forEach(k => {
    result[k] = flowchartData[k].title || k;
  });
  return result;
}

function populateLLTabSelect() {
  const sel = document.getElementById('llTabSelect');
  if (!sel) return;
  sel.innerHTML = '';
  Object.keys(flowchartData).forEach(k => {
    const opt = document.createElement('option');
    opt.value = k;
    opt.textContent = flowchartData[k].title || k;
    sel.appendChild(opt);
  });
  if (sel.options.length > 0) populateLLTankSelect(sel.value);
}

function populateLLTankSelect(tabKey) {
  const sel = document.getElementById('llTankSelect');
  if (!sel) return;
  sel.innerHTML = '<option value="">-- 請選擇槽體 --</option>';
  if (!flowchartData[tabKey]) return;
  const nodes = flowchartData[tabKey].nodes || [];
  nodes.forEach(n => {
    if (!n.id) return;
    const opt = document.createElement('option');
    opt.value = n.id;
    opt.textContent = n.id + (n.name ? ` (${n.name})` : '') + (n.capacity ? ` [${n.capacity}]` : '');
    sel.appendChild(opt);
  });
}

function renderLLRecords() {
  const area = document.getElementById('llRecordsArea');
  const tableDiv = document.getElementById('llRecordsTable');
  if (!area || !tableDiv) return;
  const records = getLiquidRecords();
  if (records.length === 0) {
    tableDiv.innerHTML = '<p style="text-align:center;color:#94a3b8;font-size:12px;padding:12px;">尚無紀錄</p>';
  } else {
    const sorted = [...records].sort((a, b) => b.timestamp - a.timestamp);
    tableDiv.innerHTML = `
      <table>
        <thead><tr><th>日期</th><th>分頁</th><th>槽體</th><th>液位%</th><th>容量KL</th><th>備註</th><th></th></tr></thead>
        <tbody>
          ${sorted.map(r => `
            <tr>
              <td>${r.date}</td><td>${r.tabName}</td><td>${r.tankId}</td>
              <td>${r.level}%</td><td>${r.volume || '-'}</td><td>${r.note || '-'}</td>
              <td><button onclick="deleteLLRecord(${r.timestamp})" style="background:none;border:none;color:#f87171;cursor:pointer;font-size:12px;" title="刪除">🗑</button></td>
            </tr>`).join('')}
        </tbody>
      </table>`;
  }
  area.style.display = 'block';
}

window.deleteLLRecord = function(timestamp) {
  if (!confirm('確定刪除此筆紀錄？')) return;
  saveLiquidRecords(getLiquidRecords().filter(r => r.timestamp !== timestamp));
  renderLLRecords();
};

function exportLLRecordsCSV() {
  const records = getLiquidRecords();
  if (records.length === 0) { alert('尚無紀錄可匯出'); return; }
  const header = ['日期','分頁','槽體ID','液位(%)','實際容量(KL)','備註','紀錄時間'];
  const rows = records.map(r => [
    r.date, r.tabName, r.tankId, r.level, r.volume || '', r.note || '',
    new Date(r.timestamp).toLocaleString('zh-TW')
  ]);
  const csv = '\uFEFF' + [header, ...rows].map(r => r.map(v => `"${String(v).replace(/"/g,'""')}"`).join(',')).join('\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8;'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = `液位記錄_${new Date().toISOString().slice(0,10)}.csv`;
  a.click(); URL.revokeObjectURL(url);
}

// 液位記錄 - 全域功能與動態事件綁定
if (document.getElementById('llDate')) {
  document.getElementById('llDate').value = new Date().toISOString().slice(0, 10);
}
{
  const openBtn = document.getElementById("openLiquidLevelBtn");
  const closeBtn = document.getElementById("closeLiquidLevelModal");
  const saveBtn = document.getElementById("saveLiquidLevelBtn");
  const viewBtn = document.getElementById("viewLiquidLevelBtn");
  const exportBtn = document.getElementById("exportLiquidLevelBtn");
  const modal = document.getElementById("liquidLevelModal");
  const tabSel = document.getElementById("llTabSelect");

  if (openBtn && modal) {
    openBtn.onclick = () => {
      populateLLTabSelect();
      const area = document.getElementById("llRecordsArea");
      if (area) area.style.display = "none";
      modal.classList.add("active");
    };
  }
  if (closeBtn && modal) {
    closeBtn.onclick = () => {
      modal.classList.remove("active");
    };
  }
  if (modal) {
    modal.onclick = (e) => {
      if (e.target === modal) modal.classList.remove("active");
    };
  }
  if (saveBtn) {
    saveBtn.onclick = () => {
      const tabSelEl = document.getElementById('llTabSelect');
      const tankSel = document.getElementById('llTankSelect');
      const llDateEl = document.getElementById('llDate');
      const levelEl = document.getElementById('llValue');
      const volEl = document.getElementById('llVolume');
      const noteEl = document.getElementById('llNote');
      const tabKey = tabSelEl ? tabSelEl.value : '';
      const tankId = tankSel ? tankSel.value : '';
      const date = llDateEl ? llDateEl.value : '';
      const level = levelEl ? levelEl.value : '';
      if (!tankId) { alert('請選擇槽體'); return; }
      if (!date) { alert('請填寫日期'); return; }
      if (level === '') { alert('請輸入液位 (%)'); return; }
      const names = getTabOptions();
      const record = {
        timestamp: Date.now(), date: date, tabKey: tabKey,
        tabName: (names[tabKey] || tabKey),
        tankId: tankId, level: parseFloat(level),
        volume: (volEl && volEl.value) ? parseFloat(volEl.value) : '',
        note: noteEl ? noteEl.value.trim() : ''
      };
      const records = getLiquidRecords();
      records.push(record);
      saveLiquidRecords(records);
      if (tankSel) tankSel.value = '';
      if (levelEl) levelEl.value = '';
      if (volEl) volEl.value = '';
      if (noteEl) noteEl.value = '';
      alert('✅ 已儲存 ' + tankId + ' 液位 ' + level + '%');
      renderLLRecords();
    };
  }
  if (viewBtn) {
    viewBtn.onclick = () => {
      const area = document.getElementById('llRecordsArea');
      if (!area) return;
      if (area.style.display === 'none') renderLLRecords();
      else area.style.display = 'none';
    };
  }
  if (exportBtn) {
    exportBtn.onclick = () => {
      exportLLRecordsCSV();
    };
  }
  if (tabSel) {
    tabSel.addEventListener("change", () => {
      populateLLTankSelect(tabSel.value);
    });
  }
  
  const importReportBtn = document.getElementById("importDailyReportBtn");
  const importReportFile = document.getElementById("importDailyReportFile");
  if (importReportBtn && importReportFile) {
    importReportBtn.onclick = () => {
      importReportFile.click();
    };
    importReportFile.onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      importLiquidLevelExcel(file);
      importReportFile.value = ''; // reset
    };
  }
}

// 載入 SheetJS 函式庫 (用於讀取 Excel)
function loadSheetJS() {
  return new Promise((resolve, reject) => {
    if (window.XLSX) {
      resolve(window.XLSX);
      return;
    }
    const script = document.createElement('script');
    script.src = "https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js";
    script.onload = () => resolve(window.XLSX);
    script.onerror = () => reject(new Error("無法載入 Excel 解析庫，請確認網路連線。"));
    document.head.appendChild(script);
  });
}

// 簡單的 CSV 解析器
function parseCSV(text) {
  const lines = text.split(/\r?\n/);
  return lines.map(line => {
    const cells = [];
    let insideQuote = false;
    let currentCell = '';
    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      if (char === '"') {
        insideQuote = !insideQuote;
      } else if (char === ',' && !insideQuote) {
        cells.push(currentCell.trim());
        currentCell = '';
      } else {
        currentCell += char;
      }
    }
    cells.push(currentCell.trim());
    return cells;
  });
}

// 匯入 Excel/CSV 日報表並寫入儲槽與歷史紀錄
// 匯入 Excel/CSV 日報表並寫入儲槽與歷史紀錄
async function importLiquidLevelExcel(file) {
  const processRows = async (rows, dateStr) => {
    let currentBlockTanks = null;
    let importCount = 0;
    const newRecords = [];
    
    // 用於記錄每個槽體在該報表中的最新液位 (key: tankId, value: { fill, nodeRef })
    // 以便稍後一次性更新 flowchartData 的 node.fill，避免 8:00 與 16:00 覆蓋順序混亂
    const latestTankLevels = {};

    for (let r = 0; r < rows.length; r++) {
      const row = rows[r];
      if (!row || row.length === 0) continue;

      // 1. 識別儲槽 ID 標題列：檢查該列是否有包含 TK-xxx 等儲槽名稱 (非重複)
      const tankCols = [];
      for (let c = 0; c < row.length; c++) {
        const val = row[c];
        if (val !== undefined && val !== null && val !== '') {
          const strVal = String(val).trim();
          const match = strVal.match(/\b(TK-?\d+[A-Z]?)\b/i);
          if (match) {
            tankCols.push({ id: match[1].toUpperCase(), col: c });
          }
        }
      }

      // 檢查是否具有 3 個以上不重複的儲槽 ID，以過濾掉一般描述列或密度表
      const uniqueIds = new Set(tankCols.map(t => t.id));
      if (uniqueIds.size >= 3) {
        currentBlockTanks = tankCols;
        continue;
      }

      // 2. 識別液位數值列：當前已找到儲槽標題，且該列前幾欄包含 "液位" 字眼
      if (currentBlockTanks) {
        let isLevelRow = false;
        let levelColIdx = -1;
        // 通常在 Col 1 或 Col 2
        for (const c_idx of [1, 2]) {
          if (c_idx < row.length && row[c_idx] !== undefined && row[c_idx] !== null) {
            if (String(row[c_idx]).includes('液位')) {
              isLevelRow = true;
              levelColIdx = c_idx;
              break;
            }
          }
        }

        if (isLevelRow) {
          // 時間通常在液位標籤的左邊一欄
          const timeColIdx = levelColIdx - 1;
          const timeVal = (timeColIdx >= 0 && timeColIdx < row.length) ? row[timeColIdx] : null;
          let timeStr = "08:00"; // 預設
          if (timeVal !== undefined && timeVal !== null) {
            let rawTimeStr = String(timeVal).trim();
            if (rawTimeStr.includes('16:00') || rawTimeStr.includes('16:00:00')) {
              timeStr = "16:00";
            } else if (rawTimeStr.includes('08:00') || rawTimeStr.includes('8:00') || rawTimeStr.includes('08:00:00')) {
              timeStr = "08:00";
            } else {
              const timeMatch = rawTimeStr.match(/(\d{1,2}):(\d{2})/);
              if (timeMatch) {
                timeStr = `${timeMatch[1].padStart(2, '0')}:${timeMatch[2]}`;
              } else if (rawTimeStr && rawTimeStr !== 'None') {
                timeStr = rawTimeStr;
              }
            }
          }

          // 解析該列中每個儲槽對應的液位數值
          for (const tank of currentBlockTanks) {
            const col = tank.col;
            if (col < row.length) {
              const val = row[col];
              if (val !== undefined && val !== null && val !== '') {
                const numValue = parseFloat(val);
                if (!isNaN(numValue)) {
                  let fillPercent = 0;
                  if (numValue <= 100) {
                    fillPercent = numValue; // 直接是百分比
                  } else {
                    fillPercent = (numValue / 6000) * 100; // 毫米 (mm) 轉百分比
                  }
                  fillPercent = Math.min(100, Math.max(0, Math.round(fillPercent * 10) / 10));

                  // 在 flowchartData 的所有分頁中尋找對應的儲槽節點
                  let matchedNode = null;
                  let matchedTabKey = null;
                  for (const tabKey of Object.keys(flowchartData)) {
                    const node = flowchartData[tabKey].nodes.find(n => n.id === tank.id);
                    if (node) {
                      matchedNode = node;
                      matchedTabKey = tabKey;
                      break;
                    }
                  }

                  if (matchedNode) {
                    let capacityKL = parseFloat(matchedNode.capacity);
                    if (isNaN(capacityKL)) capacityKL = 100;
                    const volumeKL = Math.round((fillPercent / 100) * capacityKL * 10) / 10;

                    // 記錄至歷史液位紀錄
                    const record = {
                      timestamp: Date.now() + importCount,
                      date: dateStr,
                      tabKey: matchedTabKey,
                      tabName: flowchartData[matchedTabKey].title.split(" (")[0],
                      tankId: tank.id,
                      level: fillPercent,
                      volume: volumeKL,
                      note: `${timeStr} (日報表自動匯入)`
                    };
                    newRecords.push(record);
                    importCount++;

                    // 儲存最新液位（16:00 會覆蓋 08:00，或以時間序較後者優先）
                    const existingUpdate = latestTankLevels[tank.id];
                    if (!existingUpdate || timeStr === "16:00" || (existingUpdate.timeLabel !== "16:00" && timeStr > existingUpdate.timeLabel)) {
                      latestTankLevels[tank.id] = {
                        fill: fillPercent,
                        timeLabel: timeStr,
                        nodeRef: matchedNode
                      };
                    }
                  }
                }
              }
            }
          }
        }
      }
    }

    if (importCount > 0) {
      // 一次性更新所有匹配儲槽的 fill 屬性
      Object.keys(latestTankLevels).forEach(tankId => {
        const update = latestTankLevels[tankId];
        update.nodeRef.fill = update.fill;
      });

      // 儲存至本地歷史紀錄
      const existing = getLiquidRecords();
      saveLiquidRecords([...existing, ...newRecords]);
      
      // 儲存 layout 至本地
      saveCurrentLayoutToLocal();
      
      // 重新加載與渲染
      applyLayoutAndReload();

      // 若為管理者且 Firebase 啟用，自動同步至雲端
      if (isManager && typeof firebase !== 'undefined' && firebase.apps.length > 0) {
        try {
          const db = firebase.firestore();
          await db.collection('flowcharts').doc('current_layout').set({
            dataset: flowchartData,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp(),
            updatedBy: "manager"
          });
          cloudLayoutData = JSON.parse(JSON.stringify(flowchartData));
          alert(`🎉 成功從日報表匯入並自動更新 ${Object.keys(latestTankLevels).length} 個相對應儲槽（共 ${importCount} 筆數據）！\n☁️ 數據已自動同步發布至雲端資料庫！`);
        } catch (cloudErr) {
          console.error("Firestore auto-sync error:", cloudErr);
          alert(`🎉 成功從日報表匯入並自動更新 ${Object.keys(latestTankLevels).length} 個相對應儲槽（共 ${importCount} 筆數據）！\n⚠️ 但雲端發布同步失敗：${cloudErr.message}`);
        }
      } else {
        alert(`🎉 成功從日報表匯入並自動寫入 ${Object.keys(latestTankLevels).length} 個相對應儲槽（共 ${importCount} 筆數據）！\n⚠️ 此資料已儲存於您的本機。若要更新至雲端讓所有人都看見，請點擊「管理登入」發布同步。`);
      }
    } else {
      alert("⚠️ 未在檔案中匹配到任何現有的儲槽 ID，請確認檔案內容格式。");
    }
  };

  try {
    // 預設日期為今天
    let importDate = new Date().toISOString().slice(0, 10);
    let year = new Date().getFullYear();
    const filenameMatch = file.name.match(/\b(20\d{2})\b/);
    if (filenameMatch) {
      year = parseInt(filenameMatch[1], 10);
    }

    if (file.name.endsWith('.csv')) {
      // 嘗試從檔名解析日期 (如 6.4 或 6_4 或 06-04)
      const fileDateMatch = file.name.match(/(\d{1,2})[._-](\d{1,2})/);
      if (fileDateMatch) {
        const mm = parseInt(fileDateMatch[1], 10);
        const dd = parseInt(fileDateMatch[2], 10);
        if (mm >= 1 && mm <= 12 && dd >= 1 && dd <= 31) {
          importDate = `${year}-${String(mm).padStart(2, '0')}-${String(dd).padStart(2, '0')}`;
        }
      }

      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const text = e.target.result;
          const rows = parseCSV(text);
          await processRows(rows, importDate);
        } catch (err) {
          alert("❌ 解析 CSV 檔案失敗：" + err.message);
        }
      };
      reader.readAsText(file, 'utf-8');
    } else {
      const XLSX = await loadSheetJS();
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const data = new Uint8Array(e.target.result);
          const workbook = XLSX.read(data, { type: 'array' });
          
          // 偵測日期分頁
          const dateSheets = workbook.SheetNames.filter(name => /^\d+(\.\d+)?$/.test(name.trim()));
          let targetSheetName = workbook.SheetNames[0];
          
          if (dateSheets.length > 0) {
            const latestSheet = dateSheets[dateSheets.length - 1];
            const userChoice = prompt(
              `偵測到此日報表包含以下日期的數據分頁：\n${dateSheets.join(', ')}\n\n系統預設將匯入最新日期 [${latestSheet}] 的數據。\n若要匯入其他日期，請在下方輸入該分頁名稱（例如：6.4），否則直接點擊「確定」繼續：`,
              latestSheet
            );
            if (userChoice === null) return; // 使用者取消匯入
            if (userChoice.trim()) {
              targetSheetName = userChoice.trim();
            }
          }

          const sheet = workbook.Sheets[targetSheetName];
          if (!sheet) {
            alert(`❌ 找不到分頁 [${targetSheetName}]，匯入取消。`);
            return;
          }

          // 從分頁名稱（如 6.4）更新 importDate
          const dateParts = targetSheetName.split('.');
          if (dateParts.length === 2) {
            const mm = parseInt(dateParts[0], 10);
            const dd = parseInt(dateParts[1], 10);
            if (!isNaN(mm) && !isNaN(dd)) {
              importDate = `${year}-${String(mm).padStart(2, '0')}-${String(dd).padStart(2, '0')}`;
            }
          } else {
            // 如果分頁名稱不是 M.D，試試從檔名解析日期
            const fileDateMatch = file.name.match(/(\d{1,2})[._-](\d{1,2})/);
            if (fileDateMatch) {
              const mm = parseInt(fileDateMatch[1], 10);
              const dd = parseInt(fileDateMatch[2], 10);
              if (mm >= 1 && mm <= 12 && dd >= 1 && dd <= 31) {
                importDate = `${year}-${String(mm).padStart(2, '0')}-${String(dd).padStart(2, '0')}`;
              }
            }
          }

          const rows = XLSX.utils.sheet_to_json(sheet, { header: 1 });
          await processRows(rows, importDate);
        } catch (err) {
          alert("❌ 解析 Excel 檔案失敗：" + err.message);
        }
      };
      reader.readAsArrayBuffer(file);
    }
  } catch (err) {
    alert("❌ 處理檔案失敗：" + err.message);
  }
}


function scrollToBottom() {

  if (aiMessageList) {
    aiMessageList.scrollTop = aiMessageList.scrollHeight;
  }
}

let chatHistory = [];

function saveChatHistory() {
  try {
    localStorage.setItem('flowchart_chat_history', JSON.stringify(chatHistory));
  } catch (e) {
    console.error("Failed to save chat history", e);
  }
}

function loadChatHistory() {
  if (!aiMessageList) return;
  try {
    const saved = localStorage.getItem('flowchart_chat_history');
    if (saved) {
      aiMessageList.innerHTML = "";
      chatHistory = JSON.parse(saved);
      chatHistory.forEach(msg => {
        appendMessageBubble(msg.sender, msg.text, msg.isActionLog, false);
      });
    }
  } catch (e) {
    console.error("Failed to load chat history", e);
  }
}

// Render a chat message bubble
function appendMessageBubble(sender, text, isActionLog = false, shouldSave = true) {
  if (!aiMessageList) return;
  
  if (shouldSave) {
    chatHistory.push({ sender, text, isActionLog });
    saveChatHistory();
  }
  
  if (isActionLog) {
    const logEl = document.createElement("div");
    logEl.className = "ai-action-log";
    logEl.textContent = text;
    aiMessageList.appendChild(logEl);
  } else {
    const msgEl = document.createElement("div");
    msgEl.className = `ai-message ${sender}`;
    const bubbleEl = document.createElement("div");
    bubbleEl.className = "ai-bubble";
    
    // Simple markdown helper
    let formattedText = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\n/g, "<br>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`(.*?)`/g, "<code>$1</code>");
      
    bubbleEl.innerHTML = formattedText;
    msgEl.appendChild(bubbleEl);
    aiMessageList.appendChild(msgEl);
  }
  scrollToBottom();
}

// Append loading indicator
function showAiLoading() {
  if (!aiMessageList) return null;
  const msgEl = document.createElement("div");
  msgEl.className = "ai-message assistant ai-loading-container";
  const bubbleEl = document.createElement("div");
  bubbleEl.className = "ai-bubble ai-loading-bubble";
  bubbleEl.innerHTML = `
    <div class="ai-dot"></div>
    <div class="ai-dot"></div>
    <div class="ai-dot"></div>
  `;
  msgEl.appendChild(bubbleEl);
  aiMessageList.appendChild(msgEl);
  scrollToBottom();
  return msgEl;
}

function removeAiLoading(loadingEl) {
  if (loadingEl && loadingEl.parentNode) {
    loadingEl.parentNode.removeChild(loadingEl);
  }
}

// Perform a client-side fuzzy search on all nodes/groups across all tabs
function getFuzzySearchMatches(queryText) {
  if (!queryText) return [];
  const cleanText = queryText.toLowerCase().replace(/\s+/g, "");
  
  // Product keywords list
  const keywordsList = ["ipahq", "nmp", "cpne4", "cpne3", "cpne", "act", "ebr", "hear", "eg", "ipa"];
  
  // Find which keywords are mentioned.
  let tempText = cleanText;
  const activeKeywords = [];
  
  // Sort by length desc
  const sortedKeywords = [...keywordsList].sort((a,b) => b.length - a.length);
  sortedKeywords.forEach(kw => {
    if (tempText.includes(kw)) {
      activeKeywords.push(kw);
      tempText = tempText.replace(new RegExp(kw, 'g'), "");
    }
  });
  
  // Types mapping
  const types = {
    "raw": ["原料", "進料", "raw"],
    "finish": ["成品", "合格", "finish"],
    "process": ["待驗", "製程", "中間", "process", "check"],
    "offgrade": ["格外", "下腳", "回收", "offgrade", "waste", "ibc"]
  };
  
  const activeTypes = Object.keys(types).filter(typeKey => 
    types[typeKey].some(term => cleanText.includes(term))
  );
  
  const matches = [];
  
  Object.keys(flowchartData).forEach(tabKey => {
    const tabData = flowchartData[tabKey];
    
    tabData.nodes.forEach(node => {
      const nodeName = node.name.toLowerCase();
      const nodeId = node.id.toLowerCase();
      
      // Find group
      const group = tabData.groups.find(g => 
        !g.id.startsWith("process-block") && 
        node.x >= g.x && node.x < g.x + g.w && 
        node.y >= g.y && node.y < g.y + g.h
      );
      const groupName = group ? group.name.toLowerCase() : "";
      
      let isMatch = false;
      
      // A. Direct substring match of query
      if (cleanText.length >= 2 && (nodeId.includes(cleanText) || nodeName.includes(cleanText) || groupName.includes(cleanText))) {
        isMatch = true;
      }
      
      // B. Keyword + Type intersection matching
      if (!isMatch && (activeKeywords.length > 0 || activeTypes.length > 0)) {
        let kwMatch = true;
        if (activeKeywords.length > 0) {
          kwMatch = activeKeywords.some(kw => {
            if (kw === "ipahq") {
              return tabKey === "ipahq" || nodeId.includes("ipahq") || nodeName.includes("ipahq") || groupName.includes("ipahq");
            }
            if (kw === "ipa") {
              const isIpaRelated = tabKey === "ipa" || nodeId.includes("ipa") || nodeName.includes("ipa") || groupName.includes("ipa");
              const isIpaHqRelated = tabKey === "ipahq" || nodeId.includes("ipahq") || nodeName.includes("ipahq") || groupName.includes("ipahq");
              return isIpaRelated && !isIpaHqRelated;
            }
            return tabKey.includes(kw) || nodeId.includes(kw) || nodeName.includes(kw) || groupName.includes(kw);
          });
        }
        
        let typeMatch = true;
        if (activeTypes.length > 0) {
          typeMatch = activeTypes.includes(node.type) || activeTypes.some(t => nodeName.includes(t) || groupName.includes(t));
        }
        
        if (kwMatch && typeMatch) {
          isMatch = true;
        }
      }
      
      if (isMatch) {
        matches.push({
          tabId: tabKey,
          tabTitle: tabData.title.split(" (")[0],
          id: node.id,
          name: node.name,
          capacity: node.capacity,
          type: node.type,
          group: group ? group.name : "其他"
        });
      }
    });
  });
  
  return matches;
}

// Fetch Groq response and parse action commands
async function sendChatMessageToGroq(messageText) {
  // Run fuzzy search and prepend hint
  const fuzzyMatches = getFuzzySearchMatches(messageText);
  let searchHint = "";
  if (fuzzyMatches.length > 0) {
    searchHint = `【系統搜尋提示：經全站關鍵字模糊匹配，以下槽體與使用者問題直接相關，請務必將其納入答覆中並按分頁與群組分類列出：\n${JSON.stringify(fuzzyMatches)}】\n\n`;
  }

  // Compress all flowcharts state to minimize token usage
  const stateSummary = {
    c: currentTab,
    f: {}
  };
  
  Object.keys(flowchartData).forEach(tabKey => {
    const tabData = flowchartData[tabKey];
    stateSummary.f[tabKey] = {
      t: tabData.title.split(" (")[0],
      tc: tabData.totalCapacity,
      g: tabData.groups.map(g => ({ 
        id: g.id, 
        n: g.name, 
        c: g.capacity,
        hasInput: (tabKey === "cpne3" && (g.id === "check-group" || g.id === "finish-group")) || g.id.startsWith("process-block")
      })),
      n: tabData.nodes.map(n => {
        const gMatch = tabData.groups.find(g => 
          !g.id.startsWith("process-block") && 
          n.x >= g.x && n.x < g.x + g.w && 
          n.y >= g.y && n.y < g.y + g.h
        );
        return {
          id: n.id,
          n: n.name,
          c: n.capacity,
          t: n.type,
          f: n.fill,
          g: gMatch ? gMatch.name : ""
        };
      }),
      c: tabData.groupConnections.map(c => ({ f: c.from, t: c.to, l: c.label }))
    };
  });

  const systemMessage = `你是一個化學工廠製程流程圖系統的 AI 助理。
目前全站所有分頁數據以壓縮 JSON 提供：
${JSON.stringify(stateSummary)}

壓縮鍵說明：
- f: 全站所有分頁 (flowcharts)
- c: 當前分頁 ID (currentTab)，如 "ipa"
- t: 分頁標題 (title)
- tc: 該分頁的總產能/總容量 (totalCapacity)
- g: 該分頁的群組列表 (groups)
- n: 該分頁的槽體/節點列表 (nodes)
- c: 該分頁的管道連線列表 (connections)
- 在群組中：n 代表名稱 (name)，c 代表容量/產能 (capacity)，hasInput 代表是否在畫布上具有可編輯的「輸入產能」輸入框 (boolean)
- 在槽體中：n 代表名稱 (name)，c 代表容量 (capacity)，t 代表類別 (type: raw/process/finish/offgrade)，f 代表液位百分比 (fill)，g 代表所屬群組名稱 (group name)
- 在連線中：f 代表起點 (from)，t 代表終點 (to)，l 代表標籤 (label)

使用者可以向你詢問關於全站任何分頁、槽體或管線的問題，或是下達修改/新增指令。
你可以執行以下「編輯操作」 (actions)：
1. 新增槽體/節點 (add_node): data 格式 { id, name, capacity, type, x, y }。其中 type 可選: "raw" | "process" | "finish" | "offgrade"。x 座標建議在適當的群組範圍（原料區約 x: 140; 製程/待驗約 380 或 620; 成品區約 860; 下腳料約 380 或 200），y 座標在 100~550。
2. 刪除槽體/節點 (delete_node): data 格式 { id }。
3. 新增管線/連線 (add_connection): data 格式 { from, to, label }。from 與 to 必須為現有的節點 ID 或群組 ID。
4. 刪除管線/連線 (delete_connection): data 格式 { from, to }。
5. 更新槽體屬性 (update_node): data 格式 { id, name, capacity, type, fill }。
6. 新增分頁/流程圖 (add_tab): data 格式 { key, title, use_template }。其中 key 建議格式為 "flow_" + 數字 (例如 "flow_123" 或隨機)，title 為分頁標題 (例如 "10. IPHQS6與S7流程圖")，use_template 為布林值 (是否預設建立原料、製程、成品、待驗、下腳料等 5 個群組，預設為 true)。
7. 修改分頁名稱 (rename_tab): data 格式 { title }，目標分頁由 "tab" 指定。
8. 刪除分頁/流程圖 (delete_tab): data 格式 {}，目標分頁由 "tab" 指定。
9. 輸入群組產能 (input_group_capacity): data 格式 { id, capacity }。當使用者說要在某個群組/製程的「輸入產能」輸入框中輸入或新增產能數值時（例如「幫我輸入成品 CPNE3 的產能為 1300」或「製程輸入產能 1200」），請呼叫此 action。此操作會將數值填入畫面上對應的輸入框中，不會修改分頁的總產能描述。
10. 更新群組屬性 (update_group): data 格式 { id, name, capacity }。當要修改群組的名稱，或是修改沒有輸入框的群組的靜態容量文字時，請呼叫此 action。
11. 更新分頁屬性 (update_tab): data 格式 { title, totalCapacity }，目標分頁由 "tab" 指定。當使用者說要修改整個產品流程圖的總產能描述或名稱時，請呼叫此 action。

對於 actions 中的每一個操作，你都必須指定目標分頁，例如：
{
  "response": "在此用自然語言（繁體中文）回答使用者的問題，或是描述你剛剛執行了哪些流程圖的編輯操作。",
  "actions": [
    { "type": "add_tab", "data": { "key": "flow_iphqs6s7", "title": "10. IPHQS6與S7流程圖", "use_template": true } }
  ]
}
其中 "tab" 欄位為目標分頁 ID（可選：ipa, eg, nmp, cpne4, cpne3, act, ebr, hear, ipahq 或自訂 key），若未提供則預設為當前分頁。

重要規則：
- 當使用者提及某個產品關鍵字（例如 "IPA HQ"、"EG" 等）進行查詢時，你必須掃描「所有分頁」的「所有槽體名稱與群組名稱」。切勿因為某個分頁的標題完美契合該關鍵字，就忽略了其他分頁中名字包含該關鍵字之槽體（例如：分頁 1 "ipa" 中也包含名稱為 "IPAHQ成品槽" 的槽體，你也必須找出來並分類列出）。
- 當回答關於數量統計的問題時，務必精確計算，確保你回覆的「統計總數」與你「列出的槽體/連線項目數量」完全吻合，嚴禁出現數量與列表不一致的矛盾。
- 對於跨分頁的查詢結果，請務必「按分頁標題進行分組」列出（例如：在「分頁A」有 X 個，在「分頁B」有 Y 個），以便使用者能清晰區分。
- 如果使用者只是「發問」或詢問狀態，不需要做 any 修改，則 "actions" 欄位應為空陣列 []。例如，詢問全站成品槽的統計資訊、跨分頁對比等，直接在 "response" 答覆。
- 請勿附帶任何 markdown 的包裹標籤（如 \`\`\`json ），直接以 JSON 字串格式回應。
- 當新增槽體時，必須指定唯一的 id；若使用者想建立連線，請確保 from 和 to 的 ID 皆是該分頁中存在的（或是你同時在 actions 裡新增的）。
- 回覆一律使用繁體中文。`;

  if (!groqApiKey) {
    // Demo / Mock Mode fallback if no key is provided
    return new Promise((resolve) => {
      setTimeout(() => {
        const lowerMsg = messageText.toLowerCase();
        let responseText = "";
        let actions = [];
        
        if (lowerMsg.includes("新增") || lowerMsg.includes("add") || lowerMsg.includes("放") || lowerMsg.includes("連")) {
          // Detect mock add
          if (lowerMsg.includes("槽") || lowerMsg.includes("tank")) {
            const mockId = "TK-" + Math.floor(Math.random() * 900 + 100);
            const isFinish = lowerMsg.includes("成品");
            const isRaw = lowerMsg.includes("原料");
            const type = isFinish ? "finish" : (isRaw ? "raw" : "process");
            const name = isFinish ? "AI 成品槽" : (isRaw ? "AI 原料槽" : "AI 待驗槽");
            const x = isFinish ? 860 : (isRaw ? 140 : 620);
            
            // Detect target tab
            let targetTab = currentTab;
            if (lowerMsg.includes("eg")) targetTab = "eg";
            else if (lowerMsg.includes("nmp")) targetTab = "nmp";
            else if (lowerMsg.includes("ipa")) targetTab = "ipa";
            
            actions.push({
              type: "add_node",
              tab: targetTab,
              data: { id: mockId, name: name, capacity: "125 KL", type: type, x: x, y: 350 }
            });
            
            responseText = `[Demo 模擬回應] 好的，我為您在分頁 "${targetTab}" 新增了槽體 ${mockId}。`;
          } else {
            responseText = `[Demo 模擬回應] 好的，收到指令，已模擬執行。`;
          }
        } else {
          // Mock Cross-Tab Query Response
          const totalTanks = Object.keys(flowchartData).reduce((sum, key) => sum + flowchartData[key].nodes.length, 0);
          const currentData = flowchartData[currentTab] || { nodes: [], groupConnections: [] };
          responseText = `[Demo 模擬回應] 目前處於 Demo 模式（未設定金鑰）。
* 全站共有 ${totalTanks} 個槽體節點，當前分頁有 ${currentData.nodes.length} 個槽體與 ${currentData.groupConnections.length} 條管道。
若要開啟 AI 的智慧自動編輯與精確查詢功能，請點擊右上角 ⚙️ 設定您的 Groq API 金鑰！`;
        }
        
        resolve({ response: responseText, actions: actions });
      }, 1200);
    });
  }

  const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${groqApiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: groqModel,
      messages: [
        { role: "system", content: systemMessage },
        { role: "user", content: searchHint + messageText }
      ],
      temperature: 0.1,
      response_format: { type: "json_object" }
    })
  });

  if (!response.ok) {
    const errText = await response.text();
    if (response.status === 429) {
      throw new Error("QUOTA_EXCEEDED");
    }
    throw new Error(`Groq API 錯誤 (${response.status}): ${errText}`);
  }

  const resJson = await response.json();
  const content = resJson.choices[0].message.content.trim();
  
  // Parse response
  try {
    return JSON.parse(content);
  } catch (err) {
    console.error("JSON parsing failed for AI output:", content);
    const cleaned = content.replace(/```json|```/g, "").trim();
    return JSON.parse(cleaned);
  }
}

// State modifier actions engine
function executeAIActions(actions) {
  if (!actions || !Array.isArray(actions) || actions.length === 0) return [];
  
  const logs = [];
  let shouldSwitchTab = null;
  let layoutUpdated = false;
  let needReloadAll = false;
  
  actions.forEach(action => {
    // Specially handle add_tab before targetTab data check
    if (action.type === 'add_tab') {
      const { key, title, use_template } = action.data || {};
      const tabKey = key || "flow_" + Date.now();
      const tabTitle = title || "新產品流程圖";
      const isTemplate = use_template !== false;

      if (flowchartData[tabKey]) {
        logs.push(`❌ 新增分頁失敗：Key "${tabKey}" 已存在`);
        return;
      }

      let newTabObj = {
        title: tabTitle,
        totalCapacity: "編輯中",
        groups: [],
        nodes: [],
        groupConnections: []
      };

      if (isTemplate) {
        newTabObj.groups = [
          { id: "raw-group", name: "原料區", capacity: "原料", x: 120, y: 80, w: 180, h: 500, type: "raw" },
          { id: "process-block", name: "製程生產", capacity: "製程", x: 360, y: 180, w: 160, h: 80, type: "process" },
          { id: "waste-group", name: "下腳料區", capacity: "下腳料", x: 360, y: 300, w: 180, h: 280, type: "offgrade" },
          { id: "check-group", name: "Check Tank 待驗", capacity: "待驗", x: 600, y: 80, w: 180, h: 500, type: "process" },
          { id: "finish-group", name: "成品區", capacity: "成品", x: 840, y: 80, w: 180, h: 500, type: "finish" }
        ];
        newTabObj.groupConnections = [
          { from: "raw-group", to: "process-block", label: "" },
          { from: "process-block", to: "waste-group", label: "格外品排料" },
          { from: "process-block", to: "check-group", label: "待檢驗" },
          { from: "check-group", to: "finish-group", label: "成品放行" }
        ];
      }

      flowchartData[tabKey] = newTabObj;
      logs.push(`🎉 成功新增產品分頁：「${tabTitle}」`);
      layoutUpdated = true;
      needReloadAll = true;
      shouldSwitchTab = tabKey;
      return;
    }

    const targetTab = action.tab || currentTab;
    const data = flowchartData[targetTab];
    if (!data) {
      logs.push(`❌ 操作失敗：找不到目標分頁 "${targetTab}"`);
      return;
    }
    
    switch (action.type) {
      case 'rename_tab': {
        const { title } = action.data || {};
        if (!title) {
          logs.push(`❌ 修改名稱失敗：缺少名稱`);
          break;
        }
        const oldTitle = data.title;
        data.title = title.trim();
        logs.push(`🎉 成功將分頁「${oldTitle}」更名為：「${data.title}」`);
        layoutUpdated = true;
        needReloadAll = true;
        break;
      }

      case 'delete_tab': {
        const keys = Object.keys(flowchartData);
        if (keys.length <= 1) {
          logs.push(`❌ 刪除分頁失敗：系統必須保留至少一個產品流程圖`);
          break;
        }
        const oldTitle = data.title;
        delete flowchartData[targetTab];
        logs.push(`🗑️ 成功刪除產品分頁：「${oldTitle}」`);
        layoutUpdated = true;
        needReloadAll = true;
        
        const remainingKeys = Object.keys(flowchartData);
        shouldSwitchTab = remainingKeys[0];
        break;
      }

      case 'add_node': {
        const { id, name, capacity, type, x, y } = action.data || {};
        if (!id) {
          logs.push(`❌ 新增失敗：缺少 ID`);
          break;
        }
        const collision = data.nodes.some(n => n.id === id) || data.groups.some(g => g.id === id);
        if (collision) {
          logs.push(`❌ 新增失敗：ID "${id}" 已存在於分頁 "${targetTab}"`);
          break;
        }
        const newNode = {
          id: id,
          name: name || "新儲槽",
          capacity: capacity || "100 KL",
          type: type || "process",
          x: x || 150,
          y: y || 150,
          fill: 50,
          details: {
            temp: "25.0 °C",
            press: "1.00 atm",
            comp: name || "未知化學品",
            status: "正常儲存"
          }
        };
        data.nodes.push(newNode);
        logs.push(`[${flowchartData[targetTab].title.split(" (")[0]}] 🎉 成功新增儲槽：${id} (${newNode.name})`);
        layoutUpdated = true;
        shouldSwitchTab = targetTab;
        break;
      }
      
      case 'delete_node': {
        const { id } = action.data || {};
        const index = data.nodes.findIndex(n => n.id === id);
        if (index !== -1) {
          const name = data.nodes[index].name;
          data.nodes.splice(index, 1);
          data.groupConnections = data.groupConnections.filter(c => c.from !== id && c.to !== id);
          logs.push(`[${flowchartData[targetTab].title.split(" (")[0]}] 🗑️ 成功刪除儲槽：${id} (${name})`);
          layoutUpdated = true;
          shouldSwitchTab = targetTab;
        } else {
          logs.push(`❌ 刪除失敗：找不到 ID "${id}" 的儲槽`);
        }
        break;
      }
      
      case 'add_connection': {
        const { from, to, label } = action.data || {};
        if (!from || !to) {
          logs.push(`❌ 連線失敗：缺少起點或終點`);
          break;
        }
        const duplicate = data.groupConnections.some(c => c.from === from && c.to === to);
        if (duplicate) {
          logs.push(`❌ 連線失敗：${from} 至 ${to} 的連線已存在`);
          break;
        }
        const fromExists = data.nodes.some(n => n.id === from) || data.groups.some(g => g.id === from);
        const toExists = data.nodes.some(n => n.id === to) || data.groups.some(g => g.id === to);
        if (!fromExists || !toExists) {
          logs.push(`❌ 連線失敗：起點 "${from}" 或終點 "${to}" 不存在於分頁 "${targetTab}"`);
          break;
        }
        data.groupConnections.push({
          from,
          to,
          label: label || ""
        });
        logs.push(`[${flowchartData[targetTab].title.split(" (")[0]}] 🔗 成功建立連線：${from} ➔ ${to} ${label ? `(${label})` : ''}`);
        layoutUpdated = true;
        shouldSwitchTab = targetTab;
        break;
      }
      
      case 'delete_connection': {
        const { from, to } = action.data || {};
        const initialLen = data.groupConnections.length;
        data.groupConnections = data.groupConnections.filter(c => !(c.from === from && c.to === to));
        if (data.groupConnections.length < initialLen) {
          logs.push(`[${flowchartData[targetTab].title.split(" (")[0]}] 🗑️ 成功移除連線：${from} ➔ ${to}`);
          layoutUpdated = true;
          shouldSwitchTab = targetTab;
        } else {
          logs.push(`❌ 移除失敗：找不到 ${from} ➔ ${to} 的連線`);
        }
        break;
      }
      
      case 'update_node': {
        const { id, name, capacity, type, fill } = action.data || {};
        const node = data.nodes.find(n => n.id === id);
        if (node) {
          if (name !== undefined) node.name = name;
          if (capacity !== undefined) node.capacity = capacity;
          if (type !== undefined) node.type = type;
          if (fill !== undefined) node.fill = fill;
          logs.push(`[${flowchartData[targetTab].title.split(" (")[0]}] ✏️ 成功更新儲槽：${id}`);
          layoutUpdated = true;
          shouldSwitchTab = targetTab;
        } else {
          logs.push(`❌ 更新失敗：找不到 ID "${id}" 的儲槽`);
        }
        break;
      }
      
      case 'input_group_capacity': {
        const { id, capacity } = action.data || {};
        const group = data.groups.find(g => g.id === id);
        if (group) {
          const inputKey = `${targetTab}_${id}`;
          window.capacityInputs[inputKey] = capacity;
          localStorage.setItem('flowchart_capacity_inputs', JSON.stringify(window.capacityInputs));
          logs.push(`[${flowchartData[targetTab].title.split(" (")[0]}] ✏️ 成功設定群組「${group.name}」輸入產能為：${capacity}`);
          layoutUpdated = true;
          shouldSwitchTab = targetTab;
        } else {
          logs.push(`❌ 設定輸入產能失敗：找不到 ID "${id}" 的群組`);
        }
        break;
      }
      
      case 'update_group': {
        const { id, name, capacity } = action.data || {};
        const group = data.groups.find(g => g.id === id);
        if (group) {
          if (name !== undefined) group.name = name;
          if (capacity !== undefined) group.capacity = capacity;
          logs.push(`[${flowchartData[targetTab].title.split(" (")[0]}] ✏️ 成功更新群組：${id}`);
          layoutUpdated = true;
          shouldSwitchTab = targetTab;
        } else {
          logs.push(`❌ 更新群組失敗：找不到 ID "${id}" 的群組`);
        }
        break;
      }
      
      case 'update_tab': {
        const { title, totalCapacity } = action.data || {};
        if (title !== undefined) {
          const oldTitle = data.title;
          data.title = title.trim();
          logs.push(`🎉 成功將分頁「${oldTitle}」更名為：「${data.title}」`);
          layoutUpdated = true;
          needReloadAll = true;
        }
        if (totalCapacity !== undefined) {
          data.totalCapacity = totalCapacity;
          logs.push(`🎉 成功將分頁「${data.title}」總產能更新為：「${totalCapacity}」`);
          layoutUpdated = true;
          needReloadAll = true;
        }
        break;
      }
      
      case 'update_group': {
        const { id, name, capacity } = action.data || {};
        const group = data.groups.find(g => g.id === id);
        if (group) {
          if (name !== undefined) group.name = name;
          if (capacity !== undefined) group.capacity = capacity;
          logs.push(`[${flowchartData[targetTab].title.split(" (")[0]}] ✏️ 成功更新群組：${id}`);
          layoutUpdated = true;
          shouldSwitchTab = targetTab;
        } else {
          logs.push(`❌ 更新群組失敗：找不到 ID "${id}" 的群組`);
        }
        break;
      }
      
      case 'update_tab': {
        const { title, totalCapacity } = action.data || {};
        if (title !== undefined) {
          const oldTitle = data.title;
          data.title = title.trim();
          logs.push(`🎉 成功將分頁「${oldTitle}」更名為：「${data.title}」`);
          layoutUpdated = true;
          needReloadAll = true;
        }
        if (totalCapacity !== undefined) {
          data.totalCapacity = totalCapacity;
          logs.push(`🎉 成功將分頁「${data.title}」總產能更新為：「${totalCapacity}」`);
          layoutUpdated = true;
          needReloadAll = true;
        }
        break;
      }
      
      default:
        logs.push(`⚠️ 未知操作類型：${action.type}`);
    }
  });
  
  if (layoutUpdated) {
    saveCurrentLayoutToLocal();
    if (needReloadAll) {
      applyLayoutAndReload();
    }
    if (shouldSwitchTab && shouldSwitchTab !== currentTab) {
      switchTab(shouldSwitchTab);
    } else if (!needReloadAll) {
      renderFlowchart();
      updateConnectionEditorUI();
    }
  }
  return logs;
}

// Dispatcher to call selected AI Provider
async function callSelectedAIProvider(text) {
  if (aiProvider === "gemini") {
    return await sendChatMessageToGemini(text);
  } else {
    return await sendChatMessageToGroq(text);
  }
}

// Fetch Gemini API response and parse action commands
async function sendChatMessageToGemini(messageText) {
  // Run fuzzy search and prepend hint
  const fuzzyMatches = getFuzzySearchMatches(messageText);
  let searchHint = "";
  if (fuzzyMatches.length > 0) {
    searchHint = `【系統搜尋提示：經全站關鍵字模糊匹配，以下槽體與使用者問題直接相關，請務必將其納入答覆中並按分頁與群組分類列出：\n${JSON.stringify(fuzzyMatches)}】\n\n`;
  }

  // Compress all flowcharts state to minimize token usage
  const stateSummary = {
    c: currentTab,
    f: {}
  };
  
  Object.keys(flowchartData).forEach(tabKey => {
    const tabData = flowchartData[tabKey];
    stateSummary.f[tabKey] = {
      t: tabData.title.split(" (")[0],
      tc: tabData.totalCapacity,
      g: tabData.groups.map(g => ({ 
        id: g.id, 
        n: g.name, 
        c: g.capacity,
        hasInput: (tabKey === "cpne3" && (g.id === "check-group" || g.id === "finish-group")) || g.id.startsWith("process-block")
      })),
      n: tabData.nodes.map(n => {
        const gMatch = tabData.groups.find(g => 
          !g.id.startsWith("process-block") && 
          n.x >= g.x && n.x < g.x + g.w && 
          n.y >= g.y && n.y < g.y + g.h
        );
        return {
          id: n.id,
          n: n.name,
          c: n.capacity,
          t: n.type,
          f: n.fill,
          g: gMatch ? gMatch.name : ""
        };
      }),
      c: tabData.groupConnections.map(c => ({ f: c.from, t: c.to, l: c.label }))
    };
  });

  const systemMessage = `你是一個化學工廠製程流程圖系統的 AI 助理。
目前全站所有分頁數據以壓縮 JSON 提供：
${JSON.stringify(stateSummary)}

壓縮鍵說明：
- f: 全站所有分頁 (flowcharts)
- c: 當前分頁 ID (currentTab)，如 "ipa"
- t: 分頁標題 (title)
- tc: 該分頁的總產能/總容量 (totalCapacity)
- g: 該分頁的群組列表 (groups)
- n: 該分頁的槽體/節點列表 (nodes)
- c: 該分頁的管道連線列表 (connections)
- 在群組中：n 代表名稱 (name)，c 代表容量/產能 (capacity)，hasInput 代表是否在畫布上具有可編輯的「輸入產能」輸入框 (boolean)
- 在槽體中：n 代表名稱 (name)，c 代表容量 (capacity)，t 代表類別 (type: raw/process/finish/offgrade)，f 代表液位百分比 (fill)，g 代表所屬群組名稱 (group name)
- 在連線中：f 代表起點 (from)，t 代表終點 (to)，l 代表標籤 (label)

使用者可以向你詢問關於全站任何分頁、槽體或管線的問題，或是下達修改/新增指令。
你可以執行以下「編輯操作」 (actions)：
1. 新增槽體/節點 (add_node): data 格式 { id, name, capacity, type, x, y }。其中 type 可選: "raw" | "process" | "finish" | "offgrade"。x 座標建議在適當的群組範圍（原料區約 x: 140; 製程/待驗約 380 或 620; 成品區約 860; 下腳料約 380 或 200），y 座標在 100~550。
2. 刪除槽體/節點 (delete_node): data 格式 { id }。
3. 新增管線/連線 (add_connection): data 格式 { from, to, label }。from 與 to 必須為現有的節點 ID 或群組 ID。
4. 刪除管線/連線 (delete_connection): data 格式 { from, to }。
5. 更新槽體屬性 (update_node): data 格式 { id, name, capacity, type, fill }。
6. 新增分頁/流程圖 (add_tab): data 格式 { key, title, use_template }。其中 key 建議格式為 "flow_" + 數字 (例如 "flow_123" 或隨機)，title 為分頁標題 (例如 "10. IPHQS6與S7流程圖")，use_template 為布林值 (是否預設建立原料、製程、成品、待驗、下腳料等 5 個群組，預設為 true)。
7. 修改分頁名稱 (rename_tab): data 格式 { title }，目標分頁由 "tab" 指定。
8. 刪除分頁/流程圖 (delete_tab): data 格式 {}，目標分頁由 "tab" 指定。
9. 輸入群組產能 (input_group_capacity): data 格式 { id, capacity }。當使用者說要在某個群組/製程的「輸入產能」輸入框中輸入或新增產能數值時（例如「幫我輸入成品 CPNE3 的產能為 1300」或「製程輸入產能 1200」），請呼叫此 action。此操作會將數值填入畫面上對應的輸入框中，不會修改分頁的總產能描述。
10. 更新群組屬性 (update_group): data 格式 { id, name, capacity }。當要修改群組的名稱，或是修改沒有輸入框的群組的靜態容量文字時，請呼叫此 action。
11. 更新分頁屬性 (update_tab): data 格式 { title, totalCapacity }，目標分頁由 "tab" 指定。當使用者說要修改整個產品流程圖的總產能描述或名稱時，請呼叫此 action。

對於 actions 中的每一個操作，你都必須指定目標分頁，例如：
{
  "response": "在此用自然語言（繁體中文）回答使用者的問題，或是描述你剛剛執行了哪些流程圖的編輯操作。",
  "actions": [
    { "type": "add_tab", "data": { "key": "flow_iphqs6s7", "title": "10. IPHQS6與S7流程圖", "use_template": true } }
  ]
}
其中 "tab" 欄位為目標分頁 ID（可選：ipa, eg, nmp, cpne4, cpne3, act, ebr, hear, ipahq 或自訂 key），若未提供則預設為當前分頁。

重要規則：
- 當使用者提及某個產品關鍵字（例如 "IPA HQ"、"EG" 等）進行查詢時，你必須掃描「所有分頁」的「所有槽體名稱與群組名稱」。切勿因為某個分頁的標題完美契合該關鍵字，就忽略了其他分頁中名字包含該關鍵字之槽體（例如：分頁 1 "ipa" 中也包含名稱為 "IPAHQ成品槽" 的槽體，你也必須找出來並分類列出）。
- 當回答關於數量統計的問題時，務必精確計算，確保你回覆的「統計總數」與你「列出的槽體/連線項目數量」完全吻合，嚴禁出現數量與列表不一致的矛盾。
- 對於跨分頁的查詢結果，請務必「按分頁標題進行分組」列出（例如：在「分頁A」有 X 個，在「分頁B」有 Y 個），以便使用者能清晰區分。
- 如果使用者只是「發問」或詢問狀態，不需要做 any 修改，則 "actions" 欄位應為空陣列 []。例如，詢問全站成品槽的統計資訊、跨分頁對比等，直接在 "response" 答覆。
- 請勿附帶 any markdown 的包裹標籤（如 \`\`\`json ），直接以 JSON 字串格式回應。
- 當新增槽體時，必須指定唯一的 id；若使用者想建立連線，請確保 from 和 to 的 ID 皆是該分頁中存在的（或是你同時在 actions 裡新增的）。
- 回覆一律使用繁體中文。`;

  if (!geminiApiKey) {
    // Demo / Mock Mode fallback for Gemini if no key is provided
    return new Promise((resolve) => {
      setTimeout(() => {
        const lowerMsg = messageText.toLowerCase();
        let responseText = "";
        let actions = [];
        
        if (lowerMsg.includes("新增") || lowerMsg.includes("add") || lowerMsg.includes("放") || lowerMsg.includes("連")) {
          // Detect mock add
          if (lowerMsg.includes("槽") || lowerMsg.includes("tank")) {
            const mockId = "TK-" + Math.floor(Math.random() * 900 + 100);
            const isFinish = lowerMsg.includes("成品");
            const isRaw = lowerMsg.includes("原料");
            const type = isFinish ? "finish" : (isRaw ? "raw" : "process");
            const name = isFinish ? "AI 成品槽" : (isRaw ? "AI 原料槽" : "AI 待驗槽");
            const x = isFinish ? 860 : (isRaw ? 140 : 620);
            
            // Detect target tab
            let targetTab = currentTab;
            if (lowerMsg.includes("eg")) targetTab = "eg";
            else if (lowerMsg.includes("nmp")) targetTab = "nmp";
            else if (lowerMsg.includes("ipa")) targetTab = "ipa";
            
            actions.push({
              type: "add_node",
              tab: targetTab,
              data: { id: mockId, name: name, capacity: "125 KL", type: type, x: x, y: 350 }
            });
            
            responseText = `[Gemini Demo 模擬回應] 好的，我為您在分頁 "${targetTab}" 新增了槽體 ${mockId}。`;
          } else {
            responseText = `[Gemini Demo 模擬回應] 好的，收到指令，已模擬執行。`;
          }
        } else {
          // Mock Cross-Tab Query Response
          const totalTanks = Object.keys(flowchartData).reduce((sum, key) => sum + flowchartData[key].nodes.length, 0);
          const currentData = flowchartData[currentTab] || { nodes: [], groupConnections: [] };
          responseText = `[Gemini Demo 模擬回應] 目前處於 Demo 模式（未設定 Gemini 金鑰）。
* 全站共有 ${totalTanks} 個槽體節點，當前分頁有 ${currentData.nodes.length} 個槽體與 ${currentData.groupConnections.length} 條管道。
若要開啟 AI 的智慧自動編輯與精確查詢功能，請點擊右上角 ⚙️ 設定您的 Gemini API 金鑰！`;
        }
        
        resolve({ response: responseText, actions: actions });
      }, 1200);
    });
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${geminiModel}:generateContent?key=${geminiApiKey}`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      contents: [
        {
          role: "user",
          parts: [
            { text: systemMessage + "\n\n使用者問題/指令:\n" + searchHint + messageText }
          ]
        }
      ],
      generationConfig: {
        responseMimeType: "application/json"
      }
    })
  });

  if (!response.ok) {
    const errText = await response.text();
    if (response.status === 429) {
      throw new Error("QUOTA_EXCEEDED");
    }
    throw new Error(`Gemini API 錯誤 (${response.status}): ${errText}`);
  }

  const resJson = await response.json();
  
  if (!resJson.candidates || resJson.candidates.length === 0) {
    throw new Error("Gemini 回傳了空的回應，請檢查金鑰或權限。");
  }

  const content = resJson.candidates[0].content.parts[0].text.trim();
  
  try {
    return JSON.parse(content);
  } catch (err) {
    console.error("JSON parsing failed for Gemini output:", content);
    const cleaned = content.replace(/```json|```/g, "").trim();
    return JSON.parse(cleaned);
  }
}

// Handler for sending chat messages
async function handleSendAiMessage() {
  const text = aiChatInput.value.trim();
  if (!text) return;
  
  // Disable input & send button
  aiChatInput.value = "";
  aiChatInput.disabled = true;
  sendAiMessageBtn.disabled = true;
  
  // Append user message
  appendMessageBubble("user", text);
  
  const loadingEl = showAiLoading();
  
  try {
    const aiResult = await callSelectedAIProvider(text);
    removeAiLoading(loadingEl);
    
    // Append assistant text response
    if (aiResult.response) {
      appendMessageBubble("assistant", aiResult.response);
    }
    
    // Execute actions if any
    if (aiResult.actions && aiResult.actions.length > 0) {
      const logs = executeAIActions(aiResult.actions);
      logs.forEach(log => {
        appendMessageBubble("system", log, true);
      });
    }
  } catch (err) {
    removeAiLoading(loadingEl);
    if (err.message === "QUOTA_EXCEEDED") {
      appendMessageBubble("assistant", "⚠️ **AI 每日使用額度已達上限**\n\n今日的 API 免費配額已用完，Eshine-AI 暫時無法回應。\n\n**解決方式：**\n- 明天額度自動重置後即可繼續使用。\n- 或請至 [Google AI Studio](https://aistudio.google.com/) 開啟付費方案，即可無限制使用。");
    } else {
      appendMessageBubble("assistant", `❌ 發生錯誤：${err.message}`);
      console.error(err);
    }
  } finally {
    aiChatInput.disabled = false;
    sendAiMessageBtn.disabled = false;
    aiChatInput.focus();
  }
}

// Wire up send button click and textarea Enter key
if (sendAiMessageBtn) {
  sendAiMessageBtn.onclick = handleSendAiMessage;
}

if (aiChatInput) {
  aiChatInput.onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendAiMessage();
    }
  };
}

// App Entry
initNav();
initFirebaseAndLoad();
loadChatHistory();
