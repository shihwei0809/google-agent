for folder in ["1_Web_網頁版", "2_PWA_App版"]:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    old_logic = """    let combinedDocs = item.doc_no || '';
    if (item.container && item.container.trim() !== '') {
        const sameTruckItems = t100Orders.filter(o => o !== item && o.container === item.container && o.flowType === item.flowType);"""

    new_logic = """    let combinedDocs = item.doc_no || '';
    if (item.container && item.container.trim() !== '' && item.flowType === '進料') {
        const sameTruckItems = t100Orders.filter(o => o !== item && o.container === item.container && o.flowType === item.flowType);"""

    text = text.replace(old_logic, new_logic)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Patched {folder}")
