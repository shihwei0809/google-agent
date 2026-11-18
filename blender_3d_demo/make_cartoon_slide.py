import os
from PIL import Image, ImageDraw, ImageFont

def render_ultra_clean_infographic():
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), "#F8FAFC")
    draw = ImageDraw.Draw(img)

    font_path_bold = "C:/Windows/Fonts/msjhbd.ttc"
    font_path_reg = "C:/Windows/Fonts/msjh.ttc"

    font_title = ImageFont.truetype(font_path_bold, 36)
    font_sub = ImageFont.truetype(font_path_reg, 20)
    font_card_title = ImageFont.truetype(font_path_bold, 24)
    font_card_sub = ImageFont.truetype(font_path_bold, 18)
    font_body = ImageFont.truetype(font_path_reg, 16)
    font_metric = ImageFont.truetype(font_path_bold, 21)
    font_badge = ImageFont.truetype(font_path_bold, 15)

    # Top Banner Header
    draw.rectangle([0, 0, w, 120], fill="#1E3A8A")
    draw.rectangle([0, 114, w, 120], fill="#38BDF8")
    
    # Left accent rounded pill (pure shape)
    draw.rounded_rectangle([75, 34, 83, 72], radius=4, fill="#38BDF8")
    draw.text((105, 28), "AI 智慧資材管理與數位轉型計畫", fill="#FFFFFF", font=font_title)
    draw.text((105, 78), "串接現有 ERP / PWA 數位基礎 ─ 以 AI 解決儲位與包材過渡期瓶頸 ─ 守住「零客訴」與「零工安」", fill="#93C5FD", font=font_sub)

    # 3 Main Pillars
    card_w = 540
    card_h = 580
    card_y = 150
    spacing = 50
    start_x = 75

    pillars = [
        {
            "num": "01",
            "title": "AI 智慧倉儲調度",
            "tag": "儲位優化 / 預算周轉",
            "color": "#2563EB",
            "bg": "#EFF6FF",
            "border": "#3B82F6",
            "pain": "痛點：2027 儲位缺口 (-187板)、帳篷管理不易、跨廠調度繁複",
            "solutions": [
                "跨廠儲位 PWA 導入 AI 周轉優化演算法",
                "批號自動過濾與化學品效期即時預警",
                "3D 數位孿生儲位看板動態指引"
            ],
            "metric1": "儲位周轉率提升 15%+",
            "metric2": "盤點工時大幅減少 60%"
        },
        {
            "num": "02",
            "title": "AI 視覺 OCR 與防呆",
            "tag": "零出錯 / 四重防呆",
            "color": "#D97706",
            "bg": "#FFFBEB",
            "border": "#F59E0B",
            "pain": "痛點：業務量快速成長，人工核對三合一單/COA 負荷沉重",
            "solutions": [
                "Vision AI 自動辨識槽車三合一單與 COA 數值",
                "串接 T100 ERP、QC 看板自動入庫校驗",
                "條碼與軟管對刷防呆，即時攔截錯裝"
            ],
            "metric1": "核單建檔省時 70%",
            "metric2": "達成 100% 零客訴標準"
        },
        {
            "num": "03",
            "title": "AI 數位教材與新人培訓",
            "tag": "語音SOP / 零工安",
            "color": "#059669",
            "bg": "#F0FDF4",
            "border": "#10B981",
            "pain": "痛點：2027 Q3 三廠擴建招募，資材新進人員安全培訓高壓",
            "solutions": [
                "AI 語音 (TTS) 與 3D 動畫建立氮封/卸料 SOP 教材",
                "互動式模擬演練與線上即時測驗",
                "數位化標準傳承，降低老帶新負擔"
            ],
            "metric1": "新人培訓工時節省 40%",
            "metric2": "SOP 測驗合格率 100%"
        }
    ]

    for i, p in enumerate(pillars):
        cx = start_x + i * (card_w + spacing)
        # Card Background
        draw.rounded_rectangle([cx, card_y, cx + card_w, card_y + card_h], radius=18, fill=p["bg"], outline=p["border"], width=3)
        
        # Tag Badge
        draw.rounded_rectangle([cx + 25, card_y + 25, cx + 180, card_y + 60], radius=10, fill=p["color"])
        draw.text((cx + 36, card_y + 32), p["tag"], fill="#FFFFFF", font=font_badge)

        # Large Modern Number watermark on top right
        draw.text((cx + card_w - 75, card_y + 20), p["num"], fill=p["color"], font=font_title)

        # Title
        draw.text((cx + 25, card_y + 75), p["title"], fill="#0F172A", font=font_card_title)
        
        # Divider line
        draw.line([cx + 25, card_y + 120, cx + card_w - 25, card_y + 120], fill="#CBD5E1", width=2)

        # Pain point block
        draw.rounded_rectangle([cx + 25, card_y + 135, cx + card_w - 25, card_y + 205], radius=10, fill="#FFFFFF", outline="#E2E8F0", width=1)
        draw.rounded_rectangle([cx + 35, card_y + 148, cx + 41, card_y + 168], radius=3, fill="#DC2626")
        draw.text((cx + 50, card_y + 146), "面對挑戰：", fill="#DC2626", font=font_card_sub)
        draw.text((cx + 38, card_y + 175), p["pain"], fill="#475569", font=font_body)

        # Solution block
        draw.rounded_rectangle([cx + 25, card_y + 220, cx + card_w - 25, card_y + 400], radius=10, fill="#FFFFFF", outline="#E2E8F0", width=1)
        draw.rounded_rectangle([cx + 35, card_y + 236, cx + 41, card_y + 256], radius=3, fill=p["color"])
        draw.text((cx + 50, card_y + 234), "具體 AI 導入方案：", fill=p["color"], font=font_card_sub)
        
        # Draw bullets as clean tiny squares
        for s_idx, sol_text in enumerate(p["solutions"]):
            sy = card_y + 270 + s_idx * 38
            draw.rectangle([cx + 38, sy + 6, cx + 44, sy + 12], fill=p["color"])
            draw.text((cx + 54, sy), sol_text, fill="#1E293B", font=font_body)

        # Metric Result Pill
        draw.rounded_rectangle([cx + 25, card_y + 420, cx + card_w - 25, card_y + 550], radius=14, fill=p["color"])
        draw.text((cx + 40, card_y + 435), "預期量化成效：", fill="#FFFFFF", font=font_card_sub)
        
        # Custom drawn circle bullets
        draw.ellipse([cx + 42, card_y + 478, cx + 52, card_y + 488], fill="#FFFFFF")
        draw.text((cx + 64, card_y + 470), p["metric1"], fill="#FFFFFF", font=font_metric)

        draw.ellipse([cx + 42, card_y + 514, cx + 52, card_y + 524], fill="#FFFFFF")
        draw.text((cx + 64, card_y + 506), p["metric2"], fill="#FFFFFF", font=font_metric)

    # Bottom 4-Quarter Milestones Roadmap (2027 Q1 ~ Q4)
    rm_y = 760
    rm_h = 280
    draw.rounded_rectangle([start_x, rm_y, start_x + 3 * card_w + 2 * spacing, rm_y + rm_h], radius=18, fill="#FFFFFF", outline="#CBD5E1", width=2)

    # Roadmap Header
    draw.rounded_rectangle([start_x + 30, rm_y + 22, start_x + 36, rm_y + 46], radius=3, fill="#2563EB")
    draw.text((start_x + 48, rm_y + 20), "2027 全年度 AI 落地執行藍圖 (Roadmap)", fill="#0F172A", font=font_card_title)

    quarter_w = 405
    q_spacing = 20
    q_start_x = start_x + 30
    q_y = rm_y + 70
    q_h = 180

    quarters = [
        {
            "q": "2027 Q1",
            "title": "跨廠儲位與包材預警",
            "desc": "配合辦公室改造，上線跨廠儲位 PWA、AI 周轉優化與包材安全水位預警，化解儲位缺口。",
            "bg": "#EFF6FF",
            "accent": "#2563EB"
        },
        {
            "q": "2027 Q2",
            "title": "AI OCR 與四重防呆",
            "desc": "全面啟用三合一單/COA Vision AI 讀單，串接 T100 ERP、QC 看板與條碼對刷，守住零客訴。",
            "bg": "#FFFBEB",
            "accent": "#D97706"
        },
        {
            "q": "2027 Q3",
            "title": "三廠 AI 語音 SOP 培訓",
            "desc": "配合彰濱三廠招募訓練，全面導入 AI 語音互動教材、模擬演練與線上測驗，守住零工安。",
            "bg": "#F0FDF4",
            "accent": "#059669"
        },
        {
            "q": "2027 Q4",
            "title": "L02-1 智慧危倉合規啟用",
            "desc": "新危倉 (1,776儲位) 導入 3D 儲位看板與全流程條碼防呆，實現跨廠智慧調度，迎向 2028 放量！",
            "bg": "#FAF5FF",
            "accent": "#7C3AED"
        }
    ]

    for j, q in enumerate(quarters):
        qx = q_start_x + j * (quarter_w + q_spacing)
        draw.rounded_rectangle([qx, q_y, qx + quarter_w, q_y + q_h], radius=14, fill=q["bg"], outline=q["accent"], width=2)
        # Quarter Pill
        draw.rounded_rectangle([qx + 15, q_y + 15, qx + 110, q_y + 45], radius=8, fill=q["accent"])
        draw.text((qx + 24, q_y + 20), q["q"], fill="#FFFFFF", font=font_badge)
        
        draw.text((qx + 125, q_y + 18), q["title"], fill="#0F172A", font=font_card_sub)
        
        # Desc (clean wrapping)
        line1 = q["desc"][:24]
        line2 = q["desc"][24:48]
        line3 = q["desc"][48:]
        full_text = line1 + "\n" + line2 + ("\n" + line3 if line3 else "")
        draw.text((qx + 15, q_y + 60), full_text, fill="#475569", font=font_body)

    out_file = os.path.abspath("AI智慧資材轉型計畫_卡通圖解簡報.png")
    if os.path.exists(out_file):
        try:
            os.remove(out_file)
        except:
            pass
    img.save(out_file, quality=95)
    print(f"Ultra Clean Infographic saved at: {out_file}")

if __name__ == "__main__":
    render_ultra_clean_infographic()
