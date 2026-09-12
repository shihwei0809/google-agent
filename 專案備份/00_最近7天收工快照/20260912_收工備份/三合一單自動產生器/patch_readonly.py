import codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace("wb_l = openpyxl.load_workbook(self.imported_lorry_files[0], data_only=True)", "self.update()\n                wb_l = openpyxl.load_workbook(self.imported_lorry_files[0], data_only=True, read_only=True)")

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Read-only patch applied.")
