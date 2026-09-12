import sys, codecs
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

old_path = "new_file_path = os.path.join(dir_name, new_base + ext)"
new_path = """                output_dir = os.path.join(self.base_dir, f"三合一單產出_{formatted_date}")
                os.makedirs(output_dir, exist_ok=True)
                new_file_path = os.path.join(output_dir, new_base + ext)"""

content = content.replace(old_path, new_path)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("COA path patched.")
