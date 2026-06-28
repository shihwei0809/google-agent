package com.example.barcode_out

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Color
import android.graphics.Typeface
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import org.json.JSONArray
import org.json.JSONObject

class MainActivity : AppCompatActivity() {

    private lateinit var dbHelper: DatabaseHelper
    private lateinit var tvStatus: TextView
    private var currentMode = "ship_full"

    private val fields = arrayOfNulls<EditText>(17)
    private var targetFieldIndex = -1

    // 條碼掃描回傳監聽器
    private val barcodeLauncher = registerForActivityResult(ScanContract()) { result ->
        if (result.contents != null && targetFieldIndex != -1) {
            val scannedCode = result.contents
            val validationCheck = validateBarcodeFormat(scannedCode)

            if (validationCheck != "OK") {
                fields[targetFieldIndex]?.setText("")
                NetworkHelper.sendLineAlert("掃描錯誤: $scannedCode \n原因: $validationCheck")
                Toast.makeText(this, "❌ 格式錯誤: $validationCheck", Toast.LENGTH_LONG).show()
            } else {
                // 1. 填入條碼資料
                fields[targetFieldIndex]?.setText(scannedCode)

                // 2. 自動聚焦到下一個有顯示的欄位
                autoFocusNextField(targetFieldIndex)
            }
        }
        targetFieldIndex = -1
    }

    @SuppressLint("DiscouragedApi")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 防失憶機制：找回暫存的欄位索引
        if (savedInstanceState != null) {
            targetFieldIndex = savedInstanceState.getInt("TARGET_INDEX", -1)
        }

        dbHelper = DatabaseHelper(this)
        tvStatus = findViewById(R.id.tvStatus)

        // 動態綁定 17 個欄位與按鈕
        for (i in 0..16) {
            val resIdEt = resources.getIdentifier("f$i", "id", packageName)
            fields[i] = findViewById(resIdEt)

            val btnScan = findViewById<Button>(resources.getIdentifier("btnScan_f$i", "id", packageName))
            btnScan?.setOnClickListener {
                targetFieldIndex = i
                val options = ScanOptions().apply {
                    setPrompt("請掃描條碼 (按手機【返回鍵】可退出相機)")
                    setBeepEnabled(true)
                    setOrientationLocked(false)
                }
                barcodeLauncher.launch(options)
            }

            val btnClear = findViewById<Button>(resources.getIdentifier("btnClear_f$i", "id", packageName))
            btnClear?.setOnClickListener { fields[i]?.setText("") }
        }

        // 強制黑色粗體的場所下拉選單
        val spLocation: Spinner = findViewById(R.id.spLocation)
        spLocation.adapter = getCustomSpinnerAdapter(arrayOf("彰濱二廠", "彰濱一廠"))

        // 數量下拉選單
        val spQty: Spinner = findViewById(R.id.spQty)
        spQty.adapter = getCustomSpinnerAdapter(arrayOf("1", "2", "3", "4"))
        spQty.setSelection(3)

        setupModeSwitching()

