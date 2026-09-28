import os
import re

for folder in ['1_Web_網頁版', '2_PWA_App版', '3_Cloudflare_D1版']:
    path = rf'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\{folder}\index.html'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Update handleResultChange logic to include '需特採'
    old_handle = re.search(r'function handleResultChange\(\) \{.*?(?=\n  function submitJudge)', text, re.DOTALL)
    if old_handle:
        new_handle = """function handleResultChange() {
    const sel = document.getElementById('modalResult');
    const note = document.getElementById('modalNote');
    if (sel.value === 'FAIL') {
      sel.style.color = '#dc2626'; // Red
      if (note.value === '合格放行' || note.value === '特採放行') note.value = '';
    } else if (sel.value === '需特採') {
      sel.style.color = '#d97706'; // Orange
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
        
    # 2. Update openJudge dropdown dynamically
    old_open = re.search(r'function openJudge\(id\) \{.*?(?=document\.getElementById\(\'currentId\'\)\.value)', text, re.DOTALL)
    if old_open:
        new_open = """function openJudge(id) {
    if (!sessionStorage.getItem('QC_LOGGED_IN_USER')) {
      pendingActionId = id;
      pendingActionType = 'judge';
      openAdminUnlockModal();
      return;
    }
    const sample = allData.find(s => s.id === id);
    const sel = document.getElementById('modalResult');
    if (sample && sample.qcResult === '需特採') {
      sel.innerHTML = `
        <option value="特採">PASS (特採放行)</option>
        <option value="FAIL">FAIL (駁回特採並自動重送)</option>
      `;
      sel.value = '特採';
    } else {
      sel.innerHTML = `
        <option value="PASS">PASS (合格放行)</option>
        <option value="FAIL">FAIL (不合格自動重送)</option>
        <option value="需特採">不符合內控 (需特採)</option>
      `;
      sel.value = 'PASS';
    }
    """
        text = text.replace(old_open.group(0), new_open)

    # 3. Update Kanban Badging (add '需特採' color)
    text = text.replace(
        """<b style="color:${s.qcResult==='PASS'?'#059669':(s.qcResult==='特採'?'#7c3aed':'#dc2626')}; background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':'#fee2e2')};""",
        """<b style="color:${s.qcResult==='PASS'?'#059669':(s.qcResult==='特採'?'#7c3aed':(s.qcResult==='需特採'?'#d97706':'#dc2626'))}; background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':(s.qcResult==='需特採'?'#fef3c7':'#fee2e2'))};"""
    )
    
    text = text.replace(
        """<span style="background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':'#fee2e2')}; color:${s.qcResult==='PASS'?'#065f46':(s.qcResult==='特採'?'#7c3aed':'#b91c1c')};""",
        """<span style="background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':(s.qcResult==='需特採'?'#fef3c7':'#fee2e2'))}; color:${s.qcResult==='PASS'?'#065f46':(s.qcResult==='特採'?'#7c3aed':(s.qcResult==='需特採'?'#d97706':'#b91c1c'))};"""
    )

    text = text.replace(
        """|| s.qcResult === 'FAIL' || s.qcResult === '特採')) statusBadge = `<span style="background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':'#fee2e2')}; color:${s.qcResult==='PASS'?'#065f46':(s.qcResult==='特採'?'#7c3aed':'#b91c1c')}; padding:2px 6px; border-radius:4px; font-size:0.8rem;">${s.qcResult==='PASS'?'合格(PASS)':(s.qcResult==='特採'?'特採(PASS)':'退回(FAIL)')}</span>`;""",
        """|| s.qcResult === 'FAIL' || s.qcResult === '特採' || s.qcResult === '需特採')) statusBadge = `<span style="background:${s.qcResult==='PASS'?'#d1fae5':(s.qcResult==='特採'?'#ede9fe':(s.qcResult==='需特採'?'#fef3c7':'#fee2e2'))}; color:${s.qcResult==='PASS'?'#065f46':(s.qcResult==='特採'?'#7c3aed':(s.qcResult==='需特採'?'#d97706':'#b91c1c'))}; padding:2px 6px; border-radius:4px; font-size:0.8rem;">${s.qcResult==='PASS'?'合格(PASS)':(s.qcResult==='特採'?'特採(PASS)':(s.qcResult==='需特採'?'需特採':'退回(FAIL)'))}</span>`;"""
    )
    
    # 4. Update Kanban Actions logic
    # In adaptive mode
    text = text.replace(
        """${s.qcResult === 'FAIL' ? `<button onclick="openReturnResample('${s.id}')" style="font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%;">↩️ 退回重新送樣</button><button onclick="openConcession('${s.id}')" style="font-size:0.7rem; background:#8b5cf6; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%; margin-top:3px;">🚨 變更為特採放行</button>` : ''}""",
        """${s.qcResult === '需特採' ? `<button onclick="openJudge('${s.id}')" style="font-size:0.7rem; background:#8b5cf6; color:white; border:none; border-radius:6px; padding:3px 8px; cursor:pointer; width:100%; margin-top:3px; animation: pulse 2s infinite;">🚨 主管審核特採</button>` : ''}
          ${s.qcResult === 'FAIL' ? `<div style="font-size:0.7rem; color:#b91c1c; font-weight:bold; background:#fee2e2; padding:3px; border-radius:4px; text-align:center;">已自動產生重送單</div>` : ''}"""
    )
    # In full mode
    text = text.replace(
        """${s.qcResult === 'FAIL' ? `<br><button onclick="openReturnResample('${s.id}')" style="font-size:0.7rem; background:#f97316; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;">↩️ 退回重新送樣</button><br><button onclick="openConcession('${s.id}')" style="font-size:0.7rem; background:#8b5cf6; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;">🚨 變更為特採</button>` : ''}""",
        """${s.qcResult === '需特採' ? `<br><button onclick="openJudge('${s.id}')" style="font-size:0.7rem; background:#8b5cf6; color:white; border:none; border-radius:6px; padding:2px 8px; cursor:pointer; margin-top:3px;">🚨 審核特採</button>` : ''}
            ${s.qcResult === 'FAIL' ? `<br><div style="font-size:0.7rem; color:#b91c1c; font-weight:bold;">已自動重送</div>` : ''}"""
    )

    # We also have keyframes for pulse animation if missing
    if '@keyframes pulse {' not in text:
        text = text.replace('</style>', """
    @keyframes pulse {
      0% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.7); }
      70% { box-shadow: 0 0 0 6px rgba(139, 92, 246, 0); }
      100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0); }
    }
  </style>""")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)

print("Frontend HTML patched")
