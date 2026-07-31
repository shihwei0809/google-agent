import { PLAYER_TEMPLATE } from './player_template.js';

// ════════════════════════════════════════
//  大語言模型 API 呼叫邏輯
// ════════════════════════════════════════

// 建立使用者提示詞 (SOP 轉換提示詞)
function buildPrompt(sopText, slideCount, quizCount) {
  return `請閱讀以下 SOP 或教育訓練教材內容，並將其轉化為一份精美的教學簡報與一份測驗。

【教材內容開始】
${sopText}
【教材內容結束】

【產生需求】
1. 簡報（Slides）：請產生大約 ${slideCount} 頁的簡報投影片。每頁投影片需包含：
   - 投影片標題 (title)
   - 投影片重點清單 (bullets)：最多 4 個簡要的項目（條列重點）
   - 投影片語音朗讀旁白 (narration)：字數約 100~200 字，必須是流暢且自然的繁體中文口語，適合 Web Speech TTS 朗讀，內容要詳實且呼應該頁重點。
2. 測驗（Quiz）：請產生共 ${quizCount} 題的測驗題目。每題需包含：
   - 題目 (question)：題意清晰，考驗對簡報內容的理解。
   - 選項 (options)：必須是剛好 4 個選項，請直接在選項文字內帶有 'A. ', 'B. ', 'C. ', 'D. ' 開頭。
   - 正確答案 (answer)：必須是 'A', 'B', 'C', 'D' 其中一個字元。
   - 解析說明 (explanation)：針對正確答案做簡短解析。
3. 繁體中文：請全部使用「繁體中文（台灣）」語彙產生。`;
}

// 1. 呼叫 Google Gemini (AI Studio)
async function callGemini(apiKey, model, sopText, slideCount, quizCount) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
  const prompt = buildPrompt(sopText, slideCount, quizCount);
  
  const payload = {
    contents: [
      {
        parts: [
          { text: prompt }
        ]
      }
    ],
    generationConfig: {
      responseMimeType: "application/json",
      responseSchema: {
        type: "OBJECT",
        properties: {
          title: { type: "STRING" },
          subtitle: { type: "STRING" },
          slides: {
            type: "ARRAY",
            items: {
              type: "OBJECT",
              properties: {
                title: { type: "STRING" },
                bullets: { type: "ARRAY", items: { type: "STRING" } },
                narration: { type: "STRING" }
              },
              required: ["title", "bullets", "narration"]
            }
          },
          quiz: {
            type: "ARRAY",
            items: {
              type: "OBJECT",
              properties: {
                question: { type: "STRING" },
                options: { type: "ARRAY", items: { type: "STRING" } },
                answer: { type: "STRING" },
                explanation: { type: "STRING" }
              },
              required: ["question", "options", "answer", "explanation"]
            }
          }
        },
        required: ["title", "subtitle", "slides", "quiz"]
      }
    }
  };

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Gemini API 錯誤 (HTTP ${response.status}): ${errorText}`);
  }

  const data = await response.json();
  const textContent = data.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!textContent) {
    throw new Error("Gemini API 未回傳有效內容！");
  }

  return JSON.parse(textContent);
}

// 2. 呼叫 Groq API
async function callGroq(apiKey, model, sopText, slideCount, quizCount) {
  const url = "https://api.groq.com/openai/v1/chat/completions";
  const prompt = buildPrompt(sopText, slideCount, quizCount);
  
  const systemPrompt = `You are a professional education and training materials generator. 
You must analyze the SOP/text provided by the user and respond strictly with a JSON object containing:
- title: A main title for the training (string)
- subtitle: A subtitle for the training (string)
- slides: An array of slide objects, each containing:
  - title: The slide title (string)
  - bullets: An array of strings, max 4 (bullets)
  - narration: Text for TTS voice reading, 100-200 words, detailed, natural (string)
- quiz: An array of quiz objects, each containing:
  - question: The quiz question (string)
  - options: Exactly 4 option strings, starting with "A. ", "B. ", "C. ", "D. "
  - answer: Exactly one letter: "A", "B", "C", or "D"
  - explanation: Brief explanation of the answer (string)

