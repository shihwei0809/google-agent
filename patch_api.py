path = r'C:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\functions\api\index.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the status assignment in completeSample
old_status_logic = """let status = "completed";
      if (result === "FAIL" || result === "退件" || result === "重取樣") status = "failed";"""
new_status_logic = """let status = "completed";
      if (result === "FAIL" || result === "需特採") status = "failed";
      
      let finalNote = note;
      if (result === '特採' && sample.qcResult === '需特採') {
        finalNote = `[初驗:${sample.qcApprover}] ${sample.qcNote || ''}\\n[特採:${approver}] ${note}`;
      }"""
text = text.replace(old_status_logic, new_status_logic)

# Replace the UPDATE query to use finalNote
text = text.replace(
    """.bind(status, result, note, approver || 'QC', completedAt, id).run();""",
    """.bind(status, result, finalNote, approver || 'QC', completedAt, id).run();"""
)

# Add auto-resample logic after UPDATE
auto_resample_logic = """
      // 如果是不合格(FAIL)，自動產生下一輪重送排程
      if (result === 'FAIL') {
        const newId = crypto.randomUUID();
        const parentId = sample.parentId || sample.id;
        const round = parseInt(sample.round || 1) + 1;
        await env.DB.prepare(`
          INSERT INTO QC_Samples (id, barcode, productName, tankNo, customer, quantity, flowType, dept, requester, grade, parentId, round, status, isAlerted)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 0)
        `).bind(newId, sample.barcode, sample.productName, sample.tankNo, sample.customer, sample.quantity, sample.flowType, sample.dept, sample.requester, sample.grade, parentId, round).run();
      }
"""
text = text.replace(
    """.bind(status, result, finalNote, approver || 'QC', completedAt, id).run();""",
    """.bind(status, result, finalNote, approver || 'QC', completedAt, id).run();\n""" + auto_resample_logic
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Backend patched")
