import re

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# 1. Remove ALL injected scripts first!
bad_script = '''
    async function processPhotoUpload(sampleId, isNewSample=false) {
      if(!currentPhotoBase64 || !GAS_API_URL) return null;
      try {
        const resp = await fetch(GAS_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'text/plain;charset=utf-8' },
          body: JSON.stringify({
            action: 'uploadPhoto',
            id: sampleId,
            filename: 'photo.jpg',
            mimeType: currentPhotoMime,
            base64: currentPhotoBase64
          })
        });
        const res = await resp.json();
        if(res.success && res.url) {
          // 如果有 D1 API，把 photoUrl 寫入
          if (API_URL) {
            await fetch(API_URL, {
               method: 'POST',
               headers: { 'Content-Type': 'application/json' },
               body: JSON.stringify({ action: 'updatePhotoUrl', payload: { id: sampleId, url: res.url } })
            });
          }
          return res.url;
        }
      } catch(e) {
        console.error('Photo upload failed:', e);
      }
      return null;
    }

    let currentPhotoBase64 = null;
    let currentPhotoMime = null;
    let currentPhotoTarget = null;

    function triggerPhotoUpload(target) {
      currentPhotoTarget = target;
      document.getElementById('photoInput').click();
    }

    function handlePhotoSelect(event) {
      const file = event.target.files[0];
      if(!file) return;
      const reader = new FileReader();
      reader.onload = function(e) {
        currentPhotoBase64 = e.target.result.split(',')[1];
        currentPhotoMime = file.type;
        if(currentPhotoTarget === 'submit') {
          document.getElementById('submitPhotoText').innerText = "✅ 已附加照片 (" + file.name + ")";
          document.getElementById('submitPhotoText').style.color = "#059669";
        } else if (currentPhotoTarget === 'judge') {
          document.getElementById('judgePhotoText').innerText = "✅ 已附加照片 (" + file.name + ")";
          document.getElementById('judgePhotoText').style.color = "#059669";
        }
      };
      reader.readAsDataURL(file);
    }

    function resetPhotoUpload() {
      currentPhotoBase64 = null;
      currentPhotoMime = null;
      document.getElementById('photoInput').value = '';
      const st = document.getElementById('submitPhotoText');
      if(st) { st.innerText = "附加樣品照片 (選填)"; st.style.color = "#475569"; }
      const jt = document.getElementById('judgePhotoText');
      if(jt) { jt.innerText = "附加佐證照片 (選填)"; jt.style.color = "#475569"; }
    }
'''
c = c.replace(bad_script, '')

# Now safely add it ONLY ONCE before the last </script>
idx = c.rfind('</script>')
if idx != -1:
    c = c[:idx] + bad_script + c[idx:]

# 2. Add button to qcForm
qc_form_btn = '''
          <div style="grid-column: 1 / -1; margin-top: 10px;">
            <button type="button" onclick="triggerPhotoUpload('submit')" style="background:#f1f5f9; color:#475569; border:1px dashed #cbd5e1; padding:8px 12px; border-radius:6px; cursor:pointer; width:100%; display:flex; align-items:center; justify-content:center; gap:8px;">
              <span style="font-size:1.2rem;">📷</span> <span id="submitPhotoText">附加樣品照片 (選填)</span>
            </button>
          </div>
'''
if '附加樣品照片' not in c:
    c = c.replace('<button type="button" id="submitBtn"', qc_form_btn + '          <button type="button" id="submitBtn"')

# 3. Patch submitForm to use processPhotoUpload
submit_form_patch = '''
      const payload = { 
        id: 'ID-' + Date.now(),
        barcode: barcode, 
        flowType: document.getElementById('flowType').value, 
        grade: document.getElementById('grade').value,
        productName: productName, 
        tankNo: tankNo, 
        customer: customer, 
        quantity: document.getElementById('quantity').value, 
        dept: dept, 
        requester: requester,
        remark: remark,
        status: 'pending',
        createdAt: new Date().toISOString()
      };
      
      if(currentPhotoBase64) {
         showToast("📷 正在上傳照片...");
         await processPhotoUpload(payload.id);
         resetPhotoUpload();
      }
'''
# We will just replace the payload declaration with payload + upload
import re
c = re.sub(r'const payload = {[^}]*createdAt: new Date\(\)\.toISOString\(\)\s*};', submit_form_patch, c)

# 4. Patch submitJudge
judge_patch = '''
    async function submitJudge() {
      const approver = sessionStorage.getItem('QC_LOGGED_IN_USER');
      const pin = document.getElementById('modalPin').value;
      
      const btn = document.getElementById('modalBtn'); 
      btn.disabled = true; 
      btn.innerText = "驗證權限中...";
      
      const id = document.getElementById('currentId').value;
      const result = document.getElementById('modalResult').value;
      const note = document.getElementById('modalNote').value;
      const targetItem = allData.find(d => d.id === id);

      if(currentPhotoBase64) {
         showToast("📷 正在上傳佐證照片...");
         await processPhotoUpload(id);
         resetPhotoUpload();
      }
'''
c = re.sub(r'function submitJudge\(\) \{[\s\S]*?const targetItem = allData\.find\(d => d\.id === id\);', judge_patch, c)


with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'w', encoding='utf-8') as f:
    f.write(c)

