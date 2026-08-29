package com.hongsheng.hosechecker

import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID

data class DischargeRecord(
    // ... (請保留您原本的欄位，例如時間、人員、槽號、櫃號等) ...
    val hoseNumber: String,
    
    // 👇 新增下面這兩行 (賦予預設值)
    val status: String = "🔴 待放行",
    val uuid: String = generateUUID()
) {
    companion object {
        // 自動產生「日期-亂數」系統流水號的輔助函數 (例如：20260509-A8F2)
        fun generateUUID(): String {
            val sdf = SimpleDateFormat("yyyyMMdd", Locale.getDefault())
            val dateStr = sdf.format(Date())
            // 取 UUID 的前 4 碼大寫，結合成易讀的流水號
            val randomStr = UUID.randomUUID().toString().substring(0, 4).uppercase()
            return "$dateStr-$randomStr"
        }
    }
}
