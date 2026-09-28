import os
for folder in ['1_Web_網頁版', '2_PWA_App版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    text = text.replace(
        "pBody.innerHTML = pData.length ? pData.map(s =>",
        "try { pBody.innerHTML = pData.length ? pData.map(s =>"
    )
    text = text.replace(
        "</tr>`).join('') : `<tr><td colspan=\"4\" style=\"text-align:center; color:#94a3b8; padding:30px;\">目前無待檢驗樣品</td></tr>`;",
        "</tr>`).join('') : `<tr><td colspan=\"4\" style=\"text-align:center; color:#94a3b8; padding:30px;\">目前無待檢驗樣品</td></tr>`; } catch(e) { pBody.innerHTML = `<tr><td colspan=\"4\" style=\"color:red;\">${e.toString()}</td></tr>`; }"
    )
    text = text.replace(
        "cBody.innerHTML = cData.length ? cData.slice(0, 30).map(s =>",
        "try { cBody.innerHTML = cData.length ? cData.slice(0, 30).map(s =>"
    )
    text = text.replace(
        "</tr>`).join('') : `<tr><td colspan=\"4\" style=\"text-align:center; color:#94a3b8; padding:30px;\">尚無檢驗完成紀錄</td></tr>`;",
        "</tr>`).join('') : `<tr><td colspan=\"4\" style=\"text-align:center; color:#94a3b8; padding:30px;\">尚無檢驗完成紀錄</td></tr>`; } catch(e) { cBody.innerHTML = `<tr><td colspan=\"4\" style=\"color:red;\">${e.toString()}</td></tr>`; }"
    )
    text = text.replace(
        "</tr>`).join('') : `<tr><td colspan=\"9\" style=\"text-align:center; color:#94a3b8; padding:30px;\">目前無待檢驗樣品</td></tr>`;",
        "</tr>`).join('') : `<tr><td colspan=\"9\" style=\"text-align:center; color:#94a3b8; padding:30px;\">目前無待檢驗樣品</td></tr>`; } catch(e) { pBody.innerHTML = `<tr><td colspan=\"9\" style=\"color:red;\">${e.toString()}</td></tr>`; }"
    )
    text = text.replace(
        "</tr>`).join('') : `<tr><td colspan=\"9\" style=\"text-align:center; color:#94a3b8; padding:30px;\">尚無檢驗完成紀錄</td></tr>`;",
        "</tr>`).join('') : `<tr><td colspan=\"9\" style=\"text-align:center; color:#94a3b8; padding:30px;\">尚無檢驗完成紀錄</td></tr>`; } catch(e) { cBody.innerHTML = `<tr><td colspan=\"9\" style=\"color:red;\">${e.toString()}</td></tr>`; }"
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
print("Injected try-catch to others")
