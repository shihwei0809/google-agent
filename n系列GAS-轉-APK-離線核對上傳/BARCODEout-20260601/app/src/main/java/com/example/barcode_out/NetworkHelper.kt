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

    // 2. 背景上傳至 GAS
    fun uploadToGAS(dbHelper: DatabaseHelper) {
        val pendingRecords = dbHelper.getAllPendingRecords()

        for (record in pendingRecords) {
            val id = record["id"]!!
            val barcode = record["barcode"]!!

            val json = JSONObject().apply { put("barcode", barcode) }.toString()
            val requestBody = json.toRequestBody("application/json; charset=utf-8".toMediaType())

            val request = Request.Builder()
                .url(GAS_URL)
                .post(requestBody)
                .build()

            client.newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    // 網路不穩，保留在 SQLite 待下次上傳
                }

                override fun onResponse(call: Call, response: Response) {
                    if (response.isSuccessful) {
                        // 上傳成功，從 SQLite 中移除
                        dbHelper.deleteRecord(id)
                    }
                    response.close()
                }
            })
        }
    }
}