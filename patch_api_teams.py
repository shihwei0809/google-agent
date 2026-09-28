path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the facts generation
old_title = """const title = isPass
        ? `✅【品管檢驗通過通知】${sample.product}` 
        : `❌【品管檢驗退回通知】${sample.product}`;"""
new_title = """let resultTitle = result;
      if (result === 'FAIL') resultTitle = '⛔ FAIL (已自動產生下一次重送排程)';
      else if (result === '需特採') resultTitle = '⚠️ 不符合內控 (等待主管審核特採)';
      else if (result === '特採') resultTitle = '🚨 經主管特採放行';
      
      const title = isPass
        ? `✅【檢驗完成】${sample.productName}` 
        : `❌【檢驗未通過】${sample.productName}`;"""
text = text.replace(old_title, new_title)

old_facts = """const facts = [
        { name: '檢驗結果', value: `**${result}**` },
        { name: '放行核准人', value: actualApprover },
        { name: '單號', value: sample.t100_no },
        { name: '槽號/車牌', value: `${sample.tank} / ${sample.container}` },
        { name: '檢驗備註', value: note || '無' }
      ];"""
new_facts = """const facts = [
        { name: '檢驗結果', value: `**${resultTitle}**` },
        { name: '審核人員', value: actualApprover },
        { name: '單號', value: sample.barcode || '-' },
        { name: '槽號/車牌', value: `${sample.tankNo || '-'} / ${sample.customer || '-'}` },
        { name: '檢驗備註', value: finalNote || '無' }
      ];"""
text = text.replace(old_facts, new_facts)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Backend Teams facts patched")
