function doGet() {
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('IPA 雙廠區進階製程排程系統')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

function saveAllData(payload) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    
    // 儲存系統設定
    let sheetSet = ss.getSheetByName("System_Settings") || ss.insertSheet("System_Settings");
    sheetSet.clear();
    const setRows = Object.entries(payload.settings).map(([k, v]) => [k, v]);
    if(setRows.length > 0) sheetSet.getRange(1, 1, setRows.length, 2).setValues(setRows);

    // 儲存表格數據
    let sheetGrid = ss.getSheetByName("Grid_Data") || ss.insertSheet("Grid_Data");
    sheetGrid.clear();
    const gridRows = Object.entries(payload.grid).map(([k, v]) => [k, v]);
    if(gridRows.length > 0) sheetGrid.getRange(1, 1, gridRows.length, 2).setValues(gridRows);

    return "✅ 產線設定與表格數據已自動存檔";
  } catch(e) {
    return "❌ 存檔失敗: " + e.toString();
  }
}

function loadAllData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let payload = { settings: {}, grid: {} };

  let sheetSet = ss.getSheetByName("System_Settings");
  if (sheetSet) { sheetSet.getDataRange().getValues().forEach(r => payload.settings[r[0]] = r[1]); }

  let sheetGrid = ss.getSheetByName("Grid_Data");
  if (sheetGrid) { sheetGrid.getDataRange().getValues().forEach(r => payload.grid[r[0]] = r[1]); }
  
  return payload;
}
