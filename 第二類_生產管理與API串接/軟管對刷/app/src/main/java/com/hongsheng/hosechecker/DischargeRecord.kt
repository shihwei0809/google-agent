package com.hongsheng.hosechecker

import java.util.UUID

data class DischargeRecord(
    val factory: String = "彰濱一廠",
    val operator: String,
    val tank: String,
    val hose: String,
    val containerNo: String,
    val result: String,
    var qcStatus: String = "🔴 待放行",
    var qcSigner: String = "",
    val time: String = "", // 💡 補上這個時間欄位，確保資料不會錯位
    val uuid: String = UUID.randomUUID().toString().substring(0, 8).uppercase()
)