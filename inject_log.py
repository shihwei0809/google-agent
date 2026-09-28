import os
for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Find the line with pBody.innerHTML = pData.length ? ...
    # And insert a console.log right after it
    text = text.replace(
        "</tr>`).join('') : `<tr><td colspan=\"4\" style=\"text-align:center; color:#94a3b8; padding:30px;\">目前無待檢驗樣品</td></tr>`;",
        "</tr>`).join('') : `<tr><td colspan=\"4\" style=\"text-align:center; color:#94a3b8; padding:30px;\">目前無待檢驗樣品</td></tr>`;\n      console.log('pData:', pData);\n      console.log('pBody.innerHTML length:', pBody.innerHTML.length);"
    )
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
print("Injected console.log")
