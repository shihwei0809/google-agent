import sys

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'msg_parts.append(f"• 單列 Chemical_Lorry：成功產生 {total_success_lorry} 份' in line:
        new_lines.append(line.replace('and total_success_lorry > 0', ''))
    elif 'if getattr(self, "gen_lorry_var", None) and self.gen_lorry_var.get() and total_success_lorry > 0:' in line:
        new_lines.append(line.replace(' and total_success_lorry > 0', ''))
    elif 'if not lorry_sources:' in line:
        new_lines.append(line)
        # we want to append an error message if there are no lorry sources
    else:
        new_lines.append(line)

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
