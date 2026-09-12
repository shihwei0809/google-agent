import codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

# Add self.update() after processing each file
content = content.replace("success_count += 1\n            except Exception as e:", "success_count += 1\n                self.update()\n            except Exception as e:")

# Also add self.update() inside the lorry loading loop every 100 rows
lorry_loop = "for idx, row_data in enumerate(ws_l.iter_rows(values_only=True)):"
new_lorry_loop = lorry_loop + "\n                    if idx % 100 == 0: self.update()"
content = content.replace(lorry_loop, new_lorry_loop)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("UI update patch applied.")
