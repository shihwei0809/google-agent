import sys, codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace("genai.configure(api_key=selected[\"key\"])\n        model = genai.GenerativeModel(\"gemini-2.0-flash\")\n", "")

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Removed genai.")
