import re

with open('C:\\GOOGLE ANGET\\IPAHQ排程\\public\\index.html', 'r', encoding='utf-8') as f:
    html = f.read()

modal_html = '''
    <!-- 地點代號維護 Modal -->
    <div class="modal" id="location-mapping-modal">
      <div class="modal-content card" style="max-width: 700px;">
        <div class="modal-header">
          <h3>🗺️ 地點代號對照表維護</h3>
          <span class="close-modal" id="close-location-modal">&times;</span>
        </div>
        <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
          <table class="data-table" id="location-mapping-table">
            <thead>
              <tr>
                <th>送達地簡稱</th>
                <th>送達地全名</th>
                <th>送達地點代號</th>
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
'''

if 'id="location-mapping-modal"' not in html:
    html = html.replace('<!-- 編輯訂單的 Modal 彈窗 -->', modal_html + '\n\n  <!-- 編輯訂單的 Modal 彈窗 -->')
    print('Modal injected')
else:
    print('Modal already exists')

if 'id="btn-manage-locations"' not in html:
    html = html.replace('<button id="btn-export"', '<button id="btn-manage-locations" class="btn btn-secondary" style="margin-right: 10px;">🗺️ 地點代號維護</button>\n            <button id="btn-export"')
    print('Button injected')
else:
    print('Button already exists')

with open('C:\\GOOGLE ANGET\\IPAHQ排程\\public\\index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Done')