All content must be in Traditional Chinese (繁體中文).
Respond only with the raw JSON object. Do not wrap it in Markdown formatting.`;

  const payload = {
    model: model,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: prompt }
    ],
    response_format: { type: "json_object" }
  };

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Groq API 錯誤 (HTTP ${response.status}): ${errorText}`);
  }

  const data = await response.json();
  const textContent = data.choices?.[0]?.message?.content;
  if (!textContent) {
    throw new Error("Groq API 未回傳有效內容！");
  }

  return JSON.parse(textContent);
}

// ════════════════════════════════════════
//  檔案封裝與下載邏輯
// ════════════════════════════════════════

// 組合最終 Player 的 HTML 內容
function assemblePlayerHTML(data, passScore, requireListen) {
  let html = PLAYER_TEMPLATE;
  html = html.replace(/__TRAINING_TITLE__/g, data.title || "教育訓練");
  html = html.replace(/__TRAINING_SUBTITLE__/g, data.subtitle || "請詳閱簡報內容並完成測驗");
  html = html.replace("__SLIDES_DATA__", JSON.stringify(data.slides, null, 2));
  html = html.replace("__QUIZ_DATA__", JSON.stringify(data.quiz, null, 2));
  html = html.replace("__PASS_SCORE__", passScore);
  html = html.replace("__REQUIRE_LISTEN__", requireListen ? "true" : "false");
  return html;
}

// 產生 Google Apps Script 後端程式碼
function generateAppsScriptCode(title) {
  return `// ============================================================
// 📋 Google Apps Script — 員工教育訓練測驗成績收集系統 (${title})
// ============================================================
// 
// 操作步驟：
// 1. 前往 https://sheets.new 建立一個新的試算表，命名為「員工測驗紀錄」
// 2. 點選上方選單的「擴充功能」->「Apps Script」
// 3. 將此編輯器內原有的內容清空，並貼上下方所有的程式碼後存檔。
// 4. 點選右上角的「部署」->「新增部署作業」
//    - 選取類型：網頁應用程式 (Web App)
//    - 說明：教育訓練成績回收
//    - 執行身分：我 (Me)
//    - 誰可以存取：所有人 (Anyone)
// 5. 點擊「部署」，授權存取 Google 帳號後，複製產生的「網頁應用程式 URL」。
// 6. 將複製的網址，貼入測驗網頁右上角「⚙️ 系統設定」的雲端同步欄位中即可。

const SHEET_NAME = '作答紀錄'; // 成績將自動寫入此工作表頁籤

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName(SHEET_NAME);
    
    // 若工作表不存在，自動建立
    if (!sheet) {
      sheet = ss.insertSheet(SHEET_NAME);
    }
    
    // 解析傳入的成績資料
    const name = data.name || '未知';
    const score = data.score !== undefined ? data.score : 0;
    const correctCount = data.correctCount !== undefined ? data.correctCount : 0;
    const total = data.total !== undefined ? data.total : 0;
    const timestamp = data.timestamp || new Date().toLocaleString('zh-TW', { timeZone: 'Asia/Taipei' });
    
    // 動態搜集作答題目的答案
    const qAnswers = [];
    let qIndex = 1;
    while (data['q' + qIndex] !== undefined) {
      qAnswers.push(data['q' + qIndex]);
      qIndex++;
    }
    
    // 若為全空工作表，建立標頭列
    if (sheet.getLastRow() === 0) {
      const headers = ['時間戳記', '姓名', '對題數', '得分'];
      for (let i = 1; i < qIndex; i++) {
        headers.push('第 ' + i + ' 題作答');
      }
      sheet.appendRow(headers);
      
      // 標頭樣式設計
      const range = sheet.getRange(1, 1, 1, headers.length);
      range.setBackground('#4F46E5');
      range.setFontColor('#FFFFFF');
      range.setFontWeight('bold');
    }
    
    // 寫入資料列
    const rowData = [timestamp, name, correctCount + ' / ' + total, score + ' 分'];
    qAnswers.forEach(ans => rowData.push(ans));
    sheet.appendRow(rowData);
    
    return ContentService.createTextOutput(JSON.stringify({ status: 'ok', message: '已成功存入雲端試算表！' }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}
`;
}

