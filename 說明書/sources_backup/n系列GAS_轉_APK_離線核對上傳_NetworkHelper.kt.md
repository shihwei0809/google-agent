# Source Code Backup - n系列GAS-轉-APK-離線核對上傳 - NetworkHelper.kt

> [!NOTE]
> *   **原始本機路徑**: [NetworkHelper.kt](file:///D:/GOOGLE%20ANGET/n系列GAS-轉-APK-離線核對上傳/BARCODEout-20260601/app/src/main/java/com/example/barcode_out/NetworkHelper.kt)
> *   **自動備份時間**: `2026-07-15 13:39:13`
> *   **語言類型**: `kotlin`

``` kotlin
package com.example.barcode_out

import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

object NetworkHelper {
    private val client = OkHttpClient()
    private const val TEAMS_WEBHOOK_URL = "https://defaulta46d9e33ad01451aaec52ee61979c6.d0.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/63da736f43d74caa9e6d6f8d3f93f1c6/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=PLSf5l86fsIVzKC4B5gq0CFDJYEpjynd3451r84gM4A"
    private const val GAS_URL = "https://script.google.com/macros/s/AKfycbzJ3_OUBRFZd4VDHtfpmzRS_xJ2B0YMK-meTCOaEliMC7wScFD4Ll3ylXZxLLfbY4yT/exec"

    // 1. 發送 Teams 錯誤通知
    fun sendTeamsAlert(message: String) {
        // Teams Workflow (Power Automate) 規定必須使用 MessageCard 或 AdaptiveCard 格式
        val json = JSONObject().apply {
            put("@type", "MessageCard")
            put("@context", "http://schema.org/extensions")
            put("themeColor", "E81123") // 紅色警示
            put("summary", "出貨核對異常")
            put("title", "⚠️ 出貨核對異常")
            // Teams MessageCard 支援 HTML 格式換行，將 \n 換成 <br>
            put("text", message.replace("\n", "<br>"))
        }.toString()

        val requestBody = json.toRequestBody("application/json; charset=utf-8".toMediaType())

        val request = Request.Builder()
            .url(TEAMS_WEBHOOK_URL)
            .post(requestBody)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: java.io.IOException) {
                android.util.Log.e("TeamsWebhook", "Teams Webhook 發送失敗", e)
            }
            override fun onResponse(call: Call, response: Response) {
                val body = response.body?.string() ?: ""
                android.util.Log.i("TeamsWebhook", "Teams Webhook 回傳狀態碼: ${response.code}, 回傳內容: $body")
                response.close()
            }
        })
    }

    // 2. 背景上傳至 GAS (同步傳輸，交由背景 Thread 阻塞處理)
    fun uploadToGAS(dbHelper: DatabaseHelper) {
        val pendingRecords = dbHelper.getAllPendingRecords()

        for (record in pendingRecords) {
            val id = record["id"]!!
            val barcode = record["barcode"]!!

            val innerJson = record["barcode"]!!   // 實際存的是完整 JSON: {"fields":...}
            
            // 包裝成 GAS 預期的外層結構 {"barcode": "內部JSON字串"}
            val outerJson = JSONObject().apply {
                put("barcode", innerJson)
            }.toString()

            val requestBody = outerJson.toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(GAS_URL)
                .post(requestBody)
                .build()

            // 改為同步執行，確保呼叫端 Thread 可以捕獲異常
            val response = client.newCall(request).execute()
            if (!response.isSuccessful) {
                response.close()
                throw IOException("連線失敗，狀態碼: ${response.code}")
            }

            val responseBody = response.body?.string() ?: ""
            response.close()

            // 嚴格解析 GAS 回傳內容，避免 doPost 錯誤卻誤刪暫存
            try {
                val respJson = JSONObject(responseBody)
                val status = respJson.optString("status")
                if (status == "success") {
                    // 雲端確認寫入成功，才從手機 SQLite 刪除
                    dbHelper.deleteRecord(id)
                } else {
                    val msg = respJson.optString("message", "GAS 執行失敗")
                    throw IOException(msg)
                }
            } catch (je: Exception) {
                // 如果解析失敗（如回傳 HTML 錯誤網頁），也視同失敗
                throw IOException("解析伺服器回傳失敗: $responseBody")
            }
        }
    }
}
```
