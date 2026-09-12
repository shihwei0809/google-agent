import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix genai issue
content = re.sub(
    r'\s*genai\.configure\(api_key=selected\["key"\]\)\s*model = genai\.GenerativeModel\("gemini-2\.0-flash"\)\s*',
    r'\n        ',
    content
)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Genai removed.")