// 產生 PowerShell 本機伺服器腳本
function generatePowerShellServer() {
  return `$port = 8000

# 使用 UDP 連線獲取本機對外的內網 IP
$socket = New-Object System.Net.Sockets.UdpClient
$ip = $null
try {
    $socket.Connect("8.8.8.8", 80)
    $ip = $socket.Client.LocalEndPoint.Address.IPAddressToString
} catch {} finally {
    if ($socket) { $socket.Close() }
}

if (-not $ip) {
    $ip = (Get-NetIPAddress | Where-Object { $_.AddressFamily -eq 'InterNetwork' -and $_.IPAddress -notmatch '^127\\.' -and $_.IPAddress -notmatch '^169\\.254\\.' } | Select-Object -First 1).IPAddress
}

if (-not $ip) { $ip = '127.0.0.1' }

$localIP = [System.Net.IPAddress]::Parse($ip)
$listener = New-Object System.Net.Sockets.TcpListener($localIP, $port)

try {
    $listener.Start()
} catch {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  ❌ 啟動失敗！" -ForegroundColor Red
    Write-Host "  可能原因：連接埠 $($port) 已被佔用。請關閉其他伺服器再重試。" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Read-Host "按 Enter 結束..."
    exit
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  📋 員工教育訓練測驗系統 — 本機內網網頁伺服器" -ForegroundColor Cyan
Write-Host "============================================================\`n" -ForegroundColor Cyan
Write-Host "  伺服器運行中..."
Write-Host "  💡 注意：請【勿】關閉此視窗，關閉代表結束服務。"
Write-Host "  💡 同仁的手機或電腦，必須與您連線至【同一個 Wi-Fi】或公司網路。\`n"
Write-Host "  📢 同仁請在瀏覽器輸入以下網址開啟測驗："
Write-Host "  👉 http://$($ip):$($port)/index.html" -ForegroundColor Green
Write-Host "\`n============================================================" -ForegroundColor Cyan

$currentDir = $PSScriptRoot
if (-not $currentDir) { $currentDir = (Get-Location).Path }

while ($true) {
    try {
        if (-not $listener.Pending()) {
            Start-Sleep -Milliseconds 100
            continue
        }
        $client = $listener.AcceptTcpClient()
        $stream = $client.GetStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $requestLine = $reader.ReadLine()
        
        if ($requestLine -match '^(GET|POST)\\s+(/[^\\s\\?]*)\\??[^\\s]*\\s+HTTP') {
            $method = $Matches[1]
            $urlPath = $Matches[2]
            if ($urlPath -eq "/") { $urlPath = "/index.html" }
            $urlPath = [System.Uri]::UnescapeDataString($urlPath)
            
            if ($method -eq "POST" -and $urlPath -eq "/api/submit") {
                # 處理 POST 提交成績
                $headers = @{}
                while ($line = $reader.ReadLine()) {
                    if ($line -eq "") { break }
                    if ($line -match '^([^:]+):\\s*(.*)$') {
                        $headers[$Matches[1].ToLower()] = $Matches[2].Trim()
                    }
                }
                
                $contentLength = 0
                if ($headers.ContainsKey("content-length")) {
                    [int]::TryParse($headers["content-length"], [ref]$contentLength) | Out-Null
                }
                
                $body = ""
                if ($contentLength -gt 0) {
                    $buffer = New-Object System.Char[] $contentLength
                    $read = $reader.Read($buffer, 0, $contentLength)
                    $body = New-Object System.String($buffer, 0, $read)
                }
                
                try {
                    $record = $body | ConvertFrom-Json
                    $csvPath = Join-Path $currentDir "results.csv"
                    
                    # 建立 CSV 標頭
                    if (-not (Test-Path $csvPath)) {
                        $headersLine = "時間戳記,姓名,對題數,得分"
                        $qCount = 0
                        foreach ($prop in $record.PSObject.Properties) {
                            if ($prop.Name -match '^q\\d+$') { $qCount++ }
                        }
                        for ($i = 1; $i -le $qCount; $i++) {
                            $headersLine += ",第${i}題"
                        }
                        [System.IO.File]::WriteAllText($csvPath, "$headersLine\`r\`n", [System.Text.Encoding]::UTF8)
                    }
                    
                    # 組合紀錄列
                    $qCount = 0
                    foreach ($prop in $record.PSObject.Properties) {
                        if ($prop.Name -match '^q\\d+$') { $qCount++ }
                    }
                    $correctStr = "$($record.correctCount) / $($record.total)"
                    $scoreStr = "$($record.score) 分"
                    $nameClean = $record.name -replace '"', '""'
                    $tsClean = $record.timestamp -replace '"', '""'
                    
                    $row = """$tsClean"",""$nameClean"",""$correctStr"",""$scoreStr"""
                    for ($i = 1; $i -le $qCount; $i++) {
                        $val = $record."q$i" -replace '"', '""'
                        $row += ",\`"$val\`""
                    }
                    
                    [System.IO.File]::AppendAllText($csvPath, "$row\`r\`n", [System.Text.Encoding]::UTF8)
                    
                    $respBody = '{"status":"ok","message":"saved"}'
                    $respBytes = [System.Text.Encoding]::UTF8.GetBytes($respBody)
                    $header = "HTTP/1.1 200 OK\`r\`nContent-Type: application/json; charset=utf-8\`r\`nContent-Length: $($respBytes.Length)\`r\`nAccess-Control-Allow-Origin: *\`r\`nConnection: close\`r\`n\`r\`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($respBytes, 0, $respBytes.Length)
                    Write-Host "📥 [本機紀錄] 收到同仁 $($record.name) 的作答結果，已寫入 results.csv" -ForegroundColor Yellow
                } catch {
                    $err = '{"status":"error","message":"' + $_.Exception.Message.Replace('"', '\\"') + '"}'
                    $respBytes = [System.Text.Encoding]::UTF8.GetBytes($err)
                    $header = "HTTP/1.1 500 Error\`r\`nContent-Type: application/json\`r\`nContent-Length: $($respBytes.Length)\`r\`nConnection: close\`r\`n\`r\`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($respBytes, 0, $respBytes.Length)
                }
            } else {
                # 靜態網頁載入
                $filePath = Join-Path $currentDir $urlPath
                if (Test-Path $filePath -PathType Leaf) {
                    $ext = [System.IO.Path]::GetExtension($filePath).ToLower()
                    $contentType = switch ($ext) {
                        ".html" { "text/html; charset=utf-8" }
                        ".css"  { "text/css; charset=utf-8" }
                        ".js"   { "application/javascript; charset=utf-8" }
                        default { "application/octet-stream" }
                    }
                    $bytes = [System.IO.File]::ReadAllBytes($filePath)
                    $header = "HTTP/1.1 200 OK\`r\`nContent-Type: $contentType\`r\`nContent-Length: $($bytes.Length)\`r\`nAccess-Control-Allow-Origin: *\`r\`nConnection: close\`r\`n\`r\`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($bytes, 0, $bytes.Length)
                } else {
                    $errText = "404 Not Found"
                    $errBytes = [System.Text.Encoding]::UTF8.GetBytes($errText)
                    $header = "HTTP/1.1 404 Not Found\`r\`nContent-Length: $($errBytes.Length)\`r\`nConnection: close\`r\`n\`r\`n"
                    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
                    $stream.Write($headerBytes, 0, $headerBytes.Length)
                    $stream.Write($errBytes, 0, $errBytes.Length)
                }
            }
        }
        $stream.Close()
        $client.Close()
    } catch {}
}
`;
}

