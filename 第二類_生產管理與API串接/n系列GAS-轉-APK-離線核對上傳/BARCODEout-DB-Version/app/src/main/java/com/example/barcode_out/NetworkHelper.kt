package com.example.barcode_out

import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

object NetworkHelper {
    private val client = OkHttpClient()
    private const val TEAMS_WEBHOOK_URL = "https://defaulta46d9e33ad01451aaec52ee61979c6.d0.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/63da736f43d74caa9e6d6f8d3f93f1c6/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=PLSf5l86fsIVzKC4B5gq0CFDJYEpjynd3451r84gM4A"
    // 已自動為您設定為您的電腦 IP
    private const val DATABASE_API_URL = "http://192.168.3.35:3000/api/shipments/sync"

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

    // 2. 背景上傳至資料庫 API 伺服器 (同步傳輸，交由背景 Thread 阻塞處理)
    fun uploadToDatabase(dbHelper: DatabaseHelper) {
        val pendingRecords = dbHelper.getAllPendingRecords()

        for (record in pendingRecords) {
            val id = record["id"]!!
            val innerJson = record["barcode"]!!   // 實際存的是完整 JSON: {"fields":...}

            // 直接將乾淨的 JSON 傳送至資料庫 API 後端
            val requestBody = innerJson.toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(DATABASE_API_URL)
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

            // 解析資料庫後端 API 回傳內容
            try {
                val respJson = JSONObject(responseBody)
                val status = respJson.optString("status")
                if (status == "success") {
                    // 資料庫確認寫入成功，才從手機 SQLite 刪除暫存
                    dbHelper.deleteRecord(id)
                } else {
                    val msg = respJson.optString("message", "資料庫寫入失敗")
                    throw IOException(msg)
                }
            } catch (je: Exception) {
                // 如果解析失敗，也視同失敗
                throw IOException("解析伺服器回傳失敗: $responseBody")
            }
        }
    }
}