const fs = require('fs');
let appJs = fs.readFileSync('C:/GOOGLE ANGET/IPAHQ排程/public/app.js', 'utf8');

const tsmcLogic = `
window.isTSMCOrder = function(o) {
  if (!o || !o.destination) return false;
  return o.destination.includes('台積') || o.destination.includes('F20') || o.destination.includes('TSMC');
};

window.download3in1 = async function(id) {
  try {
    const res = await fetch(\`/api/orders/\${id}/tsmc-3in1\`);
    if (res.ok) {
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = \`三合一單-\${id}.xlsx\`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } else {
      const data = await res.json();
      alert('生成失敗: ' + (data.message || ''));
    }
  } catch (err) {
    alert('下載錯誤: ' + err.message);
  }
};
`;

if (!appJs.includes('window.isTSMCOrder')) {
  appJs += '\n' + tsmcLogic;
}

// Add the button next to edit link
if (!appJs.includes('download3in1(')) {
    // 桌面版 action links
    appJs = appJs.replace(
        /(<a href="#" onclick="editOrder\('\${o\.id}'\); return false;" class="action-link text-blue">📝 編輯<\/a>)/g,
        `$1\n            \${isTSMCOrder(o) ? \`<span class="action-divider">|</span><a href="#" onclick="download3in1('\${o.id}'); return false;" class="action-link text-cyan">🖨️ 三合一單</a>\` : ''}`
    );
    // 手機版按鈕
    appJs = appJs.replace(
        /(<button onclick="editOrder\('\${o\.id}'\)" class="btn btn-primary btn-sm">📝 編輯<\/button>)/g,
        `$1\n            \${isTSMCOrder(o) ? \`<button onclick="download3in1('\${o.id}')" class="btn btn-info btn-sm">🖨️ 三合一單</button>\` : ''}`
    );
}

// Location Mappings logic
const locationLogic = `
// --- Location Mappings ---
const btnManageLocations = document.getElementById('btn-manage-locations');
const locationMappingModal = document.getElementById('location-mapping-modal');
const closeLocationModal = document.getElementById('close-location-modal');
const btnAddLocation = document.getElementById('btn-add-location');
const btnSaveLocation = document.getElementById('btn-save-location');
const locationMappingTable = document.getElementById('location-mapping-table') ? document.getElementById('location-mapping-table').querySelector('tbody') : null;

let currentLocationMappings = [];

if (btnManageLocations) {
  btnManageLocations.addEventListener('click', async () => {
    try {
      const res = await fetch('/api/location-mappings');
      const data = await res.json();
      if (data.success) {
        currentLocationMappings = data.data;
        renderLocationMappings();
        locationMappingModal.classList.add('open');
      } else {
        alert(data.message);
      }
    } catch (err) {
      console.error(err);
      alert('無法載入地點代號對照表');
    }
  });
}

if (closeLocationModal) {
  closeLocationModal.addEventListener('click', () => {
    locationMappingModal.classList.remove('open');
  });
}

if (btnAddLocation) {
  btnAddLocation.addEventListener('click', () => {
    currentLocationMappings.push({ shortName: '', longCode: '' });
    renderLocationMappings();
  });
}

if (btnSaveLocation) {
  btnSaveLocation.addEventListener('click', async () => {
    const rows = locationMappingTable.querySelectorAll('tr');
    const newMappings = [];
    rows.forEach(row => {
      const inputs = row.querySelectorAll('input');
      if (inputs.length === 2) {
        const shortName = inputs[0].value.trim();
        const longCode = inputs[1].value.trim();
        if (shortName && longCode) {
          newMappings.push({ shortName, longCode });
        }
      }
    });

    try {
      btnSaveLocation.disabled = true;
      btnSaveLocation.textContent = '儲存中...';
      const res = await fetch('/api/location-mappings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          mappings: newMappings,
          operator: currentUser ? currentUser.displayName : '未知',
          role: currentUser ? currentUser.role : 'admin'
        })
      });
      const data = await res.json();
      if (data.success) {
        alert('儲存成功！');
        locationMappingModal.classList.remove('open');
      } else {
        alert(data.message);
      }
    } catch (err) {
      console.error(err);
      alert('儲存失敗: ' + err.message);
    } finally {
      btnSaveLocation.disabled = false;
      btnSaveLocation.textContent = '儲存並反寫回 Excel';
    }
  });
}

function renderLocationMappings() {
  if (!locationMappingTable) return;
  locationMappingTable.innerHTML = '';
  currentLocationMappings.forEach((mapping, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = \`
      <td><input type="text" class="form-control" value="\${mapping.shortName || ''}" placeholder="如: 15P5"></td>
      <td><input type="text" class="form-control" value="\${mapping.longCode || ''}" placeholder="如: E1550155A"></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="removeLocationMapping(\${index})">刪除</button>
      </td>
    \`;
    locationMappingTable.appendChild(tr);
  });
}

window.removeLocationMapping = function(index) {
  currentLocationMappings.splice(index, 1);
  renderLocationMappings();
};
`;

if (!appJs.includes('btn-manage-locations')) {
  appJs += '\n' + locationLogic;
}

fs.writeFileSync('C:/GOOGLE ANGET/IPAHQ排程/public/app.js', appJs, 'utf8');
console.log('patched app.js');
