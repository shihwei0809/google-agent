import os
from PIL import Image, ImageDraw

base_dir = r'C:\GOOGLE ANGET\三合一單自動產生器'

def take_screenshots():
    if not os.path.exists(os.path.join(base_dir, 'ui_screenshot.png')):
        print("ui_screenshot.png not found!")
        return {}

    cached_img = Image.open(os.path.join(base_dir, 'ui_screenshot.png'))
    paths = {}
    
    def create_crop(step, crop_box, red_box):
        img = cached_img.crop(crop_box).copy()
        draw = ImageDraw.Draw(img)
        # red_box is [x1, y1, x2, y2] relative to full image
        rel_box = [
            red_box[0] - crop_box[0],
            red_box[1] - crop_box[1],
            red_box[2] - crop_box[0],
            red_box[3] - crop_box[1]
        ]
        draw.rectangle(rel_box, outline="red", width=4)
        p = os.path.join(base_dir, f'{step}.png')
        img.save(p)
        paths[step] = p

    # Step 1: 重新載入對照表 X=366, Y=64, W=127, H=25
    create_crop('step1', (15, 15, 600, 150), (366, 64, 366+127, 64+25))

    # Step 2: Row 1 批號 Entry X=116, Y=255, W=130, H=20
    create_crop('step2', (15, 200, 900, 350), (116, 255, 116+130, 255+20))

    # Step 3: 清除全部資料 X=489, Y=108, W=77, H=26
    create_crop('step3', (300, 50, 800, 200), (489, 108, 489+77, 108+26))

    # Step 4: 從 Excel 匯入 X=1000, Y=107, W=135, H=28
    create_crop('step4', (700, 50, 1150, 200), (1000, 107, 1000+135, 107+28))

    # Step 5: 載入既有運輸通知表修訂 X=748, Y=107, W=242, H=28
    create_crop('step5', (500, 50, 1150, 200), (748, 107, 748+242, 107+28))

    # Step 6: 開始批次產生 X=15, Y=678, W=1120, H=47
    create_crop('step6', (15, 550, 1135, 740), (15, 678, 15+1120, 678+47))
    
    return paths

if __name__ == '__main__':
    take_screenshots()
