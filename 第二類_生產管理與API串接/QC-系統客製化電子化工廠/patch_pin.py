import os
import re

for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Add pendingAction variables at the top of the JS block or before openJudge
    if 'let pendingActionId = null;' not in text:
        text = text.replace(
            "function openJudge(id) {",
            "let pendingActionId = null;\n  let pendingActionType = null;\n\n  function openJudge(id) {"
        )

    # 2. Rewrite openJudge
    old_openJudge = re.search(r'function openJudge\(id\) \{.*?(?=function closeModal\(\))', text, re.DOTALL)
    if old_openJudge:
        new_openJudge = """function openJudge(id) {
    if (!sessionStorage.getItem('QC_LOGGED_IN_USER')) {
      pendingActionId = id;
      pendingActionType = 'judge';
      openAdminUnlockModal();
      return;
    }
    document.getElementById('currentId').value = id; 
    document.getElementById('modalNote').value = '合格放行'; 
    
    const approverText = document.getElementById('judgeApproverText');
    if (approverText) {
      approverText.innerText = '👤 放行核准人：' + sessionStorage.getItem('QC_LOGGED_IN_USER');
    }
    
    const pinBox = document.getElementById('modalPin');
    if(pinBox && pinBox.parentElement) {
      pinBox.parentElement.style.display = 'none';
      pinBox.value = '8888'; // fallback
    }

    document.getElementById('judgeModal').style.display = 'flex'; 
  }
  """
        text = text.replace(old_openJudge.group(0), new_openJudge)

    # 3. Rewrite openReturnResample
    old_resample = re.search(r'function openReturnResample\(id\) \{.*?(?=function closeReturnResampleModal\(\))', text, re.DOTALL)
    if old_resample:
        new_resample = """function openReturnResample(id) {
    if (!sessionStorage.getItem('QC_LOGGED_IN_USER')) {
      pendingActionId = id;
      pendingActionType = 'resample';
      openAdminUnlockModal();
      return;
    }
    document.getElementById('returnResampleId').value = id;
    document.getElementById('returnResampleNote').value = '';
    const pinBox = document.getElementById('returnResamplePin');
    if(pinBox && pinBox.parentElement) {
      pinBox.parentElement.style.display = 'none';
      pinBox.value = '8888'; // fallback
    }
    document.getElementById('returnResampleModal').style.display = 'flex';
  }
  """
        text = text.replace(old_resample.group(0), new_resample)

    # 4. Inject pendingAction logic into confirmAdminUnlock
    if 'if (typeof pendingActionId !==' not in text:
        text = text.replace(
            "unlockAdminFeatures(true);",
            "unlockAdminFeatures(true);\n          if (typeof pendingActionId !== 'undefined' && pendingActionId) {\n             if (pendingActionType === 'judge') openJudge(pendingActionId);\n             if (pendingActionType === 'resample') openReturnResample(pendingActionId);\n             pendingActionId = null;\n             pendingActionType = null;\n          }"
        )

    # 5. Remove pin empty validation in submitJudge and submitReturnResample
    text = text.replace('if(!pin) { alert("請輸入授權密碼！"); return; }', '')
    text = text.replace("if (!pin) { alert('請輸入品管授權 PIN 碼！'); return; }", '')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

# Also patch the backend to remove pin validation
api_path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(api_path, 'r', encoding='utf-8') as f:
    api_text = f.read()

# Remove the validPin check from completeSample
api_text = re.sub(r'const validPin = configMap\[\'QC_PIN\'\] \|\| \'8888\';\s+if \(pin !== validPin\) \{\s+return new Response\(JSON\.stringify\(\{ success: false, error: "⛔ 授權失敗：品管專屬密碼錯誤！" \}\), \{ headers: h \}\);\s+\}', '', api_text)

# Remove the validPin check from returnResample
api_text = re.sub(r'const validPin = configMap\[\'QC_PIN\'\] \|\| \'8888\';\s+if \(pin !== validPin\) \{\s+return new Response\(JSON\.stringify\(\{ success: false, error: "⛔ 授權失敗：品管專屬密碼錯誤！" \}\), \{ headers: h \}\);\s+\}', '', api_text)

with open(api_path, 'w', encoding='utf-8') as f:
    f.write(api_text)

print("Patched all logic")
