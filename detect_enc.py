import os
import chardet

file_path = r'C:\GOOGLE ANGET\教育訓練教材\build_manual_doc.py'
with open(file_path, 'rb') as f:
    raw = f.read()

result = chardet.detect(raw)
print("Encoding:", result['encoding'])
print("Confidence:", result['confidence'])

if result['encoding']:
    try:
        print(raw.decode(result['encoding']))
    except:
        pass
