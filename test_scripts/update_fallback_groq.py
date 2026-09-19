import os

file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

target = '''        } else {
          generatedData = await callGroq(apiKey, model, sopText, slideCount, quizCount);
        }'''

replacement = '''        } else {
          const groqModels = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant"
          ];
          let startIndex = groqModels.indexOf(model);
          if (startIndex === -1) startIndex = 0;
          let lastError = null;
          for (let i = startIndex; i < groqModels.length; i++) {
            try {
              console.log("嘗試使用 Groq 模型: " + groqModels[i]);
              generatedData = await callGroq(apiKey, groqModels[i], sopText, slideCount, quizCount);
              if (generatedData) break;
            } catch (e) {
              console.warn("Groq 模型 " + groqModels[i] + " 失敗: ", e);
              lastError = e;
            }
          }
          if (!generatedData) {
            throw new Error("所有 Groq 模型均嘗試失敗！最後錯誤：" + (lastError ? lastError.message : "未知錯誤"));
          }
        }'''

if target in html:
    html = html.replace(target, replacement)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("Replacement successful for Groq in index.html")
else:
    print("Target not found for Groq")
