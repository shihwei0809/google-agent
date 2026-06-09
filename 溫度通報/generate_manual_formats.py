import os
import re
import docx
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def md_to_docx(md_path, docx_path):
    doc = docx.Document()
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    in_code_block = False
    code_text = []
    
    for line in lines:
        stripped = line.strip()
        
        # Code blocks
        if stripped.startswith('```'):
            if in_code_block:
                # End of code block
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = docx.shared.Inches(0.3)
                p_run = p.add_run(''.join(code_text))
                p_run.font.name = 'Consolas'
                p_run.font.size = docx.shared.Pt(9)
                code_text = []
                in_code_block = False
            else:
                in_code_block = True
            continue
            
        if in_code_block:
            code_text.append(line)
            continue
            
        # Headers
        if stripped.startswith('# '):
            doc.add_heading(stripped[2:], level=1)
        elif stripped.startswith('## '):
            doc.add_heading(stripped[3:], level=2)
        elif stripped.startswith('### '):
            doc.add_heading(stripped[4:], level=3)
        # Bullet points
        elif stripped.startswith('* ') or stripped.startswith('- '):
            p = doc.add_paragraph(style='List Bullet')
            p.add_run(stripped[2:])
        # Numbered list
        elif re.match(r'^\d+\.\s', stripped):
            match = re.match(r'^(\d+)\.\s(.*)', stripped)
            p = doc.add_paragraph(style='List Number')
            p.add_run(match.group(2))
        # Empty line
        elif not stripped:
            continue
        # Normal text
        else:
            doc.add_paragraph(stripped)
            
    doc.save(docx_path)
    print(f"Docx generated successfully at {docx_path}")

def md_to_pdf(md_path, pdf_path):
    font_path = "C:\\Windows\\Fonts\\msjh.ttc"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('MSJH', font_path))
        font_name = 'MSJH'
    else:
        font_name = 'Helvetica'
        
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    
    # Custom styles to support Chinese
    title_style = ParagraphStyle(
        'ManualTitle',
        parent=styles['Title'],
        fontName=font_name,
        fontSize=20,
        leading=24,
        spaceAfter=15,
        alignment=1 # Center
    )
    h1_style = ParagraphStyle(
        'ManualH1',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=15,
        leading=18,
        spaceBefore=15,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'ManualH2',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'ManualBody',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=10,
        leading=14,
        spaceAfter=8
    )
    code_style = ParagraphStyle(
        'ManualCode',
        parent=styles['Normal'],
        fontName='Courier' if font_name == 'Helvetica' else font_name,
        fontSize=8.5,
        leading=11,
        leftIndent=15,
        spaceAfter=4,
        backColor="#f4f4f4"
    )
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    story = []
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        
        # Code blocks
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
            
        if in_code_block:
            # Code block lines
            escaped = line.replace(' ', '&nbsp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
            story.append(Paragraph(escaped, code_style))
            continue
            
        # Headers
        if stripped.startswith('# '):
            story.append(Paragraph(stripped[2:], title_style))
            story.append(Spacer(1, 10))
        elif stripped.startswith('## '):
            story.append(Paragraph(stripped[3:], h1_style))
        elif stripped.startswith('### '):
            story.append(Paragraph(stripped[4:], h2_style))
        # Bullet points
        elif stripped.startswith('* ') or stripped.startswith('- '):
            bullet_text = f"• {stripped[2:]}"
            story.append(Paragraph(bullet_text, body_style))
        # Numbered list
        elif re.match(r'^\d+\.\s', stripped):
            story.append(Paragraph(stripped, body_style))
        # Empty line
        elif not stripped:
            story.append(Spacer(1, 6))
        # Normal text
        else:
            story.append(Paragraph(stripped, body_style))
            
    doc.build(story)
    print(f"PDF generated successfully at {pdf_path}")

if __name__ == "__main__":
    md = "溫度通報系統操作說明.md"
    docx_out = "溫度通報系統操作說明.docx"
    pdf_out = "溫度通報系統操作說明.pdf"
    
    md_to_docx(md, docx_out)
    md_to_pdf(md, pdf_out)
