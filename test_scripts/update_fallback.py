import os

file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

target = '''        if (provider === "gemini") {
          generatedData = await callGemini(apiKey, model, sopText, slideCount, quizCount);
        } else {'''

replacement = '''        if (provider === "gemini") {
          const geminiModels = [
            "gemini-3.5-flash",
            "gemini-3.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-pro"
          ];
          let startIndex = geminiModels.indexOf(model);
          if (startIndex === -1) startIndex = 0;
          let lastError = null;
          for (let i = startIndex; i < geminiModels.length; i++) {
            try {
              console.log("嘗試使用模型: " + geminiModels[i]);
              generatedData = await callGemini(apiKey, geminiModels[i], sopText, slideCount, quizCount);
              if (generatedData) break;
            } catch (e) {
              console.warn("模型 " + geminiModels[i] + " 失敗: ", e);
              lastError = e;
            }
          }
          if (!generatedData) {
            throw new Error("所有 Gemini 模型均嘗試失敗！最後錯誤：" + (lastError ? lastError.message : "未知錯誤"));
          }
        } else {'''

if target in html:
    html = html.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Replacement successful in index.html")
else:
    print("Target not found in index.html")
