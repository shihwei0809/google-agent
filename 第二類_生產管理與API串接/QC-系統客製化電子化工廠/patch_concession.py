import os
import re

for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Add Option to Dropdown
    text = text.replace(
        '<option value="PASS">PASS (合格放行)</option>',
        '<option value="PASS">PASS (合格放行)</option>\n      <option value="特採">PASS (特採放行)</option>'
    )

    # 2. Update handleResultChange
    old_handle = re.search(r'function handleResultChange\(\) \{.*?(?=\n  function submitJudge)', text, re.DOTALL)
    if old_handle:
        new_handle = """function handleResultChange() {
    const sel = document.getElementById('modalResult');
    const note = document.getElementById('modalNote');
    if (sel.value === 'FAIL') {
      sel.style.color = '#dc2626'; // Red
      if (note.value === '合格放行' || note.value === '特採放行') note.value = '';
    } else if (sel.value === '特採') {
      sel.style.color = '#7c3aed'; // Purple
      if (note.value === '合格放行' || note.value === '') note.value = '特採放行';
    } else {
      sel.style.color = '#059669'; // Green
      if (note.value === '' || note.value === '特採放行') note.value = '合格放行';
    }
  }"""
        text = text.replace(old_handle.group(0), new_handle)

    # 3. Add openConcession function & update pending action logic
    concession_func = """
  function openConcession(id) {
    if (!sessionStorage.getItem('QC_LOGGED_IN_USER')) {
      pendingActionId = id;
      pendingActionType = 'concession';
      openAdminUnlockModal();
      return;
    }
    openJudge(id);
    setTimeout(() => {
      const sel = document.getElementById('modalResult');
      if(sel) { sel.value = '特採'; handleResultChange(); }
    }, 50);
  }
"""
    if 'function openConcession(' not in text:
        text = text.replace('function openReturnResample(id) {', concession_func + '\n  function openReturnResample(id) {')

    text = text.replace(
        "if (pendingActionType === 'resample') openReturnResample(pendingActionId);",
        "if (pendingActionType === 'resample') openReturnResample(pendingActionId);\n             if (pendingActionType === 'concession') openConcession(pendingActionId);"
    )

    # 4. Update Kanban badging (cBody)
    text = text.replace(
        """<b style="color:${s.qcResult==='PASS'?'#059669':'#dc2626'}; background:${s.qcResult==='PASS'?'#d1fae5':'#fee2e2'}; padding:1px 5px; border-radius:4px; font-size:0.74rem;">${s.qcResult}</b>""",
        """<b style="color:${s.qcResult==='PASS'?'#059669':(s.qcResult==='特採'?'#7c3aed':'#dc2626')}; background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':'#fee2e2')}; padding:1px 5px; border-radius:4px; font-size:0.74rem;">${s.qcResult}</b>"""
    )
    
    # Update Full mode badging
    text = text.replace(
        """<span style="background:${s.qcResult==='PASS'?'#d1fae5':'#fee2e2'}; color:${s.qcResult==='PASS'?'#065f46':'#b91c1c'}; padding:2px 6px; border-radius:4px; font-weight:bold;">${s.qcResult}</span>""",
        """<span style="background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':'#fee2e2')}; color:${s.qcResult==='PASS'?'#065f46':(s.qcResult==='特採'?'#7c3aed':'#b91c1c')}; padding:2px 6px; border-radius:4px; font-weight:bold;">${s.qcResult}</span>"""
    )
    
    # Update Global modal badging
    text = text.replace(
        """(s.qcResult === 'PASS' || s.qcResult === 'FAIL')) statusBadge = `<span style="background:${s.qcResult==='PASS'?'#d1fae5':'#fee2e2'}; color:${s.qcResult==='PASS'?'#065f46':'#b91c1c'}; padding:2px 6px; border-radius:4px; font-size:0.8rem;">${s.qcResult==='PASS'?'合格(PASS)':'退回(FAIL)'}</span>`;""",
        """(s.qcResult === 'PASS' || s.qcResult === 'FAIL' || s.qcResult === '特採')) statusBadge = `<span style="background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':'#fee2e2')}; color:${s.qcResult==='PASS'?'#065f46':(s.qcResult==='特採'?'#7c3aed':'#b91c1c')}; padding:2px 6px; border-radius:4px; font-size:0.8rem;">${s.qcResult==='PASS'?'合格(PASS)':(s.qcResult==='特採'?'特採(PASS)':'退回(FAIL)')}</span>`;"""
    )

    # 5. Add "🚨 特採放行" button for failed items
    # In adaptive mode
    text = text.replace(
        """${s.qcResult === 'FAIL' ? `<button onclick="openReturnResample('${s.id}')" style="font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%;">↩️ 退回重新送樣</button>` : ''}""",
        """${s.qcResult === 'FAIL' ? `<button onclick="openReturnResample('${s.id}')" style="font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%;">↩️ 退回重新送樣</button><button onclick="openConcession('${s.id}')" style="font-size:0.7rem; background:#8b5cf6; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%; margin-top:3px;">🚨 變更為特採放行</button>` : ''}"""
    )
    # In full mode
    text = text.replace(
        """${s.qcResult === 'FAIL' ? `<br><button onclick="openReturnResample('${s.id}')" style="font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;">↩️ 退回重新送樣</button>` : ''}""",
        """${s.qcResult === 'FAIL' ? `<br><button onclick="openReturnResample('${s.id}')" style="font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;">↩️ 退回重新送樣</button><br><button onclick="openConcession('${s.id}')" style="font-size:0.7rem; background:#8b5cf6; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;">🚨 變更為特採</button>` : ''}"""
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

print("Patched concession")
