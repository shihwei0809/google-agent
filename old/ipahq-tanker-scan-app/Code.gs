function doGet() {
  return HtmlService.createTemplateFromFile('Index')
      .evaluate()
      .setTitle('IPAHQ 槽車掃描核對')
      .addMetaTag('viewport', 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no');
}

function processForm(formObject) {
  try {
    var mainQr = (formObject.mainQr || "").trim();
    var check1 = (formObject.check1 || "").trim();
    var check2 = (formObject.check2 || "").trim();
    var photoData = formObject.photoData;

    if (!mainQr || !check1 || !check2) throw "條碼資料不完整";

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var ws = ss.getSheetByName("ValidationData") || ss.insertSheet("ValidationData");
    
    var photoUrl = photoData ? saveImageToDrive(photoData, check1) : "無照片";

    ws.appendRow([new Date(), mainQr, "'" + check1, "'" + check2, "核對通過", photoUrl]);
    return { success: true, message: "✅ 資料上傳成功！" };
  } catch (e) {
    return { success: false, message: "錯誤: " + e.toString() };
  }
}

function saveImageToDrive(base64Data, fileName) {
  var folderId = "13CIfrHMQyFTQKc0lxjpCvImCFaA43fUP"; 
  var parts = base64Data.split(',');
  var blob = Utilities.newBlob(Utilities.base64Decode(parts[1]), parts[0].split(';')[0].split(':')[1], "Check_" + fileName + ".jpg");
  var file = DriveApp.getFolderById(folderId).createFile(blob);
  file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  return file.getUrl();
}