        spQty.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p0: AdapterView<*>?, p1: View?, position: Int, p3: Long) {
                updateLayoutVisibility()
            }
            override fun onNothingSelected(p0: AdapterView<*>?) {}
        }

        // 巡檢核對並存檔（本機資料庫）
        findViewById<Button>(R.id.btnSubmit).setOnClickListener {
            val f8Text = fields[8]?.text.toString().trim()
            if (currentMode != "ship_az" && f8Text.isEmpty()) {
                Toast.makeText(this, "❌ 四合一料號為必填！", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            val jsonObj = JSONObject()
            val jsonArray = JSONArray()
            for (i in 0..16) {
                jsonArray.put(fields[i]?.text.toString().trim())
            }
            jsonObj.put("fields", jsonArray)
            jsonObj.put("mode", currentMode)
            jsonObj.put("location", spLocation.selectedItem.toString())

            dbHelper.insertRecord(jsonObj.toString())
            Toast.makeText(this, "✅ 巡檢存檔成功", Toast.LENGTH_SHORT).show()

            for (i in 0..16) fields[i]?.setText("")
            updateStatusText()
        }

        // 手動同步按鈕（移至背景執行緒，徹底解決閃退問題）
        val btnSync = findViewById<Button>(R.id.btnSync)
        btnSync.setOnClickListener {
            if (dbHelper.getAllPendingRecords().isEmpty()) {
                Toast.makeText(this, "目前沒有需要同步的資料", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }

            Toast.makeText(this, "連線同步中...", Toast.LENGTH_SHORT).show()
            btnSync.isEnabled = false

            Thread {
                try {
                    NetworkHelper.uploadToGAS(dbHelper)
                    runOnUiThread {
                        updateStatusText()
                        btnSync.isEnabled = true
                        Toast.makeText(this@MainActivity, "✅ 同步完成", Toast.LENGTH_SHORT).show()
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                    runOnUiThread {
                        btnSync.isEnabled = true
                        Toast.makeText(this@MainActivity, "❌ 同步失敗，請檢查網路", Toast.LENGTH_SHORT).show()
                    }
                }
            }.start()
        }

        updateStatusText()

        // 啟動網路狀態監聽器（連網時背景自動同步）
        setupAutoSync()
    }

    // 自動尋找下一個可顯示的輸入框並聚焦
    private fun autoFocusNextField(currentIndex: Int) {
        for (nextIndex in (currentIndex + 1) until fields.size) {
            val nextField = fields[nextIndex]

            if (nextField != null && nextField.visibility == View.VISIBLE) {
                // 檢查該欄位的外層容器是否也處於顯示狀態
                var isParentVisible = true
                var currentParent = nextField.parent as? View
                while (currentParent != null) {
                    if (currentParent.visibility != View.VISIBLE) {
                        isParentVisible = false
                        break
                    }
                    currentParent = currentParent.parent as? View
                }

                if (isParentVisible) {
                    nextField.requestFocus()
                    nextField.setSelection(nextField.text.length)
                    break
                }
            }
        }
    }

    // 網路狀態恢復監聽器
    private fun setupAutoSync() {
        val connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val networkRequest = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .build()

        connectivityManager.registerNetworkCallback(networkRequest, object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                super.onAvailable(network)
                val pendingCount = dbHelper.getAllPendingRecords().size
                if (pendingCount > 0) {
                    Thread {
                        try {
                            NetworkHelper.uploadToGAS(dbHelper)
                            runOnUiThread {
                                updateStatusText()
                                Toast.makeText(this@MainActivity, "🔄 網路已恢復，背景自動同步完成", Toast.LENGTH_LONG).show()
                            }
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }.start()
                }
            }
        })
    }

    // 客製化下拉選單樣式 (加黑、加大、加粗)
    private fun getCustomSpinnerAdapter(items: Array<String>): ArrayAdapter<String> {
        return object : ArrayAdapter<String>(this, android.R.layout.simple_spinner_item, items) {
            override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
                val view = super.getView(position, convertView, parent) as TextView
                view.setTextColor(Color.BLACK)
                view.textSize = 16f
                view.setTypeface(null, Typeface.BOLD)
                return view
            }
            override fun getDropDownView(position: Int, convertView: View?, parent: ViewGroup): View {
                val view = super.getDropDownView(position, convertView, parent) as TextView
                view.setTextColor(Color.BLACK)
                view.textSize = 18f
                view.setTypeface(null, Typeface.BOLD)
                view.setPadding(40, 40, 40, 40)
                return view
            }
        }
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        outState.putInt("TARGET_INDEX", targetFieldIndex)
    }

    private fun setupModeSwitching() {
        val rgMode: RadioGroup = findViewById(R.id.rgMode)
        rgMode.setOnCheckedChangeListener { _, checkedId ->
            currentMode = when (checkedId) {
                R.id.rbFull -> "ship_full"
                R.id.rbMixed -> "ship_mixed"
                R.id.rbLoose -> "ship_loose"
                R.id.rbAz -> "ship_az"
                else -> "ship_full"
            }
            updateLayoutVisibility()
        }
    }

    private fun updateLayoutVisibility() {
        val tvQtyLabel: TextView = findViewById(R.id.tvQtyLabel)
        val spQty: Spinner = findViewById(R.id.spQty)
        val card4in1: LinearLayout = findViewById(R.id.card4in1)
        val cardWH: LinearLayout = findViewById(R.id.cardWH)

        val rowT2: LinearLayout = findViewById(R.id.rowT2)
        val rowT3: LinearLayout = findViewById(R.id.rowT3)
        val rowT4: LinearLayout = findViewById(R.id.rowT4)

        // 對齊您的 XML ID 設計
        val row4in112: LinearLayout = findViewById(R.id.row4in1_2)
        val row4in113: LinearLayout = findViewById(R.id.row4in1_3)
        val row4in114: LinearLayout = findViewById(R.id.row4in1_4)

        var barrelCount = 4

        when (currentMode) {
            "ship_full", "ship_mixed" -> {
                tvQtyLabel.visibility = View.GONE
                spQty.visibility = View.GONE
                card4in1.visibility = View.VISIBLE
                cardWH.visibility = View.VISIBLE
                barrelCount = 4
            }
            "ship_az" -> {
                tvQtyLabel.visibility = View.GONE
                spQty.visibility = View.GONE
                card4in1.visibility = View.GONE
                cardWH.visibility = View.GONE
                barrelCount = 1
            }
            "ship_loose" -> {
                tvQtyLabel.visibility = View.VISIBLE
                spQty.visibility = View.VISIBLE
                card4in1.visibility = View.VISIBLE
                cardWH.visibility = View.VISIBLE
                barrelCount = spQty.selectedItem.toString().toInt()
            }
        }

        rowT2.visibility = if (barrelCount >= 2) View.VISIBLE else View.GONE
        row4in112.visibility = if (barrelCount >= 2) View.VISIBLE else View.GONE

        rowT3.visibility = if (barrelCount >= 3) View.VISIBLE else View.GONE
        row4in113.visibility = if (barrelCount >= 3) View.VISIBLE else View.GONE

        rowT4.visibility = if (barrelCount >= 4) View.VISIBLE else View.GONE
        row4in114.visibility = if (barrelCount >= 4) View.VISIBLE else View.GONE
    }

    private fun validateBarcodeFormat(code: String): String {
        val s = code.trim()
        if (s.startsWith("7")) {
            if (s.length != 29) return "[7開頭] 長度需 29 碼"
            if (!s.contains("-T0", ignoreCase = true)) return "[7開頭] 需包含 '-T0'"
        } else if (s.startsWith("1")) {
            if (s.length != 20) return "[1開頭] 長度需 20 碼"
            if (!s.endsWith("TS", ignoreCase = true)) return "[1開頭] 必須以 'TS' 結尾"
        }
        return "OK"
    }

    @SuppressLint("SetTextI18n")
    private fun updateStatusText() {
        val pendingCount = dbHelper.getAllPendingRecords().size
        tvStatus.text = "目前手機暫存：$pendingCount 筆"
    }
}