path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update filter logic
old_filter = "filteredOrders = t100Orders.filter(o => !getOrderSubmissionInfo(o));"
new_filter = """filteredOrders = t100Orders.filter(o => {
        const sub = getOrderSubmissionInfo(o);
        if (!sub) return true;
        if (sub.status === 'failed') return true;
        if (sub.status === 'pending' && (sub.round > 1 || sub.parentId)) return true;
        return false;
      });"""
text = text.replace(old_filter, new_filter)

# 2. Update mark logic
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
text = text.replace(old_mark, new_mark)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated Cloudflare version index.html")
