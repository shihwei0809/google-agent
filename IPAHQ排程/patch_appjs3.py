import re

file_path = 'C:/GOOGLE ANGET/IPAHQ排程/public/app.js'
with open(file_path, 'r', encoding='utf-8') as f:
    js = f.read()

# 1. Fix login re-render bug
# Find the end of applyRolePermissions(currentUser); in checkLogin
login_fix = """      applyRolePermissions(currentUser);
      if (typeof refreshDashboardUI === 'function') refreshDashboardUI();"""

js = js.replace("      applyRolePermissions(currentUser);", login_fix)

# 2. Separate the Action cell and 3-in-1 cell
old_action_block = """      let actionLinks = '';
      if (showEdit) {
        actionLinks += `<span class="action-link" onclick="openEditModal('${o.id}', '${o.destination}', '${o.product}', '${o.expected_date}', '${o.arrival_time}')">編輯</span>`;
      }
      
      // 如果是台積電，直接在列表顯示三合一單按鈕
      if (o.client && (o.client.includes('台積') || o.client.includes('TSMC'))) {
        if (actionLinks !== '') actionLinks += ' | ';
        actionLinks += `<span class="action-link text-cyan" onclick="download3in1('${o.id}')" style="cursor: pointer;">🖨️ 三合一單</span>`;
      }
      
      const actionCell = actionLinks ? `<td>${actionLinks}</td>` : `<td>-</td>`;"""

new_action_block = """      let editLink = '';
      if (showEdit) {
        editLink = `<span class="action-link" onclick="openEditModal('${o.id}', '${o.destination}', '${o.product}', '${o.expected_date}', '${o.arrival_time}')">編輯</span>`;
      }
      const actionCell = editLink ? `<td>${editLink}</td>` : `<td>-</td>`;
      
      // 三合一單獨立一欄
      let printLink = '-';
      if (o.client && (o.client.includes('台積') || o.client.includes('TSMC'))) {
        printLink = `<button class="btn btn-primary btn-sm" onclick="download3in1('${o.id}')" style="padding: 2px 8px; font-size: 0.85rem;">🖨️ 下載</button>`;
      }
      const printCell = `<td>${printLink}</td>`;"""

if old_action_block in js:
    js = js.replace(old_action_block, new_action_block)
    print("Action block successfully separated.")
else:
    print("Action block not found, check string match.")

# 3. Add printCell to the returned row string
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
    print("Return row not found.")
    
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(js)
