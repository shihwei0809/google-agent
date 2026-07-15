# Source Code Backup - n系列GAS-轉-APK-離線核對上傳 - MainActivity.kt

> [!NOTE]
> *   **原始本機路徑**: [MainActivity.kt](file:///D:/GOOGLE%20ANGET/n系列GAS-轉-APK-離線核對上傳/BARCODEout-20260601/app/src/main/java/com/example/barcode_out/MainActivity.kt)
> *   **自動備份時間**: `2026-07-15 13:39:13`
> *   **語言類型**: `kotlin`

``` kotlin
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
                NetworkHelper.sendTeamsAlert("掃描錯誤: $scannedCode \n原因: $validationCheck")
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

            // 1. 監聽虛擬/實體鍵盤 Enter 鍵
            fields[i]?.setOnEditorActionListener { _, actionId, event ->
                val isEnter = (actionId == android.view.inputmethod.EditorInfo.IME_ACTION_NEXT ||
                               actionId == android.view.inputmethod.EditorInfo.IME_ACTION_DONE ||
                               (event != null && event.keyCode == android.view.KeyEvent.KEYCODE_ENTER && event.action == android.view.KeyEvent.ACTION_DOWN))
                if (isEnter) {
                    autoFocusNextField(i)
                    true
                } else {
                    false
                }
            }

            // 2. 監聽硬體實體 Enter 按鍵事件
            fields[i]?.setOnKeyListener { _, keyCode, event ->
                if (keyCode == android.view.KeyEvent.KEYCODE_ENTER && event.action == android.view.KeyEvent.ACTION_DOWN) {
                    autoFocusNextField(i)
                    true
                } else {
                    false
                }
            }

            // 3. 監聽輸入文字尾端是否包含 newline (某些條碼槍會直接在字串結尾輸入 \n 或 \r 且不發送 KeyEvent)
            fields[i]?.addTextChangedListener(object : android.text.TextWatcher {
                override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
                override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
                override fun afterTextChanged(s: android.text.Editable?) {
                    val original = s?.toString() ?: ""
                    if (original.endsWith("\n") || original.endsWith("\r")) {
                        val clean = original.replace("\n", "").replace("\r", "")
                        fields[i]?.removeTextChangedListener(this)
                        fields[i]?.setText(clean)
                        fields[i]?.setSelection(clean.length)
                        fields[i]?.addTextChangedListener(this)
                        autoFocusNextField(i)
                    }
                }
            })
        }

        // 強制黑色粗體的場所下拉選單
        val spLocation: Spinner = findViewById(R.id.spLocation)
        spLocation.adapter = getCustomSpinnerAdapter(arrayOf("彰濱二廠", "彰濱一廠"))

        // 數量下拉選單
        val spQty: Spinner = findViewById(R.id.spQty)
        spQty.adapter = getCustomSpinnerAdapter(arrayOf("1", "2", "3", "4"))
        spQty.setSelection(3)

        setupModeSwitching()

        // 繳庫 批號3 展開/收合開關
        val btnToggleWhBatch3: Button = findViewById(R.id.btnToggleWhBatch3)
        val rowWhBatch3: LinearLayout = findViewById(R.id.rowWhBatch3)
        btnToggleWhBatch3.setOnClickListener {
            if (rowWhBatch3.visibility == View.GONE) {
                rowWhBatch3.visibility = View.VISIBLE
                btnToggleWhBatch3.text = "− 批號3"
            } else {
                rowWhBatch3.visibility = View.GONE
                btnToggleWhBatch3.text = "+ 批號3"
                fields[16]?.setText("")   // 收合時自動清空
            }
        }

        spQty.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(p0: AdapterView<*>?, p1: View?, position: Int, p3: Long) {
                updateLayoutVisibility()
            }
            override fun onNothingSelected(p0: AdapterView<*>?) {}
        }

        // 巡檢核對並存檔（本機資料庫，包含本機比對防呆邏輯）
        findViewById<Button>(R.id.btnSubmit).setOnClickListener {
            val fieldValues = Array(17) { i -> fields[i]?.text.toString().trim() }
            
            // 執行本機欄位比對驗證
            val validationError = performLocalCheck(fieldValues, currentMode)
            if (validationError != null) {
                // 彈出錯誤對話框提示人員，且不予存檔
                showValidationErrorsDialog(validationError)
                // 同步將核對異常訊息發送到 Teams
                NetworkHelper.sendTeamsAlert("巡檢核對失敗 (場所: ${spLocation.selectedItem}, 模式: ${getModeChineseName(currentMode)})\n$validationError")
                return@setOnClickListener
            }

            val jsonObj = JSONObject()
            val jsonArray = JSONArray()
            for (i in 0..16) {
                jsonArray.put(fieldValues[i])
            }
            jsonObj.put("fields", jsonArray)
            jsonObj.put("mode", currentMode)
            jsonObj.put("location", spLocation.selectedItem.toString())

            dbHelper.insertRecord(jsonObj.toString())
            Toast.makeText(this, "✅ 巡檢核對相符，本機存檔成功", Toast.LENGTH_SHORT).show()

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
                        Toast.makeText(this@MainActivity, "⚠️ 同步失敗，請檢查網路或 GAS 設定", Toast.LENGTH_LONG).show()
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
        val errors = mutableListOf<String>()
        validate17Series(code, "掃描條碼", errors)
        if (errors.isNotEmpty()) {
            return errors.joinToString("\n\n").replace(Regex("❌ \\[掃描條碼\\] ❌ "), "❌ ")
        }
        return "OK"
    }

    @SuppressLint("SetTextI18n")
    private fun updateStatusText() {
        val pendingCount = dbHelper.getAllPendingRecords().size
        tvStatus.text = "目前手機暫存：$pendingCount 筆"
    }

    // =========================================================================
    // 🔏 本地比對法官邏輯 (由 GAS Code.gs 移植而來)
    // =========================================================================

    private fun showValidationErrorsDialog(errors: String) {
        val scrollView = ScrollView(this).apply {
            setPadding(45, 30, 45, 30)
            val textView = TextView(this@MainActivity).apply {
                text = errors
                setTextColor(Color.BLACK)
                textSize = 16f
                setTypeface(null, Typeface.BOLD)
            }
            addView(textView)
        }
        androidx.appcompat.app.AlertDialog.Builder(this)
            .setTitle("❌ 巡檢比對不符")
            .setView(scrollView)
            .setPositiveButton("確定", null)
            .show()
    }

    private fun toHalfWidth(str: String?): String {
        if (str.isNullOrEmpty()) return ""
        val sb = StringBuilder()
        for (ch in str) {
            if (ch in '\uff01'..'\uff5e') {
                sb.append((ch.code - 0xfee0).toChar())
            } else if (ch == '\u3000') {
                sb.append(' ')
            } else {
                sb.append(ch)
            }
        }
        return sb.toString()
    }

    private fun normalizeBatch(str: String?): String {
        if (str.isNullOrEmpty()) return ""
        val half = toHalfWidth(str)
        return half.replace(Regex("[^a-zA-Z0-9]"), "")
    }

    private fun extractRealBatch(fullString: String?): String {
        if (fullString.isNullOrEmpty()) return ""
        val s = fullString.trim()
        if (s.contains("@") && s.contains("+")) {
            val parts = s.split("@")
            if (parts.size > 1) return parts[1]
        }
        return s
    }

    private fun extractBatchForWarehouse(fullString: String?): String {
        var s = extractRealBatch(fullString)
        if (s.contains("+")) s = s.split("+")[0]
        if (s.contains(" ")) s = s.split(Regex("\\s+"))[0]
        return s
    }

    private fun cleanMatMaster(str: String?): String {
        if (str.isNullOrEmpty()) return ""
        var s = str.trim().uppercase()
        if (s.contains(" ")) s = s.split(" ")[0]
        s = s.replace(Regex("^\\d+L"), "L")
        return s
    }

    private fun extractRealMat(fullString: String?): String {
        if (fullString.isNullOrEmpty()) return ""
        val s = fullString.trim()
        if (s.contains("@")) {
            val parts = s.split("@")
            val part1 = parts[0]
            if (part1.length > 14) return part1.substring(14)
            return part1
        }
        return cleanMatMaster(s)
    }

    private fun getBatchBase(str: String?): String {
        val s = (str ?: "").trim()
        return when {
            s.contains("+") -> s.split("+")[0]
            s.contains(" ") -> s.split(" ")[0]
            else -> s
        }
    }

    private fun check7SeriesFormat(code: String?): String {
        val s = (code ?: "").trim()
        if (s.startsWith("7")) {
            if (s.length != 29) return "❌ 格式錯誤！\n👉 [7開頭] 長度需 29 碼 (目前 ${s.length})"
            if (!s.uppercase().contains("-T0")) return "❌ 格式錯誤！\n👉 [7開頭] 需包含 '-T0'"
        }
        if (s.uppercase().contains("-T0") && !s.startsWith("7")) {
            return "❌ 格式錯誤！\n👉 含有 '-T0' 必須以 '7' 開頭"
        }
        return "OK"
    }

    private fun check1SeriesFormat(code: String?): String {
        val s = (code ?: "").trim()
        if (s.startsWith("1")) {
            if (s.length != 20) return "❌ 格式錯誤！\n👉 [1開頭] 長度需 20 碼 (目前 ${s.length})"
            if (!s.uppercase().endsWith("TS")) return "❌ 格式錯誤！\n👉 [1開頭] 必須以 'TS' 結尾"
        }
        return "OK"
    }

    private fun getModeChineseName(mode: String): String {
        return when (mode) {
            "ship_full" -> "整板出貨"
            "ship_mixed" -> "混板出貨"
            "ship_loose" -> "散桶出貨"
            "ship_az" -> "AZ檢查"
            else -> mode
        }
    }

    private fun validate17Series(valStr: String?, label: String, errors: MutableList<String>) {
        if (valStr.isNullOrBlank()) return
        val s = valStr.trim()
        // 攔截網址型條碼 (如 HTTP://WWW.BIOFCS.COM/)
        if (s.uppercase().startsWith("HTTP") || s.contains("://")) {
            errors.add("❌ [$label] 格式錯誤！\n👉 掃到網址條碼，請改掃正確批號/料號")
            return
        }
        val c1 = check1SeriesFormat(s)
        if (c1 != "OK") errors.add("❌ [$label] $c1")
        val c7 = check7SeriesFormat(s)
        if (c7 != "OK") errors.add("❌ [$label] $c7")
    }

    data class VerifyResult(val pass: Boolean, val msg: String)

    private fun verifyPairStrict(scanVal: String, masterVal: String, localLabel: String, masterLabel: String): VerifyResult {
        val scan = scanVal.trim()
        val master = masterVal.trim()
        if (scan.isEmpty() || master.isEmpty()) return VerifyResult(false, "資料空白")

        if (scan.startsWith("1") && scan.length == 20 && scan.endsWith("TS")) {
            if (scan == master) return VerifyResult(true, "OK")
            if (scan.contains(master) && master.length > 5) return VerifyResult(true, "OK")
            return VerifyResult(false, "1字頭比對失敗\n👉 $localLabel: $scan\n👉 $masterLabel: $master")
        }

        val isQr = scan.contains("@")
        if (isQr) {
            var processedScan = ""
            val parts = scan.split("@")
            processedScan = if (parts.size > 1) parts[1] else scan
            processedScan = processedScan.replace("+", "").replace(Regex("\\s+"), "")

            var processedMaster = master
            if (processedMaster.isNotEmpty()) processedMaster = processedMaster.substring(1)
            processedMaster = processedMaster.replace(Regex("\\s+"), "")

            return if (processedScan == processedMaster) {
                VerifyResult(true, "OK")
            } else {
                VerifyResult(false, "QR比對失敗\n👉 $localLabel(去+): $processedScan\n👉 $masterLabel(去首碼): $processedMaster")
            }
        }

        if (scan == master) return VerifyResult(true, "OK")
        if (scan.replace(Regex("\\s+"), "") == master.replace(Regex("\\s+"), "")) return VerifyResult(true, "OK")
        return VerifyResult(false, "數值不一致\n👉 $localLabel: $scan\n👉 $masterLabel: $master")
    }

    private fun performLocalCheck(f: Array<String>, mode: String): String? {
        val allErrors = mutableListOf<String>()
        val tankMap = listOf(
            Triple(0, 1, "第一桶"),
            Triple(2, 3, "第二桶"),
            Triple(4, 5, "第三桶"),
            Triple(6, 7, "第四桶")
        )
        val masterBatchIndices = listOf(9, 10, 11, 12)

        if (mode == "ship_az") {
            var activeTankCount = 0
            var firstTankMaterial = ""
            val rawBatches = mutableListOf<String>()
            val seenAz = mutableMapOf<String, String>()

            for (i in 0 until tankMap.size) {
                val item = tankMap[i]
                val rawBatch = f[item.first]
                val rawMat = f[item.second]

                if (rawBatch.isNotEmpty() || rawMat.isNotEmpty()) {
                    activeTankCount++
                    rawBatches.add(rawBatch)

                    validate17Series(rawBatch, "桶${i + 1} 批號", allErrors)
                    // 【未來擴充區：AZ模式桶槽料號 檢查】
                    // validate17Series(rawMat, "桶${i + 1} 料號", allErrors)

                    val norm = normalizeBatch(rawBatch)
                    if (norm.isNotEmpty()) {
                        if (seenAz.containsKey(norm)) {
                            allErrors.add("❌ [${item.third}] 重複掃描！(與 ${seenAz[norm]} 相同)")
                        } else {
                            seenAz[norm] = item.third
                        }
                    }

                    val cleanMat = cleanMatMaster(rawMat)
                    if (firstTankMaterial.isEmpty()) firstTankMaterial = cleanMat
                    if (cleanMat != firstTankMaterial) {
                        allErrors.add("❌ [${item.third}] 料號異常！與第一桶不同。")
                    }

                    if (rawBatch.contains("@")) {
                        val qrMat = extractRealMat(rawBatch)
                        if (qrMat.isNotEmpty() && qrMat != cleanMat) {
                            allErrors.add("❌ [${item.third}] 貼紙錯誤！QR料號與掃描料號不符")
                        }
                    }
                }
            }

            if (activeTankCount == 0) return "⚠️ 未偵測到任何資料"

            if (rawBatches.size > 1) {
                val base1 = getBatchBase(rawBatches[0])
                val len1 = rawBatches[0].length

                for (k in 1 until rawBatches.size) {
                    if (getBatchBase(rawBatches[k]) != base1) {
                        allErrors.add("❌ AZ批號不一致！第${k + 1}桶與第1桶批號主體不同。")
                    }
                    val lenK = rawBatches[k].length
                    if (Math.abs(len1 - lenK) > 10) {
                        allErrors.add("❌ AZ長度異常！\n👉 第1桶長度: $len1\n👉 第${k + 1}桶長度: $lenK\n(可能發生重複掃描或殘留字元)")
                    }
                }
            }
        } else {
            val rawMasterMat = f[8]
            val masterMaterial = cleanMatMaster(rawMasterMat)
            if (masterMaterial.isEmpty()) return "❌ [四合一 料號] 為必填項目！"

            validate17Series(rawMasterMat, "四合一 料號", allErrors)

            var activeTankCount = 0
            val activeBatchesShort = mutableListOf<String>()
            val collectedBatchBases = mutableListOf<Triple<String, String, String>>()
            val seenDrumbatches = mutableMapOf<String, String>()

            for (i in 0 until tankMap.size) {
                val item = tankMap[i]
                val tankRawBatch = f[item.first]
                val tankInputMat = f[item.second]
                val masterBatchVal = f[masterBatchIndices[i]]

                val numStr = (i + 1).toString()
                val localBatchLabel = "桶$numStr 批號"
                val localMatLabel = "桶$numStr 料號"
                val masterBatchLabel = "4in1 批號$numStr"

                if (tankRawBatch.isNotEmpty() || tankInputMat.isNotEmpty()) {
                    activeTankCount++

                    validate17Series(tankRawBatch, localBatchLabel, allErrors)
                    // 【未來擴充區：現場桶槽料號 檢查】
                    // validate17Series(tankInputMat, localMatLabel, allErrors)
                    // 【未來擴充區：四合一對應批號 檢查】
                    // validate17Series(masterBatchVal, masterBatchLabel, allErrors)

                    val normBatch = normalizeBatch(tankRawBatch)
                    if (normBatch.isNotEmpty()) {
                        if (seenDrumbatches.containsKey(normBatch)) {
                            allErrors.add("❌ [${item.third}] 重複掃描！(與 ${seenDrumbatches[normBatch]} 相同)")
                        } else {
                            seenDrumbatches[normBatch] = item.third
                        }
                    }

                    // 攔截網址型條碼掃進料號欄
                    val tankCleanMat: String
                    if (tankInputMat.uppercase().startsWith("HTTP") || tankInputMat.contains("://")) {
                        allErrors.add("❌ [${item.third}] $localMatLabel 格式錯誤！\n👉 掃到網址條碼，請改掃正確料號")
                        tankCleanMat = ""
                    } else {
                        tankCleanMat = cleanMatMaster(tankInputMat)
                        if (tankCleanMat != masterMaterial) {
                            allErrors.add("❌ [${item.third}] 料號異常！\n👉 $localMatLabel: $tankCleanMat\n👉 四合一 料號: $masterMaterial")
                        }
                    }

                    if (tankRawBatch.contains("@")) {
                        val qrMat = extractRealMat(tankRawBatch)
                        if (qrMat.isNotEmpty() && tankCleanMat.isNotEmpty() && qrMat != tankCleanMat) {
                            allErrors.add("❌ [${item.third}] 貼紙錯誤！\nQR內碼: $qrMat\n與掃描不符。")
                        }
                    }

                    if (masterBatchVal.isEmpty()) {
                        allErrors.add("❌ [${item.third}] 對應的「$masterBatchLabel」未輸入！")
                    } else {
                        val verifyResult = verifyPairStrict(tankRawBatch, masterBatchVal, localBatchLabel, masterBatchLabel)
                        if (!verifyResult.pass) {
                            allErrors.add("❌ [${item.third}] 與四合一單據不符！\n${verifyResult.msg}")
                        }
                    }
                    collectedBatchBases.add(Triple(item.third, getBatchBase(tankRawBatch), tankRawBatch))
                    activeBatchesShort.add(extractBatchForWarehouse(tankRawBatch))
                }
            }

            if (activeTankCount == 0) return "⚠️ 未偵測到任何現場桶槽資料！"

            if (mode == "ship_full" && collectedBatchBases.size > 1) {
                val standardBase = collectedBatchBases[0].second
                for (k in 1 until collectedBatchBases.size) {
                    if (collectedBatchBases[k].second != standardBase) {
                        allErrors.add("❌ 整板批號異常！不同批號不可混在同板")
                    }
                }
            }

            var activeMasterCount = 0
            for (m in 9..12) {
                if (f[m].isNotEmpty()) activeMasterCount++
            }
            if (activeTankCount != activeMasterCount) {
                allErrors.add("❌ 數量異常！現場 $activeTankCount 桶 vs 四合一 $activeMasterCount 筆")
            }

            val rawWhMat = f[13]
            val cleanWhMat = cleanMatMaster(rawWhMat)
            // 【未來擴充區：繳庫單料號 檢查】
            // validate17Series(rawWhMat, "繳庫 料號", allErrors)
            
            if (cleanWhMat != masterMaterial) {
                allErrors.add("❌ [繳庫單] 料號異常！\n👉 繳庫 料號: $cleanWhMat\n👉 四合一 料號: $masterMaterial")
            }

            val whBatch1 = f[14]
            val whBatch2 = f[15]
            val whBatch3 = f[16]
            // 【未來擴充區：繳庫單批號 檢查】
            // validate17Series(whBatch1, "繳庫 批號1", allErrors)
            // validate17Series(whBatch2, "繳庫 批號2", allErrors)
            // validate17Series(whBatch3, "繳庫 批號3", allErrors)

            if (whBatch1.isEmpty() && whBatch2.isEmpty() && whBatch3.isEmpty()) {
                allErrors.add("❌ [繳庫單] 未掃描任何批號！")
            } else {
                val tempBatches = activeBatchesShort.toMutableList()
                val checkAndRemove = { valStr: String ->
                    if (valStr.isEmpty()) true
                    else {
                        var found = false
                        val whNorm = normalizeBatch(extractBatchForWarehouse(valStr))
                        for (i in 0 until tempBatches.size) {
                            val fieldNorm = normalizeBatch(tempBatches[i])
                            if (fieldNorm == whNorm || fieldNorm == "2$whNorm" || whNorm == "2$fieldNorm") {
                                tempBatches.removeAt(i)
                                found = true
                                break
                            }
                        }
                        found
                    }
                }

                if (!checkAndRemove(whBatch1)) allErrors.add("❌ [繳庫 批號1] 異常！現場沒掃到。")
                if (!checkAndRemove(whBatch2)) allErrors.add("❌ [繳庫 批號2] 異常！現場沒掃到。")
                if (!checkAndRemove(whBatch3)) allErrors.add("❌ [繳庫 批號3] 異常！現場沒掃到。")

                val whInputs = mutableListOf<String>()
                if (whBatch1.isNotEmpty()) whInputs.add(normalizeBatch(extractBatchForWarehouse(whBatch1)))
                if (whBatch2.isNotEmpty()) whInputs.add(normalizeBatch(extractBatchForWarehouse(whBatch2)))
                if (whBatch3.isNotEmpty()) whInputs.add(normalizeBatch(extractBatchForWarehouse(whBatch3)))

                val uniqueScannedBatches = mutableListOf<String>()
                for (b in 0 until activeBatchesShort.size) {
                    val bNorm = normalizeBatch(activeBatchesShort[b])
                    if (!uniqueScannedBatches.contains(bNorm)) uniqueScannedBatches.add(bNorm)
                }

                for (u in 0 until uniqueScannedBatches.size) {
                    val needed = uniqueScannedBatches[u]
                    var foundInWh = false
                    for (w in 0 until whInputs.size) {
                        val input = whInputs[w]
                        if (input == needed || input == "2$needed" || needed == "2$input") {
                            foundInWh = true
                            break
                        }
                    }
                    if (!foundInWh) {
                        allErrors.add("❌ [繳庫單] 漏打！現場有但繳庫單沒填。")
                    }
                }
            }
        }

        return if (allErrors.isNotEmpty()) allErrors.joinToString("\n\n") else null
    }
}
```
