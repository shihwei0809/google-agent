import re

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Modify submitForm to process photo
submit_patch = '''
      if (IS_GAS) {
        if(currentPhotoBase64) {
           showToast("📷 正在上傳照片...");
           await processPhotoUpload(payload.id);
           resetPhotoUpload();
        }
        google.script.run.withSuccessHandler(() => { 
'''
c = c.replace('if (IS_GAS) {\\n        google.script.run.withSuccessHandler(() => {', submit_patch)

submit_patch_gas = '''
      } else if(GAS_API_URL) {
        if(currentPhotoBase64) {
           showToast("📷 正在上傳照片...");
           await processPhotoUpload(payload.id);
           resetPhotoUpload();
        }
        fetch(GAS_API_URL, {
'''
c = c.replace('} else if(GAS_API_URL) {\\n        fetch(GAS_API_URL, {', submit_patch_gas)

# Since we use await in submitForm, submitForm must be async
c = c.replace('function submitForm() {', 'async function submitForm() {')

# Modify submitJudge
judge_patch = '''
    async function submitJudge() {
      const id = document.getElementById('currentId').value;
      const result = document.getElementById('modalResult').value;
      const note = document.getElementById('modalNote').value.trim();
      const pin = document.getElementById('modalPin').value;
      const btn = document.getElementById('modalBtn');
      
      btn.disabled = true; btn.innerText = "處理中...";

      if(currentPhotoBase64) {
         showToast("📷 正在上傳佐證照片...");
         await processPhotoUpload(id);
         resetPhotoUpload();
      }
'''
c = re.sub(r'function submitJudge\(\) \{[\s\S]*?btn\.innerText = "處理中\.\.\.";', judge_patch, c)

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'w', encoding='utf-8') as f:
    f.write(c)

