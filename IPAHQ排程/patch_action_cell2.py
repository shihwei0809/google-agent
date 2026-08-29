import re
import os

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/public/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the desktop table action cell creation logic
# Find: const showEdit = ...
# ... `<td><span class="action-link" onclick="openEditModal(...

pattern = re.compile(
    r"(const showEdit = currentUser && \(currentUser\.role === 'sales' \|\| currentUser\.role === 'tech_manager' \|\| currentUser\.role === 'transporter'\);)\s*"
    r"const actionCell = showEdit\s*\?\s*`(<td><span class=\"action-link\" onclick=\"openEditModal\('\$\{o\.id\}', '\$\{o\.destination\}', '\$\{o\.product\}', '\$\{o\.expected_date\}', '\$\{o\.arrival_time\}'\)\">.*?</span></td>)`\s*"
    r":\s*`<td>-</td>`;",
    re.DOTALL
)

new_action = """\\1
      let actionLinks = '';
      if (showEdit) {
        actionLinks += `<span class="action-link" onclick="openEditModal('${o.id}', '${o.destination}', '${o.product}', '${o.expected_date}', '${o.arrival_time}')">編輯</span>`;
      }
      
      // 如果是台積電，直接在列表顯示三合一單按鈕
      if (o.client && (o.client.includes('台積') || o.client.includes('TSMC'))) {
        if (actionLinks !== '') actionLinks += ' | ';
        actionLinks += `<span class="action-link text-cyan" onclick="download3in1('${o.id}')" style="cursor: pointer;">🖨️ 三合一單</span>`;
      }
      
      const actionCell = actionLinks ? `<td>${actionLinks}</td>` : `<td>-</td>`;"""

if pattern.search(content):
    content = pattern.sub(new_action, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Action cell patched successfully!")
else:
    print("Pattern not found!")
