for folder in ["1_Web_網頁版", "2_PWA_App版", "3_Cloudflare_D1版"]:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    text = text.replace('fetch(`${GAS_API_URL}?action=getOrders&date=${dateStr}`)', 'fetch(`${GAS_API_URL}?action=getOrders&date=${dateStr}&_t=${Date.now()}`, { cache: "no-store" })')

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Patched {folder}")
