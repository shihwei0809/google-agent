path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

old_insert = """      await env.DB.prepare("INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, remark, status, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now', '+8 hours'))")
        .bind(id||null, barcode||null, productName||null, tankNo||null, customer||null, quantity||null, flowType||null, dept||null, requester||null, grade||null, remark||null).run();"""

new_insert = """      const s_status = data.status || 'pending';
      const s_result = data.qcResult || null;
      const s_note = data.qcNote || null;
      const s_approver = data.qcApprover || null;
      const s_compAt = (s_status === 'completed') ? (data.completedAt || new Date().toISOString().replace('T', ' ').substring(0, 19)) : null;

      await env.DB.prepare("INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, remark, status, qcResult, qcNote, qcApprover, completedAt, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', '+8 hours'))")
        .bind(id||null, barcode||null, productName||null, tankNo||null, customer||null, quantity||null, flowType||null, dept||null, requester||null, grade||null, remark||null, s_status, s_result, s_note, s_approver, s_compAt).run();"""

text = text.replace(old_insert, new_insert)
with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
