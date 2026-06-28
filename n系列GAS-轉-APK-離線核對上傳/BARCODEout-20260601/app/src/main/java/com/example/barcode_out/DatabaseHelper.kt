package com.example.barcode_out

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class DatabaseHelper(context: Context) : SQLiteOpenHelper(context, "Shipment.db", null, 1) {

    override fun onCreate(db: SQLiteDatabase) {
        val createTable = """
            CREATE TABLE pending_shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                barcode TEXT, 
                timestamp TEXT
            )
        """.trimIndent()
        db.execSQL(createTable)
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        db.execSQL("DROP TABLE IF EXISTS pending_shipments")
        onCreate(db)
    }

    // 儲存核對成功的紀錄
    fun insertRecord(barcode: String) {
        val db = this.writableDatabase
        val values = ContentValues().apply {
            put("barcode", barcode)
            put("timestamp", SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault()).format(Date()))
        }
        db.insert("pending_shipments", null, values)
        db.close()
    }

    // 取得所有待上傳資料
    fun getAllPendingRecords(): List<Map<String, String>> {
        val list = mutableListOf<Map<String, String>>()
        val db = this.readableDatabase
        val cursor = db.rawQuery("SELECT * FROM pending_shipments", null)
        if (cursor.moveToFirst()) {
            do {
                val map = mapOf(
                    "id" to cursor.getInt(0).toString(),
                    "barcode" to cursor.getString(1)
                )
                list.add(map)
            } while (cursor.moveToNext())
        }
        cursor.close()
        db.close()
        return list
    }

    // 上傳成功後刪除本地紀錄
    fun deleteRecord(id: String) {
        val db = this.writableDatabase
        db.delete("pending_shipments", "id=?", arrayOf(id))
        db.close()
    }
}