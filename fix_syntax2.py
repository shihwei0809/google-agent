import re
with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'r', encoding='utf-8') as f:
    c = f.read()

# Fix the rotationTransform block
block = '''const rotationTransform = rotateMode === '90' 
      ? 	ransform: rotate(90deg) translateY(-100%); transform-origin: top left; 
      : rotateMode === '-90'
      ? 	ransform: rotate(-90deg) translateX(-100%); transform-origin: top left;
      : rotateMode === '180'
      ? 	ransform: rotate(180deg); transform-origin: center center;
      : autoRotate
      ? 	ransform: rotate(90deg) translateY(-100%); transform-origin: top left;
      : '';'''

c = re.sub(r'const rotationTransform = rotateMode === \'90\'.*?: \'\';', block, c, flags=re.DOTALL)

with open(r'd:\GOOGLE ANGET\第二類_生產管理與API串接\QC-系統客製化電子化工廠\3_Cloudflare_D1版\index.html', 'w', encoding='utf-8') as f:
    f.write(c)
