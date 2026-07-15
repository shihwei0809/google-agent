// ============================================================
// 📋 Google Apps Script — 員工教育訓練簡報與測驗系統 (氮氣閥專用)
// 版本：6.0（乾淨無冗餘版，支援自動出題、自動校對與成績回收）
// ============================================================

const SHEET_SLIDES    = '簡報設定';   // 簡報朗讀文字的工作表名稱
const SHEET_QUESTIONS = '題目設定';   // 出題用的工作表名稱
const SHEET_ANSWERS   = '作答紀錄';   // 回收答案的工作表名稱

// ── doGet：提供簡報設定與題目給網頁讀取 ──────────────────────────────
function doGet(e) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // 1. 處理簡報設定（SLIDES）
    let sSheet = ss.getSheetByName(SHEET_SLIDES);
    if (!sSheet) {
      sSheet = createSampleSlidesSheet(ss);
    }
    const sRows = sSheet.getDataRange().getValues();
    const slides = [];
    for (let i = 1; i < sRows.length; i++) {
      const r = sRows[i];
      if (!r[1] || String(r[1]).trim() === '') continue; // 圖片路徑不能為空
      slides.push({
        img:   String(r[1]).trim(),
        label: String(r[2]).trim(),
        say:   String(r[3]).trim()
      });
    }

    // 2. 處理題目設定（QUESTIONS）
    let qSheet = ss.getSheetByName(SHEET_QUESTIONS);
    if (!qSheet) {
      qSheet = createSampleQuestionsSheet(ss);
    }
    const qRows = qSheet.getDataRange().getValues();
    const questions = [];
    for (let i = 1; i < qRows.length; i++) {
      const r = qRows[i];
      if (!r[1] || String(r[1]).trim() === '') continue; // 題目不為空
      questions.push({
        num:      i,
        question: String(r[1]).trim(),
        a:        String(r[2]).trim(),
        b:        String(r[3]).trim(),
        c:        String(r[4]).trim(),
        d:        String(r[5]).trim()
      });
    }

    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok', slides: slides, questions: questions }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ── doPost：接收員工答案、自動核對正確答案並寫入 Sheet ───────────────────────
function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const ss   = SpreadsheetApp.getActiveSpreadsheet();
    let aSheet = ss.getSheetByName(SHEET_ANSWERS);

    // 若「作答紀錄」頁不存在，自動建立
    if (!aSheet) {
      aSheet = ss.insertSheet(SHEET_ANSWERS);
    }

    // 讀取題目設定與正確答案
    const qSheet = ss.getSheetByName(SHEET_QUESTIONS);
    const qRows  = qSheet ? qSheet.getDataRange().getValues() : [];
    const qCount = Math.max(0, qRows.length - 1); // 扣掉標題列

    const correctAnswers = [];
    for (let i = 1; i < qRows.length; i++) {
      const r = qRows[i];
      if (!r[1] || String(r[1]).trim() === '') continue;
      // 正確答案在 G 欄（索引值為 6）
      correctAnswers.push(String(r[6] || '').trim().toUpperCase());
    }

    // 初始化作答紀錄的標題列（若新建立或全空）
    if (aSheet.getLastRow() === 0) {
      const headers = ['時間戳記', '姓名', '得分'];
      for (let i = 1; i <= qCount; i++) {
        headers.push('第 ' + i + ' 題作答');
      }
      aSheet.appendRow(headers);
      
      // 標題樣式
      const hr = aSheet.getRange(1, 1, 1, headers.length);
      hr.setBackground('#1a73e8');
      hr.setFontColor('#ffffff');
      hr.setFontWeight('bold');
    }

    // 計算得分
    let score = 0;
    const userAnswers = [];
    for (let i = 1; i <= qCount; i++) {
      const ansKey = 'q' + i;
      const userAns = String(data[ansKey] || '').trim().toUpperCase();
      userAnswers.push(userAns);
      
      const correctAns = correctAnswers[i - 1];
      if (userAns === correctAns) {
        score += 100 / qCount;
      }
    }
    score = Math.round(score);

    // 寫入資料列
    const rowData = [
      data.timestamp || new Date(),
      data.name || '未輸入姓名',
      score
    ].concat(userAnswers);

    aSheet.appendRow(rowData);
    aSheet.autoResizeColumns(1, rowData.length);

    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok', score: score }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ── 建立範例簡報工作表 ──────────────────────────────────────
