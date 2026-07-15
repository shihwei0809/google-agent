// 當作業員點擊【提交】時的邏輯範例 (維持原樣即可)：
val newRecord = DischargeRecord(
    time = currentTime,
    operator = selectedOperator,
    tankNumber = scannedTank,
    hoseNumber = scannedHose
    // 💡 注意：這裡不需要手動寫入 status 和 uuid！
    // Kotlin 會自動啟動 generateUUID() 並帶入預設值。
)

// 1. 存入手機本地佇列 (維持您原本的離線保護邏輯，斷網也不怕)
saveToLocalQueue(newRecord)

// 2. 觸發上傳機制 (有網路就上傳，沒網路就等下次)
uploadQueueData() 
