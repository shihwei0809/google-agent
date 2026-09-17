import codecs
path = r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\static\index.html'
with codecs.open(path, 'r', 'utf-8-sig') as f:
    text = f.read()

if 'function hideLoading()' not in text:
    text = text.replace('function showLoading(msg) {', 'function hideLoading() {\n        if (typeof Swal !== "undefined") Swal.close();\n    }\n    function showLoading(msg) {')

text = text.replace('finally {\n            if (btn) {', 'finally {\n            hideLoading();\n            if (btn) {')
text = text.replace('finally {\r\n            if (btn) {', 'finally {\r\n            hideLoading();\r\n            if (btn) {')

with codecs.open(path, 'w', 'utf-8-sig') as f:
    f.write(text)
