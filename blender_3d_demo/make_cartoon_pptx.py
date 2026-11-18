import os
from pptx import Presentation
from pptx.util import Inches

def build_cartoon_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    
    # Slide 1: 3D Pixar Cartoon Hero Scene
    slide1 = prs.slides.add_slide(blank_layout)
    img_hero = os.path.abspath("C:/Users/C606/.gemini/antigravity/brain/2b21732f-da0b-485d-a7e8-f521af99bf45/ai_smart_warehouse_hero_1794980357003.jpg")
    slide1.shapes.add_picture(img_hero, Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

    # Slide 2: Full Infographic Cartoon Poster
    slide2 = prs.slides.add_slide(blank_layout)
    img_info = os.path.abspath("AI智慧資材轉型計畫_卡通圖解簡報.png")
    slide2.shapes.add_picture(img_info, Inches(0), Inches(0), width=Inches(13.333), height=Inches(7.5))

    out_pptx = os.path.abspath("AI智慧資材轉型計畫_卡通簡報.pptx")
    prs.save(out_pptx)
    print(f"PPTX with cartoon slides created: {out_pptx}")

if __name__ == "__main__":
    build_cartoon_pptx()
