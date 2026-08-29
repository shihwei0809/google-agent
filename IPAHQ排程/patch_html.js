const fs = require('fs');
let html = fs.readFileSync('C:/GOOGLE ANGET/IPAHQ排程/public/index.html', 'utf8');

const modalHtml = `
    <!-- 地點代號維護 Modal -->
    <div class="modal" id="location-mapping-modal">
      <div class="modal-content card" style="max-width: 600px;">
        <div class="modal-header">
          <h3>🗺️ 地點代號對照表維護</h3>
          <span class="close-modal" id="close-location-modal">&times;</span>
        </div>
        <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
          <table class="data-table" id="location-mapping-table">
            <thead>
              <tr>
                <th>短地點</th>
                <th>長代號 (台積電用)</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
            </tbody>
          </table>
          <button id="btn-add-location" class="btn btn-secondary" style="margin-top: 10px;">+ 新增一筆</button>
        </div>
        <div class="modal-footer">
          <button class="btn btn-primary" id="btn-save-location">儲存並反寫回 Excel</button>
        </div>
      </div>
    </div>
`;

if (!html.includes('id="location-mapping-modal"')) {
    html = html.replace('<!-- 編輯訂單的 Modal 視窗 -->', modalHtml + '\n\n    <!-- 編輯訂單的 Modal 視窗 -->');
}

if (!html.includes('id="btn-manage-locations"')) {
    html = html.replace('<button id="btn-export"', '<button id="btn-manage-locations" class="btn btn-secondary" style="margin-right: 10px;">🗺️ 地點代號維護</button>\n            <button id="btn-export"');
}

fs.writeFileSync('C:/GOOGLE ANGET/IPAHQ排程/public/index.html', html, 'utf8');
console.log('patched index.html');
