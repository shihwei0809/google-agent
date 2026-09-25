import os
file_path = r'C:\GOOGLE ANGET\教育訓練教材\README.md'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        print(f.read())
except Exception as e:
    with open(file_path, 'r', encoding='big5') as f:
        print(f.read())
