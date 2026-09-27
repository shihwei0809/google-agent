path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

start = text.find('// 自動尋找同車次的進出貨單')
end = text.find('document.getElementById(\'barcode\')', start)
old_block = text[start:end]

new_block = """// 自動尋找同車次的進出貨單 (同車牌/同動向)
    let combinedDocs = item.doc_no || '';
    if (item.container && item.container.trim() !== '') {
        const sameTruckItems = t100Orders.filter(o => o !== item && o.container === item.container && o.flowType === item.flowType);
        if (sameTruckItems.length > 0) {
            const extraDocs = sameTruckItems.map(o => o.doc_no).filter(Boolean);
            if (extraDocs.length > 0) {
                const combined = [item.doc_no, ...extraDocs].join(', ');
                if (confirm(`發現此車次 (${item.container}) 共有 ${extraDocs.length + 1} 筆排程單號：\\n${combined}\\n\\n是否要自動合併成同一張檢驗單？`)) {
                    combinedDocs = combined;
                }
            }
        }
    }

    """

text = text.replace(old_block, new_block)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
