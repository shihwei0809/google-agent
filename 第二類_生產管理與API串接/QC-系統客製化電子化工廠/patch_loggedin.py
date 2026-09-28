import os
for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Find the start of function render() {
    # and insert const loggedInUser = sessionStorage.getItem('QC_LOGGED_IN_USER');
    if "const loggedInUser = sessionStorage.getItem('QC_LOGGED_IN_USER');" not in text.split('function render() {')[1].split('const pHead')[0]:
        text = text.replace(
            "function render() {\n",
            "function render() {\n    const loggedInUser = sessionStorage.getItem('QC_LOGGED_IN_USER');\n"
        )
        
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
print("Patched loggedInUser")