// 產生啟動批次檔
function generateBatShortcut() {
  return `@echo off
chcp 65001 > nul
title 啟動員工教育訓練本機伺服器
echo ============================================================
echo   正在啟動本機內網伺服器，請稍候...
echo ============================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0serve_intranet.ps1"
pause
`;
}

// 產生說明書 Markdown
function generateReadmeText(title) {
  return `# 員工教育訓練系統 — 說明書 (SOP: ${title})

本資料夾是由「教育訓練測驗產生系統」自動產生的完整檔案包，包含簡報閱讀、自動語音朗讀、測驗防刷，以及本機/雲端雙重成績收集功能。

---

## 📁 檔案內容說明
1. **\`index.html\`**：主測驗網頁（已內嵌您的 SOP 投影片與測驗題目，免下載圖片，直接用瀏覽器開啟即可播放簡報並作答）。
2. **\`serve_intranet.ps1\`**：本機伺服器程式（以 Windows PowerShell 撰寫，負責接收同仁提交的成績並存入本機試算表）。
3. **\`點我啟動內網伺服器(Windows免安裝).bat\`**：一鍵啟動批次檔，按滑鼠雙擊即可運行。
4. **\`apps_script_code.gs\`**：Google Sheets 雲端同步腳本（供會寫 Apps Script 的人員設定雲端回收）。

---

## 🚀 收集同仁的成績（本機免設定模式 - 最簡單）

1. **解壓縮**：請確保此資料夾已解壓縮到您的電腦（不要直接在 zip 檔案中點兩下執行）。
2. **啟動本機伺服器**：
   - 雙擊執行 **\`點我啟動內網伺服器(Windows免安裝).bat\`**。
   - 電腦會彈出一個黑色的終端機視窗，並以綠色字體顯示一串連線網址（例如：\`http://192.168.1.100:8000/index.html\`）。**請勿關閉此視窗**。
3. **同仁開啟作答**：
   - 將該綠色網址傳送給同仁（或透過瀏覽器產生 QR 碼給同仁掃描）。
   - **重要前提**：同仁的手機或電腦必須連線至**與您相同的公司 Wi-Fi 或內網**。
4. **回收成績 (results.csv)**：
   - 同仁做完題目點選「送出」後，您的伺服器視窗中會同步顯示「收到同仁 XXX 的答案」。
   - 資料夾中會**自動產生 \`results.csv\`** 檔案，您直接雙擊該檔即可用 Excel 查看全體成績、作答時間以及每題答錯/答對的詳細紀錄！

---

## ☁️ 收集同仁的成績（雲端 Google Sheets 模式 - 可選填）

如果您想要讓同仁的成績自動存入雲端的 Google Sheets 試算表中：

1. **建立 Google Sheets 試算表**：
   - 前往 [Google Sheets](https://sheets.new) 建立一份新試算表，命名為「教育訓練成績回收」。
2. **建立 Apps Script 腳本**：
   - 在試算表上方點選「**擴充功能**」->「**Apps Script**」。
   - 打開資料夾中的 \`apps_script_code.gs\`，將裡面的程式碼複製，全部貼入 Apps Script 編輯器中取代原本的空函數，然後存檔。
3. **部署網頁應用程式**：
   - 點擊右上角「**部署**」->「**新增部署作業**」。
   - 選取類型：**網頁應用程式** (Web App)。
   - 專案說明：填寫「成績收集」。
   - 執行身分：選擇「**我**」(Me)。
   - 誰可以存取：選擇「**所有人**」(Anyone)。
   - 點擊「**部署**」，在出現的視窗中完成 Google 帳號授權，最後**複製網頁應用程式 URL 網址**。
4. **填入測驗系統**：
   - 開啟您的 \`index.html\`，點選右上角的 **⚙️ 系統設定**（管理員密碼預設為 \`admin888\`）。
   - 在「雲端同步網址」欄位中貼入您剛才複製的 Google Web App URL，然後儲存。
   - 同仁提交時，成績就會自動非同步備份到雲端的 Google 試算表中！
`;
}

