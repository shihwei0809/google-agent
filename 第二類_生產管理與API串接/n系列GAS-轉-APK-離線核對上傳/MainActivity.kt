package com.example.barcode_out

import android.annotation.SuppressLint
import android.graphics.Color
import android.graphics.Typeface
import android.os.Bundle
import android.view.View
import android.view.ViewGroup
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
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

    private val barcodeLauncher = registerForActivityResult(ScanContract()) { result ->
        // 確保有掃到資料，而且系統還記得是哪一個欄位
        if (result.contents != null && targetFieldIndex != -1) {
            val scannedCode = result.contents
            val validationCheck = validateBarcodeFormat(scannedCode)
            
            if (validationCheck != "OK") {
                fields[targetFieldIndex]?.setText("")
                NetworkHelper.sendLineAlert("掃描錯誤: $scannedCode \n原因: $validationCheck")
                Toast.makeText(this, "❌ 格式錯誤: $validationCheck", Toast.LENGTH_LONG).show()
            } else {
                fields[targetFieldIndex]?.setText(scannedCode)
            }
        }
        targetFieldIndex = -1 // 填寫完畢，重置目標
    }

    @SuppressLint("DiscouragedApi")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // 【修復核心一】：防失憶機制。從便條紙找回剛剛是點擊哪一個欄位
        if (savedInstanceState != null) {
            targetFieldIndex = savedInstanceState.getInt("TARGET_INDEX", -1)
        }

        dbHelper = DatabaseHelper(this)
        tvStatus = findViewById(R.id.tvStatus)

        // 綁定 17 個輸入框與按鈕
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

        // 【修復核心二】：套用強制黑色粗體的客製化下拉選單
        val spLocation: Spinner = findViewById(R.id.spLocation)
        spLocation.adapter = getCustomSpinnerAdapter(arrayOf("彰濱二廠", "彰濱一廠"))

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

        findViewById<Button>(R.id.btnSync).setOnClickListener {
            Toast.makeText(this, "連線同步中...", Toast.LENGTH_SHORT).show()
            NetworkHelper.uploadToGAS(dbHelper)
            updateStatusText()
        }

        updateStatusText()
    }

    // 建立客製化下拉選單外觀 (黑體、放大、粗體)
    private fun getCustomSpinnerAdapter(items: Array<String>): ArrayAdapter<String> {
        return object : ArrayAdapter<String>(this, android.R.layout.simple_spinner_item, items) {
            // 選擇後的顯示外觀
            override fun getView(position: Int, convertView: View?, parent: ViewGroup): View {
                val view = super.getView(position, convertView, parent) as TextView
                view.setTextColor(Color.BLACK)
                view.textSize = 16f
                view.setTypeface(null, Typeface.BOLD)
                return view
            }
            // 點開清單時的選項外觀
            override fun getDropDownView(position: Int, convertView: View?, parent: ViewGroup): View {
                val view = super.getDropDownView(position, convertView, parent) as TextView
                view.setTextColor(Color.BLACK)
                view.textSize = 18f
                view.setTypeface(null, Typeface.BOLD)
                view.setPadding(40, 40, 40, 40) // 增加上下間距讓手指更好點
                return view
            }
        }
    }

    // 在系統可能關閉 App 前，把 targetFieldIndex 抄下來
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
        
        val row4in12: LinearLayout = findViewById(R.id.row4in1_2)
        val row4in13: LinearLayout = findViewById(R.id.row4in1_3)
        val row4in14: LinearLayout = findViewById(R.id.row4in1_4)

        var barrelCount = 4

        when (currentMode) {
            "ship_full", "ship_mixed" -> {
                tvQtyLabel.visibility = View.GONE
                spQty.visibility = View.GONE
                card4in1.visibility = View.VISIBLE
                cardWH.visibility = View.VISIBLE
            }
            "ship_az" -> {
                tvQtyLabel.visibility = View.GONE
                spQty.visibility = View.GONE
                card4in1.visibility = View.GONE
                cardWH.visibility = View.GONE
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
        row4in12.visibility = if (barrelCount >= 2) View.VISIBLE else View.GONE
        
        rowT3.visibility = if (barrelCount >= 3) View.VISIBLE else View.GONE
        row4in13.visibility = if (barrelCount >= 3) View.VISIBLE else View.GONE
        
        rowT4.visibility = if (barrelCount >= 4) View.VISIBLE else View.GONE
        row4in14.visibility = if (barrelCount >= 4) View.VISIBLE else View.GONE
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
