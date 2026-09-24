import os
import re

def fix_lines(path):
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    pattern = r'(for b in missing:\s*\n\s*lines\.append)'
    replacement = r'''if wrong_factory_msgs:
                    lines.append("\\n--- 廠區異常提醒 ---")
                    lines.extend(wrong_factory_msgs)
                    lines.append("--------------------\\n")
                \1'''
    
    c = re.sub(pattern, replacement, c)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)

fix_lines(r'D:\GOOGLE ANGET\三合一單自動產生器\main.py')
fix_lines(r'D:\GOOGLE ANGET\勝一三合一單產生系統\main.py')
