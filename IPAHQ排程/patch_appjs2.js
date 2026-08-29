const fs = require('fs');
let appJs = fs.readFileSync('C:/GOOGLE ANGET/IPAHQ排程/public/app.js', 'utf8');

// Update renderLocationMappings to 3 columns
const oldRender = `function renderLocationMappings() {
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
}`;

const newRender = `function renderLocationMappings() {
  if (!locationMappingTable) return;
  locationMappingTable.innerHTML = '';
  currentLocationMappings.forEach((mapping, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = \`
      <td><input type="text" class="form-control" value="\${mapping.shortName || ''}" placeholder="如: 15P5"></td>
      <td><input type="text" class="form-control" value="\${mapping.fullName || ''}" placeholder="如: 台積電竹科15廠P5"></td>
      <td><input type="text" class="form-control" value="\${mapping.code || ''}" placeholder="如: E1550155A"></td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="removeLocationMapping(\${index})">刪除</button>
      </td>
    \`;
    locationMappingTable.appendChild(tr);
  });
}`;

if (appJs.includes(oldRender)) {
  appJs = appJs.replace(oldRender, newRender);
  console.log('renderLocationMappings patched');
} else {
  console.log('renderLocationMappings NOT FOUND - check template literals');
}

// Update gathering logic: 3 inputs per row
const oldGather = `    const rows = locationMappingTable.querySelectorAll('tr');
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
    });`;

const newGather = `    const rows = locationMappingTable.querySelectorAll('tr');
    const newMappings = [];
    rows.forEach(row => {
      const inputs = row.querySelectorAll('input');
      if (inputs.length >= 3) {
        const shortName = inputs[0].value.trim();
        const fullName  = inputs[1].value.trim();
        const code      = inputs[2].value.trim();
        if (shortName || code) {
          newMappings.push({ shortName, fullName, code });
        }
      }
    });`;

if (appJs.includes(oldGather)) {
  appJs = appJs.replace(oldGather, newGather);
  console.log('save logic patched');
} else {
  console.log('save logic NOT FOUND');
}

fs.writeFileSync('C:/GOOGLE ANGET/IPAHQ排程/public/app.js', appJs, 'utf8');
console.log('done');
