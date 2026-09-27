import re
path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_logic = """    // 2. 槽號 + 品名 + 客戶/車號/櫃號比對 (針對無單號或預先充填送樣)
    const matchDetails = allData.find(s => {
      const sameTank = order.tankNo && s.tankNo && (String(s.tankNo).trim().toLowerCase() === String(order.tankNo).trim().toLowerCase());
      const sameProd = order.productName && s.productName && (String(s.productName).trim().toLowerCase() === String(order.productName).trim().toLowerCase());
      const sameCont = order.container && s.customer && (
        String(s.customer).trim().toLowerCase().includes(String(order.container).trim().toLowerCase()) ||
        String(order.container).trim().toLowerCase().includes(String(s.customer).trim().toLowerCase())
      );
      return (sameTank && sameProd) || (sameCont && sameProd);
    });"""

new_logic = """    // 2. 槽號 + 品名 + 客戶/車號/櫃號比對 (針對無單號或預先充填送樣)
    const matchDetails = allData.find(s => {
      const sameProd = order.productName && s.productName && (String(s.productName).trim().toLowerCase() === String(order.productName).trim().toLowerCase());
      if (!sameProd) return false;

      let tankMatch = false;
      let contMatch = false;
      let hasTankData = order.tankNo && s.tankNo;
      let hasContData = order.container && s.customer;

      if (hasTankData) {
        tankMatch = String(s.tankNo).trim().toLowerCase() === String(order.tankNo).trim().toLowerCase();
      }
      if (hasContData) {
        contMatch = String(s.customer).trim().toLowerCase().includes(String(order.container).trim().toLowerCase()) ||
                    String(order.container).trim().toLowerCase().includes(String(s.customer).trim().toLowerCase());
      }

      if (hasTankData && hasContData) return tankMatch && contMatch;
      if (hasTankData) return tankMatch;
      if (hasContData) return contMatch;
      return false;
    });"""

text = text.replace(old_logic, new_logic)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
