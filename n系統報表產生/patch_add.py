import sys

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("all_output_dirs.add(output_dir)", "all_output_dirs.append(output_dir)")

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("PATCHED ADD")

