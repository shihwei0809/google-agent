import codecs
path = r'd:\GOOGLE ANGET\勝一三合一單網頁架機伺服器\server.py'
with codecs.open(path, 'r', 'utf-8-sig') as f:
    text = f.read()
text = text.replace('    import os\r\n', '')
text = text.replace('    import os\n', '')
text = text.replace('                        import re\r\n', '')
text = text.replace('                        import re\n', '')
text = text.replace('                                import csv\r\n', '')
text = text.replace('                                import csv\n', '')
text = text.replace('                                import io\r\n', '')
text = text.replace('                                import io\n', '')
text = text.replace('                            try:\r\n                                import openpyxl\r\n                                import io\r\n', '                            try:\r\n')
text = text.replace('                            try:\n                                import openpyxl\n                                import io\n', '                            try:\n')

if 'import os, re, csv, io, openpyxl' not in text:
    text = text.replace('async def generate_all_zip(payload: dict):', 'async def generate_all_zip(payload: dict):\n    import os, re, csv, io, openpyxl')

with codecs.open(path, 'w', 'utf-8-sig') as f:
    f.write(text)
