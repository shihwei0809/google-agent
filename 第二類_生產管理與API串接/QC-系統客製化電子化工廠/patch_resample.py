import os
for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    new_func = """  function openReturnResample(id) {
    document.getElementById('returnResampleId').value = id;
    document.getElementById('returnResampleNote').value = '';
    const loggedInUser = sessionStorage.getItem('QC_LOGGED_IN_USER');
    if (loggedInUser) {
      const storedPin = localStorage.getItem('HS_QC_ADMIN_PIN') || '8888';
      document.getElementById('returnResamplePin').value = storedPin;
    } else {
      document.getElementById('returnResamplePin').value = '';
    }
    document.getElementById('returnResampleModal').style.display = 'flex';
  }"""

    text = text.replace(
        "  function openReturnResample(id) {\n    document.getElementById('returnResampleId').value = id;\n    document.getElementById('returnResampleNote').value = '';\n    document.getElementById('returnResamplePin').value = '';\n    document.getElementById('returnResampleModal').style.display = 'flex';\n  }",
        new_func
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
print("Patched openReturnResample")
