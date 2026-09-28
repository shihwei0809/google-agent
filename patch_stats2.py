for folder in ["1_Web_網頁版", "2_PWA_App版"]:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    old_stats = """    const statsBadge = document.getElementById('t100StatsBadge');
    if (statsBadge) {
      if (t100FilterMode === 'today') {
        statsBadge.innerHTML = `今日排程: <b>${filteredOrders.length}</b> 車 (✅已送: ${submittedInView} | ⏳待送: ${pendingInView}) · 總排程: ${totalCount}`;
      } else if (t100FilterMode === 'pending') {
        statsBadge.innerHTML = `📦 待送樣放櫃: <b>${filteredOrders.length}</b> 車未送樣 (已送 ${submittedInTotal} / 總排程 ${totalCount})`;
      } else {
        statsBadge.innerHTML = `${filterDescription}: <b>${filteredOrders.length}</b> 車 (✅已送: ${submittedInView} | ⏳待送: ${pendingInView})`;
      }
    }"""
    new_stats = """    const pendingInTotal = totalCount - submittedInTotal;
    const statsBadge = document.getElementById('t100StatsBadge');
    if (statsBadge) {
      if (t100FilterMode === 'today') {
        statsBadge.innerHTML = `今日排程: <b>${filteredOrders.length}</b> 車 (✅已送: ${submittedInView} | ⏳待送: ${pendingInView}) · 系統尚有 ${pendingInTotal} 車未送樣`;
      } else if (t100FilterMode === 'pending') {
        statsBadge.innerHTML = `📦 待送樣放櫃: <b>${filteredOrders.length}</b> 車未送樣 (已完成 ${submittedInTotal} 車)`;
      } else {
        statsBadge.innerHTML = `${filterDescription}: <b>${filteredOrders.length}</b> 車 (✅已送: ${submittedInView} | ⏳待送: ${pendingInView})`;
      }
    }"""
    text = text.replace(old_stats, new_stats)

    old_empty = """    if (filteredOrders.length === 0) {
      if (t100FilterMode === 'today') {
        const availableDates = [...new Set(t100Orders.map(o => o.date).filter(Boolean))].sort();
        const latestDate = availableDates.length ? availableDates[availableDates.length - 1] : '';
        const hintText = latestDate ? `排程日為 ${latestDate}，可點擊上方日期切換` : '可匯入最新排程或點擊「待送樣放櫃」';
        html += `<option value="">-- 📅 今日 (${todayStr}) 尚無排程 (共 ${totalCount} 筆放櫃/預約車次，${hintText}) --</option>`;
      } else if (t100FilterMode === 'pending') {
        html += `<option value="">-- 🎉 太棒了！所有放櫃與排程車次 (共 ${totalCount} 筆) 皆已完成送樣 --</option>`;
      } else {
        html += `<option value="">-- 📅 日期 [${selectedDate}] 無排程 (共 ${totalCount} 筆其他日期排程，可切換日期查詢) --</option>`;
      }
    }"""
    new_empty = """    if (filteredOrders.length === 0) {
      if (t100FilterMode === 'today') {
        const hintText = pendingInTotal > 0 ? `系統內還有 ${pendingInTotal} 筆待送樣車次，可點擊「待送樣放櫃」查詢` : '所有排程皆已完成送樣';
        html += `<option value="">-- 📅 今日 (${todayStr}) 尚無排程 (${hintText}) --</option>`;
      } else if (t100FilterMode === 'pending') {
        html += `<option value="">-- 🎉 太棒了！所有放櫃與排程車次皆已完成送樣 --</option>`;
      } else {
        const hintText = pendingInTotal > 0 ? `尚有 ${pendingInTotal} 筆待送樣，可點擊「待送樣放櫃」查詢` : '所有排程皆已完成送樣';
        html += `<option value="">-- 📅 日期 [${selectedDate}] 無排程 (${hintText}) --</option>`;
      }
    }"""
    text = text.replace(old_empty, new_empty)

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Patched {folder}")
