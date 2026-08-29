import os

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/public/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_action = """      const showEdit = currentUser && (currentUser.role === 'sales' || currentUser.role === 'tech_manager' || currentUser.role === 'transporter');
      const actionCell = showEdit 
        ? `<td><span class="action-link" onclick="openEditModal('${o.id}', '${o.destination}', '${o.product}', '${o.expected_date}', '${o.arrival_time}')">編輯</span></td>`
        : `<td>-</td>`;"""

new_action = """      const showEdit = currentUser && (currentUser.role === 'sales' || currentUser.role === 'tech_manager' || currentUser.role === 'transporter');
      
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

if old_action in content:
    content = content.replace(old_action, new_action)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Action cell patched successfully!")
else:
    print("Old action not found!")
    
    # Let's search for "openEditModal" to see if it changed
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "openEditModal" in line:
            print("Found openEditModal at line", i, ":", line)
