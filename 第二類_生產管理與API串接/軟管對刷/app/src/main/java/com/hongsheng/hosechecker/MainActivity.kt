package com.hongsheng.hosechecker

import android.Manifest
import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.common.InputImage
import kotlinx.coroutines.*
import okhttp3.ResponseBody
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.util.concurrent.Executors
import java.text.SimpleDateFormat
import java.util.*

// 🚀 資料模型擴充：新增 status 與 uuid
class MainActivity : ComponentActivity() {
    private val cameraExecutor = Executors.newSingleThreadExecutor()

    private val qcWaitingQueue = mutableStateListOf<DischargeRecord>()
    private val uploadQueue = mutableStateListOf<DischargeRecord>()

    private var isUploadingQueue = mutableStateOf(false)
    private var operatorListState = mutableStateOf(listOf("請選擇操作人員..."))
    private var configListState = mutableStateOf(listOf<List<String>>())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        loadCachedData()
        syncCloudData()
        syncPendingTasks() // 🚀 新增：同步雲端待放行清單

        qcWaitingQueue.addAll(getQueueFromDisk(this, "qc_waiting_list"))
        uploadQueue.addAll(getQueueFromDisk(this, "upload_pending_list"))

        registerNetworkCallback()

        setContent { MaterialTheme { MainScreen() } }
    }

    private fun loadCachedData() {
        val prefs = getSharedPreferences("hose_cache", Context.MODE_PRIVATE)
        val opJson = prefs.getString("cached_operators", null)
        val configJson = prefs.getString("cached_config", null)

        if (!opJson.isNullOrEmpty()) {
            val list: List<String> = Gson().fromJson(opJson, object : TypeToken<List<String>>() {}.type)
            if (list.isNotEmpty()) operatorListState.value = list
        }
        if (!configJson.isNullOrEmpty()) {
            configListState.value = Gson().fromJson(configJson, object : TypeToken<List<List<String>>>() {}.type)
        }
    }

    private fun syncCloudData() {
        NetworkClient.api.getOperatorList("getOperators").enqueue(object : Callback<List<String>> {
            override fun onResponse(call: Call<List<String>>, response: Response<List<String>>) {
                if (response.isSuccessful && response.body() != null) {
                    val newList = listOf("請選擇操作人員...") + response.body()!!
                    operatorListState.value = newList
                    getSharedPreferences("hose_cache", Context.MODE_PRIVATE).edit()
                        .putString("cached_operators", Gson().toJson(newList)).apply()
                }
            }
            override fun onFailure(call: Call<List<String>>, t: Throwable) {}
        })
        NetworkClient.api.getConfig("getConfig").enqueue(object : Callback<List<List<String>>> {
            override fun onResponse(call: Call<List<List<String>>>, response: Response<List<List<String>>>) {
                if (response.isSuccessful) {
                    val newConfig = response.body() ?: emptyList()
                    configListState.value = newConfig
                    getSharedPreferences("hose_cache", Context.MODE_PRIVATE).edit()
                        .putString("cached_config", Gson().toJson(newConfig)).apply()
                }
            }
            override fun onFailure(call: Call<List<List<String>>>, t: Throwable) {}
        })
    }

    // 🚀 新增：從雲端抓取「🔴 待放行」清單 (解決不同手機看不到資料的問題)
    private fun syncPendingTasks() {
        NetworkClient.api.getPendingTasks("getPending").enqueue(object : Callback<List<DischargeRecord>> {
            override fun onResponse(call: Call<List<DischargeRecord>>, response: Response<List<DischargeRecord>>) {
                if (response.isSuccessful && response.body() != null) {
                    qcWaitingQueue.clear()
                    qcWaitingQueue.addAll(response.body()!!)
                    saveQueueToDisk(this@MainActivity, qcWaitingQueue, "qc_waiting_list")
                }
            }
            override fun onFailure(call: Call<List<DischargeRecord>>, t: Throwable) {}
        })
    }

    private fun registerNetworkCallback() {
        val connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val networkRequest = NetworkRequest.Builder().addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET).build()

        connectivityManager.registerNetworkCallback(networkRequest, object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                if (uploadQueue.isNotEmpty() && !isUploadingQueue.value) {
                    CoroutineScope(Dispatchers.IO).launch {
                        val validRecords = uploadQueue.filter {
                            it.operator != "請選擇操作人員..." && it.tank.isNotBlank() && it.hose.isNotBlank()
                        }

                        if (validRecords.isNotEmpty()) {
                            withContext(Dispatchers.Main) { isUploadingQueue.value = true }
                            validRecords.forEach { record ->
                                try {
                                    val response = NetworkClient.api.uploadRecord(record).execute()
                                    if (response.isSuccessful) {
                                        withContext(Dispatchers.Main) {
                                            uploadQueue.remove(record)
                                            saveQueueToDisk(this@MainActivity, uploadQueue, "upload_pending_list")
                                        }
                                    }
                                } catch (e: Exception) {}
                            }
                            withContext(Dispatchers.Main) { isUploadingQueue.value = false }
                        }
                    }
                }
                syncCloudData()
                syncPendingTasks()
            }
        })
    }

    private fun saveQueueToDisk(context: Context, queue: List<DischargeRecord>, key: String) {
        val prefs = context.getSharedPreferences("hose_backup", Context.MODE_PRIVATE)
        prefs.edit().putString(key, Gson().toJson(queue)).apply()
    }

    private fun getQueueFromDisk(context: Context, key: String): List<DischargeRecord> {
        return try {
            val prefs = context.getSharedPreferences("hose_backup", Context.MODE_PRIVATE)
            val jsonData = prefs.getString(key, null) ?: return emptyList()
            Gson().fromJson(jsonData, object : TypeToken<List<DischargeRecord>>() {}.type) ?: emptyList()
        } catch (e: Exception) {
            // 💡 終極防護：如果讀取舊資料失敗（格式不符），就自動清空重來，絕對不閃退！
            emptyList()
        }
    }

    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun MainScreen() {
        var currentTab by remember { mutableStateOf("OPERATOR") }

        Scaffold(
            topBar = {
                TopAppBar(
                    title = { Text("鴻勝化學-對刷稽核系統", color = Color.White) },
                    actions = {
                        IconButton(onClick = { syncPendingTasks(); syncCloudData() }) {
                            Icon(Icons.Default.Refresh, contentDescription = "同步", tint = Color.White)
                        }
                        if (uploadQueue.isNotEmpty()) {
                            BadgedBox(badge = { Badge { Text(uploadQueue.size.toString()) } }, modifier = Modifier.padding(end=16.dp)) {
                                Icon(Icons.Default.CloudUpload, contentDescription = null, tint = Color.Yellow)
                            }
                        } else {
                            Icon(Icons.Default.CloudDone, null, tint = Color.Green, modifier = Modifier.padding(end = 16.dp))
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = Color(0xFF1A237E))
                )
            },
            bottomBar = {
                NavigationBar {
                    NavigationBarItem(
                        selected = currentTab == "OPERATOR",
                        onClick = { currentTab = "OPERATOR" },
                        icon = { Icon(Icons.Default.Edit, "現場作業") },
                        label = { Text("現場作業") }
                    )
                    NavigationBarItem(
                        selected = currentTab == "QC",
                        onClick = { currentTab = "QC" },
                        icon = {
                            BadgedBox(badge = {
                                if (qcWaitingQueue.isNotEmpty()) {
                                    Badge(containerColor = Color.Red) { Text(qcWaitingQueue.size.toString(), color = Color.White) }
                                }
                            }) {
                                Icon(Icons.Default.FactCheck, "QC稽核")
                            }
                        },
                        label = { Text("QC稽核") }
                    )
                }
            }
        ) { padding ->
            if (currentTab == "OPERATOR") {
                OperatorView(padding)
            } else {
                QCView(padding)
            }
        }
    }

    @androidx.annotation.OptIn(androidx.camera.core.ExperimentalGetImage::class)
    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun OperatorView(padding: PaddingValues) {
        val context = LocalContext.current
        val lifecycleOwner = LocalLifecycleOwner.current

        var selectedFactory by remember { mutableStateOf("彰濱一廠") }
        var isFactoryExpanded by remember { mutableStateOf(false) }
        val factoryOptions = listOf("彰濱一廠", "彰濱二廠", "彰濱三廠")

        var selectedOperator by remember { mutableStateOf("請選擇操作人員...") }
        var isExpended by remember { mutableStateOf(false) }
        var scannedTank by remember { mutableStateOf("") }
        var scannedHose by remember { mutableStateOf("") }
        var containerNo by remember { mutableStateOf("") }

        var isScanningTank by remember { mutableStateOf(false) }
        var isScanningHose by remember { mutableStateOf(false) }
        var displayStatus by remember { mutableStateOf("待命") }
        var statusColor by remember { mutableStateOf(Color.Gray) }

        val isAllDataReady = (selectedOperator != "請選擇操作人員...") && scannedTank.isNotEmpty() && scannedHose.isNotEmpty() && containerNo.isNotBlank()

        LaunchedEffect(scannedTank, scannedHose) {
            if (scannedTank.isNotEmpty() && scannedHose.isNotEmpty()) {
                val found = configListState.value.any { it.size >= 3 && it[1].trim() == scannedTank.trim() && it[2].trim() == scannedHose.trim() }
                displayStatus = if (found) "✅ 匹配正確" else "❌ 錯誤！管線誤接"
                statusColor = if (found) Color(0xFF388E3C) else Color.Red
            }
        }

        val launcher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { }
        LaunchedEffect(Unit) { launcher.launch(Manifest.permission.CAMERA) }

        Column(modifier = Modifier.padding(padding).fillMaxSize()) {
            Row(modifier = Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 5.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Card(modifier = Modifier.weight(1f), colors = CardDefaults.cardColors(containerColor = Color(0xFFE3F2FD))) {
                    Box(modifier = Modifier.fillMaxWidth().clickable { isFactoryExpanded = true }.padding(15.dp)) {
                        Text("🏢 $selectedFactory", fontWeight = FontWeight.Bold, color = Color(0xFF0D47A1))
                        DropdownMenu(expanded = isFactoryExpanded, onDismissRequest = { isFactoryExpanded = false }) {
                            factoryOptions.forEach { name ->
                                DropdownMenuItem(text = { Text(name) }, onClick = { selectedFactory = name; isFactoryExpanded = false })
                            }
                        }
                    }
                }
                Card(modifier = Modifier.weight(1.5f), colors = CardDefaults.cardColors(containerColor = if(selectedOperator != "請選擇操作人員...") Color(0xFFE8F5E9) else Color(0xFFFCE4EC))) {
                    Box(modifier = Modifier.fillMaxWidth().clickable { isExpended = true }.padding(15.dp)) {
                        Text(selectedOperator, fontWeight = FontWeight.Bold, color = if(selectedOperator != "請選擇操作人員...") Color.Black else Color.Red)
                        DropdownMenu(expanded = isExpended, onDismissRequest = { isExpended = false }) {
                            operatorListState.value.forEach { name ->
                                DropdownMenuItem(text = { Text(name) }, onClick = { selectedOperator = name; isExpended = false })
                            }
                        }
                    }
                }
            }

            OutlinedTextField(
                value = containerNo,
                onValueChange = { containerNo = it },
                label = { Text("請輸入槽車櫃號 (必要)") },
                modifier = Modifier.fillMaxWidth().padding(horizontal = 10.dp),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(10.dp))

            Box(modifier = Modifier.weight(1.5f).fillMaxWidth().padding(horizontal = 10.dp).background(Color.Black)) {
                if (isScanningTank || isScanningHose) {
                    AndroidView(factory = { ctx ->
                        val previewView = PreviewView(ctx)
                        ProcessCameraProvider.getInstance(ctx).addListener({
                            val provider = ProcessCameraProvider.getInstance(ctx).get()
                            val preview = Preview.Builder().build().also { it.setSurfaceProvider(previewView.surfaceProvider) }
                            val analysis = ImageAnalysis.Builder().build().also {
                                it.setAnalyzer(cameraExecutor) { proxy ->
                                    val mediaImage = proxy.image
                                    if (mediaImage != null) {
                                        val image = InputImage.fromMediaImage(mediaImage, proxy.imageInfo.rotationDegrees)
                                        BarcodeScanning.getClient().process(image).addOnSuccessListener { barcodes ->
                                            if (barcodes.isNotEmpty()) {
                                                val raw = barcodes[0].rawValue ?: ""
                                                if (isScanningTank) { scannedTank = raw; isScanningTank = false }
                                                else if (isScanningHose) { scannedHose = raw; isScanningHose = false }
                                            }
                                        }.addOnCompleteListener { proxy.close() }
                                    } else proxy.close()
                                }
                            }
                            provider.unbindAll()
                            provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, analysis)
                        }, ContextCompat.getMainExecutor(ctx))
                        previewView
                    }, modifier = Modifier.fillMaxSize())
                    IconButton(onClick = { isScanningTank = false; isScanningHose = false }, modifier = Modifier.align(Alignment.TopEnd).padding(15.dp).background(Color.Black.copy(alpha = 0.5f), CircleShape)) { Icon(Icons.Default.Close, null, tint = Color.White) }
                } else {
                    Box(contentAlignment = Alignment.Center, modifier = Modifier.fillMaxSize()) { Text(if(selectedOperator != "請選擇操作人員...") "請點擊按鈕掃描" else "⚠️ 請先選擇人員", color = Color.Gray) }
                }
            }

            Column(modifier = Modifier.fillMaxWidth().padding(bottom = 12.dp)) {
                Row(modifier = Modifier.padding(10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { isScanningTank = true }, modifier = Modifier.weight(1f).height(55.dp), enabled = selectedOperator != "請選擇操作人員...") { Text(if(scannedTank.isEmpty()) "掃描儲槽" else "儲槽: $scannedTank", fontSize = 14.sp) }
                    Button(onClick = { isScanningHose = true }, modifier = Modifier.weight(1f).height(55.dp), enabled = selectedOperator != "請選擇操作人員...", colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF388E3C))) { Text(if(scannedHose.isEmpty()) "掃描軟管" else "軟管: $scannedHose", fontSize = 14.sp) }
                }
                Surface(modifier = Modifier.fillMaxWidth().padding(horizontal = 10.dp).height(70.dp), color = statusColor.copy(alpha = 0.1f), border = BorderStroke(2.dp, statusColor)) {
                    Box(contentAlignment = Alignment.Center) { Text(displayStatus, color = statusColor, fontSize = 24.sp, fontWeight = FontWeight.Bold) }
                }
                Button(
                    onClick = {
                        if (isAllDataReady) {
                            val time = SimpleDateFormat("yyyy/MM/dd HH:mm:ss", Locale.getDefault()).format(Date())
                            // 🚀 產生帶有廠別與 UUID 的紀錄，初始狀態為待放行
                            val record = DischargeRecord(selectedFactory, selectedOperator, scannedTank, scannedHose, containerNo, displayStatus, "🔴 待放行", "", time)

                            // 🚀 直接嘗試上傳 (不只存在手機本機，而是讓雲端暫存池知道)
                            uploadQueue.add(record)
                            saveQueueToDisk(context, uploadQueue, "upload_pending_list")

                            scannedTank = ""; scannedHose = ""; containerNo = ""; displayStatus = "待命"; statusColor = Color.Gray
                            Toast.makeText(context, "✅ 資料已傳送雲端暫存，請通知 QC 稽核", Toast.LENGTH_LONG).show()

                            // 觸發網路檢查上傳
                            CoroutineScope(Dispatchers.IO).launch { uploadQueueData(context) }
                        }
                    },
                    modifier = Modifier.fillMaxWidth().padding(10.dp).height(60.dp),
                    enabled = isAllDataReady,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF1B5E20))
                ) { Text("提交至 QC 稽核", fontSize = 20.sp, color = Color.White) }
            }
        }
    }

    @androidx.annotation.OptIn(androidx.camera.core.ExperimentalGetImage::class)
    @OptIn(ExperimentalMaterial3Api::class)
    @Composable
    fun QCView(padding: PaddingValues) {
        val context = LocalContext.current
        val lifecycleOwner = LocalLifecycleOwner.current
        var searchNo by remember { mutableStateOf("") }
        var activeRecord by remember { mutableStateOf<DischargeRecord?>(null) }
        var isQcScanning by remember { mutableStateOf(false) }
        var scannedQcId by remember { mutableStateOf("") } // 🚀 二段式：暫存掃描到的 ID

        Column(modifier = Modifier.padding(padding).fillMaxSize()) {
            Text("QC 授權放行端", style = MaterialTheme.typography.headlineMedium, modifier = Modifier.padding(10.dp), fontWeight = FontWeight.Bold)

            Surface(modifier = Modifier.fillMaxWidth().padding(horizontal = 10.dp, vertical = 5.dp), color = Color(0xFFE3F2FD), shape = MaterialTheme.shapes.small) {
                Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(10.dp)) {
                    Text("待稽核清單 (雲端同步)", color = Color(0xFF0D47A1), fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                    Text("${qcWaitingQueue.size} 筆", color = Color.Red, fontWeight = FontWeight.Bold)
                }
            }

            LazyRow(modifier = Modifier.padding(horizontal = 10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(qcWaitingQueue) { record ->
                    FilterChip(
                        selected = activeRecord?.uuid == record.uuid,
                        onClick = { activeRecord = record; searchNo = record.containerNo; isQcScanning = false; scannedQcId = "" },
                        label = { Text(record.containerNo) },
                        leadingIcon = { Icon(Icons.Default.LocalShipping, null, modifier = Modifier.size(18.dp)) }
                    )
                }
            }

            activeRecord?.let { record ->
                if (!isQcScanning) {
                    Card(modifier = Modifier.fillMaxWidth().padding(10.dp), colors = CardDefaults.cardColors(containerColor = Color(0xFFFFF3E0))) {
                        Column(modifier = Modifier.padding(15.dp)) {
                            Text("🏢 廠別: ${record.factory}", fontSize = 16.sp, fontWeight = FontWeight.Bold, color = Color(0xFF0D47A1))
                            Text("🚛 櫃號: ${record.containerNo}", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                            Text("🆔 流水號: ${record.uuid}", fontSize = 12.sp, color = Color.Gray)
                            Divider(modifier = Modifier.padding(vertical = 8.dp))
                            Text("👤 作業員: ${record.operator}", fontSize = 16.sp)
                            Text("🛢️ 儲槽: ${record.tank}", fontSize = 16.sp)
                            Text("🧪 軟管: ${record.hose}", fontSize = 16.sp)
                            Text("📌 狀態: ${record.result}", color = if(record.result.contains("正確")) Color(0xFF388E3C) else Color.Red)

                            Spacer(modifier = Modifier.height(15.dp))

                            // 🚀 二段式確認：如果還沒掃過，顯示掃描按鈕；如果掃過了，顯示確認按鈕
                            if (scannedQcId.isEmpty()) {
                                Button(onClick = { isQcScanning = true }, modifier = Modifier.fillMaxWidth().height(55.dp), colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0D47A1))) {
                                    Text("掃描 QC 識別證", fontSize = 18.sp)
                                }
                            } else {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("已讀取 QC: $scannedQcId", color = Color(0xFF0D47A1), fontWeight = FontWeight.Bold)
                                    Spacer(modifier = Modifier.height(8.dp))
                                    Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                                        OutlinedButton(onClick = { scannedQcId = "" }, modifier = Modifier.weight(1f)) { Text("重新掃描") }
                                        Button(
                                            onClick = {
                                                // 🚀 執行最後放行上傳
                                                val approved = record.copy(qcStatus = "🟢 已放行", qcSigner = scannedQcId)
                                                qcWaitingQueue.remove(record)
                                                uploadQueue.add(approved)
                                                saveQueueToDisk(context, qcWaitingQueue, "qc_waiting_list")
                                                saveQueueToDisk(context, uploadQueue, "upload_pending_list")

                                                activeRecord = null
                                                scannedQcId = ""

                                                NetworkClient.api.uploadRecord(approved).enqueue(object : Callback<ResponseBody> {
                                                    override fun onResponse(call: Call<ResponseBody>, response: Response<ResponseBody>) {
                                                        if (response.isSuccessful) {
                                                            uploadQueue.remove(approved)
                                                            saveQueueToDisk(context, uploadQueue, "upload_pending_list")
                                                            Toast.makeText(context, "✅ 放行上傳成功", Toast.LENGTH_SHORT).show()
                                                        }
                                                    }
                                                    override fun onFailure(call: Call<ResponseBody>, t: Throwable) {}
                                                })
                                            },
                                            modifier = Modifier.weight(1.5f),
                                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF1B5E20))
                                        ) { Text("確認放行並上傳") }
                                    }
                                }
                            }
                        }
                    }
                } else {
                    Box(modifier = Modifier.weight(1f).fillMaxWidth().padding(10.dp).background(Color.Black)) {
                        AndroidView(factory = { ctx ->
                            val previewView = PreviewView(ctx)
                            ProcessCameraProvider.getInstance(ctx).addListener({
                                val provider = ProcessCameraProvider.getInstance(ctx).get()
                                val preview = Preview.Builder().build().also { it.setSurfaceProvider(previewView.surfaceProvider) }
                                var scanHandled = false
                                val analysis = ImageAnalysis.Builder().build().also {
                                    it.setAnalyzer(cameraExecutor) { proxy ->
                                        if (scanHandled) { proxy.close(); return@setAnalyzer }
                                        val mediaImage = proxy.image
                                        if (mediaImage != null) {
                                            val image = InputImage.fromMediaImage(mediaImage, proxy.imageInfo.rotationDegrees)
                                            BarcodeScanning.getClient().process(image).addOnSuccessListener { barcodes ->
                                                if (barcodes.isNotEmpty() && !scanHandled) {
                                                    val qcId = barcodes[0].rawValue ?: ""
                                                    if (qcId.isNotEmpty()) {
                                                        scanHandled = true
                                                        scannedQcId = qcId // 🚀 掃描成功後只存入變數，不觸發上傳
                                                        isQcScanning = false
                                                    }
                                                }
                                            }.addOnCompleteListener { proxy.close() }
                                        } else proxy.close()
                                    }
                                }
                                provider.unbindAll()
                                provider.bindToLifecycle(lifecycleOwner, CameraSelector.DEFAULT_BACK_CAMERA, preview, analysis)
                            }, ContextCompat.getMainExecutor(ctx))
                            previewView
                        }, modifier = Modifier.fillMaxSize())
                        IconButton(onClick = { isQcScanning = false }, modifier = Modifier.align(Alignment.TopEnd).padding(15.dp).background(Color.Black.copy(alpha = 0.5f), CircleShape)) { Icon(Icons.Default.Close, null, tint = Color.White) }
                    }
                }
            }
        }
    }

    // 🚀 新增：模擬呼叫上傳佇列
    private suspend fun uploadQueueData(context: Context) {
        if (uploadQueue.isEmpty()) return
        val records = uploadQueue.toList()
        records.forEach { record ->
            try {
                val response = NetworkClient.api.uploadRecord(record).execute()
                if (response.isSuccessful) {
                    withContext(Dispatchers.Main) {
                        uploadQueue.remove(record)
                        saveQueueToDisk(context, uploadQueue, "upload_pending_list")
                    }
                }
            } catch (e: Exception) {}
        }
    }
}