// 打包並下載 ZIP 檔案 (使用 HTML 引入的 JSZip)
async function downloadTrainingPackage(data, passScore, requireListen) {
  if (typeof JSZip === 'undefined') {
    throw new Error('未偵測到 JSZip 函式庫，請確認網路連線是否正常！');
  }

  const zip = new JSZip();
  const folderName = (data.title || "SOP_Training").trim().replace(/[\/\\?%*:|"<>\s]/g, "_");

  // 1. 生成各檔案內容
  const playerHtml = assemblePlayerHTML(data, passScore, requireListen);
  const psServer = generatePowerShellServer();
  const batFile = generateBatShortcut();
  const appsScript = generateAppsScriptCode(data.title || "教育訓練");
  const readme = generateReadmeText(data.title || "教育訓練");

  // 2. 塞入 ZIP
  const root = zip.folder(folderName);
  root.file("index.html", playerHtml);
  root.file("serve_intranet.ps1", psServer);
  root.file("點我啟動內網伺服器(Windows免安裝).bat", batFile);
  root.file("apps_script_code.gs", appsScript);
  root.file("README.md", readme);

  // 3. 產生二進位 Blob 並觸發瀏覽器下載
  const content = await zip.generateAsync({ type: "blob" });
  const url = URL.createObjectURL(content);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${folderName}_教育訓練測驗套件.zip`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export {
  callGemini,
  callGroq,
  assemblePlayerHTML,
  downloadTrainingPackage
};
