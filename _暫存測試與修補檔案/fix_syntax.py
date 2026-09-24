path = r'D:\GOOGLE ANGET\三合一單網頁架機伺服器\server.py'
import re

with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '                except Exception as ex:\n                    print(f"[Lorry Error] {ex}")',
    '                    except Exception as ex:\n                        print(f"[Lorry Error] {ex}")'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
