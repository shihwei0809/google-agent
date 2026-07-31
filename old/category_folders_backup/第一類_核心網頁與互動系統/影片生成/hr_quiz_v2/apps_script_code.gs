// ============================================================
// 📋 Google Apps Script — 員工教育訓練簡報與測驗系統
// 版本：5.0（支援 自動欄寬調整 + 欄位自動校對 + 雲端出題與朗讀管理）
// ============================================================
//
// 【Google Sheet 結構】
//   需要三個工作表（頁籤）：
//   1. 「簡報設定」— 管理簡報的圖片路徑、標題、與語音朗讀腳本
//   2. 「題目設定」— 出題人員在此填寫題目、選項與正確答案
//   3. 「作答紀錄」— 員工作答後自動核對並寫入得分與詳細回答
//
// 【部署方式】
//   1. 開啟您的 Google Sheet
//   2. 擴充功能 → Apps Script → 貼上此程式碼
//   3. 部署 → 新增部署作業 → 網頁應用程式
//   4. 執行身分：我 ／ 誰可以存取：所有人
//   5. 複製部署 URL 貼入 index.html 的 APPS_SCRIPT_URL
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

    // 自動核對答案，計算答對題數與得分
    let correctCount = 0;
    for (let i = 1; i <= qCount; i++) {
      const userAnswer = String(data['q' + i] || '').trim().toUpperCase();
      const correctAnswer = correctAnswers[i - 1] || '';
      if (userAnswer && userAnswer === correctAnswer) {
        correctCount++;
      }
    }
    const score = qCount > 0 ? Math.round((correctCount / qCount) * 100) : 0;

    // 檢查現有標題列是否包含「答對題數」，若不包含代表是舊版結構，自動重設以防欄位錯位
    const headerValues = aSheet.getLastRow() > 0 ? aSheet.getRange(1, 1, 1, aSheet.getLastColumn()).getValues()[0] : [];
    const hasCorrectCountHeader = headerValues.indexOf('答對題數') >= 0;

    if (aSheet.getLastRow() === 0 || !hasCorrectCountHeader) {
      aSheet.clear(); // 清除舊版格式與殘留資料
      const headers = ['時間戳記', '姓名', '答對題數', '得分'];
      for (let i = 1; i <= qCount; i++) {
        headers.push('第' + i + '題');
      }
      aSheet.appendRow(headers);

      // 標題列樣式
      const hr = aSheet.getRange(1, 1, 1, headers.length);
      hr.setBackground('#1a73e8');
      hr.setFontColor('#ffffff');
      hr.setFontWeight('bold');
      hr.setHorizontalAlignment('center');
      aSheet.setFrozenRows(1);
    }

    // 組合這次提交的資料列
    const row = [
      data.timestamp || new Date().toLocaleString('zh-TW'),
      data.name      || '',
      correctCount + ' / ' + qCount,
      score + ' 分'
    ];
    for (let i = 1; i <= qCount; i++) {
      row.push(data['q' + i] || '');
    }

    aSheet.appendRow(row);

    // 格式優化：自動調整欄寬並設定最小安全寬度，防止標題被擠壓
    aSheet.autoResizeColumns(1, row.length);
    aSheet.setColumnWidth(1, 150); // 時間戳記
    aSheet.setColumnWidth(2, 100); // 姓名
    aSheet.setColumnWidth(3, 85);  // 答對題數
    aSheet.setColumnWidth(4, 85);  // 得分
    for (let i = 5; i <= row.length; i++) {
      aSheet.setColumnWidth(i, 65); // 第 N 題，剛好完整顯示「第10題」不換行
    }

    return ContentService
      .createTextOutput(JSON.stringify({ 
        status: 'success', 
        score: score, 
        correctCount: correctCount, 
        total: qCount 
      }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ── 建立範例簡報設定工作表 ──────────────────────────────────────
function createSampleSlidesSheet(ss) {
  const sheet = ss.insertSheet(SHEET_SLIDES);
  
  // 標題列
  const headers = ['頁數', '圖片路徑', '單頁標題', '語音朗讀內容'];
  sheet.appendRow(headers);
  
  // 標題列樣式
  const hr = sheet.getRange(1, 1, 1, headers.length);
  hr.setBackground('#4285f4');
  hr.setFontColor('#ffffff');
  hr.setFontWeight('bold');
  
  // 簡報預設資料
  const sampleSlides = [
    [1, 'slides/slide_01.png', '從業人員工作規則（封面）', '歡迎各位同仁。本次教育訓練簡報為「從業人員工作規則」，文件編號 SCI-PEL-01，版別二點零版。本規則依據勞動基準法及有關法令訂定，目的是建立完善勞資關係，保障全員工作福祉與營運安全。'],
    [2, 'slides/slide_02.png', '第一部分：總則與基本守則', '第一部分：總則與基本守則。本部分說明工作規則的目的、適用範疇、相關參考文件、安全守則與保密限制。'],
    [3, 'slides/slide_03.png', '1.0 目的、範圍與修訂歷程', '1.1 目的：為使本公司從業人員之管理有所遵循，特依據勞動基準法及有關法令規定訂定本規則，以促進勞雇和諧，並確保從業人員合法權益。2.0 適用範圍：適用於本公司全體同仁。本規則已完成文件修訂，並獲彰化縣政府核備。'],
    [4, 'slides/slide_04.png', '2.0 相關參考文件體系', '2.0 相關參考文件體系。薪酬與福利制度方面，包括 C10-PEL-01 薪資給付辦法、C10-PEL-02 年終獎金發放辦法，以及 C10-PEL-11 婚喪喜慶賀奠儀辦法。考勤與異動程序方面，包括 C10-PEL-03 考勤管理辦法、C10-PEL-05 增補異動管理辦法，以及 C10-PEL-06 晉升及調任管理辦法。權益保障與規範方面，包括 C10-PEL-13 人事評議委員會辦法、C10-PEL-16 性騷擾防治申訴辦法，以及 C10-PEL-21 勞資會議實施辦法。'],
    [5, 'slides/slide_05.png', '3.0 員工基本守則與安全保密義務', '3.0 員工基本守則與安全保密義務。職場安全與防護義務：廠區一律嚴禁吸菸；未經許可不得起動備用及停用機器。上班時應穿著公司制服，在廠區工作時必須配戴安全帽並嚴格遵守安全衛生工作守則。業務與職務秘密保守義務：員工應保守業務上或職務上知悉之所有秘密，此義務縱使於離職後仍應保密。職務報告應循序而上，不得越級。指派活動強制參與：無正當理由不得拒絕參加公司辦理之在職訓練、健康檢查、防災演練、緊急應變召喚或會議慶典等假日值勤任務。毀損公物、財務應負雙方協商賠償之責。'],
    [6, 'slides/slide_06.png', '第二部分：受僱、調動與解僱程序', '第二部分：受僱、調動與解僱程序。本部分說明新進招募流程、考核期規定、免預告解僱條款與資遣機制。'],
    [7, 'slides/slide_07.png', '4.0 員工招募與試用期考核機制', '4.0 員工招募與試用期考核機制。嚴謹甄選，雙向評估。法定限制：本公司禁止聘僱法定傳染病者，或經指定體檢醫院體檢不合格，無法擔任工作者。考核期程：新進同仁到職 40天 及見習期滿 3個月 各實施一次考核評估。未達標處理：若考核成績未滿 60分，將終止僱用，薪資結算至停止試用當日，並依勞基法與勞工退休金條例規定辦理。'],
    [8, 'slides/slide_08.png', '5.0 不經預告終止契約條款（免職）', '5.0 不經預告終止契約條款，即免職條款。違背誠信與法令之情事包括：第一，吸食、施打毒品或使用違禁麻醉藥品。第二，攜帶槍砲、彈藥、刀械等違禁品進入工作場所，危害財產或生命安全。第三，訂立契約時為虛偽意思表示，使公司誤信有受損害之虞。第四，連續曠工3日，或一個月內曠工達6日者。第五，職場霸凌致使受害者身心異常者。損害公司利益或暴力行為包括：第六，對雇主、家屬、代理人或同仁實施暴行或重大侮辱。第七，營私舞弊、挪用公款、收受賄賂或佣金。第八，故意損耗器具、料品，或故意洩漏公司技術、營業秘密者。第九，一年內受處分累計達3大過者。以上各款免職處分，員工不得請求加發預告工資及資遣費。'],
    [9, 'slides/slide_09.png', '第 9 頁', '請同仁注意本頁相關規定。'],
    [10, 'slides/slide_10.png', '7.0 離職移交程序與異常處理', '7.0 離職移交程序與異常處理。職務移交對象與清冊列管：員工離職須於10日前辦妥移交，項目涵蓋主管之員工清冊、現款、帳表、設備器具、技術及經營資料、電腦系統檔案與未結待辦事項。移交清冊須由移交、接交及監交三方簽章。異常、亡故與失蹤代理期限：員工因傷病亡故、失蹤或逃匿時，其直接主管應於10日內指定人員代辦移交，接任人查有遺漏應於核決後3日內補辦清楚。逾期不移交與不實遺漏懲處：逾期不移交者簽報懲處，情節重大者移送司法偵辦。接交後若有虛捏遺漏，前任嚴懲追償，直屬主管連帶議處，自行揭報者免罰。'],
    [11, 'slides/slide_11.png', '第三部分：工作時間、休息與請假規定', '第三部分：工作時間、休息與請假規定。本部分說明工作班次、出差規定、請假辦法與特別休假基準。'],
    [12, 'slides/slide_12.png', '8.0 工作時間與輪班作息規定', '8.0 工作時間與輪班作息規定。規範化工時，落實輪班休息。正常工時：每日不得超過8小時，每週不得超過40小時。實施三班制或輪班時，班次每週更換一次，更換時應給予至少11小時連續休息。三班起訖時間，連續工作4小時休息30分鐘：日班08:00至16:00，中班16:00至24:00，晚班00:00至08:00。出差補休：出差國外逾一週者，返家次日准予休假1日。天災事變緊急工作後，補休工資照給。'],
    [13, 'slides/slide_13.png', '9.0 特別休假給假標準（曆年制）', '9.0 特別休假給假標準，曆年制。本公司採曆年制特別休假，由員工自行排定之，最小動用單位為2小時。留職停薪期間，概不給予特休。年資對照表：新進報到日當天給予3天，服務滿 1年以上未滿 2年給予 7天，服務滿 2年以上未滿 3年給予 10天，服務滿 3年以上未滿 5年給予 14天，服務滿 5年以上未滿 10年給予 15天，服務滿 10年以上者每滿 1年加給 1天，上限 30天。特別休假因年度終結或契約終止而未休畢之日數，雇主應發給工資。'],
    [14, 'slides/slide_14.png', '10.0 請假規範：事假、普通傷病假與公傷假', '10.0 請假規範：事假、普通傷病假與公傷假。事假與普通傷病假之計薪：第一，事假：全年累計限 14日。課長級（含）以上主管薪資照給，其他員工不給薪。第二，病假：未住院限 30日，住院者二年內累計不得超逾一年，連續 2日以上病假須出具醫院證明。30日以內病假，課長級以上主管薪資照給，其他員工折半發給；超過 30日病假，課長級以上折半發給，其他員工僅請領勞保傷病補助，不另發薪。留職停薪與公傷病假：第三，普通傷病留職停薪：傷病假超額抵充特休後仍未痊癒，可辦理留停，以一年為限，屆滿仍未痊癒可預告終止契約發給資遣費，符合退休者准其退休。第四，公傷假：職業災害失能、傷害之醫療、休養期間，給予公傷假，最長 2年，公傷假期間依勞基法規定予以工資補償。'],
    [15, 'slides/slide_15.png', '11.0 請假規範：婚假、喪假、產假與陪產假', '11.0 請假規範：婚假、喪假、產假與陪產假。婚假與喪假規範：婚假給予 8日，薪資照給。喪假分次申請，百日內請完，父母或配偶喪亡 8日，祖父母、子女或配偶父母 6日，兄弟姊妹 3日，伯叔舅姑姨喪亡 1日。產假、流產假與產檢假：產假受僱 6個月以上全薪，分娩給予 8星期，妊娠 3個月以上流產給予 4星期。流產假減半薪病假計算，2個月以上未滿 3個月流產 1星期，未滿 2個月流產 5日。產檢假給予 7日，全薪。陪產檢與家庭照顧假：配偶產檢或分娩，給予 7日陪產檢及陪產假，於分娩當日及其前後 15日內請完，全薪。其餘生理假、家庭照顧假、育嬰留職停薪等，皆依性別工作平等法辦理。'],
    [16, 'slides/slide_16.png', '第四部分：考勤、考績與薪資獎懲', '第四部分：考勤、考績與薪資獎懲。本部分說明刷卡考核、遲到扣罰、加班費計算、獎懲辦法與人事評議委員會相關規定。'],
    [17, 'slides/slide_17.png', '12.0 考勤刷卡管理與忘打卡處理程序', '12.0 考勤刷卡管理與忘打卡處理程序。刷卡考勤、遲到與早退：第一，出勤紀律，上班應親自刷卡，託人代刷卡或代人刷卡者，雙方皆記大過乙次，未到工期間以曠職論。第二，遲到早退定義，上班開始 3至 15分鐘內到工者為遲到，下班前 15分鐘內離開為早退，操作 15分鐘以請假論。第三，遲到累計扣罰，每月第一次不計，第二次起列入，年度累計達 3次扣 1天年終，達 6次扣 2天年終，以此類推。忘打卡申請與未請假銷假：第四，忘打卡申請，當天上下班確有到工但忘刷卡，最遲於再上班之日電子登錄忘打卡單送主管簽核銷案，未辦理者以曠職論，不實登錄者記大過乙次並連帶處分主管。第五，曠職認定，未依規定請假，或請假屆滿未續假、未銷假上班者以曠職論，曠職不發薪資。'],
    [18, 'slides/slide_18.png', '13.0 加班工資發給與補休標準', '13.0 加班工資發給與補休標準。本頁說明各類加班工資計算方式與補休規定，請同仁仔細閱讀頁面中的加班費計算表格，了解平日、休息日及例假日加班的工資計算標準。'],
    [19, 'slides/slide_19.png', '14.0 員工獎懲、功過相抵與申訴程序', '14.0 員工獎懲、功過相抵與申訴程序。獎懲種類與申報：獎勵包括嘉獎、小功、大功、發獎金，用於重大改善、特殊專案、防患未然或特殊發明。懲處包括警告、小過、大過、免職，適用怠惰延宕、曠工、公器私用、託代刷卡、洩密等。功過抵銷換算標準：換算倍率為 3嘉獎等於 1小功，3小功等於 1大功，3警告等於 1小過，3小過等於 1大過。同年度大功與大過、小功與小過、嘉獎與警告可相抵，留廠查看期間功過不可相抵。人評會議與申訴渠道：記大過以上處分必須送人評會審議核定，並聽取當事人說明。循序申訴，書面須署名，爭議性事項 1週內確認真相，視情況提人評會裁議，並對申訴者予以保密。'],
    [20, 'slides/slide_20.png', '15.0 職災補償、退休金與福利保障', '15.0 職災補償、退休金與福利保障。職業災害補償：因職災致失能、傷害或疾病者，公傷假限 2年，醫療費用及工資均予補償。撫卹金：在職期間死亡，因公死亡給予喪葬費 5個月平均工資及死亡補償 40個月平均工資，順位為配偶、子女優先，次為父母、祖父母。退休標準：自請退休為年資滿 10年且年滿 57歲，或年資滿 15年年滿 55歲，或年資滿 25年；強制退休為年滿 65歲或身心障礙。退休金基數前 15年每滿 1年給 2基數，超過 15年給 1基數，上限 45基數，新制按月提撥 6%。公司福利包括免費午餐、一級主管專用車、公務手機、端午及中秋禮金、健康檢查。福委會提供旅遊補助、勞動節及春節禮金、生日補助、子女教育獎學金及急難救助。以上是全部教育訓練內容，感謝各位同仁耐心完成，請進行下方測驗。']
  ];
  
  sampleSlides.forEach(s => {
    sheet.appendRow(s);
  });
  
  sheet.autoResizeColumns(1, headers.length);
  sheet.setColumnWidth(1, 60);  // 頁數
  sheet.setColumnWidth(2, 150); // 圖片路徑
  sheet.setColumnWidth(3, 200); // 單頁標題
  sheet.setColumnWidth(4, 500); // 語音內容設寬一點
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
    ['', '新進同仁到職幾天後，實施第一次考核評估？', '30天', '40天', '60天', '90天', 'B'],
    ['', '依本工作規則，考核成績未滿幾分將終止僱用？', '50分', '55分', '60分', '70分', 'C'],
    ['', '正常工時規定，每週不得超過幾小時？', '44小時', '48小時', '36小時', '40小時', 'D'],
    ['', '連續曠工幾日，公司可不經預告終止契約（免職）？', '2日', '3日', '5日', '7日', 'B'],
    ['', '事假全年累計最多幾日？', '7日', '10日', '14日', '21日', 'C'],
    ['', '婚假給予幾日且薪資照給？', '3日', '5日', '6日', '8日', 'D'],
    ['', '特別休假最小動用單位為何？', '1小時', '2小時', '半天', '1天', 'B'],
    ['', '託人代刷卡或代人刷卡者，雙方將受何種懲處？', '警告乙次', '小過乙次', '大過乙次', '直接免職', 'C'],
    ['', '員工離職時，須於離職幾日前辦妥職務移交？', '3日', '5日', '7日', '10日', 'D'],
    ['', '父母喪亡時，員工可請幾日喪假？', '3日', '6日', '8日', '10日', 'C']
  ];
  sampleQ.forEach((q, idx) => {
    q[0] = idx + 1; // 自動填題號
    sheet.appendRow(q);
  });

  // 自動調整欄寬並設定安全寬度
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
        q1: 'B', q2: 'C', q3: 'D', q4: 'B', q5: 'C',
        q6: 'D', q7: 'B', q8: 'C', q9: 'D', q10: 'C'
      })
    }
  };
  const result = doPost(fakePost);
  Logger.log(result.getContent());
}
