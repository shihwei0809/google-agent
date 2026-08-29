import re

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/public/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

old_return = """          <td>${o.driver_code || '-'}</td>
          ${actionCell}
        </tr>
      `;"""
new_return = """          <td>${o.driver_code || '-'}</td>
          ${printCell}
          ${actionCell}
        </tr>
      `;"""

if old_return in js:
    js = js.replace(old_return, new_return)
    print("Return row updated.")
else:
    # Use regex to be safe about spaces
    js = re.sub(r'(<td>\$\{o\.driver_code \|\| \'-\'\}</td>\s*)\$\{actionCell\}', r'\1${printCell}\n          ${actionCell}', js)
    print("Return row updated via regex.")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
