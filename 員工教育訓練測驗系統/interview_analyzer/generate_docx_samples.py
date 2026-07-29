import json, os
from docx_generator import generate_interview_report_docx

with open("data/db.json", "r", encoding="utf-8") as f:
    records = json.load(f)

for r in records:
    if r.get("status") == "analyzed":
        out_filename = f"data/面試特質與DISC說明評估報告_{r['id'][:8]}.docx"
        try:
            generate_interview_report_docx(r, out_filename)
            print("Generated sample docx:", out_filename)
        except PermissionError:
            out_filename = f"data/面試特質與DISC說明評估報告_{r['id'][:8]}_v2.docx"
            generate_interview_report_docx(r, out_filename)
            print("Generated sample docx:", out_filename)
