package com.hongsheng.hosechecker

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object NetworkClient {
    // 💡 注意：網址最後面保留 "/"，但把 "exec" 拿掉
    private const val BASE_URL = "https://script.google.com/macros/s/AKfycbzXbs0f90xTh9Ws0Zvje-ThBGilfiPa1tPerBVOYReXELZqEnpUwsdtK3Y5qrW89-tW/"

    val api: GoogleSheetApi by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(GoogleSheetApi::class.java)
    }
}