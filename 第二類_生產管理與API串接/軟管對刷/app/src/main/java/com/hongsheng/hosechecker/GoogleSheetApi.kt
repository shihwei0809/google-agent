package com.hongsheng.hosechecker

import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Query

interface GoogleSheetApi {
    // 💡 統一在這裡補上 "exec"
    @POST("exec")
    fun uploadRecord(@Body record: DischargeRecord): Call<ResponseBody>

    @GET("exec")
    fun getOperatorList(@Query("action") action: String): Call<List<String>>

    @GET("exec")
    fun getConfig(@Query("action") action: String): Call<List<List<String>>>

    @GET("exec")
    fun getPendingTasks(@Query("action") action: String): Call<List<DischargeRecord>>
}