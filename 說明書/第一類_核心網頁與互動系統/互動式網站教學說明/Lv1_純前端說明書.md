# Level 1：純前端單機測驗 - 使用說明書

> 🔗 **GitHub 專案庫**：[shihwei0809/google-agent/tree/main/互動式網站](https://github.com/shihwei0809/google-agent/tree/main/互動式網站)


---

## 📝 模組概述
本模組為互動式教學的第一步：**單機純網頁測驗**。所有題庫、作答逻辑與計分演算法皆封裝在瀏覽器端（前端），無須任何後端伺服器或資料庫。

*   **適用場景**：課堂前的快速複習、學員自我評量、無須保存數據的單純互動練習。
*   **優點**：零主機成本、載入速度極快、原始碼完全公開。
*   **缺點**：學員一旦重新整理或關閉網頁，作答紀錄與分數即會完全歸零，且不安全，無法防護 AI API 金鑰。

---

## 🛠️ 技術實作與程式架構

### 檔案位置
*   `互動式網站/lv1-frontend.html`

### 前端 JavaScript 判定邏輯
我們將正確答案陣列硬編碼於前端，透過 DOM 操作即時更改選項的邊框顏色，並顯示原先隱藏的 `class="explanation"` 區塊：

```javascript
const correctAnswers = ['B', 'A']; // 正確選項
let userAnswers = [null, null];   // 學員作答狀態
let isGraded = false;

function selectOption(qIndex, optionLetter) {
  if (isGraded) return;
  // 更新 UI 選取項樣式...
  userAnswers[qIndex] = optionLetter;
}

function submitQuiz() {
  // 1. 檢查是否回答完畢
  // 2. 顯示隱藏的解析區塊 (.style.display = 'block')
  // 3. 與 correctAnswers 對照，答對加分，並為選項套用 .correct / .incorrect 樣式
  // 4. 顯示總分
}
```

---

## 🚀 操作說明
1.  **開啟方式**：在檔案總管中雙擊 `互動式網站/lv1-frontend.html`，直接以瀏覽器開啟即可，不依賴任何本地伺服器。
2.  **進行測驗**：
    *   在單選題中點擊選項，該選項將以霓虹藍邊框標記為已選。
    *   點擊「**送出測驗**」按鈕，題目下方會即時顯示**綠色（答對）**與**紅色（答錯）**的反饋。
    *   解析區塊會自動展開，最下方會顯示總分圓環與回饋評語。
    *   點擊「**重新挑戰**」會重置所有狀態。