function createSampleSlidesSheet(ss) {
  const sheet = ss.insertSheet(SHEET_SLIDES);
  
  // 標題列
  const headers = ['頁數', '圖片路徑', '單頁標題', '語音內容'];
  sheet.appendRow(headers);
  
  // 標題列樣式
  const hr = sheet.getRange(1, 1, 1, headers.length);
  hr.setBackground('#1a73e8');
  hr.setFontColor('#ffffff');
  hr.setFontWeight('bold');
  
  // 範例簡報內容
  const sampleSlides = [
    [1, 'slides/slide_01.png', '第 1 頁｜作動原理教育訓練', '各位同仁好，歡迎參加本次教育訓練。今天我們要學習的是「儲槽氮氣閥與氮封系統之作動原理」。氮封系統是石化及化學工廠中，保護儲槽安全、防止火災爆炸及防止物料變質的重要安全設施。請大家仔細學習其作動機制。'],
    [2, 'slides/slide_02.png', '第 2 頁｜什麼是氮封系統？', '氮封系統的主要目的，是在儲槽頂部的氣相空間充入惰性氮氣，維持微正壓。這樣做有三個核心作用：第一，排除氧氣，避免形成爆炸性混合氣體；第二，防止外部空氣及水氣進入，避免物料氧化、受潮或變質；第三，透過精密閥門控制，避免儲槽因溫度變化或物料進出而發生超壓變形或真空癟罐。'],
    [3, 'slides/slide_03.png', '第 3 頁｜供氮閥作動原理', '供氮閥是一種自力式微壓調節閥。當儲槽進行出料操作，或夜間氣溫下降使槽內氣體收縮時，儲槽內的壓力會開始下降。當槽內壓力低於供氮閥的設定點時，控制膜片受壓減小，彈簧推動閥芯開啟，氮氣隨之流入槽內。當槽內壓力回升到設定值時，膜片克服彈簧力，帶動閥芯關閉，停止供氮。'],
    [4, 'slides/slide_04.png', '第 4 頁｜洩氮閥作動原理', '與供氮閥相反，洩氮閥負責槽內超壓時的排氣。當儲槽進行進料操作，或日間太陽曝曬使槽內溫度升高時，槽內壓力會上升。當壓力高於洩氮閥的設定點時，槽內壓力推動膜片克服彈簧力，使閥門開啟，將槽內多餘 of 氮氣或混合氣體排出。當槽內壓力降回設定值時，閥門自動關閉，維持系統微正壓。'],
    [5, 'slides/slide_05.png', '第 5 頁｜雙重安全保障機制', '為了防止供氮閥或洩氮閥故障，儲槽設有雙重防護機制。第一重是安全呼吸閥，在槽內壓力達到極限高壓或真空度時，分別向外排氣或向內吸入空氣，防止儲槽破裂或吸扁。第二重是緊急洩爆人孔，當遭遇外部大火導致槽內急劇升壓時，洩爆人孔會瞬間開啟，進行大排量洩壓，是儲槽的最終安全保障。'],
    [6, 'slides/slide_06.png', '第 6 頁｜教育訓練總結', '本次課程我們學習了氮封系統「降壓補充、升壓排放」的自力式反饋原理，以及呼吸閥與緊急洩爆孔的雙重安全保護機制。請同仁務記各閥門的作動方向與目的。簡報播放已結束，請點擊下方按鈕，填寫姓名並開始進行課後測驗，祝大家順利通過！']
  ];
  
  sampleSlides.forEach(s => {
    sheet.appendRow(s);
  });
  
  sheet.autoResizeColumns(1, headers.length);
  sheet.setColumnWidth(1, 60);  // 頁數
  sheet.setColumnWidth(2, 150); // 圖片路徑
  sheet.setColumnWidth(3, 200); // 頁籤標題
  sheet.setColumnWidth(4, 500); // 語音內容
  sheet.setFrozenRows(1);
  return sheet;
}

