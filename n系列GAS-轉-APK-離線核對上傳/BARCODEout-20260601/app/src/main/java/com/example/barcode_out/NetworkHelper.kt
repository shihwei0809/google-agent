package com.example.barcode_out

import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

object NetworkHelper {
    private val client = OkHttpClient()
    private const val LINE_TOKEN = "請在此填入您的_LINE_NOTIFY_TOKEN"
    private const val GAS_URL = "請在此填入您的_GAS_WEBAPP_URL"

    // 1. 發送 Line 錯誤通知
    fun sendLineAlert(message: String) {
        val formBody = FormBody.Builder()
            .add("message", "\n⚠️ 出貨核對異常\n$message")
            .build()

        val request = Request.Builder()
            .url("https://notify-api.line.me/api/notify")
            .addHeader("Authorization", "Bearer $LINE_TOKEN")
            .post(formBody)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                e.printStackTrace()
            }
            override fun onResponse(call: Call, response: Response) {
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