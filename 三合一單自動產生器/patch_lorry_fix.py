import sys, codecs, re
with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'r', 'utf-8') as f:
    content = f.read()

content = re.sub(
    r'out_l_path = os\.path\.join\(output_dir, lorry_out_name\)',
    r'out_l_path = os.path.join(loc_folder, lorry_out_name)',
    content
)

with codecs.open(r'C:\GOOGLE ANGET\三合一單自動產生器\main.py', 'w', 'utf-8') as f:
    f.write(content)
print("Lorry location patched.")
