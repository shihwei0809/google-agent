for folder in ["1_Web_網頁版", "2_PWA_App版", "3_Cloudflare_D1版"]:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Modify openJudge to auto-fill or hide PIN
    injection = """
  function openJudge(id) { 
    document.getElementById('currentId').value = id; 
    document.getElementById('modalNote').value = '合格放行'; 
    
    const loggedInUser = sessionStorage.getItem('QC_LOGGED_IN_USER');
    const approverText = document.getElementById('judgeApproverText');
    if (approverText) {
      approverText.innerText = '👤 放行核准人：' + (loggedInUser || '未登入');
    }
    
    const pinBox = document.getElementById('modalPin').parentElement;
    if (loggedInUser) {
      // 已經登入，隱藏密碼輸入框，並自動帶入密碼
      pinBox.style.display = 'none';
      const storedPin = localStorage.getItem('HS_QC_ADMIN_PIN') || '8888';
      document.getElementById('modalPin').value = storedPin;
    } else {
      // 未登入，顯示密碼輸入框
      pinBox.style.display = 'block';
      document.getElementById('modalPin').value = '';
    }

    document.getElementById('judgeModal').style.display = 'flex'; 
    if (!loggedInUser) document.getElementById('modalPin').focus();
  }
"""

    import re
    # We replace the entire openJudge function
    text = re.sub(r'function openJudge\(id\) \{.*?\n  \}', injection.strip(), text, flags=re.DOTALL)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Patched openJudge in {folder}")
