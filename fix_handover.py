import subprocess
import collections

# Get the list of changed files from git
result = subprocess.run(['git', 'log', '--since="midnight"', '--name-status', '--oneline'], capture_output=True, text=True, encoding='utf-8')

changed_files = set()
for line in result.stdout.splitlines():
    parts = line.strip().split('\t')
    if len(parts) >= 2 and parts[0] in ['A', 'M', 'D', 'R']:
        # the file path might be enclosed in quotes and octal escaped by git if it contains non-ascii
        filename = parts[-1]
        if filename.startswith('"') and filename.endswith('"'):
            # git octal escapes, let's decode
            filename = filename[1:-1]
            # Simple unescape using python's unicode_escape
            try:
                # git escapes look like \346
                # a trick is to encode to latin1 then decode to utf8
                filename = filename.encode('latin1').decode('unicode_escape').encode('latin1').decode('utf8')
            except:
                pass
        changed_files.add(filename)

grouped = collections.defaultdict(list)
for f in sorted(changed_files):
    if '/' in f:
        root, rest = f.split('/', 1)
        grouped[root].append(rest)
    else:
        grouped['ROOT'].append(f)

report = "\n### 📂 跨專案異動掃描 (今日所有更新檔案)\n"
for root, files in grouped.items():
    if root == 'ROOT':
        report += "- **[專案根目錄]**\n"
    else:
        report += f"- **{root}/**\n"
    for file in files:
        report += f"  - {file}\n"

# read HANDOVER.md
with open('HANDOVER.md', 'r', encoding='utf-8') as f:
    text = f.read()

# remove the broken part added previously
import re
text = re.sub(r'### 📂 跨專案異動掃描 \(自動生成清單\).*', '', text, flags=re.DOTALL)

with open('HANDOVER.md', 'w', encoding='utf-8') as f:
    f.write(text.strip() + '\n' + report)
print("Fixed HANDOVER.md")
