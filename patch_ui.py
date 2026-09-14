import os

file_path = r'C:\GOOGLE ANGET\第一類_核心網頁與互動系統\員工教育訓練測驗系統\sop_generator\index.html'
with open(file_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Replace geminiModels array
target_fallback = '''const geminiModels = [
            "gemini-3.8-flash",
            "gemini-3.8-pro",
            "gemini-3.5-flash",
            "gemini-3.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-pro"
          ];'''
replacement_fallback = '''const geminiModels = [
            "gemini-3.8-flash",
            "gemini-3.7-flash",
            "gemini-3.6-flash",
            "gemini-3.5-pro",
            "gemini-3.5-flash",
            "gemini-2.5-pro",
            "gemini-2.5-flash"
          ];'''
html = html.replace(target_fallback, replacement_fallback)

# Replace dropdown
target_dropdown = '''gemini: [
        { value: "gemini-3.8-flash", name: "Gemini 3.8 Flash (最新推薦，速度最快)", selected: true },
        { value: "gemini-3.8-pro", name: "Gemini 3.8 Pro (最新極高精準度)" },
        { value: "gemini-3.5-flash", name: "Gemini 3.5 Flash" },
        { value: "gemini-3.5-pro", name: "Gemini 3.5 Pro" },
        { value: "gemini-2.5-flash", name: "Gemini 2.5 Flash" },
        { value: "gemini-2.5-pro", name: "Gemini 2.5 Pro" }
      ],'''
replacement_dropdown = '''gemini: [
        { value: "gemini-3.8-flash", name: "Gemini 3.8 Flash (最新，極速推理)", selected: true },
        { value: "gemini-3.7-flash", name: "Gemini 3.7 Flash" },
        { value: "gemini-3.6-flash", name: "Gemini 3.6 Flash" },
        { value: "gemini-3.5-pro", name: "Gemini 3.5 Pro (穩定高精準度)" },
        { value: "gemini-3.5-flash", name: "Gemini 3.5 Flash" },
        { value: "gemini-2.5-pro", name: "Gemini 2.5 Pro" },
        { value: "gemini-2.5-flash", name: "Gemini 2.5 Flash" }
      ],'''
html = html.replace(target_dropdown, replacement_dropdown)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(html)
