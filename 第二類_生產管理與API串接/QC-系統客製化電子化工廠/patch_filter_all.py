import os

old_filter = "filteredOrders = t100Orders.filter(o => !getOrderSubmissionInfo(o));"
new_filter = """filteredOrders = t100Orders.filter(o => {
        const sub = getOrderSubmissionInfo(o);
        if (!sub) return true;
        if (sub.status === 'failed') return true;
        if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) return true;
        return false;
      });"""

old_mark = """let mark = '⏳[待送樣] ';
          if (sub) {
            if (sub.status === 'completed') mark = '✅[已驗合格] ';
            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';
            else mark = '✅[已送樣待驗] ';
          }"""
new_mark = """let mark = '⏳[待送樣] ';
          if (sub) {
            if (sub.status === 'completed') mark = '✅[已驗合格] ';
            else if (sub.status === 'failed' && sub.qcResult === '需特採') mark = '⚠️[不符內控需特採] ';
            else if (sub.status === 'failed') mark = '⛔[被退件需重送] ';
            else if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) mark = '🔄[已自動重送待驗] ';
            else mark = '✅[已送樣待驗] ';
          }"""

for folder in ['1_Web_網頁版', '2_PWA_App版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    text = text.replace(old_filter, new_filter)
    text = text.replace(old_mark, new_mark)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

print("Updated 1 and 2")
