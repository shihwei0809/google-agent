with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Add file inputs
html_addition = '''
  <input type="file" id="photoInput" accept="image/*" style="display:none;" onchange="handlePhotoSelect(event)">
'''
c = c.replace('</body>', html_addition + '</body>')

# Add photo button to qcForm
qc_form_btn = '''
          <div style="grid-column: 1 / -1; margin-top: 10px;">
            <button type="button" onclick="triggerPhotoUpload('submit')" style="background:#f1f5f9; color:#475569; border:1px dashed #cbd5e1; padding:8px 12px; border-radius:6px; cursor:pointer; width:100%; display:flex; align-items:center; justify-content:center; gap:8px;">
              <span style="font-size:1.2rem;">📷</span> <span id="submitPhotoText">附加樣品照片 (選填)</span>
            </button>
          </div>
'''
c = re.sub(r'(<button type="submit"[^>]*id="submitBtn"[^>]*>.*?</button>)', qc_form_btn + r'\1', c, flags=re.DOTALL)

# Add photo button to judgeModal
judge_btn = '''
      <div style="margin-bottom:15px;">
        <button type="button" onclick="triggerPhotoUpload('judge')" style="background:#f1f5f9; color:#475569; border:1px dashed #cbd5e1; padding:8px 12px; border-radius:6px; cursor:pointer; width:100%; display:flex; align-items:center; justify-content:center; gap:8px;">
          <span style="font-size:1.2rem;">📷</span> <span id="judgePhotoText">附加佐證照片 (選填)</span>
        </button>
      </div>
'''
c = c.replace('<div style="background:#fef2f2; padding:12px; border-radius:6px; margin-bottom:20px; border-left:4px solid var(--red);">', judge_btn + '<div style="background:#fef2f2; padding:12px; border-radius:6px; margin-bottom:20px; border-left:4px solid var(--red);">')

# Add Javascript logic
js_addition = '''
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
c = c.replace('</script>', js_addition + '</script>')

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'w', encoding='utf-8') as f:
    f.write(c)
