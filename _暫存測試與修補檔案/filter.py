import re
with open(r'D:\GOOGLE ANGET\temp_main.py', encoding='utf-8', errors='ignore') as f:
    text = f.read()
text = re.sub(r'["\'][A-Za-z0-9+/=]{1000,}["\']', '""', text)
with open(r'D:\GOOGLE ANGET\code.txt', 'w', encoding='utf-8') as f:
    f.write(text)