// ── 建立範例題目工作表 ──────────────────────────────────────
function createSampleQuestionsSheet(ss) {
  const sheet = ss.insertSheet(SHEET_QUESTIONS);

  // 標題列
  const headers = ['題號（自動）', '題目', '選項 A', '選項 B', '選項 C', '選項 D', '正確答案（僅供參考）'];
  sheet.appendRow(headers);

  // 標題列樣式
  const hr = sheet.getRange(1, 1, 1, headers.length);
  hr.setBackground('#34a853');
  hr.setFontColor('#ffffff');
  hr.setFontWeight('bold');

  // 範例題目
  const sampleQ = [
    ['', '關於儲槽氮封系統的主要目的，以下何者錯誤？', 'A. 充入惰性氮氣以排除氧氣，防止火災與爆炸', 'B. 防止外部空氣與水分進入，保護槽內物料不變質', 'C. 使儲槽內部維持微正壓，保護槽體結構安全', 'D. 為了冷卻槽內液體，降低儲槽的整體操作溫度', 'D'],
    ['', '當儲槽進行「出料（泵出）」或「溫度降低」時，儲槽壓力會如何變化？此時哪一個閥門會自動開啟？', 'A. 儲槽壓力上升；洩氮閥開啟', 'B. 儲槽壓力下降；供氮閥開啟', 'C. 儲槽壓力上升；供氮閥開啟', 'D. 儲槽壓力下降；洩氮閥開啟', 'B'],
    ['', '氮封系統中的供氮閥與洩氮閥，通常採用何種形式的閥門來達到自動控制？', 'A. 需要外部電源驅動的電動球閥', 'B. 需要氣源信號控制的氣動調節閥', 'C. 無需外部動力、利用儲槽壓力自我反饋的自力式調節閥', 'D. 需要人工手動操作的閘閥', 'C'],
    ['', '當槽內壓力因異常狀況急劇升高，且洩氮閥來不及排放時，下列哪一個安全防護設施會首先發揮排氣作用以防止儲槽超壓破裂？', 'A. 安全呼吸閥 (Breather Valve)', 'B. 緊急洩爆人孔 (Emergency Vent)', 'C. 供氮閥 (Nitrogen Supply Valve)', 'D. 排泥閥 (Drain Valve)', 'A'],
    ['', '為了避免儲槽在極端真空狀態下被大氣壓「吸扁（癟罐）」，安全呼吸閥的真空閥座在達到設定真空度時會進行什麼作動？', 'A. 關閉閥門，完全封鎖槽內氣體', 'B. 開啟閥門，允許外部空氣進入槽內以平衡壓力', 'C. 開啟供氮閥，以超高壓注入更多氮氣', 'D. 開啟排泥閥，把槽內液體排出', 'B']
  ];
  
  sampleQ.forEach(q => {
    sheet.appendRow(q);
  });
  
  sheet.autoResizeColumns(1, headers.length);
  sheet.setColumnWidth(1, 90);  // 題號
  sheet.setColumnWidth(2, 350); // 題目
  sheet.setColumnWidth(3, 100); // 選項 A
  sheet.setColumnWidth(4, 100); // 選項 B
  sheet.setColumnWidth(5, 100); // 選項 C
  sheet.setColumnWidth(6, 100); // 選項 D
  sheet.setColumnWidth(7, 120); // 正確答案
  sheet.setFrozenRows(1);

  return sheet;
}

// ── 測試函式 ──────────────────────────────────────
function testGetQuestions() {
  const result = doGet({});
  Logger.log(result.getContent());
}

function testSubmitAnswer() {
  const fakePost = {
    postData: {
      contents: JSON.stringify({
        timestamp: '2026/06/24 16:00:00',
        name: '測試人員',
        q1: 'B', q2: 'C', q3: 'D', q4: 'B', q5: 'C'
      })
    }
  };
  const result = doPost(fakePost);
  Logger.log(result.getContent());
}
